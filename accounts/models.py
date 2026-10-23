"""Foydalanuvchilar, rollar ierarxiyasi va rol so'rovlari."""

from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import models, transaction
from django.http import HttpRequest
from django.utils import timezone


class Role(models.IntegerChoices):
    """Rollar darajasi: har yuqori rol pastdagilar huquqini o'z ichiga oladi."""

    USER = 1, "Foydalanuvchi"
    JURY = 2, "Jury"
    JURY_PRO = 3, "Jury Pro"
    MODERATOR = 4, "Moderator"
    SUPERADMIN = 5, "Super admin"


class KodxUserManager(UserManager):
    """Superuser yaratilganda unga avtomatik superadmin roli beriladi."""

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", Role.SUPERADMIN)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    """kodx.uz foydalanuvchisi."""

    email = models.EmailField(
        "email",
        unique=True,
        null=True,
        blank=True,
        help_text="Ixtiyoriy. Boshqa foydalanuvchilarga ko'rinmaydi.",
    )
    role = models.PositiveSmallIntegerField(
        "rol", choices=Role.choices, default=Role.USER, db_index=True
    )
    rating = models.IntegerField("kontest reytingi", default=1200)
    bio = models.TextField("o'zi haqida", blank=True, max_length=1000)
    avatar = models.ImageField("avatar", upload_to="avatars/", blank=True)
    must_change_password = models.BooleanField(
        "parolni almashtirishi shart",
        default=False,
        help_text="Belgilansa, foydalanuvchi keyingi kirishda yangi parol o'rnatadi.",
    )
    is_seed = models.BooleanField(
        "demo/seed akkaunt",
        default=False,
        db_index=True,
        help_text="seed_demo yaratgan akkaunt — bosh sahifa statistikasida hisobga olinmaydi.",
    )

    objects = KodxUserManager()

    # Email ixtiyoriy — createsuperuser uni so'ramaydi.
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        verbose_name = "foydalanuvchi"
        verbose_name_plural = "foydalanuvchilar"

    def save(self, *args, **kwargs) -> None:
        # Bo'sh email NULL sifatida saqlanadi — unikal cheklov buzilmasligi uchun.
        if not self.email:
            self.email = None
        # Admin panelga kirish roldan kelib chiqadi: moderator va undan yuqori.
        self.is_staff = self.is_superuser or int(self.role) >= Role.MODERATOR
        update_fields = kwargs.get("update_fields")
        if update_fields is not None and "role" in update_fields:
            kwargs["update_fields"] = {*update_fields, "is_staff"}
        super().save(*args, **kwargs)

    @property
    def role_level(self) -> int:
        """Samarali rol darajasi; Django superuser doim superadmin darajasida."""
        if self.is_superuser:
            return Role.SUPERADMIN
        return int(self.role)

    def has_role_at_least(self, role: int) -> bool:
        """Foydalanuvchi darajasi berilgan roldan past emasligini tekshiradi."""
        if not self.is_active:
            return False
        return self.role_level >= int(role)

    @property
    def is_jury(self) -> bool:
        return self.has_role_at_least(Role.JURY)

    @property
    def is_jury_pro(self) -> bool:
        return self.has_role_at_least(Role.JURY_PRO)

    @property
    def is_moderator(self) -> bool:
        return self.has_role_at_least(Role.MODERATOR)

    @property
    def is_superadmin(self) -> bool:
        return self.has_role_at_least(Role.SUPERADMIN)

    def can_assign_role(self, role: int) -> bool:
        """
        Berilgan rolni boshqa foydalanuvchiga bera oladimi.

        Moderator — faqat jury va jury_pro (va user ga qaytarish);
        superadmin — barcha rollar.
        """
        if self.is_superadmin:
            return True
        if self.is_moderator:
            return int(role) in (Role.USER, Role.JURY, Role.JURY_PRO)
        return False


class RoleRequest(models.Model):
    """Foydalanuvchining Jury yoki Jury Pro roli uchun so'rovi."""

    REQUESTABLE_ROLES = (Role.JURY, Role.JURY_PRO)

    class Status(models.TextChoices):
        PENDING = "pending", "Kutilmoqda"
        APPROVED = "approved", "Tasdiqlangan"
        REJECTED = "rejected", "Rad etilgan"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="role_requests",
        verbose_name="foydalanuvchi",
    )
    requested_role = models.PositiveSmallIntegerField(
        "so'ralgan rol",
        choices=[(r.value, r.label) for r in REQUESTABLE_ROLES],
    )
    status = models.CharField(
        "holat",
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    reason = models.TextField("sabab", blank=True, max_length=1000)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_role_requests",
        verbose_name="ko'rib chiqqan",
    )
    reviewed_at = models.DateTimeField("ko'rib chiqilgan sana", null=True, blank=True)
    review_comment = models.TextField("izoh", blank=True, max_length=1000)
    created_at = models.DateTimeField("yuborilgan sana", auto_now_add=True)

    class Meta:
        verbose_name = "rol so'rovi"
        verbose_name_plural = "rol so'rovlari"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user} → {self.get_requested_role_display()} ({self.get_status_display()})"

    def clean(self) -> None:
        """Bitta foydalanuvchida faqat bitta kutilayotgan so'rov bo'lishi mumkin."""
        if self.status == self.Status.PENDING and self.user_id:
            others = RoleRequest.objects.filter(
                user_id=self.user_id, status=self.Status.PENDING
            ).exclude(pk=self.pk)
            if others.exists():
                raise ValidationError("Bu foydalanuvchida kutilayotgan so'rov allaqachon bor.")

    def _review(
        self,
        reviewer: User,
        status: str,
        comment: str = "",
        request: HttpRequest | None = None,
    ) -> None:
        """So'rovni ko'rib chiqish (umumiy qism): huquq va holatni tekshiradi, audit yozadi."""
        from audit.services import log_action

        if not reviewer.is_moderator:
            raise PermissionDenied("Rol so'rovlarini faqat moderator ko'rib chiqa oladi.")
        if self.status != self.Status.PENDING:
            raise ValidationError("So'rov allaqachon ko'rib chiqilgan.")

        with transaction.atomic():
            self.status = status
            self.reviewed_by = reviewer
            self.reviewed_at = timezone.now()
            self.review_comment = comment
            self.save()

            details = {"requested_role": self.requested_role, "user": self.user.username}
            if status == self.Status.APPROVED and self.user.role < self.requested_role:
                details["old_role"] = self.user.role
                self.user.role = self.requested_role
                self.user.save(update_fields=["role"])

            log_action(reviewer, f"role_request_{status}", self, details, request)

    def approve(self, reviewer: User, comment: str = "", request: HttpRequest | None = None) -> None:
        """So'rovni tasdiqlaydi va foydalanuvchiga so'ralgan rolni beradi."""
        self._review(reviewer, self.Status.APPROVED, comment, request)

    def reject(self, reviewer: User, comment: str = "", request: HttpRequest | None = None) -> None:
        """So'rovni rad etadi."""
        self._review(reviewer, self.Status.REJECTED, comment, request)


class LoginAttempt(models.Model):
    """Kirish urinishi (parolni terib topishga qarshi cheklov uchun)."""

    username = models.CharField("username", max_length=150, db_index=True)
    ip = models.GenericIPAddressField("IP manzil", null=True, blank=True)
    success = models.BooleanField("muvaffaqiyatli", default=False)
    created_at = models.DateTimeField("vaqt", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "kirish urinishi"
        verbose_name_plural = "kirish urinishlari"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.username} · {'+' if self.success else '-'} · {self.created_at:%Y-%m-%d %H:%M}"
