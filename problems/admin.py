"""Vazifalar banki admin paneli."""

from django.contrib import admin, messages
from django.db.models import Count, QuerySet
from django.http import HttpRequest

from accounts.models import Role
from accounts.permissions import RoleAdminMixin
from audit.services import log_action

from .models import LessonProblem, Problem, QuizOption, QuizQuestion, RubricCriterion, Tag, TestCase


class TestCaseInline(admin.TabularInline):
    model = TestCase
    extra = 0
    fields = ("order", "input_file", "output_file", "is_sample", "points")


class RubricInline(admin.TabularInline):
    model = RubricCriterion
    extra = 0
    fields = ("order", "title", "max_points", "description")


class LessonProblemInline(admin.TabularInline):
    model = LessonProblem
    extra = 0
    fields = ("lesson", "kind", "order", "deadline", "is_required")
    autocomplete_fields = ("lesson",)


class QuizOptionInline(admin.TabularInline):
    model = QuizOption
    extra = 0
    fields = ("order", "text", "is_correct")


@admin.register(Tag)
class TagAdmin(RoleAdminMixin, admin.ModelAdmin):
    admin_role = Role.MODERATOR
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Problem)
class ProblemAdmin(RoleAdminMixin, admin.ModelAdmin):
    """
    Moderator hamma vazifani ko'radi va nashr etadi; tahrirlash — muallif (Jury Pro) yoki super admin.
    Jury Pro o'z vazifalarini 5-bosqichdagi panel orqali boshqaradi.
    """

    admin_role = Role.SUPERADMIN
    admin_view_role = Role.MODERATOR
    list_display = ("slug", "title", "type", "status", "difficulty", "author", "test_count", "is_seed")
    list_filter = ("type", "status", "difficulty", "is_seed", "tags")
    search_fields = ("slug", "title")
    filter_horizontal = ("tags",)
    readonly_fields = ("created_at", "updated_at")
    inlines = (TestCaseInline, RubricInline, LessonProblemInline)
    actions = ("publish", "send_to_review", "unpublish")
    fieldsets = (
        (None, {"fields": ("slug", "title", "type", "status", "author", "difficulty", "points", "tags", "is_seed")}),
        ("Shart", {"fields": ("statement", "input_format", "output_format", "notes")}),
        ("Tekshiruv", {"fields": ("time_limit", "memory_limit", "checker", "float_epsilon", "reference_solution")}),
        ("Sanalar", {"fields": ("created_at", "updated_at")}),
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[Problem]:
        return super().get_queryset(request).select_related("author").annotate(_tests=Count("test_cases"))

    @admin.display(description="testlar", ordering="_tests")
    def test_count(self, obj: Problem) -> int:
        return obj._tests

    def has_change_permission(self, request: HttpRequest, obj: Problem | None = None) -> bool:
        if obj is not None:
            return request.user.is_staff and obj.can_edit(request.user)
        return super().has_change_permission(request, obj)

    def save_model(self, request: HttpRequest, obj: Problem, form, change: bool) -> None:
        super().save_model(request, obj, form, change)
        log_action(request.user, "problem_updated" if change else "problem_created", obj,
                   {"changed": form.changed_data}, request)

    def _set_status(self, request: HttpRequest, queryset: QuerySet[Problem], status: str, action: str) -> None:
        if not request.user.is_moderator:
            self.message_user(request, "Faqat moderator holatni o‘zgartira oladi.", messages.ERROR)
            return
        for problem in queryset:
            old = problem.status
            problem.status = status
            problem.save(update_fields=["status", "updated_at"])
            log_action(request.user, action, problem, {"old": old, "new": status}, request)
        self.message_user(request, f"{queryset.count()} ta vazifa yangilandi.", messages.SUCCESS)

    @admin.action(description="Nashr etish")
    def publish(self, request: HttpRequest, queryset: QuerySet[Problem]) -> None:
        self._set_status(request, queryset, Problem.Status.PUBLISHED, "problem_published")

    @admin.action(description="Ko‘rib chiqishga yuborish")
    def send_to_review(self, request: HttpRequest, queryset: QuerySet[Problem]) -> None:
        self._set_status(request, queryset, Problem.Status.REVIEW, "problem_sent_to_review")

    @admin.action(description="Qoralamaga qaytarish")
    def unpublish(self, request: HttpRequest, queryset: QuerySet[Problem]) -> None:
        self._set_status(request, queryset, Problem.Status.DRAFT, "problem_unpublished")


@admin.register(QuizQuestion)
class QuizQuestionAdmin(RoleAdminMixin, admin.ModelAdmin):
    admin_role = Role.SUPERADMIN
    admin_view_role = Role.MODERATOR
    list_display = ("problem", "order", "kind", "points")
    list_filter = ("kind",)
    search_fields = ("problem__slug", "text")
    inlines = (QuizOptionInline,)


@admin.register(LessonProblem)
class LessonProblemAdmin(RoleAdminMixin, admin.ModelAdmin):
    admin_role = Role.MODERATOR
    list_display = ("lesson", "problem", "kind", "deadline", "is_required")
    list_filter = ("kind", "lesson__module", "is_required")
    search_fields = ("problem__slug", "lesson__title")
    autocomplete_fields = ("lesson", "problem")
