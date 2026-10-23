"""Yechimlar admin paneli (moderator va undan yuqori, faqat ko'rish + qayta tekshirish)."""

from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest

from accounts.models import Role
from accounts.permissions import RoleAdminMixin

from .models import ProjectSubmission, QuizAttempt, SimilarityMatch, Submission, SubmissionResult
from .services import rejudge


class ReadOnlyMixin(RoleAdminMixin):
    admin_role = Role.SUPERADMIN
    admin_view_role = Role.MODERATOR

    def has_add_permission(self, request: HttpRequest, *args) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj=None) -> bool:
        return False


class SubmissionResultInline(admin.TabularInline):
    model = SubmissionResult
    extra = 0
    can_delete = False
    fields = ("order", "verdict", "time_ms", "memory_kb", "points")
    readonly_fields = fields

    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        return False


@admin.register(Submission)
class SubmissionAdmin(ReadOnlyMixin, admin.ModelAdmin):
    list_display = ("id", "user", "problem", "verdict", "score", "time_ms", "status", "created_at")
    list_filter = ("verdict", "status", "language")
    search_fields = ("user__username", "problem__slug")
    list_select_related = ("user", "problem")
    readonly_fields = [f.name for f in Submission._meta.fields]
    inlines = (SubmissionResultInline,)
    actions = ("rejudge_selected",)

    @admin.action(description="Qayta tekshirish")
    def rejudge_selected(self, request: HttpRequest, queryset: QuerySet[Submission]) -> None:
        if not request.user.is_moderator:
            self.message_user(request, "Faqat moderator.", messages.ERROR)
            return
        for submission in queryset:
            rejudge(submission, request.user, request)
        self.message_user(request, f"{queryset.count()} ta yechim navbatga qo‘yildi.", messages.SUCCESS)


@admin.register(QuizAttempt)
class QuizAttemptAdmin(ReadOnlyMixin, admin.ModelAdmin):
    list_display = ("user", "problem", "score", "max_score", "created_at")
    search_fields = ("user__username", "problem__slug")
    readonly_fields = [f.name for f in QuizAttempt._meta.fields]


@admin.register(ProjectSubmission)
class ProjectSubmissionAdmin(ReadOnlyMixin, admin.ModelAdmin):
    """Loyihalar baholash navbati 5-bosqichdagi o'qituvchi panelida; admin — ko'rish uchun."""

    list_display = ("user", "problem", "status", "score", "graded_by", "created_at")
    list_filter = ("status",)
    search_fields = ("user__username", "problem__slug")
    readonly_fields = [f.name for f in ProjectSubmission._meta.fields]


@admin.register(SimilarityMatch)
class SimilarityMatchAdmin(ReadOnlyMixin, admin.ModelAdmin):
    list_display = ("problem", "submission_a", "submission_b", "score", "created_at")
    list_filter = ("problem",)
