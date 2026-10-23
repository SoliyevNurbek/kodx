"""Foydalanuvchi statistikasi: yechilgan vazifalar, faollik kalendari, top ro'yxat."""

from collections import Counter
from datetime import date, timedelta

from django.core.cache import cache
from django.db.models import Count, F, Q
from django.utils import timezone

from judge.types import Verdict

from .models import ProjectSubmission, QuizAttempt, Submission


def solved_ids(user) -> set[int]:
    """Foydalanuvchi yechgan vazifalar ID lari (code — AC, quiz — 100%, loyiha — baholangan)."""
    if not (user and user.is_authenticated):
        return set()
    ids = set(Submission.objects.filter(user=user, verdict=Verdict.ACCEPTED).values_list("problem_id", flat=True))
    ids |= set(QuizAttempt.objects.filter(user=user, max_score__gt=0, score=F("max_score"))
               .values_list("problem_id", flat=True))
    ids |= set(ProjectSubmission.objects.filter(user=user, status=ProjectSubmission.Status.GRADED)
               .values_list("problem_id", flat=True))
    return ids


def attempted_ids(user) -> set[int]:
    """Foydalanuvchi urinib ko'rgan barcha vazifalar."""
    if not (user and user.is_authenticated):
        return set()
    ids = set(Submission.objects.filter(user=user).values_list("problem_id", flat=True))
    ids |= set(QuizAttempt.objects.filter(user=user).values_list("problem_id", flat=True))
    ids |= set(ProjectSubmission.objects.filter(user=user).values_list("problem_id", flat=True))
    return ids


def problem_status(problem_id: int, solved: set[int], attempted: set[int]) -> str:
    """'solved' / 'attempted' / 'new'."""
    if problem_id in solved:
        return "solved"
    if problem_id in attempted:
        return "attempted"
    return "new"


def activity_calendar(user, days: int = 182) -> list[list[dict]]:
    """
    So'nggi `days` kun faolligi haftalarga bo'lingan holda (GitHub uslubida).

    Sana mahalliy vaqt bo'yicha Python'da hisoblanadi (MySQL vaqt zonasi jadvallariga bog'liq emas).
    """
    today = timezone.localdate()
    start = today - timedelta(days=days - 1)
    start -= timedelta(days=start.weekday())  # dushanbadan boshlash
    since = timezone.make_aware(timezone.datetime.combine(start, timezone.datetime.min.time()))
    counts: Counter[date] = Counter()
    for model in (Submission, QuizAttempt, ProjectSubmission):
        for created in model.objects.filter(user=user, created_at__gte=since).values_list("created_at", flat=True):
            counts[timezone.localtime(created).date()] += 1
    weeks: list[list[dict]] = []
    day = start
    while day <= today:
        week = []
        for _ in range(7):
            if day <= today:
                n = counts.get(day, 0)
                level = 0 if n == 0 else 1 if n < 3 else 2 if n < 6 else 3
                week.append({"date": day, "count": n, "level": level})
            day += timedelta(days=1)
        weeks.append(week)
    return weeks


def top_solvers(limit: int = 10) -> list[dict]:
    """Eng ko'p code masala yechganlar (6-bosqichda mashq reytingi bilan almashtiriladi)."""
    rows = (Submission.objects.filter(verdict=Verdict.ACCEPTED, user__is_active=True)
            .values("user__username").annotate(solved=Count("problem", distinct=True))
            .order_by("-solved", "user__username")[:limit])
    return [{"username": r["user__username"], "solved": r["solved"], "points": r["solved"]} for r in rows]


SITE_COUNTERS_CACHE_KEY = "kodx:site_counters"
SITE_COUNTERS_TTL = 600  # 10 daqiqa


def site_counters() -> dict[str, int]:
    """
    Bosh sahifa statistikasi (10 daqiqa keshlanadi).

    seed_demo akkauntlari (`is_seed`) va ularning yechimlari hisobga olinmaydi; vazifalar — faqat nashr etilganlar.
    """
    from accounts.models import User
    from problems.models import Problem

    counters = cache.get(SITE_COUNTERS_CACHE_KEY)
    if counters is None:
        real = Submission.objects.filter(user__is_seed=False)
        counters = {
            "users": User.objects.filter(is_active=True, is_seed=False).count(),
            "problems": Problem.objects.filter(status=Problem.Status.PUBLISHED).count(),
            "submissions": real.count(),
            "accepted": real.filter(verdict=Verdict.ACCEPTED).count(),
        }
        cache.set(SITE_COUNTERS_CACHE_KEY, counters, SITE_COUNTERS_TTL)
    return counters


def solved_count_by_user(user_ids: list[int]) -> dict[int, int]:
    """Bir nechta foydalanuvchi uchun yechilgan code masalalar soni."""
    rows = (Submission.objects.filter(user_id__in=user_ids).values("user_id")
            .annotate(n=Count("problem", distinct=True, filter=Q(verdict=Verdict.ACCEPTED))))
    return {r["user_id"]: r["n"] for r in rows}


def solved_map(user_ids: list[int]) -> dict[int, set[int]]:
    """{user_id: yechilgan vazifalar ID lari} — bir nechta foydalanuvchi uchun 3 ta so'rov bilan."""
    result: dict[int, set[int]] = {uid: set() for uid in user_ids}
    pairs = list(Submission.objects.filter(user_id__in=user_ids, verdict=Verdict.ACCEPTED)
                 .values_list("user_id", "problem_id").distinct())
    pairs += list(QuizAttempt.objects.filter(user_id__in=user_ids, max_score__gt=0, score=F("max_score"))
                  .values_list("user_id", "problem_id").distinct())
    pairs += list(ProjectSubmission.objects.filter(user_id__in=user_ids, status=ProjectSubmission.Status.GRADED)
                  .values_list("user_id", "problem_id").distinct())
    for user_id, problem_id in pairs:
        result[user_id].add(problem_id)
    return result
