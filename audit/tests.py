"""Audit jurnali va admin xavfsizligi testlari."""

from django.test import RequestFactory, TestCase
from django.urls import reverse

from accounts.models import Role, User

from .models import AuditLog
from .services import log_action


class LogActionTests(TestCase):
    """log_action yordamchisi."""

    def test_log_action_saves_object_and_ip(self) -> None:
        actor = User.objects.create_user("mod", password="Sinov-parol-2026", role=Role.MODERATOR)
        target = User.objects.create_user("talaba", password="Sinov-parol-2026")
        request = RequestFactory().get("/", REMOTE_ADDR="10.0.0.7")
        log = log_action(actor, "test_action", target, {"k": "v"}, request)
        self.assertEqual(log.object_type, "accounts.user")
        self.assertEqual(log.object_id, str(target.pk))
        self.assertEqual(log.details, {"k": "v"})
        self.assertEqual(log.ip, "10.0.0.7")


class AdminSecurityTests(TestCase):
    """Admin panelda parol ko'rinmasligi va audit jurnali o'zgarmasligi."""

    def setUp(self) -> None:
        self.admin = User.objects.create_superuser("bosh", password="Sinov-parol-2026")
        self.student = User.objects.create_user("talaba", password="Sinov-parol-2026")
        self.client.force_login(self.admin)

    def test_user_change_page_hides_password_hash(self) -> None:
        url = reverse("admin:accounts_user_change", args=[self.student.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "argon2")
        self.assertNotContains(response, self.student.password)

    def test_admin_password_change_page_disabled(self) -> None:
        url = f"/admin/accounts/user/{self.student.pk}/password/"
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 200)

    def test_role_change_in_admin_is_audited(self) -> None:
        url = reverse("admin:accounts_user_change", args=[self.student.pk])
        data = {
            "username": "talaba", "first_name": "", "last_name": "", "email": "", "bio": "",
            "role": Role.JURY, "is_active": "on",
            "last_login_0": "", "last_login_1": "",
            "date_joined_0": "2026-10-23", "date_joined_1": "10:00:00",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.student.refresh_from_db()
        self.assertEqual(self.student.role, Role.JURY)
        log = AuditLog.objects.get(action="user_updated")
        self.assertEqual(log.details["role"], {"old": Role.USER, "new": Role.JURY})

    def test_audit_log_is_read_only_in_admin(self) -> None:
        log = log_action(self.admin, "x")
        self.assertEqual(self.client.get(reverse("admin:audit_auditlog_add")).status_code, 403)
        delete_url = reverse("admin:audit_auditlog_delete", args=[log.pk])
        self.assertEqual(self.client.post(delete_url, {"post": "yes"}).status_code, 403)
        self.assertTrue(AuditLog.objects.filter(pk=log.pk).exists())
