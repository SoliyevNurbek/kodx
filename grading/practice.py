"""
Mashq reytingi: yechilgan vazifalar ballari yig'indisi, kunlik seriya (streak) va nishonlar.

Statistika `PracticeStats` da saqlanadi va har yangi yechimdan keyin `refresh_practice_stats` bilan
yangilanadi (judge, quiz va loyiha baholash servislari chaqiradi).
"""

from datetime import date, datetime, timedelta

from django.db.models import F, Min
from django.utils import timezone

from judge.types import Verdict
from problems.models import LessonProblem, Problem
from submissions.models import ProjectSubmission, QuizAttempt, Submission

from .models import Badge, PracticeStats, UserBadge


def first_solve_times(user) -> dict[int, datetime]:
    """{problem_id: birinchi muvaffaqiyatli topshiriq vaqti}."""
    times: dict[int, datetime] = {}
    sources = [
        Submission.objects.filter(user=user, verdict=Verdict.ACCEPTED),
        QuizAttempt.objects.filter(user=user, max_score__gt=0, score=F("max_score")),
        ProjectSubmission.objects.filter(user=user, status=ProjectSubmission.Status.GRADED),
    ]
    for queryset in sources:
        for row in queryset.values("problem_id").annotate(first=Min("created_at")):
            current = times.get(row["problem_id"])
            if current is None or row["first"] < current:
                times[row["problem_id"]] = row["first"]
    return times


def streaks(days: set[date], today: date) -> tuple[int, int]:
    """
    (joriy seriya, eng uzun seriya). Joriy seriya bugun yoki kecha tugagan ketma-ket kunlar
    (bugun hali yechmagan o'quvchi seriyasini yo'qotmaydi).
    """
    if not days:
        return 0, 0
    best = run = 0
    previous: date | None = None
    for day in sorted(days):
        run = run + 1 if previous is not None and day - previous == timedelta(days=1) else 1
        best = max(best, run)
        previous = day
    current = 0
    cursor = today if today in days else today - timedelta(days=1)
    while cursor in days:
        current += 1
        cursor -= timedelta(days=1)
    return current, best


# (kod, nomi, tavsif, belgi) — tartib bo'yicha; seed migratsiya ham shu ro'yxatdan foydalanadi
BADGES = [
    ("first-solve", "Birinchi qadam", "Birinchi vazifani yechdi", "🌱"),
    ("solved-10", "O‘nlik", "10 ta vazifa yechdi", "🔟"),
    ("solved-50", "Ellik", "50 ta vazifa yechdi", "🚀"),
    ("solved-100", "Yuzlik", "100 ta vazifa yechdi", "💯"),
    ("streak-7", "Bir hafta", "7 kun ketma-ket vazifa yechdi", "🔥"),
    ("streak-30", "Bir oy", "30 kun ketma-ket vazifa yechdi", "🌋"),
    ("challenge-5", "Challenge ustasi", "5 ta qo‘shimcha (challenge) masalani yechdi", "🧗"),
    ("project-first", "Loyihachi", "Birinchi loyihasi baholandi", "🛠️"),
    ("module-1", "Modul 1 yakunlandi", "1-modulning barcha majburiy vazifalarini bajardi", "1️⃣"),
    ("module-2", "Modul 2 yakunlandi", "2-modulning barcha majburiy vazifalarini bajardi", "2️⃣"),
    ("module-3", "Modul 3 yakunlandi", "3-modulning barcha majburiy vazifalarini bajardi", "3️⃣"),
    ("module-4", "Modul 4 yakunlandi", "4-modulning barcha majburiy vazifalarini bajardi", "4️⃣"),
]


def earned_badges(user, solved: set[int], current_streak: int, best_streak: int) -> set[str]:
    """Foydalanuvchi qozongan nishonlar kodlari."""
    codes: set[str] = set()
    for threshold, code in ((1, "first-solve"), (10, "solved-10"), (50, "solved-50"), (100, "solved-100")):
        if len(solved) >= threshold:
            codes.add(code)
    for threshold, code in ((7, "streak-7"), (30, "streak-30")):
        if best_streak >= threshold:
            codes.add(code)
    challenges = set(LessonProblem.objects.filter(kind=LessonProblem.Kind.CHALLENGE).values_list("problem_id",
                                                                                               flat=True))
    if len(challenges & solved) >= 5:
        codes.add("challenge-5")
    if Problem.objects.filter(pk__in=solved, type=Problem.Type.PROJECT).exists():
        codes.add("project-first")
    required: dict[int, set[int]] = {}
    for module_number, problem_id in LessonProblem.objects.filter(
            is_required=True, problem__status=Problem.Status.PUBLISHED
    ).values_list("lesson__module__number", "problem_id"):
        required.setdefault(module_number, set()).add(problem_id)
    for module_number, problems in required.items():
        if problems and problems <= solved and module_number <= 4:
            codes.add(f"module-{module_number}")
    return codes


def refresh_practice_stats(user) -> PracticeStats:
    """Foydalanuvchi mashq statistikasini qayta hisoblaydi va yangi nishonlarni beradi."""
    times = first_solve_times(user)
    points = dict(Problem.objects.filter(pk__in=times).values_list("pk", "points"))
    days = {timezone.localtime(moment).date() for moment in times.values()}
    current, best = streaks(days, timezone.localdate())
    stats, _ = PracticeStats.objects.get_or_create(user=user)
    stats.score = sum(points.values())
    stats.solved_count = len(times)
    stats.current_streak = current
    stats.best_streak = max(best, stats.best_streak)
    stats.last_solved_at = max(times.values()) if times else None
    stats.save()

    codes = earned_badges(user, set(times), current, stats.best_streak)
    have = set(UserBadge.objects.filter(user=user).values_list("badge__code", flat=True))
    new = Badge.objects.filter(code__in=codes - have)
    UserBadge.objects.bulk_create([UserBadge(user=user, badge=badge) for badge in new], ignore_conflicts=True)
    return stats
