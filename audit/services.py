"""Audit jurnaliga yozish uchun yordamchi funksiyalar."""

from typing import Any

from django.db import models
from django.http import HttpRequest

from .models import AuditLog


def get_client_ip(request: HttpRequest | None) -> str | None:
    """So'rovdan mijoz IP manzilini oladi (REMOTE_ADDR)."""
    if request is None:
        return None
    return request.META.get("REMOTE_ADDR") or None


def log_action(
    actor: Any,
    action: str,
    obj: models.Model | None = None,
    details: dict[str, Any] | None = None,
    request: HttpRequest | None = None,
) -> AuditLog:
    """
    Audit jurnaliga yozuv qo'shadi.

    actor — harakatni bajargan foydalanuvchi (yoki None — tizim);
    obj — harakat qaratilgan obyekt; details — JSON ga yaroqli qo'shimcha ma'lumot.
    """
    if actor is not None and not getattr(actor, "is_authenticated", False):
        actor = None
    return AuditLog.objects.create(
        actor=actor,
        action=action,
        object_type=obj._meta.label_lower if obj is not None else "",
        object_id=str(obj.pk) if obj is not None else "",
        details=details or {},
        ip=get_client_ip(request),
    )
