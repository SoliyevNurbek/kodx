"""Baholash va reyting hisoblari testlari (chekka holatlar bilan)."""

from datetime import date, timedelta
from decimal import Decimal
from unittest import mock

from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role, User
from audit.models import AuditLog
from courses.models import Course, Group, GroupMember, Lesson
from judge.types import JudgeResult, TestOutcome, Verdict
from problems.models import LessonProblem, Problem
from submissions.models import ProjectSubmission, QuizAttempt, Submission
from submissions.services import create_submission, judge_submission

from . import leaderboard as boards
from .course_grade import best_fraction, compute_course_grade
from .models import Attendance, GradingPolicy, PracticeStats, UserBadge
from .practice import refresh_practice_stats, streaks
from .rating import Standing, competition_ranks, rating_changes

NOW = timezone.now()


def make_user(username: str, role: int = Role.USER) -> User:
    return User.objects.create_user(username=username, password="Sinov-parol-2026", role=role)


def accept(user, slug: str, when=None, score: int | None = None) -> Submission:
    problem = Problem.objects.get(slug=slug)
    submission = Submission.objects.create(user=user, problem=problem, code="x", status=Submission.Status.DONE,
                                           verdict=Verdict.ACCEPTED, score=problem.points if score is None else score)
    if when is not None:
        Submission.objects.filter(pk=submission.pk).update(created_at=when)
    return submission


class BestFractionTests(SimpleTestCase):
    def test_empty_is_zero(self) -> None:
        self.assertEqual(best_fraction([], None, 20), 0.0)

    def test_on_time_full(self) -> None:
        self.assertEqual(best_fraction([(NOW, 1.0)], NOW + timedelta(days=1), 20), 1.0)

    def test_late_penalty(self) -> None:
        self.assertAlmostEqual(best_fraction([(NOW, 1.0)], NOW - timedelta(days=1), 20), 0.8)

    def test_best_of_early_partial_and_late_full(self) -> None:
        deadline = NOW
        entries = [(NOW - timedelta(hours=1), 0.5), (NOW + timedelta(hours=1), 1.0)]
        self.assertAlmostEqual(best_fraction(entries, deadline, 20), 0.8)
        self.assertAlmostEqual(best_fraction(entries, deadline, 60), 0.5)

    def test_full_penalty_and_clamping(self) -> None:
        self.assertEqual(best_fraction([(NOW, 1.0)], NOW - timedelta(seconds=1), 100), 0.0)
        self.assertEqual(best_fraction([(NOW, 3.0), (NOW, -1.0)], None, 0), 1.0)


class StreakTests(SimpleTestCase):
    TODAY = date(2026, 10, 23)

    def days(self, *offsets: int) -> set[date]:
        return {self.TODAY - timedelta(days=o) for o in offsets}

    def test_empty(self) -> None:
        self.assertEqual(streaks(set(), self.TODAY), (0, 0))

    def test_today_only(self) -> None:
        self.assertEqual(streaks(self.days(0), self.TODAY), (1, 1))

    def test_yesterday_keeps_streak_alive(self) -> None:
        self.assertEqual(streaks(self.days(1, 2, 3), self.TODAY), (3, 3))

    def test_broken_streak(self) -> None:
        self.assertEqual(streaks(self.days(2, 3, 4, 5), self.TODAY), (0, 4))

    def test_current_shorter_than_best(self) -> None:
        self.assertEqual(streaks(self.days(0, 1, 5, 6, 7, 8, 9), self.TODAY), (2, 5))


class RatingTests(SimpleTestCase):
    def test_single_participant_no_change(self) -> None:
        self.assertEqual(rating_changes([Standing("a", 1200, 1)]), {"a": 0})
        self.assertEqual(rating_changes([]), {})

    def test_two_equal_players(self) -> None:
        deltas = rating_changes([Standing("a", 1200, 1), Standing("b", 1200, 2)])
        self.assertGreater(deltas["a"], 0)
        self.assertLess(deltas["b"], 0)
        self.assertLessEqual(deltas["a"] + deltas["b"], 0)

    def test_underdog_gains_more(self) -> None:
        upset = rating_changes([Standing("weak", 1000, 1), Standing("strong", 1600, 2)])
        expected = rating_changes([Standing("weak", 1000, 2), Standing("strong", 1600, 1)])
        self.assertGreater(upset["weak"], expected["strong"])
        self.assertLess(upset["strong"], 0)

    def test_tie_between_equals_is_small(self) -> None:
        deltas = rating_changes([Standing("a", 1500, 1), Standing("b", 1500, 1)])
        self.assertEqual(deltas["a"], deltas["b"])
        self.assertLessEqual(abs(deltas["a"]), 10)

    def test_no_inflation_many_players(self) -> None:
        standings = [Standing(i, 1200 + 37 * (i % 7), i + 1) for i in range(30)]
        self.assertLessEqual(sum(rating_changes(standings).values()), 0)

    def test_competition_ranks_ties(self) -> None:
        ranks = competition_ranks([("a", (-10,)), ("b", (-15,)), ("c", (-10,)), ("d", (-1,))])
        self.assertEqual(ranks, [("b", 1), ("a", 2), ("c", 2), ("d", 4)])


class CourseGradeTests(TestCase):
    def setUp(self) -> None:
        self.course = Course.objects.get(slug="dasturlash-va-ai-asoslari")
        self.user = make_user("talaba")
        self.group = Group.objects.get(name="Python-1")
        GroupMember.objects.create(group=self.group, user=self.user)

    def test_no_work_is_zero_with_max_80(self) -> None:
        grade = compute_course_grade(self.user, self.course)
        self.assertEqual(len(grade.modules), 4)
        self.assertEqual(grade.total, Decimal(0))
        self.assertEqual(grade.max_total, Decimal(80))

    def test_components(self) -> None:
        # Modul 1: 24 ta majburiy code masala, 12 ta quiz, 1 ta loyiha (12-dars)
        accept(self.user, "l05-salom")
        quiz = Problem.objects.get(slug="l05-quiz")
        QuizAttempt.objects.create(user=self.user, problem=quiz, score=5, max_score=5)
        ProjectSubmission.objects.create(user=self.user, problem=Problem.objects.get(slug="l12-loyiha-1"),
                                         github_url="https://github.com/a/b", status="graded", score=80)
        m1 = compute_course_grade(self.user, self.course).modules[0]
        self.assertEqual(m1.tasks, Decimal("0.21"))   # 5 × 1/24
        self.assertEqual(m1.quiz, Decimal("0.21"))    # 2.5 × 1/12
        self.assertEqual(m1.project, Decimal("8.00"))  # 10 × 80/100
        self.assertEqual(m1.attendance, Decimal(0))

    def test_challenge_problems_do_not_count(self) -> None:
        accept(self.user, "l05-xarid-cheki")  # challenge, majburiy emas
        self.assertEqual(compute_course_grade(self.user, self.course).modules[0].tasks, Decimal(0))

    def test_attendance_counts_only_marked_lessons(self) -> None:
        other = make_user("boshqa")
        GroupMember.objects.create(group=self.group, user=other)
        lesson1, lesson2 = Lesson.objects.get(number=1), Lesson.objects.get(number=2)
        Attendance.objects.create(group=self.group, lesson=lesson1, user=self.user, present=True)
        Attendance.objects.create(group=self.group, lesson=lesson2, user=self.user, present=False)
        Attendance.objects.create(group=self.group, lesson=lesson2, user=other, present=True)
        grade = compute_course_grade(self.user, self.course)
        self.assertEqual(grade.modules[0].attendance, Decimal("1.25"))
        self.assertEqual(grade.modules[1].attendance, Decimal(0))

    def test_late_submission_penalized(self) -> None:
        link = LessonProblem.objects.get(problem__slug="l05-ikki-son")
        link.deadline = NOW - timedelta(days=1)
        link.save()
        accept(self.user, "l05-ikki-son")
        self.assertEqual(compute_course_grade(self.user, self.course).modules[0].tasks, Decimal("0.17"))  # 5×0.8/24
        policy = GradingPolicy.for_course(self.course)
        policy.late_penalty_percent = 0
        policy.save()
        self.assertEqual(compute_course_grade(self.user, self.course).modules[0].tasks, Decimal("0.21"))

    def test_partial_and_best_score(self) -> None:
        accept(self.user, "l05-ikki-son", score=40)   # 40/100
        accept(self.user, "l05-ikki-son", score=100)
        accept(self.user, "l05-salom", score=50)
        self.assertEqual(compute_course_grade(self.user, self.course).modules[0].tasks, Decimal("0.31"))  # 5×1.5/24

    def test_project_needing_revision_not_counted(self) -> None:
        ProjectSubmission.objects.create(user=self.user, problem=Problem.objects.get(slug="l12-loyiha-1"),
                                         github_url="https://github.com/a/b", status="revision", score=90)
        self.assertEqual(compute_course_grade(self.user, self.course).modules[0].project, Decimal(0))

    def test_custom_policy_weights(self) -> None:
        policy = GradingPolicy.for_course(self.course)
        policy.project_points = Decimal("20")
        policy.save()
        ProjectSubmission.objects.create(user=self.user, problem=Problem.objects.get(slug="l12-loyiha-1"),
                                         github_url="https://github.com/a/b", status="graded", score=100)
        grade = compute_course_grade(self.user, self.course)
        self.assertEqual(grade.modules[0].project, Decimal("20.00"))
        self.assertEqual(grade.max_total, Decimal(120))


class PracticeStatsTests(TestCase):
    def setUp(self) -> None:
        self.user = make_user("talaba")

    def test_score_is_sum_of_solved_points(self) -> None:
        accept(self.user, "l05-salom")         # 100
        accept(self.user, "l08-kvadrat-tenglama")  # 300
        accept(self.user, "l05-salom")         # takror — hisobga olinmaydi
        stats = refresh_practice_stats(self.user)
        self.assertEqual((stats.score, stats.solved_count), (400, 2))

    def test_wrong_answers_do_not_count(self) -> None:
        Submission.objects.create(user=self.user, problem=Problem.objects.get(slug="l05-salom"), code="x",
                                  verdict=Verdict.WRONG_ANSWER)
        self.assertEqual(refresh_practice_stats(self.user).score, 0)

    def test_first_solve_badge_idempotent(self) -> None:
        accept(self.user, "l05-salom")
        refresh_practice_stats(self.user)
        refresh_practice_stats(self.user)
        self.assertEqual(list(UserBadge.objects.filter(user=self.user).values_list("badge__code", flat=True)),
                         ["first-solve"])

    def test_streak_badge(self) -> None:
        slugs = list(Problem.objects.filter(type="code").values_list("slug", flat=True)[:7])
        for offset, slug in enumerate(slugs):
            accept(self.user, slug, when=timezone.now() - timedelta(days=offset))
        stats = refresh_practice_stats(self.user)
        self.assertEqual((stats.current_streak, stats.best_streak), (7, 7))
        self.assertTrue(UserBadge.objects.filter(user=self.user, badge__code="streak-7").exists())

    def test_challenge_badge(self) -> None:
        for link in LessonProblem.objects.filter(kind=LessonProblem.Kind.CHALLENGE).select_related("problem")[:5]:
            accept(self.user, link.problem.slug)
        refresh_practice_stats(self.user)
        self.assertTrue(UserBadge.objects.filter(user=self.user, badge__code="challenge-5").exists())

    def test_module_badge_requires_all_required_tasks(self) -> None:
        required = LessonProblem.objects.filter(lesson__module__number=1, is_required=True).select_related("problem")
        problems = [link.problem for link in required]
        for problem in problems[:-1]:
            self._solve(problem)
        refresh_practice_stats(self.user)
        self.assertFalse(UserBadge.objects.filter(user=self.user, badge__code="module-1").exists())
        self._solve(problems[-1])
        refresh_practice_stats(self.user)
        self.assertTrue(UserBadge.objects.filter(user=self.user, badge__code="module-1").exists())

    def _solve(self, problem: Problem) -> None:
        if problem.type == "code":
            accept(self.user, problem.slug)
        elif problem.type == "quiz":
            QuizAttempt.objects.create(user=self.user, problem=problem, score=5, max_score=5)
        else:
            ProjectSubmission.objects.create(user=self.user, problem=problem, github_url="https://github.com/a/b",
                                             status="graded", score=70)

    def test_accepted_judgement_refreshes_stats(self) -> None:
        submission = create_submission(self.user, Problem.objects.get(slug="l05-salom"), "print(1)")
        backend = mock.Mock()
        backend.submit.return_value = JudgeResult(verdict=Verdict.ACCEPTED, tests=[
            TestOutcome(test_id=tc.pk, verdict=Verdict.ACCEPTED, points=tc.points)
            for tc in submission.problem.test_cases.all()])
        judge_submission(submission, backend)
        self.assertEqual(PracticeStats.objects.get(user=self.user).score, 100)


class LeaderboardTests(TestCase):
    def setUp(self) -> None:
        self.a, self.b, self.c = make_user("a"), make_user("b"), make_user("c")
        accept(self.a, "l08-kvadrat-tenglama")
        accept(self.b, "l08-kvadrat-tenglama")
        accept(self.c, "l05-salom", when=timezone.now() - timedelta(days=30))
        for user in (self.a, self.b, self.c):
            refresh_practice_stats(user)

    def test_overall_ties_share_place(self) -> None:
        rows = boards.overall()
        self.assertEqual([(r["user"].username, r["place"], r["score"]) for r in rows],
                         [("a", 1, 300), ("b", 1, 300), ("c", 3, 100)])

    def test_weekly_excludes_old_solves(self) -> None:
        self.assertEqual([r["user"].username for r in boards.weekly()], ["a", "b"])

    def test_group_board_and_own_place(self) -> None:
        group = Group.objects.get(name="Python-1")
        GroupMember.objects.create(group=group, user=self.c)
        rows = boards.by_group(group)
        self.assertEqual([r["user"].username for r in rows], ["c"])
        self.assertEqual(boards.find_place(rows, self.c)["place"], 1)
        self.assertIsNone(boards.find_place(rows, self.a))
        self.assertEqual(len(boards.by_course(group.course)), 1)

    def test_leaderboard_page_tabs(self) -> None:
        self.client.force_login(self.c)
        for tab in ("overall", "weekly", "group", "course", "noma"):
            self.assertEqual(self.client.get(reverse("leaderboard") + f"?tab={tab}").status_code, 200, tab)
        response = self.client.get(reverse("leaderboard"))
        self.assertEqual(response.context["me"]["place"], 3)
        self.assertContains(self.client.get(reverse("home")), "300")


class TeacherGradingViewsTests(TestCase):
    def setUp(self) -> None:
        self.moderator = make_user("ustoz", Role.MODERATOR)
        self.student = make_user("talaba")
        self.group = Group.objects.get(name="Python-1")
        GroupMember.objects.create(group=self.group, user=self.student)
        self.client.force_login(self.moderator)

    def test_grades_page_and_csv(self) -> None:
        accept(self.student, "l05-salom")
        response = self.client.get(reverse("panel:group_grades", args=[self.group.pk]))
        self.assertContains(response, "talaba")
        csv_response = self.client.get(reverse("panel:group_grades", args=[self.group.pk]) + "?format=csv")
        self.assertEqual(csv_response["Content-Type"], "text/csv; charset=utf-8")
        lines = csv_response.content.decode("utf-8-sig").splitlines()
        self.assertTrue(lines[0].startswith("username,ism,M1 davomat"))
        self.assertTrue(lines[1].startswith("talaba,"))
        self.assertTrue(AuditLog.objects.filter(action="grades_exported").exists())

    def test_attendance_marking(self) -> None:
        url = reverse("panel:group_attendance", args=[self.group.pk])
        self.assertEqual(self.client.get(url + "?lesson=3").status_code, 200)
        self.client.post(url, {"lesson": 3, "present": [str(self.student.pk)]})
        record = Attendance.objects.get(group=self.group, lesson__number=3, user=self.student)
        self.assertTrue(record.present)
        self.client.post(url, {"lesson": 3})
        record.refresh_from_db()
        self.assertFalse(record.present)
        self.assertEqual(Attendance.objects.filter(group=self.group).count(), 1)
        self.assertTrue(AuditLog.objects.filter(action="attendance_marked").exists())

    def test_student_cannot_access(self) -> None:
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(reverse("panel:group_grades", args=[self.group.pk])).status_code, 403)
        self.assertEqual(self.client.get(reverse("panel:group_attendance", args=[self.group.pk])).status_code, 403)

    def test_profile_shows_badges_and_streak(self) -> None:
        accept(self.student, "l05-salom")
        refresh_practice_stats(self.student)
        response = self.client.get(reverse("profile", args=["talaba"]))
        self.assertContains(response, "Birinchi qadam")
        self.assertContains(response, "Joriy seriya")
