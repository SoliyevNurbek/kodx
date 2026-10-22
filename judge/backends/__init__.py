"""Judge backend'larini tanlash."""

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .base import JudgeBackend


def get_backend(name: str | None = None) -> JudgeBackend:
    """
    Sozlamadagi (JUDGE_BACKEND) yoki nomi berilgan backend'ni qaytaradi.

    "local" — LocalDevBackend (faqat DEBUG), "judge0" — Judge0Backend.
    """
    name = name or getattr(settings, "JUDGE_BACKEND", "local")
    if name == "local":
        from .local import LocalDevBackend

        return LocalDevBackend()
    if name == "judge0":
        from .judge0 import Judge0Backend

        return Judge0Backend()
    raise ImproperlyConfigured(f"Noma'lum JUDGE_BACKEND: {name}")


__all__ = ["JudgeBackend", "get_backend"]
