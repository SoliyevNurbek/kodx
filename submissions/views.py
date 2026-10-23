"""Urinishlar sahifalari: «Mening urinishlarim», urinish tafsiloti va jonli holat (HTMX)."""

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from judge.types import Verdict

from .models import Submission


@login_required
def my_submissions(request: HttpRequest) -> HttpResponse:
    submissions = Submission.objects.filter(user=request.user).select_related("problem")
    verdict = request.GET.get("verdict", "")
    if verdict in Verdict.values:
        submissions = submissions.filter(verdict=verdict)
    page = Paginator(submissions, 30).get_page(request.GET.get("page"))
    return render(request, "submissions/my_submissions.html",
                  {"page": page, "verdicts": Verdict.choices, "verdict": verdict})


def _submission_context(request: HttpRequest, submission: Submission) -> dict:
    user = request.user
    is_staff_view = user.is_authenticated and user.is_moderator
    is_owner = user.is_authenticated and user.pk == submission.user_id
    results = list(submission.results.select_related("test_case"))
    for result in results:
        is_sample = bool(result.test_case and result.test_case.is_sample)
        # Yopiq testlar chiqishi/xatosi o'quvchiga ko'rsatilmaydi (testni «sizdirmaslik» uchun)
        result.show_details = is_staff_view or (is_owner and is_sample)
    return {
        "submission": submission,
        "results": results,
        "show_code": submission.can_view_code(user),
        "show_compile": is_owner or is_staff_view,
    }


def submission_detail(request: HttpRequest, pk: int) -> HttpResponse:
    submission = get_object_or_404(Submission.objects.select_related("problem", "user"), pk=pk)
    if not submission.can_view(request.user):
        raise PermissionDenied
    return render(request, "submissions/submission_detail.html", _submission_context(request, submission))


def submission_status(request: HttpRequest, pk: int) -> HttpResponse:
    """HTMX polling uchun qisman shablon: tugamaguncha har 2 soniyada yangilanadi."""
    submission = get_object_or_404(Submission.objects.select_related("problem", "user"), pk=pk)
    if not submission.can_view(request.user):
        raise PermissionDenied
    return render(request, "submissions/_status.html", _submission_context(request, submission))
