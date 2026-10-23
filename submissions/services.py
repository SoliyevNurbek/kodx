"""Yechimlar bilan ishlash servislari: yuborish, tekshirish, quiz va loyiha baholash."""

import logging
import re
from datetime import timedelta
from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.http import HttpRequest
from django.utils import timezone

from audit.services import log_action
from judge.backends import JudgeBackend, get_backend
from judge.types import Language, Verdict
from problems.models import Problem

from .models import MAX_CODE_BYTES, ProjectSubmission, QuizAttempt, Submission, SubmissionResult
from .queue import get_queue

logger = logging.getLogger(__name__)

RATE_LIMIT_COUNT = 6
RATE_LIMIT_WINDOW = timedelta(minutes=1)
GITHUB_URL_RE = re.compile(r"^https://github\.com/[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})/[A-Za-z0-9._-]{1,100}/?$")


class SubmissionError(ValidationError):
    """Yechimni qabul qilib bo'lmaydi (foydalanuvchiga ko'rsatiladigan xabar bilan)."""


def _check_problem(user, problem: Problem, expected_type: str) -> None:
    if problem.type != expected_type:
        raise SubmissionError("Bu vazifa turi uchun boshqa topshirish usuli ishlatiladi.")
    if not problem.can_view(user):
        raise PermissionDenied("Vazifa topilmadi.")


def check_rate_limit(user) -> None:
    """1 daqiqada 6 tadan ortiq yechim yuborishni taqiqlaydi."""
    since = timezone.now() - RATE_LIMIT_WINDOW
    if Submission.objects.filter(user=user, created_at__gte=since).count() >= RATE_LIMIT_COUNT:
        raise SubmissionError("Juda tez yuboryapsiz: 1 daqiqada ko‘pi bilan 6 ta yechim. Biroz kuting.")


def create_submission(user, problem: Problem, code: str, language: str = Language.PYTHON3,
                      lesson=None) -> Submission:
    """Yechimni tekshiradi, saqlaydi va navbatga qo'yadi (kod bu yerda BAJARILMAYDI)."""
    _check_problem(user, problem, Problem.Type.CODE)
    if language not in Language.values:
        raise SubmissionError("Bu til qo‘llab-quvvatlanmaydi.")
    if not code.strip():
        raise SubmissionError("Kod bo‘sh.")
    if len(code.encode("utf-8")) > MAX_CODE_BYTES:
        raise SubmissionError("Kod hajmi 64 KB dan oshmasligi kerak.")
    check_rate_limit(user)
    submission = Submission.objects.create(user=user, problem=problem, code=code, language=language, lesson=lesson)
    get_queue().enqueue(submission)
    return submission


def judge_submission(submission: Submission, backend: JudgeBackend | None = None) -> Submission:
    """
    Yechimni judge backend'da tekshiradi va natijalarni yozadi.

    Faqat worker jarayonidan chaqiriladi. Backend xatosi — «Ichki xato» verdikti.
    """
    problem = submission.problem
    test_cases = list(problem.test_cases.all())
    order_by_id = {tc.pk: tc.order for tc in test_cases}
    try:
        backend = backend or get_backend()
        result = backend.submit(submission.code, submission.language,
                                [tc.as_judge_test() for tc in test_cases], problem.limits)
    except Exception as exc:  # noqa: BLE001 - worker hech qachon yiqilmasligi kerak
        logger.exception("Judge xatosi: submission %s", submission.pk)
        with transaction.atomic():
            submission.results.all().delete()
            submission.verdict = Verdict.INTERNAL_ERROR
            submission.compile_output = f"Ichki xato: {exc.__class__.__name__}"
            submission.score = 0
            submission.status = Submission.Status.DONE
            submission.judged_at = timezone.now()
            submission.save()
        return submission

    max_points = sum(tc.points for tc in test_cases)
    with transaction.atomic():
        submission.results.all().delete()
        SubmissionResult.objects.bulk_create([
            SubmissionResult(
                submission=submission,
                test_case_id=outcome.test_id if outcome.test_id in order_by_id else None,
                order=order_by_id.get(outcome.test_id, index),
                verdict=outcome.verdict, time_ms=outcome.time_ms, memory_kb=outcome.memory_kb,
                points=outcome.points, output=outcome.output, error=outcome.error,
            )
            for index, outcome in enumerate(result.tests, start=1)
        ])
        submission.verdict = result.verdict
        submission.score = round(problem.points * result.score / max_points) if max_points else 0
        submission.time_ms = result.max_time_ms
        submission.memory_kb = result.max_memory_kb
        submission.compile_output = result.compile_output
        submission.status = Submission.Status.DONE
        submission.judged_at = timezone.now()
        submission.save()
    return submission


def rejudge(submission: Submission, actor, request: HttpRequest | None = None) -> None:
    """Qayta tekshiruvga qo'yish (moderator+)."""
    if not actor.is_moderator:
        raise PermissionDenied("Qayta tekshirish — faqat moderator.")
    submission.status = Submission.Status.QUEUED
    submission.save(update_fields=["status"])
    get_queue().enqueue(submission)
    log_action(actor, "submission_rejudge", submission, {"old_verdict": submission.verdict}, request)


def user_solved(user, problem: Problem) -> bool:
    """Foydalanuvchi masalani yechganmi (code — AC; quiz — 100%; loyiha — baholangan)."""
    if not (user and user.is_authenticated):
        return False
    if problem.type == Problem.Type.CODE:
        return Submission.objects.filter(user=user, problem=problem, verdict=Verdict.ACCEPTED).exists()
    if problem.type == Problem.Type.QUIZ:
        return any(a.score == a.max_score and a.max_score for a in
                   QuizAttempt.objects.filter(user=user, problem=problem))
    return ProjectSubmission.objects.filter(user=user, problem=problem,
                                            status=ProjectSubmission.Status.GRADED).exists()


# ---------------- Quiz ----------------

def _normalize_choice(value: Any) -> set[int]:
    if value is None:
        return set()
    if isinstance(value, list | tuple | set):
        return {int(v) for v in value}
    return {int(value)}


def grade_quiz(user, problem: Problem, answers: dict[str, Any], lesson=None) -> QuizAttempt:
    """
    Quiz javoblarini baholaydi.

    `answers`: {"<savol tartibi>": [variant tartibi, ...] | variant tartibi | "matn"}.
    single/multiple — tanlangan variantlar to'plami to'g'rilari bilan aynan mos bo'lsa ball beriladi;
    text — katta-kichik harf va chetdagi bo'shliqlarsiz solishtiriladi.
    """
    _check_problem(user, problem, Problem.Type.QUIZ)
    details: dict[str, dict[str, Any]] = {}
    clean_answers: dict[str, Any] = {}
    score = max_score = 0
    for question in problem.questions.prefetch_related("options"):
        key = str(question.order)
        raw = answers.get(key)
        max_score += question.points
        if question.kind == question.Kind.TEXT:
            given = str(raw or "").strip()
            clean_answers[key] = given
            correct = given.casefold() in question.accepted_answers()
        else:
            try:
                chosen = _normalize_choice(raw)
            except (TypeError, ValueError):
                chosen = set()
            clean_answers[key] = sorted(chosen)
            right = {o.order for o in question.options.all() if o.is_correct}
            correct = chosen == right
        points = question.points if correct else 0
        score += points
        details[key] = {"correct": correct, "points": points}
    return QuizAttempt.objects.create(user=user, problem=problem, lesson=lesson, answers=clean_answers,
                                      details=details, score=score, max_score=max_score)


# ---------------- Loyihalar ----------------

def submit_project(user, problem: Problem, github_url: str, comment: str = "", lesson=None) -> ProjectSubmission:
    """Loyiha havolasini qabul qiladi (qayta topshirish mumkin — har biri alohida yozuv)."""
    _check_problem(user, problem, Problem.Type.PROJECT)
    url = github_url.strip()
    if not GITHUB_URL_RE.match(url):
        raise SubmissionError("Havola https://github.com/<foydalanuvchi>/<repozitoriy> ko‘rinishida bo‘lishi kerak.")
    return ProjectSubmission.objects.create(user=user, problem=problem, github_url=url,
                                            comment=comment.strip(), lesson=lesson)


def grade_project(grader, submission: ProjectSubmission, scores: dict[str, int], feedback: str = "",
                  needs_revision: bool = False, request: HttpRequest | None = None) -> ProjectSubmission:
    """Moderator rubrika bo'yicha baholaydi. Har mezon 0..max oralig'ida."""
    if not (grader and grader.is_moderator):
        raise PermissionDenied("Loyihani faqat moderator baholaydi.")
    clean: dict[str, int] = {}
    for criterion in submission.problem.rubric.all():
        key = str(criterion.order)
        try:
            value = int(scores.get(key, 0))
        except (TypeError, ValueError) as exc:
            raise SubmissionError(f"«{criterion.title}»: ball butun son bo‘lishi kerak.") from exc
        if not 0 <= value <= criterion.max_points:
            raise SubmissionError(f"«{criterion.title}»: ball 0–{criterion.max_points} oralig‘ida bo‘lishi kerak.")
        clean[key] = value
    submission.rubric_scores = clean
    submission.score = sum(clean.values())
    submission.feedback = feedback.strip()
    submission.status = (ProjectSubmission.Status.NEEDS_REVISION if needs_revision
                         else ProjectSubmission.Status.GRADED)
    submission.graded_by = grader
    submission.graded_at = timezone.now()
    submission.save()
    log_action(grader, "project_graded", submission,
               {"score": submission.score, "status": submission.status, "user": submission.user.username}, request)
    return submission
