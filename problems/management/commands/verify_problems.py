"""`manage.py verify_problems` — etalon yechimlarni barcha testlarda tekshirish (LocalDevBackend)."""

from django.core.management.base import BaseCommand, CommandError

from judge.backends.local import LocalDevBackend
from judge.types import Language, Verdict
from problems.models import Problem


def verify_problem(problem: Problem, backend: LocalDevBackend) -> tuple[bool, str]:
    """Etalon yechim barcha testlardan o'tadimi. (natija, izoh)"""
    if not problem.reference_solution.strip():
        return False, "etalon yechim yo'q"
    tests = problem.judge_tests()
    if not tests:
        return False, "testlar yo'q"
    result = backend.submit(problem.reference_solution, Language.PYTHON3, tests, problem.limits)
    if result.verdict != Verdict.ACCEPTED:
        failed = next((t for t in result.tests if t.verdict != Verdict.ACCEPTED), None)
        detail = f"test {failed.test_id}: {failed.verdict}" if failed else result.compile_output[:200]
        return False, f"{result.verdict} ({detail})"
    return True, f"{len(tests)} test, {result.max_time_ms} ms"


class Command(BaseCommand):
    help = "Code masalalarning etalon yechimlarini barcha testlarda tekshiradi."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--slug", action="append", help="Faqat shu masala(lar)")
        parser.add_argument("--seed", action="store_true", help="Faqat seed masalalar")

    def handle(self, *args, slug: list[str] | None, seed: bool, **options) -> None:
        problems = Problem.objects.filter(type=Problem.Type.CODE).prefetch_related("test_cases")
        if slug:
            problems = problems.filter(slug__in=slug)
        if seed:
            problems = problems.filter(is_seed=True)
        backend = LocalDevBackend()
        failures = 0
        for problem in problems:
            ok, info = verify_problem(problem, backend)
            failures += not ok
            style = self.style.SUCCESS if ok else self.style.ERROR
            self.stdout.write(style(f"{'OK ' if ok else 'XATO'} {problem.slug}: {info}"))
        total = problems.count()
        if failures:
            raise CommandError(f"{failures}/{total} ta masala tekshiruvdan o'tmadi.")
        self.stdout.write(self.style.SUCCESS(f"{total} ta masala — barchasi o'tdi."))
