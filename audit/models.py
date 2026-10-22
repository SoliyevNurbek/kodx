"""Audit jurnali: muhim admin harakatlarini qayd etish."""

from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """Bitta muhim harakat yozuvi (kim, nima qildi, qaysi obyekt ustida)."""

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        verbose_name="bajaruvchi",
    )
    action = models.CharField("harakat", max_length=64, db_index=True)
    object_type = models.CharField("obyekt turi", max_length=64, blank=True)
    object_id = models.CharField("obyekt ID", max_length=64, blank=True)
    details = models.JSONField("tafsilotlar", default=dict, blank=True)
    ip = models.GenericIPAddressField("IP manzil", null=True, blank=True)
    created_at = models.DateTimeField("vaqt", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "audit yozuvi"
        verbose_name_plural = "audit jurnali"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["object_type", "object_id"])]

    def __str__(self) -> str:
        actor = self.actor.username if self.actor else "tizim"
        return f"{self.created_at:%Y-%m-%d %H:%M} · {actor} · {self.action}"
