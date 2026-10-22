"""Foydalanuvchilar va rol so'rovlari admin paneli."""

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import QuerySet
from django.http import HttpRequest

from audit.services import log_action

from .models import RoleRequest, User

# O'zgarishi audit jurnaliga yoziladigan maydonlar
SENSITIVE_FIELDS = ("role", "is_active", "is_staff", "is_superuser", "must_change_password")


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Foydalanuvchilar admini.

    Parol maydoni (hatto xesh ham) hech qayerda ko'rsatilmaydi va parolni
    to'g'ridan-to'g'ri almashtirish sahifasi o'chirilgan — faqat
    "qayta tiklashga majburlash" mumkin.
    """

    list_display = ("username", "first_name", "last_name", "role", "rating", "is_active", "date_joined")
    list_filter = ("role", "is_active", "is_staff", "must_change_password")
    search_fields = ("username", "first_name", "last_name", "email")
    ordering = ("-date_joined",)
    readonly_fields = ("last_login", "date_joined", "rating")
    actions = ("force_password_reset",)

    fieldsets = (
        (None, {"fields": ("username",)}),
        ("Shaxsiy ma'lumotlar", {"fields": ("first_name", "last_name", "email", "bio", "avatar")}),
        ("Rol va reyting", {"fields": ("role", "rating")}),
        ("Holat", {"fields": ("is_active", "must_change_password", "is_staff", "is_superuser")}),
        ("Sanalar", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("username", "role", "password1", "password2")}),
    )

    def get_urls(self):
        """Parolni admin tomonidan almashtirish sahifasini olib tashlaydi."""
        return [u for u in super().get_urls() if "password" not in str(u.pattern)]

    def save_model(self, request: HttpRequest, obj: User, form, change: bool) -> None:
        """Rol huquqini tekshiradi va muhim o'zgarishlarni audit jurnaliga yozadi."""
        changed = [f for f in SENSITIVE_FIELDS if f in form.changed_data]
        if "role" in changed and not request.user.can_assign_role(obj.role):
            raise PermissionDenied("Bu rolni berishga huquqingiz yo'q.")
        super().save_model(request, obj, form, change)
        if not change:
            log_action(request.user, "user_created", obj, {"role": obj.role}, request)
        elif changed:
            details = {f: {"old": form.initial.get(f), "new": getattr(obj, f)} for f in changed}
            log_action(request.user, "user_updated", obj, details, request)

    @admin.action(description="Parolni qayta tiklashga majburlash")
    def force_password_reset(self, request: HttpRequest, queryset: QuerySet[User]) -> None:
        """Tanlangan foydalanuvchilarni keyingi kirishda parol almashtirishga majburlaydi."""
        for user in queryset:
            user.must_change_password = True
            user.save(update_fields=["must_change_password"])
            log_action(request.user, "user_force_password_reset", user, request=request)
        self.message_user(request, f"{queryset.count()} ta foydalanuvchi belgilandi.", messages.SUCCESS)


@admin.register(RoleRequest)
class RoleRequestAdmin(admin.ModelAdmin):
    """Rol so'rovlari: tasdiqlash va rad etish admin harakatlari orqali."""

    list_display = ("user", "requested_role", "status", "created_at", "reviewed_by", "reviewed_at")
    list_filter = ("status", "requested_role")
    search_fields = ("user__username",)
    readonly_fields = ("status", "reviewed_by", "reviewed_at", "created_at")
    autocomplete_fields = ("user",)
    actions = ("approve_requests", "reject_requests")

    def _review(self, request: HttpRequest, queryset: QuerySet[RoleRequest], approve: bool) -> None:
        done = 0
        for role_request in queryset.select_related("user"):
            try:
                if approve:
                    role_request.approve(request.user, request=request)
                else:
                    role_request.reject(request.user, request=request)
                done += 1
            except (PermissionDenied, ValidationError) as exc:
                self.message_user(request, f"{role_request}: {exc}", messages.ERROR)
        if done:
            self.message_user(request, f"{done} ta so'rov ko'rib chiqildi.", messages.SUCCESS)

    @admin.action(description="Tanlangan so'rovlarni tasdiqlash")
    def approve_requests(self, request: HttpRequest, queryset: QuerySet[RoleRequest]) -> None:
        self._review(request, queryset, approve=True)

    @admin.action(description="Tanlangan so'rovlarni rad etish")
    def reject_requests(self, request: HttpRequest, queryset: QuerySet[RoleRequest]) -> None:
        self._review(request, queryset, approve=False)
