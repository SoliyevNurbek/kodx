"""Kontestlar admin paneli (moderator va undan yuqori)."""

from django.contrib import admin

from accounts.models import Role
from accounts.permissions import RoleAdminMixin

from .models import Contest, ContestParticipant, ContestProblem, RatingHistory


class ContestProblemInline(admin.TabularInline):
    model = ContestProblem
    extra = 0
    autocomplete_fields = ("problem",)


@admin.register(Contest)
class ContestAdmin(RoleAdminMixin, admin.ModelAdmin):
    admin_role = Role.MODERATOR
    list_display = ("title", "start_at", "duration_minutes", "scoring", "visibility", "is_rated", "owner")
    list_filter = ("scoring", "visibility", "is_rated")
    search_fields = ("title", "slug")
    exclude = ("password_hash",)
    inlines = (ContestProblemInline,)


@admin.register(ContestParticipant)
class ContestParticipantAdmin(RoleAdminMixin, admin.ModelAdmin):
    admin_role = Role.MODERATOR
    list_display = ("contest", "user", "registered_at")
    search_fields = ("user__username", "contest__title")


@admin.register(RatingHistory)
class RatingHistoryAdmin(RoleAdminMixin, admin.ModelAdmin):
    admin_role = Role.SUPERADMIN
    admin_view_role = Role.MODERATOR
    list_display = ("user", "contest", "old_rating", "new_rating", "rank", "created_at")
    search_fields = ("user__username",)
