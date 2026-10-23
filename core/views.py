"""Bosh sahifa va reyting jadvallari."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse

from courses.models import Course, Group, Lesson
from grading import leaderboard as boards
from submissions.stats import site_counters

from .models import SiteSettings

TABS = (("overall", "Umumiy"), ("weekly", "Haftalik"), ("group", "Guruh"), ("course", "Kurs"))


STAT_LABELS = (("users", "o‘quvchilar"), ("problems", "vazifalar"), ("submissions", "yechimlar"),
               ("accepted", "qabul qilingan"))


def hero_links(request: HttpRequest, course: Course | None) -> dict[str, str]:
    """
    Hero tugmalari manzillari.

    «Kursni boshlash»: mehmon → ro'yxatdan o'tish (yopiq bo'lsa — kirish), kirgan → kurs sahifasi.
    «1-dars BEPUL!» — kursning 1-darsi (bo'lmasa belgi ko'rsatilmaydi).
    """
    if not request.user.is_authenticated:
        start = reverse("register") if SiteSettings.load().registration_enabled else reverse("login")
    elif course is not None:
        start = reverse("course_detail", args=[course.slug])
    else:
        start = reverse("problem_list")
    first = course and Lesson.objects.filter(module__course=course, number=1).exists()
    return {
        "start": start,
        "problems": reverse("problem_list"),
        "lesson1": reverse("lesson_detail", args=[course.slug, 1]) if first else "",
    }


def home(request: HttpRequest) -> HttpResponse:
    """Bosh sahifa: hero (CTA, statistika), kurs modullari, top-10."""
    course = Course.objects.filter(is_active=True).prefetch_related("modules__lessons").first()
    top = [{"username": r["user"].username, "points": r["score"]} for r in boards.overall(limit=10)]
    counters = site_counters()
    stats = [{"key": key, "label": label, "value": counters[key]} for key, label in STAT_LABELS]
    return render(request, "core/home.html", {
        "course": course, "stats": stats, "top": top, "hero": hero_links(request, course),
    })


def leaderboard(request: HttpRequest) -> HttpResponse:
    """Reyting jadvallari: umumiy, haftalik, guruh va kurs bo'yicha; foydalanuvchi o'z o'rnini ko'radi."""
    tab = request.GET.get("tab", "overall")
    groups = Group.objects.filter(is_active=True).order_by("name")
    courses = Course.objects.filter(is_active=True)
    selected = request.GET.get("id", "")
    if tab == "weekly":
        rows = boards.weekly()
    elif tab == "group":
        group = groups.filter(pk=selected).first() if selected.isdigit() else None
        if group is None and request.user.is_authenticated:
            group = groups.filter(members__user=request.user, members__is_active=True).first()
        group = group or groups.first()
        selected = str(group.pk) if group else ""
        rows = boards.by_group(group) if group else []
    elif tab == "course":
        course = courses.filter(pk=selected).first() if selected.isdigit() else courses.first()
        selected = str(course.pk) if course else ""
        rows = boards.by_course(course) if course else []
    else:
        tab = "overall"
        rows = boards.overall()
    return render(request, "core/leaderboard.html", {
        "tab": tab, "tabs": TABS, "rows": rows[:200], "me": boards.find_place(rows, request.user),
        "groups": groups, "courses": courses, "selected": selected,
    })
