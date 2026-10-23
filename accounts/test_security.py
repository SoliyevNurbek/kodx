"""8-bosqich xavfsizlik testlari: kirish cheklovi, vaqtinchalik parol, rol so'rovi, 2FA, CSP, ko'chirmachilik."""

import subprocess
import sys
from io import StringIO

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django_otp.oath import totp
from django_otp.plugins.otp_totp.models import TOTPDevice

from audit.models import AuditLog
from judge.types import Verdict
from problems.models import Problem
from submissions.models import SimilarityMatch, Submission
from submissions.similarity import check_problem, normalize_tokens, similarity

from .models import LoginAttempt, Role, RoleRequest, User

PASSWORD = "Sinov-parol-2026"


def make_user(username: str, role: int = Role.USER) -> User:
    return User.objects.create_user(username=username, password=PASSWORD, role=role)


class LoginLockoutTests(TestCase):
    def login(self, username: str, password: str):
        return self.client.post(reverse("login"), {"username": username, "password": password})

    def test_lockout_after_five_failures(self) -> None:
        make_user("ali")
        for _ in range(5):
            self.assertEqual(self.login("ali", "noto'g'ri").status_code, 200)
        response = self.login("ali", PASSWORD)  # to'g'ri parol ham bloklangan
        self.assertContains(response, "Juda ko‘p noto‘g‘ri urinish")
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(LoginAttempt.objects.filter(username="ali", success=False).count(), 5)

    def test_other_users_not_affected_and_success_resets(self) -> None:
        make_user("ali")
        make_user("vali")
        for _ in range(4):
            self.login("ali", "xato")
        self.assertEqual(self.login("vali", PASSWORD).status_code, 302)
        self.client.logout()
        self.assertEqual(self.login("ali", PASSWORD).status_code, 302)  # 4 ta xato — hali ruxsat
        self.client.logout()
        for _ in range(4):
            self.login("ali", "xato")
        self.assertEqual(self.login("ali", PASSWORD).status_code, 302)  # muvaffaqiyatdan keyin hisob yangilandi

    def test_superadmin_failures_audited(self) -> None:
        make_user("bosh", Role.SUPERADMIN)
        self.login("bosh", "xato")
        self.assertTrue(AuditLog.objects.filter(action="superadmin_login_failed").exists())


class TemporaryPasswordTests(TestCase):
    def setUp(self) -> None:
        self.moderator = make_user("ustoz", Role.MODERATOR)
        self.student = make_user("talaba")
        self.client.force_login(self.moderator)

    def test_issue_and_forced_change(self) -> None:
        response = self.client.post(reverse("panel:temp_password", args=[self.student.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "no-store")
        password = response.context["password"]
        self.student.refresh_from_db()
        self.assertTrue(self.student.must_change_password)
        self.assertTrue(self.student.check_password(password))
        self.assertNotIn(password, self.student.password)  # bazada faqat xesh
        log = AuditLog.objects.get(action="temporary_password_issued")
        self.assertNotIn(password, str(log.details))
        self.client.logout()
        self.client.post(reverse("login"), {"username": "talaba", "password": password})
        self.assertRedirects(self.client.get(reverse("home")), reverse("password_change"))

    def test_cannot_issue_for_equal_role_or_self(self) -> None:
        other = make_user("ustoz2", Role.MODERATOR)
        self.assertEqual(self.client.post(reverse("panel:temp_password", args=[other.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse("panel:temp_password", args=[self.moderator.pk])).status_code,
                         403)

    def test_student_and_get_not_allowed(self) -> None:
        self.assertEqual(self.client.get(reverse("panel:temp_password", args=[self.student.pk])).status_code, 405)
        self.client.force_login(make_user("boshqa"))
        self.assertEqual(self.client.post(reverse("panel:temp_password", args=[self.student.pk])).status_code, 403)


class RoleRequestFlowTests(TestCase):
    def test_student_requests_jury_and_moderator_approves(self) -> None:
        student = make_user("talaba")
        self.client.force_login(student)
        self.client.post(reverse("role_request"), {"requested_role": Role.JURY, "reason": "Kontest o‘tkazaman"})
        request_obj = RoleRequest.objects.get(user=student)
        self.assertEqual(request_obj.status, RoleRequest.Status.PENDING)
        self.assertContains(self.client.get(reverse("role_request")), "ko‘rib chiqilmoqda")
        self.client.post(reverse("role_request"), {"requested_role": Role.JURY_PRO, "reason": "yana"})
        self.assertEqual(RoleRequest.objects.filter(user=student).count(), 1)  # ikkinchi kutilayotgan so'rov yo'q
        moderator = make_user("ustoz", Role.MODERATOR)
        self.client.force_login(moderator)
        self.client.post(reverse("panel:role_requests"), {"request_id": request_obj.pk, "decision": "approve"})
        student.refresh_from_db()
        self.assertEqual(student.role, Role.JURY)

    def test_role_choices_depend_on_current_role(self) -> None:
        jury = make_user("jury", Role.JURY)
        self.client.force_login(jury)
        choices = self.client.get(reverse("role_request")).context["form"].fields["requested_role"].choices
        self.assertEqual([value for value, _ in choices], [Role.JURY_PRO])
        response = self.client.post(reverse("role_request"), {"requested_role": Role.JURY, "reason": "x"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(RoleRequest.objects.exists())
        self.client.force_login(make_user("pro", Role.JURY_PRO))
        self.assertFalse(self.client.get(reverse("role_request")).context["can_request"])

    def test_requires_login(self) -> None:
        self.assertEqual(self.client.get(reverse("role_request")).status_code, 302)


class SuperadminTwoFactorTests(TestCase):
    def setUp(self) -> None:
        self.admin = make_user("bosh", Role.SUPERADMIN)

    def _token(self, device: TOTPDevice) -> str:
        return f"{totp(device.bin_key, device.step, device.t0, device.digits, device.drift):06d}"

    def test_setup_then_verify_flow(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("panel:system"))
        self.assertTrue(response["Location"].startswith(reverse("two_factor_setup")))
        setup = self.client.get(response["Location"])
        self.assertContains(setup, "<svg")
        device = TOTPDevice.objects.get(user=self.admin)
        self.assertFalse(device.confirmed)
        bad = self.client.post(reverse("two_factor_setup"), {"token": "000000", "next": "/panel/tizim/"})
        self.assertEqual(bad.status_code, 200)
        device.refresh_from_db()
        self.assertGreater(device.throttling_failure_count, 0)  # noto'g'ri kod — throttling
        device.throttle_reset()
        good = self.client.post(reverse("two_factor_setup"), {"token": self._token(device), "next": "/panel/tizim/"})
        self.assertRedirects(good, reverse("panel:system"))
        self.assertEqual(self.client.get(reverse("panel:system")).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:index")).status_code, 200)
        self.assertTrue(AuditLog.objects.filter(action="two_factor_enabled").exists())

        # Yangi sessiya: kod qayta so'raladi
        self.client.logout()
        self.client.force_login(self.admin)
        response = self.client.get(reverse("admin:index"))
        self.assertTrue(response["Location"].startswith(reverse("two_factor_verify")))
        device.refresh_from_db()
        device.last_t = -1  # testda bir xil kodni qayta ishlatishga ruxsat
        device.save()
        self.assertEqual(self.client.post(reverse("two_factor_verify"), {"token": "123456"}).status_code, 200)
        device.refresh_from_db()
        device.throttle_reset()
        ok = self.client.post(reverse("two_factor_verify"), {"token": self._token(device), "next": "/admin/"})
        self.assertRedirects(ok, reverse("admin:index"), fetch_redirect_response=False)

    def test_open_redirect_blocked(self) -> None:
        self.client.force_login(self.admin)
        self.client.get(reverse("two_factor_setup"))
        device = TOTPDevice.objects.get(user=self.admin)
        response = self.client.post(reverse("two_factor_setup"),
                                    {"token": self._token(device), "next": "https://evil.example/"})
        self.assertEqual(response["Location"], "/panel/")

    def test_moderator_not_required(self) -> None:
        self.client.force_login(make_user("ustoz", Role.MODERATOR))
        self.assertEqual(self.client.get(reverse("panel:groups")).status_code, 200)

    def test_public_pages_not_blocked(self) -> None:
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("home")).status_code, 200)


class ContentSecurityPolicyTests(TestCase):
    def test_csp_header_with_nonce(self) -> None:
        response = self.client.get(reverse("problem_detail", args=["l05-salom"]))
        csp = response["Content-Security-Policy"]
        nonce = response.wsgi_request.csp_nonce
        self.assertIn(f"'nonce-{nonce}'", csp)
        self.assertIn("frame-ancestors 'none'", csp)
        script_src = next(part for part in csp.split("; ") if part.startswith("script-src"))
        self.assertNotIn("unsafe-inline", script_src)
        self.assertNotIn("unsafe-eval", script_src)
        self.assertContains(response, f'nonce="{nonce}"')
        self.assertNotContains(response, "onclick=")

    def test_nonce_changes_per_request(self) -> None:
        first = self.client.get(reverse("home")).wsgi_request.csp_nonce
        second = self.client.get(reverse("home")).wsgi_request.csp_nonce
        self.assertNotEqual(first, second)

    def test_security_headers(self) -> None:
        response = self.client.get(reverse("home"))
        self.assertEqual(response["X-Frame-Options"], "DENY")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")


ORIGINAL = """
def solve(numbers):
    total = 0
    for value in numbers:
        if value % 2 == 0:
            total += value * value
    return total

n = int(input())
print(solve(list(map(int, input().split()))))
"""

RENAMED = """
# boshqa izoh
def hisobla(sonlar):
    jami = 0
    for x in sonlar:
        if x % 2 == 0:
            jami += x * x
    return jami

k = int(input())
print(hisobla(list(map(int, input().split()))))
"""

DIFFERENT = """
import sys
data = sys.stdin.read().split()
values = [int(v) for v in data[1:]]
print(sum(v * v for v in values if not v & 1))
"""


class SimilarityTests(TestCase):
    def setUp(self) -> None:
        self.problem = Problem.objects.get(slug="l13-max-min")
        self.users = [make_user(f"o{i}") for i in range(3)]

    def _accept(self, user: User, code: str) -> Submission:
        return Submission.objects.create(user=user, problem=self.problem, code=code, status="done",
                                         verdict=Verdict.ACCEPTED)

    def test_renamed_copy_detected_different_code_not(self) -> None:
        self.assertEqual(normalize_tokens("a = 1  # izoh"), ["ID", "=", "NUM"])
        self.assertGreater(similarity(ORIGINAL, RENAMED), 0.95)
        self.assertLess(similarity(ORIGINAL, DIFFERENT), 0.6)
        self.assertEqual(similarity("", ORIGINAL), 0.0)

    def test_check_problem_and_command(self) -> None:
        a = self._accept(self.users[0], ORIGINAL)
        b = self._accept(self.users[1], RENAMED)
        self._accept(self.users[2], DIFFERENT)
        matches = check_problem(self.problem)
        self.assertEqual([(m.submission_a_id, m.submission_b_id) for m in matches], [(a.pk, b.pk)])
        out = StringIO()
        call_command("check_similarity", problem=["l13-max-min"], stdout=out)
        self.assertIn("1 ta shubhali juftlik", out.getvalue())
        self.assertEqual(SimilarityMatch.objects.count(), 1)  # qayta ishga tushirish dublikat yaratmaydi

    def test_only_latest_per_user_and_short_code_ignored(self) -> None:
        self._accept(self.users[0], ORIGINAL)
        self._accept(self.users[0], RENAMED)  # bir foydalanuvchining o'zi bilan solishtirilmaydi
        self._accept(self.users[1], "print(1)")
        self._accept(self.users[2], "print(1)")
        self.assertEqual(check_problem(self.problem), [])

    def test_results_visible_only_to_moderators(self) -> None:
        self._accept(self.users[0], ORIGINAL)
        self._accept(self.users[1], RENAMED)
        check_problem(self.problem)
        self.client.force_login(self.users[0])
        self.assertEqual(self.client.get(reverse("panel:similarity")).status_code, 403)
        self.client.force_login(make_user("ustoz", Role.MODERATOR))
        self.assertContains(self.client.get(reverse("panel:similarity")), "o0")


class DeployCheckTests(TestCase):
    def test_check_deploy_without_warnings(self) -> None:
        result = subprocess.run(
            [sys.executable, "manage.py", "check", "--deploy", "--settings=config.settings_prod",
             "--fail-level", "WARNING"],
            cwd=settings.BASE_DIR, capture_output=True, text=True, timeout=120,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("no issues", result.stdout)
