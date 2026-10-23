"""Yechimlar: kod urinishlari (judge orqali), quiz javoblari va loyiha topshiriqlari."""

from django.conf import settings
from django.db import models

from judge.types import Language, Verdict

MAX_CODE_BYTES = 64 * 1024


class Submission(models.Model):
    """Code masalaga yuborilgan yechim. Judge worker navbat orqali tekshiradi."""

    class Status(models.TextChoices):
        QUEUED = "queued", "Navbatda"
        RUNNING = "running", "Tekshirilmoqda"
        DONE = "done", "Tekshirildi"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="submissions",
                             verbose_name="foydalanuvchi")
    problem = models.ForeignKey("problems.Problem", on_delete=models.CASCADE, related_name="submissions",
                                verbose_name="masala")
    lesson = models.ForeignKey("courses.Lesson", on_delete=models.SET_NULL, null=True, blank=True,
                               related_name="submissions", verbose_name="dars")
    language = models.CharField("til", max_length=20, choices=Language.choices, default=Language.PYTHON3)
    code = models.TextField("kod")
    status = models.CharField("holat", max_length=10, choices=Status.choices, default=Status.QUEUED,
                              db_index=True)
    verdict = models.CharField("verdikt", max_length=4, choices=Verdict.choices, blank=True, db_index=True)
    score = models.PositiveIntegerField("ball", default=0)
    time_ms = models.PositiveIntegerField("vaqt (ms)", default=0)
    memory_kb = models.PositiveIntegerField("xotira (KB)", default=0)
    compile_output = models.TextField("kompilyator xabari", blank=True)
    judge_attempts = models.PositiveSmallIntegerField("tekshiruv urinishlari", default=0)
    created_at = models.DateTimeField("yuborilgan", auto_now_add=True, db_index=True)
    judged_at = models.DateTimeField("tekshirilgan", null=True, blank=True)

    class Meta:
        verbose_name = "yechim"
        verbose_name_plural = "yechimlar"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "problem", "verdict"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"#{self.pk} {self.user} · {self.problem.slug} · {self.verdict or self.status}"

    @property
    def is_accepted(self) -> bool:
        return self.verdict == Verdict.ACCEPTED

    @property
    def is_finished(self) -> bool:
        return self.status == self.Status.DONE

    def can_view(self, user) -> bool:
        """Natijani (verdikt, ball) ko'rish: egasi, moderator+ yoki kodni ko'ra oladigan har kim."""
        return self.can_view_code(user)

    def can_view_code(self, user) -> bool:
        """
        Kodni ko'rish (bolalar xavfsizligi va adolat qoidasi):
        egasi va moderator+ — doim; boshqalar — faqat o'zi shu masalani yechgan bo'lsa
        yoki yechim tugagan kontestga tegishli bo'lsa.
        """
        if not (user and user.is_authenticated):
            return False
        if user.pk == self.user_id or user.is_moderator:
            return True
        if self._contest_finished():
            return True
        return Submission.objects.filter(user=user, problem_id=self.problem_id, verdict=Verdict.ACCEPTED).exists()

    def _contest_finished(self) -> bool:
        """Kontest tugaganmi (kontestlar 7-bosqichda qo'shiladi)."""
        contest = getattr(self, "contest", None)
        return bool(contest and contest.is_finished)


class SubmissionResult(models.Model):
    """Bitta test bo'yicha natija."""

    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name="results",
                                   verbose_name="yechim")
    test_case = models.ForeignKey("problems.TestCase", on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name="results", verbose_name="test")
    order = models.PositiveIntegerField("tartib")
    verdict = models.CharField("verdikt", max_length=4, choices=Verdict.choices)
    time_ms = models.PositiveIntegerField("vaqt (ms)", default=0)
    memory_kb = models.PositiveIntegerField("xotira (KB)", default=0)
    points = models.PositiveIntegerField("ball", default=0)
    output = models.TextField("chiqish (qisqartirilgan)", blank=True)
    error = models.TextField("xato (qisqartirilgan)", blank=True)

    class Meta:
        verbose_name = "test natijasi"
        verbose_name_plural = "test natijalari"
        ordering = ["submission", "order"]

    def __str__(self) -> str:
        return f"#{self.submission_id} test {self.order}: {self.verdict}"


class QuizAttempt(models.Model):
    """Quiz javoblari. Avtomatik baholanadi (kod bajarilmaydi)."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quiz_attempts",
                             verbose_name="foydalanuvchi")
    problem = models.ForeignKey("problems.Problem", on_delete=models.CASCADE, related_name="quiz_attempts",
                                verbose_name="quiz")
    lesson = models.ForeignKey("courses.Lesson", on_delete=models.SET_NULL, null=True, blank=True,
                               related_name="quiz_attempts", verbose_name="dars")
    # {"<savol tartibi>": [variant tartiblari] yoki "matn"}
    answers = models.JSONField("javoblar", default=dict)
    # {"<savol tartibi>": {"correct": bool, "points": int}}
    details = models.JSONField("natijalar", default=dict)
    score = models.PositiveIntegerField("to‘plangan ball", default=0)
    max_score = models.PositiveIntegerField("maksimal ball", default=0)
    created_at = models.DateTimeField("topshirilgan", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "quiz urinishi"
        verbose_name_plural = "quiz urinishlari"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user} · {self.problem.slug} · {self.score}/{self.max_score}"

    @property
    def percent(self) -> float:
        return 100 * self.score / self.max_score if self.max_score else 0.0

    @property
    def problem_points(self) -> int:
        """Vazifa bali bo'yicha natija (masalan, 50 dan)."""
        return round(self.problem.points * self.score / self.max_score) if self.max_score else 0


class ProjectSubmission(models.Model):
    """Loyiha topshirig'i: GitHub havolasi, o'qituvchi rubrika bo'yicha baholaydi."""

    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Topshirildi"
        GRADED = "graded", "Baholandi"
        NEEDS_REVISION = "revision", "Qayta ishlash kerak"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="project_submissions", verbose_name="foydalanuvchi")
    problem = models.ForeignKey("problems.Problem", on_delete=models.CASCADE, related_name="project_submissions",
                                verbose_name="loyiha")
    lesson = models.ForeignKey("courses.Lesson", on_delete=models.SET_NULL, null=True, blank=True,
                               related_name="project_submissions", verbose_name="dars")
    github_url = models.URLField("GitHub havolasi", max_length=300)
    comment = models.TextField("izoh", blank=True, max_length=2000)
    status = models.CharField("holat", max_length=10, choices=Status.choices, default=Status.SUBMITTED,
                              db_index=True)
    # {"<mezon tartibi>": ball}
    rubric_scores = models.JSONField("rubrika ballari", default=dict, blank=True)
    score = models.PositiveIntegerField("ball", default=0)
    feedback = models.TextField("o‘qituvchi izohi", blank=True)
    graded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name="graded_projects", verbose_name="baholagan")
    graded_at = models.DateTimeField("baholangan", null=True, blank=True)
    created_at = models.DateTimeField("topshirilgan", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "loyiha topshirig‘i"
        verbose_name_plural = "loyiha topshiriqlari"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user} · {self.problem.slug} · {self.get_status_display()}"

    def can_view(self, user) -> bool:
        return bool(user and user.is_authenticated and (user.pk == self.user_id or user.is_moderator))
