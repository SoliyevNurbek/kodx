"""Vazifalar ro'yxati va vazifa sahifasi (code / quiz / project) hamda topshirish."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from courses.models import Lesson
from judge.types import Language
from submissions.models import ProjectSubmission, QuizAttempt, Submission
from submissions.services import SubmissionError, create_submission, grade_quiz, submit_project
from submissions.stats import attempted_ids, problem_status, solved_ids

from .markdown import render_markdown
from .models import Problem, Tag


def _visible_problem(request: HttpRequest, slug: str) -> Problem:
    problem = get_object_or_404(Problem.objects.select_related("author"), slug=slug)
    if not problem.can_view(request.user):
        raise Http404
    return problem


def _lesson_from_request(request: HttpRequest, problem: Problem) -> Lesson | None:
    """?lesson=<id> — vazifa shu darsga biriktirilgan bo'lsagina hisobga olinadi."""
    lesson_id = request.POST.get("lesson") or request.GET.get("lesson")
    if not (lesson_id and str(lesson_id).isdigit()):
        return None
    return Lesson.objects.filter(pk=lesson_id, lesson_problems__problem=problem).first()


def problem_list(request: HttpRequest) -> HttpResponse:
    """Nashr etilgan vazifalar: tur, teg va qiyinlik bo'yicha filtr."""
    problems = Problem.objects.filter(status=Problem.Status.PUBLISHED).prefetch_related("tags")
    ptype, tag, difficulty, query = (request.GET.get(k, "") for k in ("type", "tag", "difficulty", "q"))
    if ptype in Problem.Type.values:
        problems = problems.filter(type=ptype)
    if tag:
        problems = problems.filter(tags__slug=tag)
    if difficulty.isdigit():
        problems = problems.filter(difficulty=int(difficulty))
    if query:
        problems = problems.filter(title__icontains=query)
    page = Paginator(problems.distinct().order_by("slug"), 30).get_page(request.GET.get("page"))
    solved, attempted = solved_ids(request.user), attempted_ids(request.user)
    rows = [{"problem": p, "status": problem_status(p.pk, solved, attempted)} for p in page]
    return render(request, "problems/problem_list.html", {
        "page": page, "rows": rows, "tags": Tag.objects.all(), "types": Problem.Type.choices,
        "filters": {"type": ptype, "tag": tag, "difficulty": difficulty, "q": query},
    })


def problem_detail(request: HttpRequest, slug: str) -> HttpResponse:
    """Vazifa sahifasi — turiga qarab code / quiz / project shabloni."""
    problem = _visible_problem(request, slug)
    lesson = _lesson_from_request(request, problem)
    context = {
        "problem": problem,
        "statement_html": render_markdown(problem.statement),
        "lesson": lesson,
        "status": problem_status(problem.pk, solved_ids(request.user), attempted_ids(request.user)),
        "can_edit": problem.can_edit(request.user),
    }
    if problem.type == Problem.Type.CODE:
        context["samples"] = [{"input": tc.read_input(), "output": tc.read_output()}
                              for tc in problem.test_cases.filter(is_sample=True)]
        context["languages"] = Language.choices
        if request.user.is_authenticated:
            context["recent"] = Submission.objects.filter(user=request.user, problem=problem)[:5]
        return render(request, "problems/problem_code.html", context)
    if problem.type == Problem.Type.QUIZ:
        context["questions"] = problem.questions.prefetch_related("options")
        if request.user.is_authenticated:
            context["attempts"] = QuizAttempt.objects.filter(user=request.user, problem=problem)[:5]
        return render(request, "problems/problem_quiz.html", context)
    context["rubric"] = problem.rubric.all()
    if request.user.is_authenticated:
        context["project_submissions"] = ProjectSubmission.objects.filter(user=request.user, problem=problem)
    return render(request, "problems/problem_project.html", context)


@login_required
@require_POST
def submit_code(request: HttpRequest, slug: str) -> HttpResponse:
    problem = _visible_problem(request, slug)
    try:
        submission = create_submission(request.user, problem, request.POST.get("code", ""),
                                       request.POST.get("language", Language.PYTHON3),
                                       lesson=_lesson_from_request(request, problem))
    except SubmissionError as exc:
        messages.error(request, exc.messages[0])
        return redirect("problem_detail", slug=slug)
    return redirect("submission_detail", pk=submission.pk)


@login_required
@require_POST
def submit_quiz(request: HttpRequest, slug: str) -> HttpResponse:
    problem = _visible_problem(request, slug)
    answers: dict[str, object] = {}
    for question in problem.questions.all():
        key = f"q{question.order}"
        if question.kind == question.Kind.MULTIPLE:
            answers[str(question.order)] = request.POST.getlist(key)
        else:
            answers[str(question.order)] = request.POST.get(key, "")
    try:
        attempt = grade_quiz(request.user, problem, answers, lesson=_lesson_from_request(request, problem))
    except SubmissionError as exc:
        messages.error(request, exc.messages[0])
        return redirect("problem_detail", slug=slug)
    return redirect("quiz_result", pk=attempt.pk)


@login_required
def quiz_result(request: HttpRequest, pk: int) -> HttpResponse:
    attempt = get_object_or_404(QuizAttempt.objects.select_related("problem"), pk=pk)
    if attempt.user_id != request.user.pk and not request.user.is_moderator:
        raise PermissionDenied
    rows = []
    for question in attempt.problem.questions.prefetch_related("options"):
        key = str(question.order)
        rows.append({"question": question, "answer": attempt.answers.get(key),
                     "result": attempt.details.get(key, {"correct": False, "points": 0})})
    return render(request, "problems/quiz_result.html", {"attempt": attempt, "rows": rows})


@login_required
@require_POST
def submit_project_view(request: HttpRequest, slug: str) -> HttpResponse:
    problem = _visible_problem(request, slug)
    try:
        submit_project(request.user, problem, request.POST.get("github_url", ""), request.POST.get("comment", ""),
                       lesson=_lesson_from_request(request, problem))
    except SubmissionError as exc:
        messages.error(request, exc.messages[0])
    else:
        messages.success(request, "Loyiha topshirildi. O‘qituvchi baholagach, natija shu yerda ko‘rinadi.")
    return redirect("problem_detail", slug=slug)
