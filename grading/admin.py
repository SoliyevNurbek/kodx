"""Baholash admin paneli."""

from django.contrib import admin

from accounts.models import Role
from accounts.permissions import RoleAdminMixin

from .models import Attendance, Badge, GradingPolicy, PracticeStats, UserBadge


@admin.register(GradingPolicy)
class GradingPolicyAdmin(RoleAdminMixin, admin.ModelAdmin):
    admin_role = Role.SUPERADMIN
    admin_view_role = Role.MODERATOR
    list_display = ("course", "attendance_points", "tasks_points", "quiz_points", "project_points",
                    "late_penalty_percent")


@admin.register(Attendance)
class AttendanceAdmin(RoleAdminMixin, admin.ModelAdmin):
    admin_role = Role.MODERATOR
    list_display = ("group", "lesson", "user", "present", "marked_by", "marked_at")
    list_filter = ("group", "present")
    search_fields = ("user__username",)


@admin.register(PracticeStats)
class PracticeStatsAdmin(RoleAdminMixin, admin.ModelAdmin):
    admin_role = Role.SUPERADMIN
    admin_view_role = Role.MODERATOR
    list_display = ("user", "score", "solved_count", "current_streak", "best_streak", "updated_at")
    search_fields = ("user__username",)


@admin.register(Badge)
class BadgeAdmin(RoleAdminMixin, admin.ModelAdmin):
    admin_role = Role.SUPERADMIN
    admin_view_role = Role.MODERATOR
    list_display = ("icon", "name", "code", "description", "order")


@admin.register(UserBadge)
class UserBadgeAdmin(RoleAdminMixin, admin.ModelAdmin):
    admin_role = Role.SUPERADMIN
    admin_view_role = Role.MODERATOR
    list_display = ("user", "badge", "awarded_at")
    search_fields = ("user__username",)
