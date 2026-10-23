"""Bosh sahifa va reyting."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from courses.models import Course
from submissions.stats import site_counters, top_solvers


def home(request: HttpRequest) -> HttpResponse:
    """Bosh sahifa: kurs, modullar, statistika, top-10."""
    course = Course.objects.filter(is_active=True).prefetch_related("modules__lessons").first()
    return render(request, "core/home.html", {
        "course": course,
        "counters": site_counters(),
        "top": top_solvers(10),
    })


def leaderboard(request: HttpRequest) -> HttpResponse:
    """Reyting jadvali (6-bosqichda kengaytiriladi)."""
    return render(request, "core/leaderboard.html", {"rows": top_solvers(100)})
