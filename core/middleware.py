"""Xavfsizlik middleware'lari: majburiy parol almashtirish, super admin 2FA, CSP."""

import secrets
from collections.abc import Callable
from urllib.parse import urlencode

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse

ALLOWED_PREFIXES = ("/static/", "/media/")
ALLOWED_NAMES = ("password_change", "password_change_done", "logout", "two_factor_setup", "two_factor_verify")


class ForcePasswordChangeMiddleware:
    """Vaqtinchalik paroldan keyin foydalanuvchi avval yangi parol o'rnatadi."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated and getattr(user, "must_change_password", False):
            allowed = {reverse(name) for name in ALLOWED_NAMES}
            if request.path not in allowed and not request.path.startswith(ALLOWED_PREFIXES):
                return redirect("password_change")
        return self.get_response(request)


class SuperadminOTPMiddleware:
    """
    Super admin /panel/ va /admin/ sahifalariga faqat TOTP (2FA) tasdiqlangan sessiyada kiradi.
    Qurilma ulanmagan bo'lsa — ulash sahifasiga, ulangan bo'lsa — kod so'rash sahifasiga yuboriladi.
    """

    PROTECTED_PREFIXES = ("/panel/", "/admin/")

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        user = getattr(request, "user", None)
        if (settings.KODX_REQUIRE_SUPERADMIN_2FA and user is not None and user.is_authenticated
                and user.is_superadmin and request.path.startswith(self.PROTECTED_PREFIXES)
                and not user.is_verified()):
            from django_otp.plugins.otp_totp.models import TOTPDevice

            has_device = TOTPDevice.objects.filter(user=user, confirmed=True).exists()
            target = reverse("two_factor_verify" if has_device else "two_factor_setup")
            return redirect(f"{target}?{urlencode({'next': request.get_full_path()})}")
        return self.get_response(request)


# Tashqi manbalar: Tailwind (CDN), HTMX (unpkg), KaTeX (jsdelivr), CodeMirror (esm.sh)
CSP_SCRIPT_SOURCES = "https://cdn.tailwindcss.com https://unpkg.com https://cdn.jsdelivr.net https://esm.sh"


class ContentSecurityPolicyMiddleware:
    """
    Content-Security-Policy sarlavhasi. Inline skriptlar faqat har so'rov uchun yangi nonce bilan
    (`{{ request.csp_nonce }}`); inline `on*` handler'lar ishlamaydi.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request.csp_nonce = secrets.token_urlsafe(16)
        response = self.get_response(request)
        if settings.CSP_ENABLED and "Content-Security-Policy" not in response:
            response["Content-Security-Policy"] = "; ".join([
                "default-src 'self'",
                f"script-src 'self' 'nonce-{request.csp_nonce}' {CSP_SCRIPT_SOURCES}",
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
                "font-src 'self' data: https://cdn.jsdelivr.net",
                "img-src 'self' data: blob:",
                "connect-src 'self' https://esm.sh",
                "object-src 'none'",
                "base-uri 'self'",
                "form-action 'self'",
                "frame-ancestors 'none'",
            ])
        return response
