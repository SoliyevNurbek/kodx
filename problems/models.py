"""Vazifalar banki: masalalar (code/quiz/project), testlar, quiz savollari, rubrika, darsga biriktirish."""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from judge.types import CheckerMode, JudgeTest, Limits


class Tag(models.Model):
    """Masala mavzusi (masalan: if, tsikl, satrlar)."""

    name = models.CharField("nomi", max_length=50, unique=True)
    slug = models.SlugField("slug", max_length=50, unique=True)

    class Meta:
        verbose_name = "teg"
        verbose_name_plural = "teglar"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Problem(models.Model):
    """Vazifa: avtomatik tekshiriladigan masala, test (quiz) yoki loyiha."""

    class Type(models.TextChoices):
        CODE = "code", "Masala (kod)"
        QUIZ = "quiz", "Test (quiz)"
        PROJECT = "project", "Loyiha"

    class Status(models.TextChoices):
        DRAFT = "draft", "Qoralama"
        REVIEW = "review", "Ko‘rib chiqishda"
        PUBLISHED = "published", "Nashr etilgan"

    slug = models.SlugField("slug", max_length=80, unique=True)
    title = models.CharField("nomi", max_length=200)
    type = models.CharField("turi", max_length=10, choices=Type.choices, default=Type.CODE, db_index=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="authored_problems", verbose_name="muallif"
    )
    status = models.CharField("holat", max_length=10, choices=Status.choices, default=Status.DRAFT, db_index=True)
    difficulty = models.PositiveSmallIntegerField(
        "qiyinlik", default=1, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    points = models.PositiveIntegerField("ball", default=100)
    tags = models.ManyToManyField(Tag, blank=True, related_name="problems", verbose_name="teglar")

    statement = models.TextField("shart (Markdown, LaTeX)", blank=True)
    input_format = models.TextField("kirish formati", blank=True)
    output_format = models.TextField("chiqish formati", blank=True)
    notes = models.TextField("izoh", blank=True)

    time_limit = models.PositiveIntegerField("vaqt chegarasi (ms)", default=1000)
    memory_limit = models.PositiveIntegerField("xotira chegarasi (MB)", default=256)
    checker = models.CharField("solishtirish", max_length=12, choices=CheckerMode.choices,
                               default=CheckerMode.WHITESPACE)
    float_epsilon = models.FloatField("epsilon", default=1e-6)
    reference_solution = models.TextField("etalon yechim", blank=True)

    is_seed = models.BooleanField("seed kontent", default=False, db_index=True)
    created_at = models.DateTimeField("yaratilgan", auto_now_add=True)
    updated_at = models.DateTimeField("yangilangan", auto_now=True)

    class Meta:
        verbose_name = "vazifa"
        verbose_name_plural = "vazifalar"
        ordering = ["slug"]

    def __str__(self) -> str:
        return self.title

    # --- ruxsatlar (ob'ekt darajasida) ---

    def can_view(self, user) -> bool:
        """Nashr etilgan — hammaga; qoralama — muallif va moderator+."""
        if self.status == self.Status.PUBLISHED:
            return True
        return self.can_view_hidden(user)

    def can_view_hidden(self, user) -> bool:
        """Yopiq testlar va etalon yechim: muallif yoki moderator+."""
        if not (user and user.is_authenticated):
            return False
        return user.is_moderator or (self.author_id == user.pk and user.is_jury_pro)

    def can_edit(self, user) -> bool:
        """Jury Pro faqat o'z masalasini, super admin — hammasini tahrirlaydi."""
        if not (user and user.is_authenticated):
            return False
        return user.is_superadmin or (self.author_id == user.pk and user.is_jury_pro)

    def can_publish(self, user) -> bool:
        """Nashr etish — moderator va undan yuqori."""
        return bool(user and user.is_authenticated and user.is_moderator)

    # --- judge uchun ---

    @property
    def limits(self) -> Limits:
        return Limits(time_ms=self.time_limit, memory_mb=self.memory_limit,
                      checker=self.checker, epsilon=self.float_epsilon)

    def judge_tests(self) -> list[JudgeTest]:
        """Barcha testlarni judge formatida qaytaradi."""
        return [tc.as_judge_test() for tc in self.test_cases.all()]

    @property
    def max_test_points(self) -> int:
        return sum(tc.points for tc in self.test_cases.all())


def test_file_path(instance: "TestCase", filename: str) -> str:
    return f"tests/{instance.problem.slug}/{filename}"


class TestCase(models.Model):
    """Kirish/chiqish testi. Fayllar media/tests/<slug>/ da, bazada faqat yo'l."""

    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name="test_cases", verbose_name="vazifa")
    order = models.PositiveIntegerField("tartib")
    input_file = models.FileField("kirish fayli", upload_to=test_file_path, max_length=255)
    output_file = models.FileField("chiqish fayli", upload_to=test_file_path, max_length=255)
    is_sample = models.BooleanField("namuna", default=False)
    points = models.PositiveIntegerField("ball", default=1)

    class Meta:
        verbose_name = "test"
        verbose_name_plural = "testlar"
        ordering = ["problem", "order"]
        constraints = [models.UniqueConstraint(fields=["problem", "order"], name="uniq_test_order")]

    def __str__(self) -> str:
        return f"{self.problem.slug} #{self.order}"

    @staticmethod
    def _read(field) -> str:
        field.open("rb")
        try:
            return field.read().decode("utf-8")
        finally:
            field.close()

    def read_input(self) -> str:
        return self._read(self.input_file)

    def read_output(self) -> str:
        return self._read(self.output_file)

    def as_judge_test(self) -> JudgeTest:
        return JudgeTest(id=self.pk, input=self.read_input(), expected=self.read_output(), points=self.points)


class QuizQuestion(models.Model):
    """Quiz savoli."""

    class Kind(models.TextChoices):
        SINGLE = "single", "Bitta javob"
        MULTIPLE = "multiple", "Bir nechta javob"
        TEXT = "text", "Qisqa matn"

    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name="questions", verbose_name="vazifa")
    order = models.PositiveIntegerField("tartib")
    kind = models.CharField("turi", max_length=10, choices=Kind.choices, default=Kind.SINGLE)
    text = models.TextField("savol")
    points = models.PositiveIntegerField("ball", default=1)
    correct_text = models.CharField(
        "to‘g‘ri javob(lar)", max_length=255, blank=True,
        help_text="Qisqa matnli savol uchun; bir nechta variant | bilan ajratiladi.",
    )
    explanation = models.TextField("izoh", blank=True)

    class Meta:
        verbose_name = "quiz savoli"
        verbose_name_plural = "quiz savollari"
        ordering = ["problem", "order"]
        constraints = [models.UniqueConstraint(fields=["problem", "order"], name="uniq_question_order")]

    def __str__(self) -> str:
        return f"{self.problem.slug} · {self.order}"

    def accepted_answers(self) -> list[str]:
        return [a.strip().casefold() for a in self.correct_text.split("|") if a.strip()]


class QuizOption(models.Model):
    """Quiz savoli varianti."""

    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name="options",
                                 verbose_name="savol")
    order = models.PositiveIntegerField("tartib")
    text = models.CharField("variant", max_length=500)
    is_correct = models.BooleanField("to‘g‘ri", default=False)

    class Meta:
        verbose_name = "variant"
        verbose_name_plural = "variantlar"
        ordering = ["question", "order"]

    def __str__(self) -> str:
        return self.text


class RubricCriterion(models.Model):
    """Loyiha baholash rubrikasi mezoni."""

    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name="rubric", verbose_name="vazifa")
    order = models.PositiveIntegerField("tartib")
    title = models.CharField("mezon", max_length=200)
    description = models.TextField("tavsif", blank=True)
    max_points = models.PositiveIntegerField("maksimal ball")

    class Meta:
        verbose_name = "rubrika mezoni"
        verbose_name_plural = "rubrika"
        ordering = ["problem", "order"]

    def __str__(self) -> str:
        return f"{self.title} ({self.max_points})"


class LessonProblem(models.Model):
    """Vazifani darsga biriktirish: sinf ishi / uyga vazifa / qo'shimcha."""

    class Kind(models.TextChoices):
        CLASSWORK = "classwork", "Sinf ishi"
        HOMEWORK = "homework", "Uyga vazifa"
        CHALLENGE = "challenge", "Qo‘shimcha (challenge)"

    lesson = models.ForeignKey("courses.Lesson", on_delete=models.CASCADE, related_name="lesson_problems",
                               verbose_name="dars")
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name="lesson_links",
                                verbose_name="vazifa")
    kind = models.CharField("turi", max_length=10, choices=Kind.choices, default=Kind.CLASSWORK)
    order = models.PositiveIntegerField("tartib", default=0)
    deadline = models.DateTimeField("muddat", null=True, blank=True)
    is_required = models.BooleanField("majburiy", default=True)

    class Meta:
        verbose_name = "dars vazifasi"
        verbose_name_plural = "dars vazifalari"
        ordering = ["lesson", "order"]
        constraints = [models.UniqueConstraint(fields=["lesson", "problem"], name="uniq_lesson_problem")]

    def __str__(self) -> str:
        return f"{self.lesson} → {self.problem}"
