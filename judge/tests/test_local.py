"""LocalDevBackend testlari (haqiqiy alohida jarayonlar bilan)."""

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings

from judge.backends import get_backend
from judge.backends.local import LocalDevBackend
from judge.types import JudgeTest, Limits, Verdict

SUM = "a, b = map(int, input().split())\nprint(a + b)\n"
TESTS = [JudgeTest(1, "2 3\n", "5\n", points=2), JudgeTest(2, "10 -4\n", "6\n", points=3)]


class LocalBackendTests(SimpleTestCase):
    def setUp(self) -> None:
        self.backend = LocalDevBackend()
        self.limits = Limits(time_ms=1000, memory_mb=64)

    def test_accepted_with_score(self) -> None:
        result = self.backend.submit(SUM, "python3", TESTS, self.limits)
        self.assertEqual(result.verdict, Verdict.ACCEPTED)
        self.assertEqual(result.score, 5)
        self.assertEqual([t.verdict for t in result.tests], [Verdict.ACCEPTED] * 2)

    def test_wrong_answer_partial_score(self) -> None:
        code = "a, b = map(int, input().split())\nprint(5)\n"
        result = self.backend.submit(code, "python3", TESTS, self.limits)
        self.assertEqual(result.verdict, Verdict.WRONG_ANSWER)
        self.assertEqual(result.score, 2)

    def test_time_limit(self) -> None:
        result = self.backend.submit("while True:\n    pass\n", "python3", TESTS[:1], Limits(time_ms=300))
        self.assertEqual(result.verdict, Verdict.TIME_LIMIT)

    def test_runtime_error(self) -> None:
        result = self.backend.submit("print(1 / 0)\n", "python3", TESTS[:1], self.limits)
        self.assertEqual(result.verdict, Verdict.RUNTIME_ERROR)
        self.assertIn("ZeroDivisionError", result.tests[0].error)

    def test_memory_limit(self) -> None:
        result = self.backend.submit("x = bytearray(300 * 1024 * 1024)\n", "python3", TESTS[:1], self.limits)
        self.assertEqual(result.verdict, Verdict.MEMORY_LIMIT)

    def test_compilation_error_runs_no_tests(self) -> None:
        result = self.backend.submit("print((\n", "python3", TESTS, self.limits)
        self.assertEqual(result.verdict, Verdict.COMPILATION_ERROR)
        self.assertEqual(result.tests, [])
        self.assertIn("SyntaxError", result.compile_output)

    def test_unicode_io(self) -> None:
        tests = [JudgeTest(1, "Oʻzbekiston\n", "Salom, Oʻzbekiston!\n")]
        result = self.backend.submit("print(f'Salom, {input()}!')\n", "python3", tests, self.limits)
        self.assertEqual(result.verdict, Verdict.ACCEPTED)

    def test_user_code_cannot_import_project_packages(self) -> None:
        result = self.backend.submit("import django\nprint(5)\n", "python3", TESTS[:1], self.limits)
        self.assertEqual(result.verdict, Verdict.RUNTIME_ERROR)

    def test_stop_on_failure(self) -> None:
        result = self.backend.submit("print(0)\n", "python3", TESTS, self.limits, stop_on_failure=True)
        self.assertEqual(len(result.tests), 1)

    def test_unsupported_language(self) -> None:
        result = self.backend.submit("x", "cobol", TESTS, self.limits)
        self.assertEqual(result.verdict, Verdict.INTERNAL_ERROR)

    def test_execute_returns_full_output(self) -> None:
        run = self.backend.execute("print('x' * 5000)\n", "", self.limits)
        self.assertTrue(run.ok)
        self.assertEqual(len(run.stdout.strip()), 5000)

    @override_settings(DEBUG=False, TESTING=False)
    def test_refuses_to_run_in_production(self) -> None:
        with self.assertRaises(ImproperlyConfigured):
            LocalDevBackend()

    @override_settings(JUDGE_BACKEND="nomalum")
    def test_get_backend_unknown(self) -> None:
        with self.assertRaises(ImproperlyConfigured):
            get_backend()

    def test_get_backend_local(self) -> None:
        self.assertIsInstance(get_backend("local"), LocalDevBackend)
