"""Kontest sahifalari: ro'yxat, kontest, masala, yechim yuborish va natijalar jadvali."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from judge.types import Language
from problems.markdown import render_markdown
from submissions.models import Submission
from submissions.services import SubmissionError, create_submission

from .models import Contest, ContestProblem
from .services import register, scoreboard


def _contest(request: HttpRequest, slug: str) -> Contest:
    contest = get_object_or_404(Contest.objects.select_related("owner", "group"), slug=slug)
    if not contest.can_view(request.user):
        raise Http404
    return contest


def contest_list(request: HttpRequest) -> HttpResponse:
    now = timezone.now()
    visible = [c for c in Contest.objects.select_related("group").order_by("-start_at") if c.can_view(request.user)]
    return render(request, "contests/contest_list.html", {
        "running": [c for c in visible if c.is_running(now)],
        "upcoming": sorted((c for c in visible if c.is_upcoming(now)), key=lambda c: c.start_at),
        "finished": [c for c in visible if c.is_finished][:30],
    })


def contest_detail(request: HttpRequest, slug: str) -> HttpResponse:
    contest = _contest(request, slug)
    show_problems = contest.can_see_problems(request.user)
    my_submissions = []
    if request.user.is_authenticated:
        my_submissions = Submission.objects.filter(contest=contest, user=request.user).select_related("problem")[:20]
    return render(request, "contests/contest_detail.html", {
        "contest": contest,
        "problems": contest.problems.select_related("problem") if show_problems else [],
        "show_problems": show_problems,
        "is_participant": contest.is_participant(request.user),
        "can_manage": contest.can_manage(request.user),
        "participants_count": contest.participants.count(),
        "my_submissions": my_submissions,
        "description_html": render_markdown(contest.description),
    })


@login_required
@require_POST
def contest_register(request: HttpRequest, slug: str) -> HttpResponse:
    contest = _contest(request, slug)
    try:
        register(request.user, contest, request.POST.get("password", ""))
    except (PermissionDenied, ValidationError) as exc:
        messages.error(request, "; ".join(getattr(exc, "messages", [str(exc)])))
    else:
        messages.success(request, "Siz kontestda ro‘yxatdan o‘tdingiz.")
    return redirect("contest_detail", slug=slug)


def contest_problem(request: HttpRequest, slug: str, label: str) -> HttpResponse:
    contest = _contest(request, slug)
    if not contest.can_see_problems(request.user):
        raise PermissionDenied("Masalalar kontest boshlangach faqat ishtirokchilarga ko‘rinadi.")
    link = get_object_or_404(ContestProblem.objects.select_related("problem"), contest=contest, label=label.upper())
    problem = link.problem
    return render(request, "contests/contest_problem.html", {
        "contest": contest, "link": link, "problem": problem,
        "statement_html": render_markdown(problem.statement),
        "samples": [{"input": tc.read_input(), "output": tc.read_output()}
                    for tc in problem.test_cases.filter(is_sample=True)],
        "languages": Language.choices,
        "can_submit": contest.is_running() and contest.is_participant(request.user),
        "labels": contest.problems.values_list("label", flat=True),
    })


@login_required
@require_POST
def contest_submit(request: HttpRequest, slug: str, label: str) -> HttpResponse:
    contest = _contest(request, slug)
    link = get_object_or_404(ContestProblem.objects.select_related("problem"), contest=contest, label=label.upper())
    try:
        submission = create_submission(request.user, link.problem, request.POST.get("code", ""),
                                       request.POST.get("language", Language.PYTHON3), contest=contest)
    except SubmissionError as exc:
        messages.error(request, exc.messages[0])
        return redirect("contest_problem", slug=slug, label=link.label)
    return redirect("submission_detail", pk=submission.pk)


def contest_scoreboard(request: HttpRequest, slug: str) -> HttpResponse:
    contest = _contest(request, slug)
    board = scoreboard(contest, request.user)
    template = "contests/_scoreboard.html" if request.GET.get("partial") else "contests/scoreboard.html"
    return render(request, template, {"contest": contest, "board": board})
