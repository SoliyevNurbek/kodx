"""Ommaviy sahifalar, hisob va urinish sahifalarining view testlari (ruxsat bor / yo'q)."""

from django.core import mail
from django.test import TestCase
from django.urls import reverse

from accounts.models import Role, User
from audit.models import AuditLog
from courses.models import Lesson
from judge.types import Verdict
from problems.models import Problem
from submissions.models import ProjectSubmission, QuizAttempt, Submission

from .models import SiteSettings

PASSWORD = "Sinov-parol-2026"


def make_user(username: str, role: int = Role.USER, **extra) -> User:
    return User.objects.create_user(username=username, password=PASSWORD, role=role, **extra)


class PublicPagesTests(TestCase):
    """Anonim foydalanuvchiga ochiq sahifalar."""

    def test_public_pages_render(self) -> None:
        lesson = Lesson.objects.get(number=8)
        urls = [
            reverse("home"), reverse("leaderboard"), reverse("problem_list"),
            reverse("problem_list") + "?type=code&difficulty=2&q=a&tag=if",
            reverse("problem_detail", args=["l08-baho"]), reverse("problem_detail", args=["l08-quiz"]),
            reverse("problem_detail", args=["l25-vizitka"]),
            reverse("course_detail", args=[lesson.module.course.slug]),
            reverse("lesson_detail", args=[lesson.module.course.slug, 8]),
            reverse("contest_list"), reverse("login"), reverse("register"), reverse("password_reset"),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)
            self.assertContains(response, 'name="viewport"')  # mobil ko'rinish

    def test_problem_page_shows_samples_but_not_hidden_tests(self) -> None:
        problem = Problem.objects.get(slug="l06-vaqt-formati")
        response = self.client.get(reverse("problem_detail", args=[problem.slug]))
        self.assertContains(response, "1:02:05")  # namuna
        self.assertNotContains(response, "277:46:39")  # yopiq test javobi
        self.assertNotContains(response, "print(f")  # etalon yechim

    def test_unknown_or_draft_problem_404(self) -> None:
        self.assertEqual(self.client.get(reverse("problem_detail", args=["yoq-masala"])).status_code, 404)
        problem = Problem.objects.get(slug="l05-salom")
        problem.status = Problem.Status.DRAFT
        problem.save()
        self.assertEqual(self.client.get(reverse("problem_detail", args=["l05-salom"])).status_code, 404)

    def test_lesson_page_lists_tasks_with_status(self) -> None:
        user = make_user("talaba")
        Submission.objects.create(user=user, problem=Problem.objects.get(slug="l08-ishora"), code="x",
                                  status=Submission.Status.DONE, verdict=Verdict.ACCEPTED)
        self.client.force_login(user)
        lesson = Lesson.objects.get(number=8)
        response = self.client.get(reverse("lesson_detail", args=[lesson.module.course.slug, 8]))
        self.assertContains(response, "Sonning ishorasi")
        self.assertContains(response, "badge-solved")
        self.assertContains(response, "Test: Shartli operatorlar")

    def test_home_top_list(self) -> None:
        user = make_user("chempion")
        Submission.objects.create(user=user, problem=Problem.objects.get(slug="l05-salom"), code="x",
                                  verdict=Verdict.ACCEPTED)
        self.assertContains(self.client.get(reverse("home")), "chempion")


class AccountTests(TestCase):
    def test_register_and_login(self) -> None:
        response = self.client.post(reverse("register"), {
            "username": "yangi", "first_name": "Ali", "last_name": "", "email": "",
            "password1": "Juda-kuchli-parol-77", "password2": "Juda-kuchli-parol-77",
        })
        self.assertRedirects(response, reverse("home"))
        user = User.objects.get(username="yangi")
        self.assertEqual(user.role, Role.USER)
        self.assertIsNone(user.email)
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)
        self.assertTrue(AuditLog.objects.filter(action="user_registered").exists())

    def test_registration_can_be_disabled(self) -> None:
        settings = SiteSettings.load()
        settings.registration_enabled = False
        settings.save()
        self.assertEqual(self.client.get(reverse("register")).status_code, 403)
        self.assertNotContains(self.client.get(reverse("home")), reverse("register"))

    def test_login_view(self) -> None:
        make_user("ali")
        response = self.client.post(reverse("login"), {"username": "ali", "password": PASSWORD})
        self.assertRedirects(response, reverse("home"))

    def test_profile_hides_private_contacts(self) -> None:
        owner = make_user("egasi", email="maxfiy@kodx.uz")
        response = self.client.get(reverse("profile", args=["egasi"]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "maxfiy@kodx.uz")
        self.client.force_login(make_user("boshqa"))
        self.assertNotContains(self.client.get(reverse("profile", args=["egasi"])), "maxfiy@kodx.uz")
        self.client.force_login(owner)
        self.assertContains(self.client.get(reverse("profile", args=["egasi"])), "maxfiy@kodx.uz")

    def test_inactive_profile_404(self) -> None:
        make_user("bloklangan", is_active=False)
        self.assertEqual(self.client.get(reverse("profile", args=["bloklangan"])).status_code, 404)

    def test_profile_edit_requires_login_and_saves(self) -> None:
        self.assertEqual(self.client.get(reverse("profile_edit")).status_code, 302)
        user = make_user("ali")
        self.client.force_login(user)
        response = self.client.post(reverse("profile_edit"), {"first_name": "Ali", "last_name": "Valiyev",
                                                              "bio": "Python o‘rganyapman", "email": ""})
        self.assertRedirects(response, reverse("profile", args=["ali"]))
        user.refresh_from_db()
        self.assertEqual(user.bio, "Python o‘rganyapman")

    def test_forced_password_change(self) -> None:
        user = make_user("vaqtinchalik", must_change_password=True)
        self.client.force_login(user)
        self.assertRedirects(self.client.get(reverse("problem_list")), reverse("password_change"))
        self.assertEqual(self.client.get(reverse("password_change")).status_code, 200)
        response = self.client.post(reverse("password_change"), {
            "old_password": PASSWORD,
            "new_password1": "Yangi-kuchli-parol-88", "new_password2": "Yangi-kuchli-parol-88",
        })
        self.assertRedirects(response, reverse("password_change_done"))
        user.refresh_from_db()
        self.assertFalse(user.must_change_password)
        self.assertEqual(self.client.get(reverse("problem_list")).status_code, 200)
        self.assertTrue(AuditLog.objects.filter(action="password_changed", actor=user).exists())

    def test_password_reset_email_to_console(self) -> None:
        make_user("ali", email="ali@kodx.uz")
        self.client.post(reverse("password_reset"), {"email": "ali@kodx.uz"})
        self.assertEqual(len(mail.outbox), 1)


class SubmitFlowTests(TestCase):
    """Yechim, quiz va loyiha topshirish sahifalari."""

    def setUp(self) -> None:
        self.user = make_user("talaba")
        self.client.force_login(self.user)

    def test_submit_requires_login(self) -> None:
        self.client.logout()
        response = self.client.post(reverse("submit_code", args=["l05-salom"]), {"code": "print(1)"})
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])
        self.assertEqual(Submission.objects.count(), 0)

    def test_submit_code_redirects_to_detail(self) -> None:
        lesson = Lesson.objects.get(number=5)
        response = self.client.post(reverse("submit_code", args=["l05-salom"]),
                                    {"code": "print('Salom, ' + input() + '!')", "language": "python3",
                                     "lesson": lesson.pk})
        submission = Submission.objects.get()
        self.assertRedirects(response, reverse("submission_detail", args=[submission.pk]))
        self.assertEqual(submission.lesson, lesson)
        detail = self.client.get(reverse("submission_detail", args=[submission.pk]))
        self.assertContains(detail, 'hx-trigger="every 2s"')  # tugamaguncha polling

    def test_submit_errors_shown_as_message(self) -> None:
        response = self.client.post(reverse("submit_code", args=["l05-salom"]), {"code": "  "}, follow=True)
        self.assertContains(response, "Kod bo‘sh")

    def test_submit_ignores_foreign_lesson(self) -> None:
        self.client.post(reverse("submit_code", args=["l05-salom"]),
                         {"code": "print(1)", "lesson": Lesson.objects.get(number=30).pk})
        self.assertIsNone(Submission.objects.get().lesson)

    def test_get_not_allowed_for_submit(self) -> None:
        self.assertEqual(self.client.get(reverse("submit_code", args=["l05-salom"])).status_code, 405)

    def test_quiz_submit_and_result(self) -> None:
        quiz = Problem.objects.get(slug="l10-quiz")
        data = {}
        for q in quiz.questions.prefetch_related("options"):
            if q.kind == "text":
                data[f"q{q.order}"] = q.accepted_answers()[0]
            else:
                data[f"q{q.order}"] = [str(o.order) for o in q.options.all() if o.is_correct]
        response = self.client.post(reverse("submit_quiz", args=[quiz.slug]), data)
        attempt = QuizAttempt.objects.get()
        self.assertRedirects(response, reverse("quiz_result", args=[attempt.pk]))
        self.assertEqual(attempt.score, attempt.max_score)
        self.assertContains(self.client.get(reverse("quiz_result", args=[attempt.pk])), "5/5")

    def test_quiz_result_private(self) -> None:
        attempt = QuizAttempt.objects.create(user=make_user("boshqa"), problem=Problem.objects.get(slug="l10-quiz"))
        self.assertEqual(self.client.get(reverse("quiz_result", args=[attempt.pk])).status_code, 403)

    def test_project_submit(self) -> None:
        response = self.client.post(reverse("submit_project", args=["l25-vizitka"]),
                                    {"github_url": "https://github.com/ali/vizitka"}, follow=True)
        self.assertContains(response, "Loyiha topshirildi")
        self.assertEqual(ProjectSubmission.objects.count(), 1)
        response = self.client.post(reverse("submit_project", args=["l25-vizitka"]),
                                    {"github_url": "https://evil.example/x"}, follow=True)
        self.assertContains(response, "https://github.com/")
        self.assertEqual(ProjectSubmission.objects.count(), 1)

    def test_my_submissions_only_own(self) -> None:
        mine = Submission.objects.create(user=self.user, problem=Problem.objects.get(slug="l05-salom"), code="a")
        other = Submission.objects.create(user=make_user("boshqa"), problem=mine.problem, code="b")
        response = self.client.get(reverse("my_submissions") + "?verdict=")
        self.assertContains(response, reverse("submission_detail", args=[mine.pk]))
        self.assertNotContains(response, reverse("submission_detail", args=[other.pk]))


class SubmissionDetailPermissionTests(TestCase):
    def setUp(self) -> None:
        self.owner = make_user("egasi")
        self.problem = Problem.objects.get(slug="l05-salom")
        self.submission = Submission.objects.create(user=self.owner, problem=self.problem, code="MAXFIY_KOD = 1",
                                                    status=Submission.Status.DONE, verdict=Verdict.WRONG_ANSWER)
        self.url = reverse("submission_detail", args=[self.submission.pk])

    def test_owner_sees_code(self) -> None:
        self.client.force_login(self.owner)
        self.assertContains(self.client.get(self.url), "MAXFIY_KOD")

    def test_other_user_forbidden(self) -> None:
        self.client.force_login(make_user("boshqa"))
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(self.client.get(reverse("submission_status", args=[self.submission.pk])).status_code, 403)

    def test_anonymous_forbidden(self) -> None:
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_solver_and_moderator_see_code(self) -> None:
        solver = make_user("yechgan")
        Submission.objects.create(user=solver, problem=self.problem, code="x", verdict=Verdict.ACCEPTED)
        self.client.force_login(solver)
        self.assertContains(self.client.get(self.url), "MAXFIY_KOD")
        self.client.force_login(make_user("mod", Role.MODERATOR))
        self.assertContains(self.client.get(self.url), "MAXFIY_KOD")

    def test_finished_status_partial_stops_polling(self) -> None:
        self.client.force_login(self.owner)
        response = self.client.get(reverse("submission_status", args=[self.submission.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "hx-trigger")
        self.assertNotContains(response, "<html")
