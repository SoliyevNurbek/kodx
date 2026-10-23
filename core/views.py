"""Bosh sahifa va reyting jadvallari."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from courses.models import Course, Group
from grading import leaderboard as boards
from submissions.stats import site_counters

TABS = (("overall", "Umumiy"), ("weekly", "Haftalik"), ("group", "Guruh"), ("course", "Kurs"))


def home(request: HttpRequest) -> HttpResponse:
    """Bosh sahifa: kurs, modullar, statistika, top-10."""
    course = Course.objects.filter(is_active=True).prefetch_related("modules__lessons").first()
    top = [{"username": r["user"].username, "points": r["score"]} for r in boards.overall(limit=10)]
    return render(request, "core/home.html", {"course": course, "counters": site_counters(), "top": top})


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
