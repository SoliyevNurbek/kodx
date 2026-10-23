"""Kontest servislari: ro'yxatdan o'tish, natijalar jadvali (ICPC/IOI, muzlatish) va reyting hisoblash."""

from dataclasses import dataclass, field
from datetime import datetime

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from audit.services import log_action
from grading.rating import Standing, competition_ranks, rating_changes
from judge.types import Verdict
from submissions.models import Submission

from .models import Contest, ContestParticipant, RatingHistory

# ICPC'da jarimaga sabab bo'lmaydigan verdiktlar
NO_PENALTY = {Verdict.COMPILATION_ERROR, Verdict.INTERNAL_ERROR}


def register(user, contest: Contest, password: str = "") -> ContestParticipant:
    """Kontestga ro'yxatdan o'tish (tugaguncha; parolli kontestda parol bilan)."""
    if not contest.can_register(user):
        raise PermissionDenied("Bu kontestda ro‘yxatdan o‘tib bo‘lmaydi.")
    if contest.visibility == Contest.Visibility.PASSWORD and not contest.can_manage(user) \
            and not contest.check_password(password):
        raise ValidationError("Parol noto‘g‘ri.")
    participant, _ = ContestParticipant.objects.get_or_create(contest=contest, user=user)
    return participant


@dataclass
class Cell:
    label: str
    solved: bool = False
    attempts: int = 0          # ICPC: AC dan oldingi noto'g'ri urinishlar
    time_minutes: int = 0      # ICPC: birinchi AC vaqti
    score: int = 0             # IOI: eng yaxshi ball
    pending: int = 0           # tekshirilmagan yoki muzlatilgan urinishlar
    first_solver: bool = False


@dataclass
class Row:
    user: object
    cells: dict[str, Cell] = field(default_factory=dict)
    rank: int = 0

    @property
    def solved(self) -> int:
        return sum(c.solved for c in self.cells.values())

    @property
    def penalty(self) -> int:
        return sum(c.time_minutes + c.attempts * self._penalty for c in self.cells.values() if c.solved)

    @property
    def score(self) -> int:
        return sum(c.score for c in self.cells.values())

    _penalty: int = 20


@dataclass
class Scoreboard:
    contest: Contest
    labels: list[str]
    rows: list[Row]
    frozen: bool


def scoreboard(contest: Contest, viewer=None, now: datetime | None = None) -> Scoreboard:
    """
    Natijalar jadvali. Muzlatish vaqtida (va kontest tugamaguncha) boshqaruvchi bo'lmaganlar
    faqat muzlatishgacha yuborilgan yechimlar natijasini ko'radi; keyingilari «kutilmoqda» deb ko'rsatiladi.
    """
    now = now or timezone.now()
    frozen = contest.is_frozen(now) and not contest.can_manage(viewer)
    links = list(contest.problems.select_related("problem"))
    by_problem = {link.problem_id: link for link in links}
    participants = list(contest.participants.select_related("user"))
    rows = {p.user_id: Row(user=p.user, cells={link.label: Cell(link.label) for link in links},
                           _penalty=contest.penalty_minutes) for p in participants}

    submissions = Submission.objects.filter(
        contest=contest, user_id__in=list(rows), created_at__gte=contest.start_at, created_at__lt=contest.end_at,
    ).order_by("created_at", "pk").values("user_id", "problem_id", "status", "verdict", "score", "created_at")
    first_ac: dict[str, tuple[datetime, int]] = {}
    for sub in submissions:
        link = by_problem.get(sub["problem_id"])
        if link is None:
            continue
        cell = rows[sub["user_id"]].cells[link.label]
        hidden = frozen and sub["created_at"] >= contest.freeze_at
        if hidden or sub["status"] != Submission.Status.DONE:
            if not cell.solved:
                cell.pending += 1
            continue
        if contest.scoring == Contest.Scoring.IOI:
            points = link.problem.points or 1
            cell.score = max(cell.score, round(link.points * sub["score"] / points))
            cell.solved = cell.solved or sub["verdict"] == Verdict.ACCEPTED
            continue
        if cell.solved:
            continue
        if sub["verdict"] == Verdict.ACCEPTED:
            cell.solved = True
            cell.time_minutes = int((sub["created_at"] - contest.start_at).total_seconds() // 60)
            if link.label not in first_ac or sub["created_at"] < first_ac[link.label][0]:
                first_ac[link.label] = (sub["created_at"], sub["user_id"])
        elif sub["verdict"] not in NO_PENALTY:
            cell.attempts += 1
    for label, (_, user_id) in first_ac.items():
        rows[user_id].cells[label].first_solver = True

    if contest.scoring == Contest.Scoring.IOI:
        keys = [(uid, (-row.score,)) for uid, row in rows.items()]
    else:
        keys = [(uid, (-row.solved, row.penalty)) for uid, row in rows.items()]
    ordered = []
    for uid, rank in competition_ranks(keys):
        rows[uid].rank = rank
        ordered.append(rows[uid])
    ordered.sort(key=lambda r: (r.rank, r.user.username))
    return Scoreboard(contest=contest, labels=[link.label for link in links], rows=ordered, frozen=frozen)


def apply_ratings(contest: Contest, actor=None) -> dict[int, int]:
    """
    Reytingli kontest tugagach reytinglarni yangilaydi (bir marta). Kamida bitta tekshirilgan yechim yuborgan
    ishtirokchilar hisobga olinadi. Navbatda tekshirilmagan yechim bo'lsa — kutadi (ValidationError).
    """
    if not contest.is_rated or contest.ratings_applied:
        return {}
    if not contest.is_finished:
        raise ValidationError("Kontest hali tugamagan.")
    if Submission.objects.filter(contest=contest).exclude(status=Submission.Status.DONE).exists():
        raise ValidationError("Barcha yechimlar hali tekshirilmagan.")
    board = scoreboard(contest)
    active = set(Submission.objects.filter(contest=contest).values_list("user_id", flat=True))
    rows = [row for row in board.rows if row.user.pk in active]
    standings = [Standing(row.user.pk, row.user.rating, row.rank) for row in rows]
    deltas = rating_changes(standings)
    with transaction.atomic():
        locked = Contest.objects.select_for_update().get(pk=contest.pk)
        if locked.ratings_applied:
            return {}
        for row in rows:
            user = row.user
            old = user.rating
            user.rating = old + deltas[user.pk]
            user.save(update_fields=["rating"])
            RatingHistory.objects.create(user=user, contest=contest, old_rating=old, new_rating=user.rating,
                                         rank=row.rank)
        locked.ratings_applied = True
        locked.save(update_fields=["ratings_applied"])
    contest.ratings_applied = True
    log_action(actor, "contest_ratings_applied", contest, {"participants": len(rows)})
    return deltas


def apply_due_ratings() -> int:
    """Tugagan, reytingli va hali hisoblanmagan kontestlar reytingini hisoblaydi (worker/cron chaqiradi)."""
    done = 0
    for contest in Contest.objects.filter(is_rated=True, ratings_applied=False, start_at__lte=timezone.now()):
        if not contest.is_finished:
            continue
        try:
            apply_ratings(contest)
        except ValidationError:
            continue
        done += 1
    return done
