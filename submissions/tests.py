"""Yechimlar, navbat, worker, quiz va loyiha baholash testlari."""

from datetime import timedelta
from io import StringIO
from unittest import mock

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from accounts.models import Role, User
from audit.models import AuditLog
from judge.types import Verdict
from problems.models import Problem

from .models import MAX_CODE_BYTES, ProjectSubmission, Submission
from .queue import DatabaseQueue, get_queue
from .services import (
    SubmissionError,
    create_submission,
    grade_project,
    grade_quiz,
    judge_submission,
    rejudge,
    submit_project,
    user_solved,
)

AC = "a = int(input())\nb = int(input())\nprint(a + b)\n"


def make_user(username: str, role: int = Role.USER) -> User:
    return User.objects.create_user(username=username, password="Sinov-parol-2026", role=role)


def run_worker() -> str:
    out = StringIO()
    call_command("run_judge_worker", once=True, stdout=out)
    return out.getvalue()


class SubmitValidationTests(TestCase):
    def setUp(self) -> None:
        self.user = make_user("talaba")
        self.problem = Problem.objects.get(slug="l05-ikki-son")

    def test_creates_queued_submission(self) -> None:
        submission = create_submission(self.user, self.problem, AC)
        self.assertEqual(submission.status, Submission.Status.QUEUED)
        self.assertEqual(submission.verdict, "")

    def test_empty_code_rejected(self) -> None:
        with self.assertRaises(SubmissionError):
            create_submission(self.user, self.problem, "   \n")

    def test_code_size_limit(self) -> None:
        with self.assertRaisesMessage(SubmissionError, "64 KB"):
            create_submission(self.user, self.problem, "#" * (MAX_CODE_BYTES + 1))
        create_submission(self.user, self.problem, "#" * (MAX_CODE_BYTES - 10))

    def test_unicode_counted_in_bytes(self) -> None:
        with self.assertRaises(SubmissionError):
            create_submission(self.user, self.problem, "ў" * (MAX_CODE_BYTES // 2 + 1))

    def test_rate_limit_six_per_minute(self) -> None:
        for _ in range(6):
            create_submission(self.user, self.problem, AC)
        with self.assertRaisesMessage(SubmissionError, "6 ta"):
            create_submission(self.user, self.problem, AC)
        Submission.objects.update(created_at=timezone.now() - timedelta(minutes=2))
        create_submission(self.user, self.problem, AC)

    def test_rate_limit_is_per_user(self) -> None:
        for _ in range(6):
            create_submission(self.user, self.problem, AC)
        create_submission(make_user("boshqa"), self.problem, AC)

    def test_wrong_problem_type(self) -> None:
        with self.assertRaises(SubmissionError):
            create_submission(self.user, Problem.objects.get(slug="l05-quiz"), AC)

    def test_unknown_language(self) -> None:
        with self.assertRaises(SubmissionError):
            create_submission(self.user, self.problem, AC, language="brainfuck")

    def test_draft_problem_hidden(self) -> None:
        self.problem.status = Problem.Status.DRAFT
        self.problem.save()
        with self.assertRaises(PermissionDenied):
            create_submission(self.user, self.problem, AC)


class WorkerVerdictTests(TestCase):
    """Worker yechimlarni LocalDevBackend'da tekshiradi."""

    def setUp(self) -> None:
        self.user = make_user("talaba")
        self.problem = Problem.objects.get(slug="l05-ikki-son")

    def _judge(self, code: str) -> Submission:
        submission = create_submission(self.user, self.problem, code)
        run_worker()
        submission.refresh_from_db()
        return submission

    def test_accepted(self) -> None:
        submission = self._judge(AC)
        self.assertEqual(submission.status, Submission.Status.DONE)
        self.assertEqual(submission.verdict, Verdict.ACCEPTED)
        self.assertEqual(submission.score, self.problem.points)
        self.assertEqual(submission.results.count(), self.problem.test_cases.count())
        self.assertTrue(all(r.verdict == Verdict.ACCEPTED for r in submission.results.all()))
        self.assertIsNotNone(submission.judged_at)

    def test_wrong_answer_gives_partial_score(self) -> None:
        # "2 3", "0 0" va "-5 5" testlarida to'g'ri: 5 testdan 3 tasi
        submission = self._judge("a = int(input())\nb = int(input())\nprint(5 if a == 2 else 0)\n")
        self.assertEqual(submission.verdict, Verdict.WRONG_ANSWER)
        self.assertEqual(submission.score, round(self.problem.points * 3 / 5))

    def test_time_limit(self) -> None:
        self.problem.time_limit = 200
        self.problem.save()
        submission = self._judge("while True:\n    pass\n")
        self.assertEqual(submission.verdict, Verdict.TIME_LIMIT)
        self.assertEqual(submission.score, 0)

    def test_runtime_error(self) -> None:
        submission = self._judge("print(int('x'))\n")
        self.assertEqual(submission.verdict, Verdict.RUNTIME_ERROR)
        self.assertIn("ValueError", submission.results.first().error)

    def test_compilation_error(self) -> None:
        submission = self._judge("def f(:\n")
        self.assertEqual(submission.verdict, Verdict.COMPILATION_ERROR)
        self.assertIn("SyntaxError", submission.compile_output)
        self.assertEqual(submission.results.count(), 0)

    def test_backend_crash_gives_internal_error(self) -> None:
        submission = create_submission(self.user, self.problem, AC)
        broken = mock.Mock()
        broken.submit.side_effect = RuntimeError("judge o'chgan")
        with self.assertLogs("submissions.services", level="ERROR"):
            judge_submission(submission, broken)
        submission.refresh_from_db()
        self.assertEqual(submission.verdict, Verdict.INTERNAL_ERROR)
        self.assertEqual(submission.status, Submission.Status.DONE)

    def test_worker_processes_queue_in_order(self) -> None:
        first = create_submission(self.user, self.problem, AC)
        second = create_submission(self.user, self.problem, "print(0)\n")
        output = run_worker()
        self.assertIn("Jami tekshirildi: 2", output)
        self.assertLess(output.index(f"#{first.pk}"), output.index(f"#{second.pk}"))


class QueueTests(TestCase):
    def setUp(self) -> None:
        self.user = make_user("talaba")
        self.problem = Problem.objects.get(slug="l05-ikki-son")

    def test_claim_marks_running_once(self) -> None:
        submission = create_submission(self.user, self.problem, AC)
        queue = get_queue()
        self.assertEqual(queue.size(), 1)
        claimed = queue.claim_next()
        self.assertEqual(claimed.pk, submission.pk)
        self.assertEqual(claimed.status, Submission.Status.RUNNING)
        self.assertEqual(claimed.judge_attempts, 1)
        self.assertIsNone(queue.claim_next())

    def test_requeue_stale(self) -> None:
        submission = create_submission(self.user, self.problem, AC)
        DatabaseQueue().claim_next()
        Submission.objects.filter(pk=submission.pk).update(created_at=timezone.now() - timedelta(minutes=10))
        self.assertEqual(DatabaseQueue().requeue_stale(), 1)
        submission.refresh_from_db()
        self.assertEqual(submission.status, Submission.Status.QUEUED)

    def test_rejudge_requires_moderator_and_is_audited(self) -> None:
        submission = create_submission(self.user, self.problem, AC)
        run_worker()
        submission.refresh_from_db()
        with self.assertRaises(PermissionDenied):
            rejudge(submission, self.user)
        moderator = make_user("mod", Role.MODERATOR)
        rejudge(submission, moderator)
        submission.refresh_from_db()
        self.assertEqual(submission.status, Submission.Status.QUEUED)
        self.assertTrue(AuditLog.objects.filter(action="submission_rejudge", actor=moderator).exists())


class VisibilityTests(TestCase):
    """Boshqalarning kodi faqat masala yechilgandan keyin ochiladi."""

    def setUp(self) -> None:
        self.owner = make_user("egasi")
        self.other = make_user("boshqa")
        self.problem = Problem.objects.get(slug="l05-ikki-son")
        self.submission = Submission.objects.create(user=self.owner, problem=self.problem, code=AC,
                                                    status=Submission.Status.DONE, verdict=Verdict.WRONG_ANSWER)

    def test_owner_and_moderator_see_code(self) -> None:
        self.assertTrue(self.submission.can_view_code(self.owner))
        self.assertTrue(self.submission.can_view_code(make_user("mod", Role.MODERATOR)))

    def test_others_and_anonymous_do_not(self) -> None:
        self.assertFalse(self.submission.can_view_code(self.other))
        self.assertFalse(self.submission.can_view_code(make_user("jp", Role.JURY_PRO)))
        self.assertFalse(self.submission.can_view_code(AnonymousUser()))

    def test_others_see_code_after_solving(self) -> None:
        Submission.objects.create(user=self.other, problem=self.problem, code=AC, status=Submission.Status.DONE,
                                  verdict=Verdict.ACCEPTED)
        self.assertTrue(self.submission.can_view_code(self.other))

    def test_solving_other_problem_does_not_help(self) -> None:
        Submission.objects.create(user=self.other, problem=Problem.objects.get(slug="l05-salom"), code="x",
                                  status=Submission.Status.DONE, verdict=Verdict.ACCEPTED)
        self.assertFalse(self.submission.can_view_code(self.other))

    def test_user_solved(self) -> None:
        self.assertFalse(user_solved(self.owner, self.problem))
        Submission.objects.create(user=self.owner, problem=self.problem, code=AC, verdict=Verdict.ACCEPTED)
        self.assertTrue(user_solved(self.owner, self.problem))
        self.assertFalse(user_solved(AnonymousUser(), self.problem))


class QuizGradingTests(TestCase):
    def setUp(self) -> None:
        self.user = make_user("talaba")
        self.quiz = Problem.objects.get(slug="misol-quiz") if Problem.objects.filter(slug="misol-quiz").exists() \
            else self._make_quiz()

    def _make_quiz(self) -> Problem:
        from django.conf import settings

        from problems.importer import import_directory

        author = make_user("ustoz", Role.JURY_PRO)
        import_directory(settings.BASE_DIR / "docs" / "examples" / "problems" / "misol-quiz", author,
                         status="published")
        return Problem.objects.get(slug="misol-quiz")

    def test_all_correct(self) -> None:
        attempt = grade_quiz(self.user, self.quiz, {"1": [1], "2": [1, 2], "3": "  BESH "})
        self.assertEqual((attempt.score, attempt.max_score), (4, 4))
        self.assertEqual(attempt.problem_points, self.quiz.points)
        self.assertTrue(user_solved(self.user, self.quiz))

    def test_multiple_requires_exact_set(self) -> None:
        attempt = grade_quiz(self.user, self.quiz, {"1": 1, "2": [1], "3": "4"})
        self.assertEqual(attempt.score, 1)
        self.assertEqual(attempt.details["2"], {"correct": False, "points": 0})
        attempt = grade_quiz(self.user, self.quiz, {"2": [1, 2, 3]})
        self.assertEqual(attempt.details["2"]["correct"], False)

    def test_garbage_answers_score_zero(self) -> None:
        attempt = grade_quiz(self.user, self.quiz, {"1": "abc", "2": None})
        self.assertEqual(attempt.score, 0)
        self.assertFalse(user_solved(self.user, self.quiz))

    def test_seed_quiz_full_score_with_correct_options(self) -> None:
        quiz = Problem.objects.get(slug="l10-quiz")
        answers = {}
        for question in quiz.questions.all():
            if question.kind == "text":
                answers[str(question.order)] = question.accepted_answers()[0]
            else:
                answers[str(question.order)] = [o.order for o in question.options.all() if o.is_correct]
        attempt = grade_quiz(self.user, quiz, answers)
        self.assertEqual(attempt.score, attempt.max_score)


class ProjectTests(TestCase):
    def setUp(self) -> None:
        self.user = make_user("talaba")
        self.moderator = make_user("mod", Role.MODERATOR)
        self.project = Problem.objects.get(slug="l25-vizitka")

    def test_url_validation(self) -> None:
        for bad in ["http://github.com/a/b", "https://gitlab.com/a/b", "https://github.com/a", "salom"]:
            with self.assertRaises(SubmissionError, msg=bad):
                submit_project(self.user, self.project, bad)
        submission = submit_project(self.user, self.project, " https://github.com/ali-dev/vizitka.v1/ ")
        self.assertEqual(submission.github_url, "https://github.com/ali-dev/vizitka.v1/")

    def test_grading_by_moderator(self) -> None:
        submission = submit_project(self.user, self.project, "https://github.com/ali/vizitka")
        max_scores = {str(c.order): c.max_points for c in self.project.rubric.all()}
        grade_project(self.moderator, submission, max_scores, feedback="Zo‘r!")
        submission.refresh_from_db()
        self.assertEqual(submission.score, 100)
        self.assertEqual(submission.status, ProjectSubmission.Status.GRADED)
        self.assertEqual(submission.graded_by, self.moderator)
        self.assertTrue(AuditLog.objects.filter(action="project_graded").exists())
        self.assertTrue(user_solved(self.user, self.project))

    def test_grading_validation_and_permissions(self) -> None:
        submission = submit_project(self.user, self.project, "https://github.com/ali/vizitka")
        with self.assertRaises(PermissionDenied):
            grade_project(make_user("pro", Role.JURY_PRO), submission, {})
        with self.assertRaises(SubmissionError):
            grade_project(self.moderator, submission, {"1": 999})
        with self.assertRaises(SubmissionError):
            grade_project(self.moderator, submission, {"1": "ko'p"})

    def test_revision_and_resubmission(self) -> None:
        first = submit_project(self.user, self.project, "https://github.com/ali/vizitka")
        grade_project(self.moderator, first, {"1": 10}, needs_revision=True)
        self.assertEqual(first.status, ProjectSubmission.Status.NEEDS_REVISION)
        submit_project(self.user, self.project, "https://github.com/ali/vizitka")
        self.assertEqual(ProjectSubmission.objects.filter(user=self.user).count(), 2)
        self.assertFalse(user_solved(self.user, self.project))

    def test_visibility(self) -> None:
        submission = submit_project(self.user, self.project, "https://github.com/ali/vizitka")
        self.assertTrue(submission.can_view(self.user))
        self.assertTrue(submission.can_view(self.moderator))
        self.assertFalse(submission.can_view(make_user("boshqa")))
