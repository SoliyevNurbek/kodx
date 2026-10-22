"""Kurs tuzilmasi: kurs, modul, dars, guruh va guruh a'zolari."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Course(models.Model):
    """O'quv kursi (masalan, «Dasturlash va sun'iy intellekt asoslari»)."""

    title = models.CharField("nomi", max_length=200)
    slug = models.SlugField("slug", max_length=80, unique=True)
    description = models.TextField("tavsif", blank=True)
    is_active = models.BooleanField("faol", default=True)
    created_at = models.DateTimeField("yaratilgan", auto_now_add=True)

    class Meta:
        verbose_name = "kurs"
        verbose_name_plural = "kurslar"
        ordering = ["title"]

    def __str__(self) -> str:
        return self.title


class Module(models.Model):
    """Kurs moduli (1–4)."""

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="modules", verbose_name="kurs")
    number = models.PositiveSmallIntegerField("raqami")
    title = models.CharField("nomi", max_length=200)
    description = models.TextField("tavsif", blank=True)

    class Meta:
        verbose_name = "modul"
        verbose_name_plural = "modullar"
        ordering = ["course", "number"]
        constraints = [
            models.UniqueConstraint(fields=["course", "number"], name="uniq_module_number_in_course"),
        ]

    def __str__(self) -> str:
        return f"Modul {self.number}. {self.title}"


class Lesson(models.Model):
    """Dars. Raqami kurs bo'yicha uzluksiz (1–48)."""

    class Kind(models.TextChoices):
        LESSON = "lesson", "Dars"
        PROJECT_DEFENSE = "project_defense", "Loyiha himoyasi"
        DEMO_DAY = "demo_day", "Demo Day"

    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="lessons", verbose_name="modul")
    number = models.PositiveSmallIntegerField("raqami")
    title = models.CharField("nomi", max_length=200)
    kind = models.CharField("turi", max_length=20, choices=Kind.choices, default=Kind.LESSON)
    description = models.TextField("tavsif", blank=True)

    class Meta:
        verbose_name = "dars"
        verbose_name_plural = "darslar"
        ordering = ["number"]
        constraints = [
            models.UniqueConstraint(fields=["module", "number"], name="uniq_lesson_number_in_module"),
        ]

    def __str__(self) -> str:
        return f"{self.number}. {self.title}"

    @property
    def course(self) -> Course:
        return self.module.course

    def clean(self) -> None:
        """Dars raqami butun kurs bo'yicha takrorlanmasligi kerak."""
        if self.module_id and self.number:
            clash = Lesson.objects.filter(
                module__course_id=self.module.course_id, number=self.number
            ).exclude(pk=self.pk)
            if clash.exists():
                raise ValidationError({"number": "Bu kursda shu raqamli dars allaqachon bor."})


class Group(models.Model):
    """O'quv guruhi. O'qituvchisi kamida moderator bo'lishi shart."""

    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name="groups", verbose_name="kurs")
    name = models.CharField("nomi", max_length=100)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="teaching_groups",
        verbose_name="o'qituvchi",
    )
    start_date = models.DateField("boshlanish sanasi", null=True, blank=True)
    is_active = models.BooleanField("faol", default=True)
    created_at = models.DateTimeField("yaratilgan", auto_now_add=True)

    class Meta:
        verbose_name = "guruh"
        verbose_name_plural = "guruhlar"
        ordering = ["course", "name"]
        constraints = [
            models.UniqueConstraint(fields=["course", "name"], name="uniq_group_name_in_course"),
        ]

    def __str__(self) -> str:
        return self.name

    def clean(self) -> None:
        """O'qituvchi kamida moderator darajasida bo'lishi kerak."""
        from accounts.models import Role

        if self.teacher_id and not self.teacher.has_role_at_least(Role.MODERATOR):
            raise ValidationError({"teacher": "Guruh o'qituvchisi kamida moderator bo'lishi kerak."})


class GroupMember(models.Model):
    """
    Guruh a'zosi (o'quvchi).

    O'quvchi bir nechta guruhda bo'lishi mumkin, lekin bitta kursda faqat
    bitta faol guruhda.
    """

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="members", verbose_name="guruh")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="group_memberships",
        verbose_name="o'quvchi",
    )
    is_active = models.BooleanField("faol", default=True)
    joined_at = models.DateTimeField("qo'shilgan", auto_now_add=True)

    class Meta:
        verbose_name = "guruh a'zosi"
        verbose_name_plural = "guruh a'zolari"
        ordering = ["group", "user__username"]
        constraints = [
            models.UniqueConstraint(fields=["group", "user"], name="uniq_group_member"),
        ]

    def __str__(self) -> str:
        return f"{self.user} @ {self.group}"

    def save(self, *args, **kwargs) -> None:
        # Qoidani admin, shell va servislar uchun bir xil qo'llash
        self.clean()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        """Bitta kursda faqat bitta faol guruh a'zoligi."""
        if not (self.is_active and self.group_id and self.user_id):
            return
        clash = GroupMember.objects.filter(
            user_id=self.user_id,
            is_active=True,
            group__course_id=self.group.course_id,
        ).exclude(pk=self.pk)
        if clash.exists():
            raise ValidationError("O'quvchi bu kursda allaqachon boshqa faol guruhda.")
