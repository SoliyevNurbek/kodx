"""
Rolga asoslangan ruxsatlar: view dekoratori, CBV mixin va admin mixin.

Rollar ierarxiyasi CLAUDE.md dagi 5 daraja (accounts.models.Role).
"""

from collections.abc import Callable
from functools import wraps
from typing import Any

from django.contrib.auth.mixins import AccessMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse

from .models import Role


def user_has_role(user: Any, role: int) -> bool:
    """Foydalanuvchi autentifikatsiyadan o'tgan va kamida `role` darajasida."""
    return bool(user and user.is_authenticated and user.has_role_at_least(role))


def role_required(role: int) -> Callable:
    """
    Funksiya-view uchun dekorator.

    Anonim foydalanuvchi login sahifasiga yuboriladi, darajasi yetmagan — 403.
    """

    def decorator(view: Callable[..., HttpResponse]) -> Callable[..., HttpResponse]:
        @wraps(view)
        def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if not request.user.has_role_at_least(role):
                raise PermissionDenied("Bu sahifa uchun huquqingiz yetarli emas.")
            return view(request, *args, **kwargs)

        return wrapper

    return decorator


class RoleRequiredMixin(AccessMixin):
    """Class-based view uchun: `required_role` darajasini talab qiladi."""

    required_role: int = Role.USER

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.has_role_at_least(self.required_role):
            raise PermissionDenied("Bu sahifa uchun huquqingiz yetarli emas.")
        return super().dispatch(request, *args, **kwargs)


class RoleAdminMixin:
    """
    ModelAdmin uchun: Django model-permission o'rniga rol darajasi ishlatiladi.

    `admin_role` — ko'rish va boshqarish uchun minimal rol.
    `admin_view_role` — faqat ko'rish uchun (standart: admin_role).
    """

    admin_role: int = Role.SUPERADMIN
    admin_view_role: int | None = None

    def _has(self, request: HttpRequest, role: int) -> bool:
        user = request.user
        return bool(user.is_active and user.is_staff and user_has_role(user, role))

    def has_module_permission(self, request: HttpRequest) -> bool:
        return self._has(request, self.admin_view_role or self.admin_role)

    def has_view_permission(self, request: HttpRequest, obj=None) -> bool:
        return self._has(request, self.admin_view_role or self.admin_role)

    def has_add_permission(self, request: HttpRequest, *args) -> bool:
        return self._has(request, self.admin_role)

    def has_change_permission(self, request: HttpRequest, obj=None) -> bool:
        return self._has(request, self.admin_role)

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return self._has(request, self.admin_role)
