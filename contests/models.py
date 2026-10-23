"""Kontestlar: kontest, masalalari, ishtirokchilar va reyting tarixi."""

from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class Contest(models.Model):
    """Musobaqa. Egasi — Jury (yoki undan yuqori); moderator barcha kontestlarni boshqaradi."""

    class Scoring(models.TextChoices):
        ICPC = "icpc", "ICPC (yechilganlar soni + jarima vaqti)"
        IOI = "ioi", "IOI (qisman ballar)"

    class Visibility(models.TextChoices):
        PUBLIC = "public", "Ochiq"
        GROUP = "group", "Guruh uchun"
        PASSWORD = "password", "Parol bilan"

    title = models.CharField("nomi", max_length=200)
    slug = models.SlugField("slug", max_length=80, unique=True)
    description = models.TextField("tavsif", blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_contests",
                              verbose_name="egasi")
    start_at = models.DateTimeField("boshlanish vaqti")
    duration_minutes = models.PositiveIntegerField(
        "davomiyligi (daqiqa)", default=120, validators=[MinValueValidator(5), MaxValueValidator(60 * 24 * 14)])
    scoring = models.CharField("hisoblash turi", max_length=4, choices=Scoring.choices, default=Scoring.ICPC)
    penalty_minutes = models.PositiveSmallIntegerField("ICPC jarima (daqiqa)", default=20)
    freeze_minutes = models.PositiveSmallIntegerField(
        "muzlatish (daqiqa)", default=0,
        help_text="Oxirgi N daqiqada jadval ishtirokchilar uchun muzlatiladi; 0 — yo‘q.")
    visibility = models.CharField("ko‘rinish", max_length=10, choices=Visibility.choices, default=Visibility.PUBLIC)
    group = models.ForeignKey("courses.Group", on_delete=models.SET_NULL, null=True, blank=True,
                              related_name="contests", verbose_name="guruh")
    password_hash = models.CharField("parol (xesh)", max_length=128, blank=True)
    is_rated = models.BooleanField("reytingli", default=False)
    ratings_applied = models.BooleanField("reyting hisoblangan", default=False)
    created_at = models.DateTimeField("yaratilgan", auto_now_add=True)

    class Meta:
        verbose_name = "kontest"
        verbose_name_plural = "kontestlar"
        ordering = ["-start_at"]

    def __str__(self) -> str:
        return self.title

    def clean(self) -> None:
        if self.visibility == self.Visibility.GROUP and not self.group_id:
            raise ValidationError({"group": "Guruh uchun kontestda guruhni tanlang."})
        if self.freeze_minutes >= self.duration_minutes:
            raise ValidationError({"freeze_minutes": "Muzlatish vaqti davomiylikdan kam bo‘lishi kerak."})

    # --- vaqt ---

    @property
    def end_at(self) -> datetime:
        return self.start_at + timedelta(minutes=self.duration_minutes)

    @property
    def freeze_at(self) -> datetime | None:
        return self.end_at - timedelta(minutes=self.freeze_minutes) if self.freeze_minutes else None

    def is_upcoming(self, now: datetime | None = None) -> bool:
        return (now or timezone.now()) < self.start_at

    def is_running(self, now: datetime | None = None) -> bool:
        now = now or timezone.now()
        return self.start_at <= now < self.end_at

    @property
    def is_finished(self) -> bool:
        return timezone.now() >= self.end_at

    def is_frozen(self, now: datetime | None = None) -> bool:
        now = now or timezone.now()
        return bool(self.freeze_at and self.freeze_at <= now < self.end_at)

    @property
    def status_label(self) -> str:
        if self.is_upcoming():
            return "Kutilmoqda"
        return "Davom etmoqda" if self.is_running() else "Tugagan"

    # --- parol ---

    def set_password(self, raw: str) -> None:
        self.password_hash = make_password(raw) if raw else ""

    def check_password(self, raw: str) -> bool:
        return bool(self.password_hash) and check_password(raw, self.password_hash)

    # --- ruxsatlar ---

    def can_manage(self, user) -> bool:
        """Jury — o'z kontestlari, moderator+ — barcha kontestlar."""
        if not (user and user.is_authenticated):
            return False
        return user.is_moderator or (self.owner_id == user.pk and user.is_jury)

    def is_participant(self, user) -> bool:
        return bool(user and user.is_authenticated and self.participants.filter(user=user).exists())

    def can_view(self, user) -> bool:
        """Kontest sahifasini ko'rish (ro'yxatda ko'rinish)."""
        if self.visibility != self.Visibility.GROUP or self.can_manage(user):
            return True
        if not (user and user.is_authenticated):
            return False
        return self.group is not None and self.group.members.filter(user=user, is_active=True).exists()

    def can_register(self, user) -> bool:
        return bool(user and user.is_authenticated and self.can_view(user) and not self.is_finished)

    def can_see_problems(self, user) -> bool:
        """Kontest paytida masalalar faqat ishtirokchilarga; tugagach — ko'ra oladigan hammaga."""
        if self.can_manage(user):
            return True
        if self.is_upcoming():
            return False
        if self.is_running():
            return self.is_participant(user)
        return self.can_view(user)


class ContestProblem(models.Model):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name="problems", verbose_name="kontest")
    problem = models.ForeignKey("problems.Problem", on_delete=models.PROTECT, related_name="contest_links",
                                verbose_name="masala")
    label = models.CharField("harf", max_length=3)
    points = models.PositiveIntegerField("ball (IOI)", default=100)

    class Meta:
        verbose_name = "kontest masalasi"
        verbose_name_plural = "kontest masalalari"
        ordering = ["contest", "label"]
        constraints = [
            models.UniqueConstraint(fields=["contest", "label"], name="uniq_contest_label"),
            models.UniqueConstraint(fields=["contest", "problem"], name="uniq_contest_problem"),
        ]

    def __str__(self) -> str:
        return f"{self.label}. {self.problem.title}"


class ContestParticipant(models.Model):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name="participants",
                                verbose_name="kontest")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="contest_entries",
                             verbose_name="ishtirokchi")
    registered_at = models.DateTimeField("ro‘yxatdan o‘tgan", auto_now_add=True)

    class Meta:
        verbose_name = "ishtirokchi"
        verbose_name_plural = "ishtirokchilar"
        constraints = [models.UniqueConstraint(fields=["contest", "user"], name="uniq_contest_participant")]

    def __str__(self) -> str:
        return f"{self.user} @ {self.contest}"


class RatingHistory(models.Model):
    """Reytingli kontestdan keyingi reyting o'zgarishi (profil grafigi uchun)."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="rating_history",
                             verbose_name="foydalanuvchi")
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name="rating_changes",
                                verbose_name="kontest")
    old_rating = models.IntegerField("eski reyting")
    new_rating = models.IntegerField("yangi reyting")
    rank = models.PositiveIntegerField("o‘rin")
    created_at = models.DateTimeField("vaqt", auto_now_add=True)

    class Meta:
        verbose_name = "reyting tarixi"
        verbose_name_plural = "reyting tarixi"
        ordering = ["created_at"]
        constraints = [models.UniqueConstraint(fields=["user", "contest"], name="uniq_rating_history")]

    def __str__(self) -> str:
        return f"{self.user}: {self.old_rating} → {self.new_rating}"

    @property
    def delta(self) -> int:
        return self.new_rating - self.old_rating
