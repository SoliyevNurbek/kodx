"""Sayt sozlamalari admini (faqat super admin)."""

from django.contrib import admin
from django.http import HttpRequest

from accounts.models import Role
from accounts.permissions import RoleAdminMixin

from .models import SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(RoleAdminMixin, admin.ModelAdmin):
    admin_role = Role.SUPERADMIN
    list_display = ("site_name", "registration_enabled", "updated_at")

    def has_add_permission(self, request: HttpRequest, *args) -> bool:
        return self._has(request, Role.SUPERADMIN) and not SiteSettings.objects.exists()

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return False
