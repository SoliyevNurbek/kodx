"""Kurs, modul va dars sahifalari."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from problems.models import LessonProblem, Problem
from submissions.stats import attempted_ids, problem_status, solved_ids

from .models import Course, Lesson


def course_detail(request: HttpRequest, slug: str) -> HttpResponse:
    """Kurs: modullar va darslar, har dars bo'yicha yechilgan vazifalar ulushi."""
    course = get_object_or_404(Course, slug=slug, is_active=True)
    modules = course.modules.prefetch_related("lessons")
    solved = solved_ids(request.user)
    progress: dict[int, tuple[int, int]] = {}
    links = (LessonProblem.objects.filter(lesson__module__course=course, problem__status=Problem.Status.PUBLISHED)
             .values_list("lesson_id", "problem_id"))
    for lesson_id, problem_id in links:
        done, total = progress.get(lesson_id, (0, 0))
        progress[lesson_id] = (done + (problem_id in solved), total + 1)
    return render(request, "courses/course_detail.html",
                  {"course": course, "modules": modules, "progress": progress})


def lesson_detail(request: HttpRequest, slug: str, number: int) -> HttpResponse:
    """Dars: vazifalar ro'yxati, holati (yechilgan / urinilgan / yangi) va muddatlari."""
    lesson = get_object_or_404(Lesson.objects.select_related("module__course"),
                               module__course__slug=slug, number=number)
    links = (lesson.lesson_problems.filter(problem__status=Problem.Status.PUBLISHED)
             .select_related("problem").order_by("problem__type", "order"))
    solved, attempted = solved_ids(request.user), attempted_ids(request.user)
    rows = [{"link": link, "problem": link.problem,
             "status": problem_status(link.problem_id, solved, attempted)} for link in links]
    siblings = Lesson.objects.filter(module__course=lesson.module.course)
    return render(request, "courses/lesson_detail.html", {
        "lesson": lesson, "rows": rows,
        "prev": siblings.filter(number=number - 1).first(),
        "next": siblings.filter(number=number + 1).first(),
    })
