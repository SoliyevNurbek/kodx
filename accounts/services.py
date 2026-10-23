"""Hisob xavfsizligi servislari: kirish cheklovi, vaqtinchalik parol, rol so'rovi."""

import secrets
import string
from datetime import timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpRequest
from django.utils import timezone

from audit.services import get_client_ip, log_action

from .models import LoginAttempt, Role, RoleRequest, User

MAX_FAILED_LOGINS = 5
LOCKOUT_WINDOW = timedelta(minutes=15)


def is_locked_out(username: str) -> bool:
    """So'nggi 15 daqiqada shu username bo'yicha 5 ta muvaffaqiyatsiz urinish bo'lsa — vaqtincha bloklangan."""
    since = timezone.now() - LOCKOUT_WINDOW
    last_success = (LoginAttempt.objects.filter(username__iexact=username, success=True, created_at__gte=since)
                    .order_by("-created_at").values_list("created_at", flat=True).first())
    failures = LoginAttempt.objects.filter(username__iexact=username, success=False,
                                           created_at__gte=last_success or since)
    return failures.count() >= MAX_FAILED_LOGINS


def record_login_attempt(username: str, request: HttpRequest | None, success: bool) -> None:
    LoginAttempt.objects.create(username=username[:150], ip=get_client_ip(request), success=success)
    if not success:
        user = User.objects.filter(username__iexact=username).first()
        # Super admin akkauntiga muvaffaqiyatsiz urinishlar audit jurnaliga yoziladi
        if user is not None and user.is_superadmin:
            log_action(None, "superadmin_login_failed", user, request=request)


def generate_temporary_password(length: int = 12) -> str:
    """O'quvchi oson tera oladigan vaqtinchalik parol (chalkash belgilarsiz: 0/O, 1/l/I)."""
    alphabet = "".join(c for c in string.ascii_letters + string.digits if c not in "0O1lI")
    while True:
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        if any(c.isdigit() for c in password) and any(c.isalpha() for c in password):
            return password


def issue_temporary_password(actor: User, target: User, request: HttpRequest | None = None) -> str:
    """
    Moderator+ o'zidan past darajadagi foydalanuvchiga vaqtinchalik parol beradi.
    Parol faqat bir marta (shu javobda) ko'rsatiladi, bazada faqat xesh; keyingi kirishda almashtirish majburiy.
    """
    if not actor.is_moderator:
        raise PermissionDenied("Vaqtinchalik parolni faqat moderator bera oladi.")
    if target.pk == actor.pk or (not actor.is_superadmin and target.role_level >= actor.role_level):
        raise PermissionDenied("Bu foydalanuvchiga parol bera olmaysiz.")
    password = generate_temporary_password()
    target.set_password(password)
    target.must_change_password = True
    target.save(update_fields=["password", "must_change_password"])
    LoginAttempt.objects.filter(username__iexact=target.username, success=False).delete()  # blokdan chiqarish
    log_action(actor, "temporary_password_issued", target, request=request)
    return password


def create_role_request(user: User, requested_role: int, reason: str = "") -> RoleRequest:
    """O'quvchi Jury (yoki Jury → Jury Pro) rolini so'raydi."""
    if requested_role not in RoleRequest.REQUESTABLE_ROLES:
        raise ValidationError("Bu rolni so‘rab bo‘lmaydi.")
    if user.role_level >= requested_role:
        raise ValidationError("Sizda bu rol (yoki undan yuqorisi) allaqachon bor.")
    role_request = RoleRequest(user=user, requested_role=requested_role, reason=reason.strip()[:1000])
    role_request.full_clean()
    role_request.save()
    log_action(user, "role_requested", role_request, {"role": int(requested_role)})
    return role_request


def requestable_roles(user: User) -> list[tuple[int, str]]:
    return [(r.value, r.label) for r in (Role.JURY, Role.JURY_PRO) if user.role_level < r]
