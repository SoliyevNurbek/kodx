"""Rol panellari view testlari: har sahifa uchun ruxsat bor / yo'q va asosiy amallar."""

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import Role, RoleRequest, User
from audit.models import AuditLog
from core.models import SiteSettings
from courses.models import Group, GroupMember
from judge.types import Verdict
from problems.models import Problem
from submissions.models import ProjectSubmission, Submission

PASSWORD = "Sinov-parol-2026"


def make_user(username: str, role: int = Role.USER) -> User:
    return User.objects.create_user(username=username, password=PASSWORD, role=role)


@override_settings(KODX_REQUIRE_SUPERADMIN_2FA=False)  # 2FA alohida testlanadi
class PanelAccessMatrixTests(TestCase):
    """Har bir panel sahifasi uchun minimal rol."""

    PAGES = {
        Role.JURY: ["panel:home"],
        Role.JURY_PRO: ["panel:my_problems", "panel:problem_create"],
        Role.MODERATOR: ["panel:groups", "panel:submissions", "panel:projects", "panel:role_requests", "panel:users"],
        Role.SUPERADMIN: ["panel:system", "panel:audit"],
    }

    def setUp(self) -> None:
        self.users = {role: make_user(f"u{role.value}", role) for role in Role}

    def test_anonymous_redirected_to_login(self) -> None:
        for names in self.PAGES.values():
            for name in names:
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 302, name)
                self.assertIn(reverse("login"), response["Location"])

    def test_role_matrix(self) -> None:
        for required, names in self.PAGES.items():
            for role, user in self.users.items():
                self.client.force_login(user)
                for name in names:
                    expected = 200 if role >= required else 403
                    self.assertEqual(self.client.get(reverse(name)).status_code, expected,
                                     f"{name} — {role.label}")


class TeacherPanelTests(TestCase):
    def setUp(self) -> None:
        self.moderator = make_user("ustoz", Role.MODERATOR)
        self.student = make_user("talaba")
        self.group = Group.objects.get(name="Python-1")
        GroupMember.objects.create(group=self.group, user=self.student)
        self.client.force_login(self.moderator)

    def test_group_progress_matrix(self) -> None:
        Submission.objects.create(user=self.student, problem=Problem.objects.get(slug="l05-salom"), code="x",
                                  verdict=Verdict.ACCEPTED)
        response = self.client.get(reverse("panel:group_progress", args=[self.group.pk]))
        self.assertEqual(response.status_code, 200)
        row = response.context["rows"][0]
        self.assertEqual(row["user"], self.student)
        lesson5 = next(c for c in row["cells"] if c["lesson"].number == 5)
        self.assertEqual((lesson5["done"], lesson5["total"]), (1, 3))  # 2 code (majburiy) + quiz
        self.assertEqual(row["total"], 1)

    def test_submissions_feed_filter_by_group(self) -> None:
        mine = Submission.objects.create(user=self.student, problem=Problem.objects.get(slug="l05-salom"), code="x")
        outsider = Submission.objects.create(user=make_user("begona"), problem=mine.problem, code="y")
        response = self.client.get(reverse("panel:submissions") + f"?group={self.group.pk}")
        ids = [s.pk for s in response.context["page"]]
        self.assertIn(mine.pk, ids)
        self.assertNotIn(outsider.pk, ids)

    def test_project_grading(self) -> None:
        project = Problem.objects.get(slug="l25-vizitka")
        submission = ProjectSubmission.objects.create(user=self.student, problem=project,
                                                      github_url="https://github.com/t/v")
        url = reverse("panel:project_grade", args=[submission.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        data = {f"c{c.order}": c.max_points for c in project.rubric.all()} | {"feedback": "Barakalla"}
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse("panel:projects"))
        submission.refresh_from_db()
        self.assertEqual((submission.score, submission.status), (100, ProjectSubmission.Status.GRADED))

    def test_project_grading_rejects_too_many_points(self) -> None:
        project = Problem.objects.get(slug="l25-vizitka")
        submission = ProjectSubmission.objects.create(user=self.student, problem=project,
                                                      github_url="https://github.com/t/v")
        response = self.client.post(reverse("panel:project_grade", args=[submission.pk]), {"c1": 999})
        self.assertEqual(response.status_code, 200)
        submission.refresh_from_db()
        self.assertEqual(submission.status, ProjectSubmission.Status.SUBMITTED)

    def test_role_request_approval(self) -> None:
        role_request = RoleRequest.objects.create(user=self.student, requested_role=Role.JURY)
        response = self.client.post(reverse("panel:role_requests"),
                                    {"request_id": role_request.pk, "decision": "approve"})
        self.assertRedirects(response, reverse("panel:role_requests"))
        self.student.refresh_from_db()
        self.assertEqual(self.student.role, Role.JURY)

    def test_role_assignment_limits(self) -> None:
        url = reverse("panel:users")
        self.client.post(url, {"user_id": self.student.pk, "role": Role.JURY_PRO})
        self.student.refresh_from_db()
        self.assertEqual(self.student.role, Role.JURY_PRO)
        self.assertTrue(AuditLog.objects.filter(action="user_role_changed", actor=self.moderator).exists())
        # moderator moderator tayinlay olmaydi
        self.assertEqual(self.client.post(url, {"user_id": self.student.pk, "role": Role.MODERATOR}).status_code, 403)
        # boshqa moderatorning rolini o'zgartira olmaydi
        other = make_user("mod2", Role.MODERATOR)
        self.assertEqual(self.client.post(url, {"user_id": other.pk, "role": Role.USER}).status_code, 403)
        # o'zining rolini o'zgartira olmaydi
        self.assertEqual(self.client.post(url, {"user_id": self.moderator.pk, "role": Role.USER}).status_code, 403)


class JuryProPanelTests(TestCase):
    def setUp(self) -> None:
        self.author = make_user("muallif", Role.JURY_PRO)
        self.client.force_login(self.author)

    def _create(self, slug: str = "mening-masalam") -> Problem:
        response = self.client.post(reverse("panel:problem_create"), {
            "title": "Mening masalam", "slug": slug, "type": "code", "difficulty": 2, "points": 200,
            "statement": "Ikki sonni qo‘shing.", "time_limit": 1000, "memory_limit": 256, "checker": "whitespace",
            "float_epsilon": 1e-6, "reference_solution": "print(sum(map(int, input().split())))",
        })
        self.assertRedirects(response, reverse("panel:problem_tests", args=[slug]))
        return Problem.objects.get(slug=slug)

    def _upload(self, problem: Problem, inp: bytes = b"2 3\n", out: bytes = b"5\n", name: str = "t.in"):
        return self.client.post(reverse("panel:problem_tests", args=[problem.slug]), {
            "input_file": SimpleUploadedFile(name, inp), "output_file": SimpleUploadedFile("t.out", out),
            "is_sample": "on", "points": 1,
        })

    def test_create_problem_as_draft(self) -> None:
        problem = self._create()
        self.assertEqual((problem.author, problem.status), (self.author, Problem.Status.DRAFT))
        self.assertTrue(AuditLog.objects.filter(action="problem_created", actor=self.author).exists())

    def test_upload_tests_and_validation(self) -> None:
        problem = self._create()
        self.assertRedirects(self._upload(problem), reverse("panel:problem_tests", args=[problem.slug]))
        test = problem.test_cases.get()
        self.assertEqual((test.order, test.read_input()), (1, "2 3\n"))
        self.assertEqual(self._upload(problem, name="virus.exe").status_code, 200)
        self.assertEqual(self._upload(problem, inp=b"\xff\xfe\x00bad").status_code, 200)
        self.assertEqual(problem.test_cases.count(), 1)

    def test_delete_test(self) -> None:
        problem = self._create()
        self._upload(problem)
        test = problem.test_cases.get()
        self.client.post(reverse("panel:test_delete", args=[problem.slug, test.pk]))
        self.assertFalse(problem.test_cases.exists())

    def test_check_with_reference_goes_through_queue(self) -> None:
        problem = self._create()
        self._upload(problem)
        response = self.client.post(reverse("panel:problem_check", args=[problem.slug]))
        submission = Submission.objects.get(problem=problem)
        self.assertRedirects(response, reverse("submission_detail", args=[submission.pk]))
        self.assertEqual(submission.status, Submission.Status.QUEUED)  # web jarayonda bajarilmadi

    def test_submit_for_review(self) -> None:
        problem = self._create()
        self.client.post(reverse("panel:problem_submit_review", args=[problem.slug]))
        problem.refresh_from_db()
        self.assertEqual(problem.status, Problem.Status.DRAFT)  # testsiz yuborilmaydi
        self._upload(problem)
        self.client.post(reverse("panel:problem_submit_review", args=[problem.slug]))
        problem.refresh_from_db()
        self.assertEqual(problem.status, Problem.Status.REVIEW)

    def test_cannot_edit_others_problem(self) -> None:
        foreign = Problem.objects.get(slug="l05-salom")  # muallifi nurbek
        for name in ("panel:problem_edit", "panel:problem_tests"):
            self.assertEqual(self.client.get(reverse(name, args=[foreign.slug])).status_code, 403, name)
        self.assertEqual(self.client.post(reverse("panel:problem_check", args=[foreign.slug])).status_code, 403)
        self.assertEqual(self.client.post(reverse("panel:problem_submit_review", args=[foreign.slug])).status_code,
                         403)

    def test_edit_own_problem_slug_locked(self) -> None:
        problem = self._create()
        response = self.client.post(reverse("panel:problem_edit", args=[problem.slug]), {
            "title": "Yangi nom", "slug": "boshqa-slug", "type": "code", "difficulty": 3, "points": 300,
            "statement": "x", "time_limit": 2000, "memory_limit": 128, "checker": "exact", "float_epsilon": 1e-6,
        })
        self.assertRedirects(response, reverse("panel:problem_edit", args=[problem.slug]))
        problem.refresh_from_db()
        self.assertEqual((problem.title, problem.slug), ("Yangi nom", "mening-masalam"))

    def test_draft_visible_to_author_only(self) -> None:
        problem = self._create()
        self.assertEqual(self.client.get(reverse("problem_detail", args=[problem.slug])).status_code, 200)
        self.client.force_login(make_user("talaba"))
        self.assertEqual(self.client.get(reverse("problem_detail", args=[problem.slug])).status_code, 404)


@override_settings(KODX_REQUIRE_SUPERADMIN_2FA=False)  # 2FA alohida testlanadi
class SuperadminPanelTests(TestCase):
    def setUp(self) -> None:
        self.admin = make_user("bosh", Role.SUPERADMIN)
        self.client.force_login(self.admin)

    def test_site_settings_update(self) -> None:
        response = self.client.post(reverse("panel:system"), {
            "site_name": "kodx", "tagline": "Yangi shior", "color_background": "#101010",
            "color_accent": "#00FF00", "color_gold": "#D9B25F",
        })
        self.assertRedirects(response, reverse("panel:system"))
        settings = SiteSettings.load()
        self.assertFalse(settings.registration_enabled)
        self.assertEqual(settings.color_accent, "#00FF00")
        self.assertTrue(AuditLog.objects.filter(action="site_settings_updated").exists())
        self.assertContains(self.client.get(reverse("home")), "--kx-accent: #00FF00")

    def test_invalid_color_rejected(self) -> None:
        response = self.client.post(reverse("panel:system"), {
            "site_name": "kodx", "tagline": "x", "color_background": "red;}</style>",
            "color_accent": "#00FF00", "color_gold": "#D9B25F",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SiteSettings.load().color_background, "#0E1A2E")

    def test_system_status_and_audit_pages(self) -> None:
        response = self.client.get(reverse("panel:system"))
        self.assertEqual(response.context["status"]["queue_size"], 0)
        self.assertTrue(response.context["status"]["worker_ok"])
        AuditLog.objects.create(actor=self.admin, action="test_action")
        response = self.client.get(reverse("panel:audit") + "?action=test_action&actor=bosh")
        self.assertContains(response, "test_action")
