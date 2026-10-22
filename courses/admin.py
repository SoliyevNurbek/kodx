"""Kurs tuzilmasi va guruhlar admin paneli (moderator va undan yuqori)."""

from django.contrib import admin
from django.http import HttpRequest

from accounts.models import Role, User
from accounts.permissions import RoleAdminMixin
from audit.services import log_action

from .models import Course, Group, GroupMember, Lesson, Module


class ModuleInline(admin.TabularInline):
    model = Module
    extra = 0
    fields = ("number", "title")


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0
    fields = ("number", "title", "kind")


class GroupMemberInline(admin.TabularInline):
    model = GroupMember
    extra = 0
    fields = ("user", "is_active", "joined_at")
    readonly_fields = ("joined_at",)
    autocomplete_fields = ("user",)


@admin.register(Course)
class CourseAdmin(RoleAdminMixin, admin.ModelAdmin):
    admin_role = Role.SUPERADMIN
    admin_view_role = Role.MODERATOR
    list_display = ("title", "slug", "is_active", "created_at")
    prepopulated_fields = {"slug": ("title",)}
    inlines = (ModuleInline,)


@admin.register(Module)
class ModuleAdmin(RoleAdminMixin, admin.ModelAdmin):
    admin_role = Role.SUPERADMIN
    admin_view_role = Role.MODERATOR
    list_display = ("number", "title", "course")
    list_filter = ("course",)
    inlines = (LessonInline,)


@admin.register(Lesson)
class LessonAdmin(RoleAdminMixin, admin.ModelAdmin):
    admin_role = Role.SUPERADMIN
    admin_view_role = Role.MODERATOR
    list_display = ("number", "title", "kind", "module")
    list_filter = ("module__course", "module", "kind")
    search_fields = ("title",)


@admin.register(Group)
class GroupAdmin(RoleAdminMixin, admin.ModelAdmin):
    """Guruhlar: moderator va undan yuqori boshqaradi; o'zgarishlar auditga yoziladi."""

    admin_role = Role.MODERATOR
    list_display = ("name", "course", "teacher", "start_date", "is_active")
    list_filter = ("course", "is_active")
    search_fields = ("name",)
    inlines = (GroupMemberInline,)

    def formfield_for_foreignkey(self, db_field, request: HttpRequest, **kwargs):
        if db_field.name == "teacher":
            kwargs["queryset"] = User.objects.filter(is_active=True, role__gte=Role.MODERATOR)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request: HttpRequest, obj: Group, form, change: bool) -> None:
        super().save_model(request, obj, form, change)
        action = "group_updated" if change else "group_created"
        log_action(request.user, action, obj, {"changed": form.changed_data}, request)

    def save_formset(self, request: HttpRequest, form, formset, change: bool) -> None:
        instances = formset.save(commit=False)
        for removed in formset.deleted_objects:
            log_action(request.user, "group_member_removed", removed.group,
                       {"user": removed.user.username}, request)
            removed.delete()
        for member in instances:
            is_new = member.pk is None
            member.save()
            action = "group_member_added" if is_new else "group_member_updated"
            log_action(request.user, action, member.group,
                       {"user": member.user.username, "is_active": member.is_active}, request)
        formset.save_m2m()

    def delete_model(self, request: HttpRequest, obj: Group) -> None:
        log_action(request.user, "group_deleted", obj, {"name": obj.name}, request)
        super().delete_model(request, obj)


@admin.register(GroupMember)
class GroupMemberAdmin(RoleAdminMixin, admin.ModelAdmin):
    admin_role = Role.MODERATOR
    list_display = ("user", "group", "is_active", "joined_at")
    list_filter = ("group__course", "group", "is_active")
    search_fields = ("user__username", "group__name")
    autocomplete_fields = ("user",)

    def save_model(self, request: HttpRequest, obj: GroupMember, form, change: bool) -> None:
        super().save_model(request, obj, form, change)
        action = "group_member_updated" if change else "group_member_added"
        log_action(request.user, action, obj.group,
                   {"user": obj.user.username, "is_active": obj.is_active}, request)
