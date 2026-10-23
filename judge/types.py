"""Judge uchun umumiy ma'lumot turlari va verdiktlar."""

from dataclasses import dataclass, field

from django.db import models


class Verdict(models.TextChoices):
    """Yechim (yoki bitta test) natijasi."""

    ACCEPTED = "AC", "Qabul qilindi"
    WRONG_ANSWER = "WA", "Noto‘g‘ri javob"
    TIME_LIMIT = "TLE", "Vaqt chegarasidan oshdi"
    MEMORY_LIMIT = "MLE", "Xotira chegarasidan oshdi"
    RUNTIME_ERROR = "RE", "Bajarilish xatosi"
    COMPILATION_ERROR = "CE", "Kompilyatsiya xatosi"
    INTERNAL_ERROR = "IE", "Ichki xato"


class Language(models.TextChoices):
    """Qo'llab-quvvatlanadigan tillar. Yangi til — shu yerga va backend jadvaliga qo'shiladi."""

    PYTHON3 = "python3", "Python 3"


class CheckerMode(models.TextChoices):
    """Chiqishni solishtirish usuli."""

    EXACT = "exact", "Aniq (qator oxiridagi bo‘shliqlarsiz)"
    WHITESPACE = "whitespace", "Bo‘shliqlarni hisobga olmasdan"
    FLOAT = "float", "Sonlar epsilon bilan"


@dataclass(frozen=True)
class Limits:
    """Bitta yechim uchun cheklovlar va solishtirish usuli."""

    time_ms: int = 1000
    memory_mb: int = 256
    checker: str = CheckerMode.WHITESPACE
    epsilon: float = 1e-6


@dataclass(frozen=True)
class JudgeTest:
    """Judge'ga yuboriladigan bitta test."""

    id: int | str
    input: str
    expected: str
    points: int = 1


@dataclass
class TestOutcome:
    """Bitta test natijasi."""

    test_id: int | str
    verdict: str
    time_ms: int = 0
    memory_kb: int = 0
    points: int = 0
    output: str = ""
    error: str = ""


@dataclass
class JudgeResult:
    """Butun yechim natijasi."""

    verdict: str
    tests: list[TestOutcome] = field(default_factory=list)
    compile_output: str = ""

    @property
    def score(self) -> int:
        """To'plangan ball (o'tgan testlar ballari yig'indisi)."""
        return sum(t.points for t in self.tests if t.verdict == Verdict.ACCEPTED)

    @property
    def max_time_ms(self) -> int:
        return max((t.time_ms for t in self.tests), default=0)

    @property
    def max_memory_kb(self) -> int:
        return max((t.memory_kb for t in self.tests), default=0)


# Umumiy verdikt — birinchi muvaffaqiyatsiz testning verdikti.
def overall_verdict(outcomes: list[TestOutcome]) -> str:
    """Testlar natijasidan yakuniy verdiktni chiqaradi."""
    for outcome in outcomes:
        if outcome.verdict != Verdict.ACCEPTED:
            return outcome.verdict
    return Verdict.ACCEPTED
