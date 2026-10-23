"""
Masalalarni papkadan import qilish (format: docs/PROBLEM_FORMAT.md).

    <slug>/problem.yaml   — metama'lumot (majburiy)
    <slug>/statement.md   — shart (Markdown)
    <slug>/solution.py    — etalon yechim (code uchun)
    <slug>/tests/01.in, 01.out, ...

Modul ikki joyda ishlatiladi: `manage.py import_problems` (joriy modellar) va seed
data migratsiya (tarixiy modellar). Shuning uchun model metodlariga emas, faqat
ORM asoslariga tayanadi va mavjud bo'lmagan maydonlarni o'tkazib yuboradi.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import yaml
from django.conf import settings
from django.utils.text import slugify

PROBLEM_TYPES = {"code", "quiz", "project"}
CHECKERS = {"exact", "whitespace", "float"}
LESSON_KINDS = {"classwork", "homework", "challenge"}
QUESTION_KINDS = {"single", "multiple", "text"}
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,79}$")


class ProblemFormatError(ValueError):
    """Masala papkasi formati noto'g'ri."""


@dataclass
class TestSpec:
    order: int
    input: str
    output: str
    is_sample: bool
    points: int


@dataclass
class QuestionSpec:
    order: int
    kind: str
    text: str
    points: int
    options: list[tuple[str, bool]]
    answers: list[str]
    explanation: str


@dataclass
class RubricSpec:
    order: int
    title: str
    points: int
    description: str


@dataclass
class LessonLinkSpec:
    lesson: int
    kind: str
    required: bool
    order: int


@dataclass
class ProblemSpec:
    slug: str
    title: str
    type: str
    difficulty: int
    points: int
    tags: list[str]
    time_limit: int
    memory_limit: int
    checker: str
    epsilon: float
    statement: str
    input_format: str
    output_format: str
    notes: str
    solution: str
    course_slug: str
    tests: list[TestSpec] = field(default_factory=list)
    questions: list[QuestionSpec] = field(default_factory=list)
    rubric: list[RubricSpec] = field(default_factory=list)
    lessons: list[LessonLinkSpec] = field(default_factory=list)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _require(condition: bool, slug: str, message: str) -> None:
    if not condition:
        raise ProblemFormatError(f"{slug}: {message}")


def parse_problem_dir(path: Path) -> ProblemSpec:
    """Bitta masala papkasini o'qib, tekshiradi va ProblemSpec qaytaradi."""
    path = Path(path)
    slug = path.name
    _require(SLUG_RE.match(slug) is not None, slug, "papka nomi slug bo'lishi kerak (a-z, 0-9, -)")
    meta_path = path / "problem.yaml"
    _require(meta_path.exists(), slug, "problem.yaml topilmadi")
    meta: dict[str, Any] = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}

    ptype = meta.get("type", "code")
    _require(ptype in PROBLEM_TYPES, slug, f"noto'g'ri type: {ptype}")
    _require(bool(meta.get("title")), slug, "title majburiy")
    difficulty = int(meta.get("difficulty", 1))
    _require(1 <= difficulty <= 5, slug, "difficulty 1–5 oralig'ida bo'lishi kerak")
    checker = meta.get("checker", "whitespace")
    _require(checker in CHECKERS, slug, f"noto'g'ri checker: {checker}")

    spec = ProblemSpec(
        slug=slug,
        title=str(meta["title"]),
        type=ptype,
        difficulty=difficulty,
        points=int(meta.get("points", 100)),
        tags=[str(t) for t in meta.get("tags", [])],
        time_limit=int(meta.get("time_limit", 1000)),
        memory_limit=int(meta.get("memory_limit", 256)),
        checker=checker,
        epsilon=float(meta.get("epsilon", 1e-6)),
        statement=_read(path / "statement.md"),
        input_format=str(meta.get("input_format", "")),
        output_format=str(meta.get("output_format", "")),
        notes=str(meta.get("notes", "")),
        solution=_read(path / "solution.py"),
        course_slug=str(meta.get("course", "dasturlash-va-ai-asoslari")),
    )

    if ptype == "code":
        tests_dir = path / "tests"
        inputs = sorted(tests_dir.glob("*.in")) if tests_dir.exists() else []
        _require(bool(inputs), slug, "code masala uchun tests/*.in kerak")
        samples = set(meta.get("samples", [1, 2]))
        test_points = int(meta.get("test_points", 1))
        for order, input_path in enumerate(inputs, start=1):
            output_path = input_path.with_suffix(".out")
            _require(output_path.exists(), slug, f"{output_path.name} topilmadi")
            spec.tests.append(TestSpec(order=order, input=_read(input_path), output=_read(output_path),
                                       is_sample=order in samples, points=test_points))

    for order, raw in enumerate(meta.get("questions", []), start=1):
        kind = raw.get("kind", "single")
        _require(kind in QUESTION_KINDS, slug, f"savol {order}: noto'g'ri kind {kind}")
        options = []
        for option in raw.get("options", []):
            if isinstance(option, dict):
                options.append((str(option["text"]), bool(option.get("correct", False))))
            else:
                options.append((str(option), False))
        answers = [str(a) for a in raw.get("answers", [])]
        correct_count = sum(1 for _, ok in options if ok)
        if kind == "single":
            _require(correct_count == 1, slug, f"savol {order}: aynan bitta to'g'ri variant kerak")
        elif kind == "multiple":
            _require(correct_count >= 1, slug, f"savol {order}: kamida bitta to'g'ri variant kerak")
        else:
            _require(bool(answers), slug, f"savol {order}: answers kerak")
        spec.questions.append(QuestionSpec(order=order, kind=kind, text=str(raw["text"]),
                                           points=int(raw.get("points", 1)), options=options,
                                           answers=answers, explanation=str(raw.get("explanation", ""))))
    if ptype == "quiz":
        _require(bool(spec.questions), slug, "quiz uchun questions kerak")

    for order, raw in enumerate(meta.get("rubric", []), start=1):
        spec.rubric.append(RubricSpec(order=order, title=str(raw["title"]), points=int(raw["points"]),
                                      description=str(raw.get("description", ""))))
    if ptype == "project":
        _require(bool(spec.rubric), slug, "project uchun rubric kerak")

    for order, raw in enumerate(meta.get("lessons", []), start=1):
        kind = raw.get("kind", "classwork")
        _require(kind in LESSON_KINDS, slug, f"noto'g'ri lesson kind: {kind}")
        spec.lessons.append(LessonLinkSpec(lesson=int(raw["lesson"]), kind=kind,
                                           required=bool(raw.get("required", True)),
                                           order=int(raw.get("order", order))))
    return spec


def find_problem_dirs(root: Path) -> list[Path]:
    """`root` — bitta masala papkasi yoki masala papkalari to'plami."""
    root = Path(root)
    if (root / "problem.yaml").exists():
        return [root]
    return sorted(p for p in root.iterdir() if p.is_dir() and (p / "problem.yaml").exists())


def current_models() -> SimpleNamespace:
    """Joriy (runtime) modellar to'plami."""
    from courses.models import Lesson

    from .models import LessonProblem, Problem, QuizOption, QuizQuestion, RubricCriterion, Tag, TestCase

    return SimpleNamespace(Problem=Problem, Tag=Tag, TestCase=TestCase, QuizQuestion=QuizQuestion,
                           QuizOption=QuizOption, RubricCriterion=RubricCriterion,
                           LessonProblem=LessonProblem, Lesson=Lesson)


def _only_existing(model, values: dict[str, Any]) -> dict[str, Any]:
    """Modelda mavjud bo'lmagan maydonlarni tashlab yuboradi (tarixiy modellar uchun)."""
    names = {f.name for f in model._meta.get_fields()}
    return {k: v for k, v in values.items() if k in names}


def _write_media(relative: str, content: str) -> None:
    target = Path(settings.MEDIA_ROOT) / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8", newline="\n")


def save_problem(spec: ProblemSpec, author, models: SimpleNamespace | None = None,
                 status: str = "draft", is_seed: bool = False) -> tuple[Any, bool]:
    """
    ProblemSpec ni bazaga yozadi (slug bo'yicha yaratadi yoki yangilaydi).

    Testlar, savollar va rubrika tartib raqami bo'yicha yangilanadi, ortiqchalari o'chiriladi.
    """
    m = models or current_models()
    problem_values = _only_existing(m.Problem, {
        "title": spec.title, "type": spec.type, "author": author, "status": status,
        "difficulty": spec.difficulty, "points": spec.points, "statement": spec.statement,
        "input_format": spec.input_format, "output_format": spec.output_format, "notes": spec.notes,
        "time_limit": spec.time_limit, "memory_limit": spec.memory_limit, "checker": spec.checker,
        "float_epsilon": spec.epsilon, "reference_solution": spec.solution, "is_seed": is_seed,
    })
    problem, created = m.Problem.objects.update_or_create(slug=spec.slug, defaults=problem_values)

    tags = []
    for name in spec.tags:
        tag, _ = m.Tag.objects.get_or_create(slug=slugify(name) or name.lower(), defaults={"name": name})
        tags.append(tag)
    problem.tags.set(tags)

    for test in spec.tests:
        base = f"tests/{spec.slug}/{test.order:02d}"
        _write_media(base + ".in", test.input)
        _write_media(base + ".out", test.output)
        m.TestCase.objects.update_or_create(problem=problem, order=test.order, defaults={
            "input_file": base + ".in", "output_file": base + ".out",
            "is_sample": test.is_sample, "points": test.points,
        })
    m.TestCase.objects.filter(problem=problem, order__gt=len(spec.tests)).delete()

    for question in spec.questions:
        obj, _ = m.QuizQuestion.objects.update_or_create(problem=problem, order=question.order, defaults={
            "kind": question.kind, "text": question.text, "points": question.points,
            "correct_text": "|".join(question.answers), "explanation": question.explanation,
        })
        m.QuizOption.objects.filter(question=obj).delete()
        m.QuizOption.objects.bulk_create([
            m.QuizOption(question=obj, order=i, text=text, is_correct=ok)
            for i, (text, ok) in enumerate(question.options, start=1)
        ])
    m.QuizQuestion.objects.filter(problem=problem, order__gt=len(spec.questions)).delete()

    for criterion in spec.rubric:
        m.RubricCriterion.objects.update_or_create(problem=problem, order=criterion.order, defaults={
            "title": criterion.title, "max_points": criterion.points, "description": criterion.description,
        })
    m.RubricCriterion.objects.filter(problem=problem, order__gt=len(spec.rubric)).delete()

    for link in spec.lessons:
        lesson = m.Lesson.objects.get(module__course__slug=spec.course_slug, number=link.lesson)
        m.LessonProblem.objects.update_or_create(lesson=lesson, problem=problem, defaults={
            "kind": link.kind, "is_required": link.required, "order": link.order,
        })
    return problem, created


def import_directory(root: Path, author, models: SimpleNamespace | None = None,
                     status: str = "draft", is_seed: bool = False) -> list[tuple[Any, bool]]:
    """Papkadagi barcha masalalarni import qiladi. Avval hammasi tekshiriladi, keyin yoziladi."""
    specs = [parse_problem_dir(path) for path in find_problem_dirs(root)]
    return [save_problem(spec, author, models, status=status, is_seed=is_seed) for spec in specs]
