"""Parolni majburiy almashtirish: must_change_password=True bo'lsa, boshqa sahifalar yopiq."""

from collections.abc import Callable

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse

ALLOWED_PREFIXES = ("/static/", "/media/")
ALLOWED_NAMES = ("password_change", "password_change_done", "logout")


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
