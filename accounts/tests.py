"""Rollar ierarxiyasi va rol so'rovlari testlari."""

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from audit.models import AuditLog

from .models import Role, RoleRequest, User


def make_user(username: str, role: int = Role.USER, **extra) -> User:
    """Test uchun foydalanuvchi yaratadi."""
    return User.objects.create_user(username=username, password="Sinov-parol-2026", role=role, **extra)


class RoleHierarchyTests(TestCase):
    """has_role_at_least va rol xossalari."""

    def test_each_role_includes_lower_roles(self) -> None:
        for level in Role:
            user = make_user(f"u{level.value}", role=level)
            for other in Role:
                self.assertEqual(
                    user.has_role_at_least(other),
                    level >= other,
                    f"{level.label} → {other.label}",
                )

    def test_plain_user_has_no_staff_roles(self) -> None:
        user = make_user("oddiy")
        self.assertTrue(user.has_role_at_least(Role.USER))
        self.assertFalse(user.is_jury)
        self.assertFalse(user.is_jury_pro)
        self.assertFalse(user.is_moderator)
        self.assertFalse(user.is_superadmin)

    def test_jury_pro_is_jury_but_not_moderator(self) -> None:
        user = make_user("pro", role=Role.JURY_PRO)
        self.assertTrue(user.is_jury)
        self.assertTrue(user.is_jury_pro)
        self.assertFalse(user.is_moderator)

    def test_create_superuser_gets_superadmin_role(self) -> None:
        admin = User.objects.create_superuser("bosh", password="Sinov-parol-2026")
        self.assertEqual(admin.role, Role.SUPERADMIN)
        self.assertTrue(admin.is_superadmin)

    def test_django_superuser_flag_counts_as_superadmin(self) -> None:
        user = make_user("flag", is_superuser=True)
        self.assertEqual(user.role, Role.USER)
        self.assertTrue(user.is_superadmin)

    def test_inactive_user_has_no_roles(self) -> None:
        user = make_user("bloklangan", role=Role.MODERATOR, is_active=False)
        self.assertFalse(user.has_role_at_least(Role.USER))
        self.assertFalse(user.is_moderator)

    def test_can_assign_role(self) -> None:
        moderator = make_user("mod", role=Role.MODERATOR)
        superadmin = make_user("sa", role=Role.SUPERADMIN)
        jury = make_user("jury", role=Role.JURY)
        self.assertTrue(moderator.can_assign_role(Role.JURY_PRO))
        self.assertFalse(moderator.can_assign_role(Role.MODERATOR))
        self.assertFalse(moderator.can_assign_role(Role.SUPERADMIN))
        self.assertTrue(superadmin.can_assign_role(Role.MODERATOR))
        self.assertFalse(jury.can_assign_role(Role.JURY))


class UserFieldTests(TestCase):
    """Parol xeshlash va email cheklovlari."""

    def test_password_hashed_with_argon2(self) -> None:
        user = make_user("xesh")
        self.assertTrue(user.password.startswith("argon2"))
        self.assertTrue(user.check_password("Sinov-parol-2026"))

    def test_blank_email_saved_as_null_and_not_unique_conflict(self) -> None:
        a = make_user("a", email="")
        b = make_user("b", email="")
        a.refresh_from_db()
        b.refresh_from_db()
        self.assertIsNone(a.email)
        self.assertIsNone(b.email)

    def test_filled_email_is_unique(self) -> None:
        from django.db import IntegrityError, transaction

        make_user("c", email="x@kodx.uz")
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_user("d", email="x@kodx.uz")


class RoleRequestTests(TestCase):
    """Rol so'rovlarini ko'rib chiqish."""

    def setUp(self) -> None:
        self.student = make_user("talaba")
        self.moderator = make_user("moderator", role=Role.MODERATOR)
        self.request = RoleRequest.objects.create(user=self.student, requested_role=Role.JURY)

    def test_approve_grants_role_and_writes_audit(self) -> None:
        self.request.approve(self.moderator)
        self.student.refresh_from_db()
        self.request.refresh_from_db()
        self.assertEqual(self.student.role, Role.JURY)
        self.assertEqual(self.request.status, RoleRequest.Status.APPROVED)
        self.assertEqual(self.request.reviewed_by, self.moderator)
        log = AuditLog.objects.get(action="role_request_approved")
        self.assertEqual(log.actor, self.moderator)
        self.assertEqual(log.object_id, str(self.request.pk))

    def test_reject_keeps_role(self) -> None:
        self.request.reject(self.moderator, comment="Hali erta")
        self.student.refresh_from_db()
        self.assertEqual(self.student.role, Role.USER)
        self.assertTrue(AuditLog.objects.filter(action="role_request_rejected").exists())

    def test_non_moderator_cannot_review(self) -> None:
        jury_pro = make_user("pro", role=Role.JURY_PRO)
        with self.assertRaises(PermissionDenied):
            self.request.approve(jury_pro)
        self.student.refresh_from_db()
        self.assertEqual(self.student.role, Role.USER)
        self.assertFalse(AuditLog.objects.exists())

    def test_cannot_review_twice(self) -> None:
        self.request.approve(self.moderator)
        with self.assertRaises(ValidationError):
            self.request.reject(self.moderator)

    def test_only_one_pending_request_per_user(self) -> None:
        second = RoleRequest(user=self.student, requested_role=Role.JURY_PRO)
        with self.assertRaises(ValidationError):
            second.full_clean()


class PermissionToolTests(TestCase):
    """role_required, RoleRequiredMixin va is_staff sinxronizatsiyasi."""

    def setUp(self) -> None:
        from django.http import HttpResponse
        from django.test import RequestFactory
        from django.views import View

        from .permissions import RoleRequiredMixin, role_required

        self.factory = RequestFactory()

        @role_required(Role.JURY_PRO)
        def fn_view(request):
            return HttpResponse("ok")

        class CbView(RoleRequiredMixin, View):
            required_role = Role.MODERATOR

            def get(self, request):
                return HttpResponse("ok")

        self.fn_view = fn_view
        self.cb_view = CbView.as_view()

    def _request(self, user=None):
        from django.contrib.auth.models import AnonymousUser

        request = self.factory.get("/panel/")
        request.user = user or AnonymousUser()
        return request

    def test_decorator_redirects_anonymous_to_login(self) -> None:
        response = self.fn_view(self._request())
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response["Location"])

    def test_decorator_denies_lower_role_and_allows_higher(self) -> None:
        with self.assertRaises(PermissionDenied):
            self.fn_view(self._request(make_user("j", role=Role.JURY)))
        self.assertEqual(self.fn_view(self._request(make_user("jp", role=Role.JURY_PRO))).status_code, 200)
        self.assertEqual(self.fn_view(self._request(make_user("m", role=Role.MODERATOR))).status_code, 200)

    def test_mixin_checks_role(self) -> None:
        with self.assertRaises(PermissionDenied):
            self.cb_view(self._request(make_user("jp", role=Role.JURY_PRO)))
        self.assertEqual(self.cb_view(self._request(make_user("m", role=Role.MODERATOR))).status_code, 200)
        self.assertEqual(self.cb_view(self._request()).status_code, 302)

    def test_is_staff_follows_role(self) -> None:
        user = make_user("o")
        self.assertFalse(user.is_staff)
        user.role = Role.MODERATOR
        user.save(update_fields=["role"])
        user.refresh_from_db()
        self.assertTrue(user.is_staff)
        user.role = Role.JURY
        user.save()
        self.assertFalse(user.is_staff)


class ModeratorAdminTests(TestCase):
    """Moderatorning admin paneldagi chegaralari."""

    def setUp(self) -> None:
        from django.urls import reverse

        self.reverse = reverse
        self.moderator = make_user("mod", role=Role.MODERATOR)
        self.client.force_login(self.moderator)

    def test_moderator_cannot_edit_other_moderator(self) -> None:
        other = make_user("mod2", role=Role.MODERATOR)
        url = self.reverse("admin:accounts_user_change", args=[other.pk])
        response = self.client.post(url, {"username": "mod2", "role": Role.USER})
        self.assertEqual(response.status_code, 403)
        other.refresh_from_db()
        self.assertEqual(other.role, Role.MODERATOR)

    def test_moderator_role_choices_limited(self) -> None:
        student = make_user("talaba")
        response = self.client.get(self.reverse("admin:accounts_user_change", args=[student.pk]))
        self.assertEqual(response.status_code, 200)
        choices = [value for value, _ in response.context["adminform"].form.fields["role"].choices]
        self.assertEqual(choices, [Role.USER, Role.JURY, Role.JURY_PRO])

    def test_moderator_cannot_view_audit_log(self) -> None:
        response = self.client.get(self.reverse("admin:audit_auditlog_changelist"))
        self.assertEqual(response.status_code, 403)

    def test_moderator_cannot_delete_users(self) -> None:
        student = make_user("talaba")
        response = self.client.post(self.reverse("admin:accounts_user_delete", args=[student.pk]), {"post": "yes"})
        self.assertEqual(response.status_code, 403)
        self.assertTrue(User.objects.filter(pk=student.pk).exists())
