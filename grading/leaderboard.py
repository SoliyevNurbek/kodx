"""Reyting jadvallari: umumiy, haftalik, guruh va kurs bo'yicha."""

from collections import defaultdict
from datetime import timedelta

from django.db.models import F, Min
from django.utils import timezone

from accounts.models import User
from courses.models import Course, Group, GroupMember
from judge.types import Verdict
from problems.models import Problem
from submissions.models import ProjectSubmission, QuizAttempt, Submission

from .models import PracticeStats
from .rating import competition_ranks


def _rank_rows(scores: dict[int, int], solved: dict[int, int] | None = None, limit: int | None = None) -> list[dict]:
    users = User.objects.in_bulk(list(scores))
    ranked = competition_ranks([(uid, (-score, users[uid].username)) for uid, score in scores.items()
                                if uid in users])
    # Teng ball — bir xil o'rin (ismga qaramasdan): o'rinni faqat ball bo'yicha qayta hisoblaymiz
    rows, place, previous = [], 0, None
    for index, (uid, _) in enumerate(ranked, start=1):
        if scores[uid] != previous:
            place, previous = index, scores[uid]
        rows.append({"place": place, "user": users[uid], "score": scores[uid],
                     "solved": (solved or {}).get(uid, 0)})
    return rows[:limit] if limit else rows


def overall(limit: int | None = None, user_ids: list[int] | None = None) -> list[dict]:
    """Mashq bali bo'yicha (PracticeStats)."""
    stats = PracticeStats.objects.filter(user__is_active=True, score__gt=0)
    if user_ids is not None:
        stats = stats.filter(user_id__in=user_ids)
    data = list(stats.values_list("user_id", "score", "solved_count"))
    return _rank_rows({u: s for u, s, _ in data}, {u: c for u, _, c in data}, limit)


def weekly(days: int = 7, limit: int | None = None) -> list[dict]:
    """So'nggi `days` kunda BIRINCHI marta yechilgan vazifalar ballari."""
    since = timezone.now() - timedelta(days=days)
    firsts: dict[tuple[int, int], object] = {}
    sources = [
        Submission.objects.filter(verdict=Verdict.ACCEPTED),
        QuizAttempt.objects.filter(max_score__gt=0, score=F("max_score")),
        ProjectSubmission.objects.filter(status=ProjectSubmission.Status.GRADED),
    ]
    for queryset in sources:
        for row in queryset.filter(user__is_active=True).values("user_id", "problem_id").annotate(
                first=Min("created_at")):
            key = (row["user_id"], row["problem_id"])
            if key not in firsts or row["first"] < firsts[key]:
                firsts[key] = row["first"]
    points = dict(Problem.objects.values_list("pk", "points"))
    scores: dict[int, int] = defaultdict(int)
    solved: dict[int, int] = defaultdict(int)
    for (user_id, problem_id), first in firsts.items():
        if first >= since:
            scores[user_id] += points.get(problem_id, 0)
            solved[user_id] += 1
    return _rank_rows(dict(scores), dict(solved), limit)


def by_group(group: Group, limit: int | None = None) -> list[dict]:
    ids = list(GroupMember.objects.filter(group=group, is_active=True).values_list("user_id", flat=True))
    return overall(limit, user_ids=ids)


def by_course(course: Course, limit: int | None = None) -> list[dict]:
    ids = list(GroupMember.objects.filter(group__course=course, is_active=True).values_list("user_id", flat=True))
    return overall(limit, user_ids=ids)


def find_place(rows: list[dict], user) -> dict | None:
    """Foydalanuvchining jadvaldagi qatori (o'z o'rnini ko'rishi uchun)."""
    if not (user and user.is_authenticated):
        return None
    return next((row for row in rows if row["user"].pk == user.pk), None)
