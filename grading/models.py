"""Kurs bahosi (davomat, siyosat), mashq statistikasi va nishonlar."""

from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class GradingPolicy(models.Model):
    """
    Kurs bahosi siyosati: har modul uchun ballar taqsimoti (standart 20 = 2,5 + 5 + 2,5 + 10)
    va muddatdan keyin topshirilgan ish uchun jarima.
    """

    course = models.OneToOneField("courses.Course", on_delete=models.CASCADE, related_name="grading_policy",
                                  verbose_name="kurs")
    attendance_points = models.DecimalField("davomat", max_digits=5, decimal_places=2, default=Decimal("2.5"))
    tasks_points = models.DecimalField("mustaqil vazifalar", max_digits=5, decimal_places=2, default=Decimal("5"))
    quiz_points = models.DecimalField("test", max_digits=5, decimal_places=2, default=Decimal("2.5"))
    project_points = models.DecimalField("loyiha", max_digits=5, decimal_places=2, default=Decimal("10"))
    late_penalty_percent = models.PositiveSmallIntegerField(
        "kechikish jarimasi (%)", default=20, validators=[MaxValueValidator(100)],
        help_text="Muddatdan keyin topshirilgan ish bali shu foizga kamaytiriladi.")

    class Meta:
        verbose_name = "baholash siyosati"
        verbose_name_plural = "baholash siyosatlari"

    def __str__(self) -> str:
        return f"{self.course}: {self.module_total} / modul"

    @property
    def module_total(self) -> Decimal:
        return self.attendance_points + self.tasks_points + self.quiz_points + self.project_points

    @classmethod
    def for_course(cls, course) -> "GradingPolicy":
        policy, _ = cls.objects.get_or_create(course=course)
        return policy


class Attendance(models.Model):
    """Dars davomati (guruh bo'yicha)."""

    group = models.ForeignKey("courses.Group", on_delete=models.CASCADE, related_name="attendance",
                              verbose_name="guruh")
    lesson = models.ForeignKey("courses.Lesson", on_delete=models.CASCADE, related_name="attendance",
                               verbose_name="dars")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="attendance",
                             verbose_name="o‘quvchi")
    present = models.BooleanField("qatnashdi", default=True)
    marked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                  related_name="+", verbose_name="belgilagan")
    marked_at = models.DateTimeField("belgilangan", auto_now=True)

    class Meta:
        verbose_name = "davomat"
        verbose_name_plural = "davomat"
        constraints = [models.UniqueConstraint(fields=["group", "lesson", "user"], name="uniq_attendance")]

    def __str__(self) -> str:
        return f"{self.user} · {self.lesson.number} · {'+' if self.present else '-'}"


class PracticeStats(models.Model):
    """Mashq statistikasi (denormalizatsiya — reyting jadvallari tez ishlashi uchun)."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="practice",
                                verbose_name="foydalanuvchi")
    score = models.PositiveIntegerField("mashq bali", default=0, db_index=True)
    solved_count = models.PositiveIntegerField("yechilgan", default=0)
    current_streak = models.PositiveIntegerField("joriy seriya (kun)", default=0)
    best_streak = models.PositiveIntegerField("eng uzun seriya (kun)", default=0)
    last_solved_at = models.DateTimeField("oxirgi yechim", null=True, blank=True)
    updated_at = models.DateTimeField("yangilangan", auto_now=True)

    class Meta:
        verbose_name = "mashq statistikasi"
        verbose_name_plural = "mashq statistikasi"
        ordering = ["-score"]

    def __str__(self) -> str:
        return f"{self.user}: {self.score}"


class Badge(models.Model):
    """Nishon turi (seed migratsiyada yaratiladi)."""

    code = models.SlugField("kod", max_length=40, unique=True)
    name = models.CharField("nomi", max_length=100)
    description = models.CharField("tavsif", max_length=255)
    icon = models.CharField("belgi", max_length=8, default="🏅")
    order = models.PositiveSmallIntegerField("tartib", default=0, validators=[MinValueValidator(0)])

    class Meta:
        verbose_name = "nishon"
        verbose_name_plural = "nishonlar"
        ordering = ["order"]

    def __str__(self) -> str:
        return self.name


class UserBadge(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="badges",
                             verbose_name="foydalanuvchi")
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name="awards", verbose_name="nishon")
    awarded_at = models.DateTimeField("berilgan", auto_now_add=True)

    class Meta:
        verbose_name = "berilgan nishon"
        verbose_name_plural = "berilgan nishonlar"
        ordering = ["badge__order"]
        constraints = [models.UniqueConstraint(fields=["user", "badge"], name="uniq_user_badge")]

    def __str__(self) -> str:
        return f"{self.user} · {self.badge}"
