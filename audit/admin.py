"""Audit jurnali admin paneli — faqat o'qish uchun, faqat super admin."""

from django.contrib import admin
from django.http import HttpRequest

from accounts.models import Role
from accounts.permissions import RoleAdminMixin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(RoleAdminMixin, admin.ModelAdmin):
    """Audit yozuvlarini ko'rish; qo'shish, tahrirlash va o'chirish taqiqlangan."""

    admin_role = Role.SUPERADMIN

    list_display = ("created_at", "actor", "action", "object_type", "object_id", "ip")
    list_filter = ("action", "object_type", "created_at")
    search_fields = ("actor__username", "action", "object_id")
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return False
