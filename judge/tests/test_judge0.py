"""Judge0Backend testlari (HTTP so'rovlar almashtirilgan)."""

import base64
import urllib.error

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings

from judge.backends.judge0 import Judge0Backend
from judge.types import JudgeTest, Limits, Verdict


def b64(text: str) -> str:
    return base64.b64encode(text.encode()).decode()


class FakeJudge0(Judge0Backend):
    """Tayyor javoblar qaytaruvchi Judge0."""

    def __init__(self, results: list[dict], polls_before_done: int = 1) -> None:
        super().__init__(url="http://judge0.test", token="t", poll_interval=0)
        self.results = results
        self.polls_left = polls_before_done
        self.calls: list[tuple[str, str, object]] = []

    def _request(self, method, path, body=None):
        self.calls.append((method, path, body))
        if method == "POST":
            return [{"token": f"t{i}"} for i in range(len(body["submissions"]))]
        if self.polls_left > 0:
            self.polls_left -= 1
            return {"submissions": [{"status": {"id": 2}} for _ in self.results]}
        return {"submissions": self.results}


class BrokenJudge0(FakeJudge0):
    def _request(self, method, path, body=None):
        raise urllib.error.URLError("ulanish yoq")


TESTS = [JudgeTest(1, "1 2\n", "3\n", 1), JudgeTest(2, "2 2\n", "4\n", 1)]


class Judge0Tests(SimpleTestCase):
    def test_accepted_and_payload(self) -> None:
        backend = FakeJudge0([{"status": {"id": 3}, "stdout": b64("3\n"), "time": "0.01", "memory": 900},
                              {"status": {"id": 3}, "stdout": b64("4\n"), "time": "0.02", "memory": 1000}])
        result = backend.submit("code", "python3", TESTS, Limits(time_ms=2000, memory_mb=128))
        self.assertEqual(result.verdict, Verdict.ACCEPTED)
        self.assertEqual(result.score, 2)
        self.assertEqual(result.max_time_ms, 20)
        submission = backend.calls[0][2]["submissions"][0]
        self.assertEqual(submission["language_id"], 71)
        self.assertEqual(submission["memory_limit"], 128 * 1024)
        self.assertEqual(submission["cpu_time_limit"], 2.0)
        self.assertEqual(base64.b64decode(submission["stdin"]).decode(), "1 2\n")

    def test_wrong_answer_and_tle(self) -> None:
        backend = FakeJudge0([{"status": {"id": 3}, "stdout": b64("0\n")}, {"status": {"id": 5}}])
        result = backend.submit("code", "python3", TESTS, Limits())
        self.assertEqual([t.verdict for t in result.tests], [Verdict.WRONG_ANSWER, Verdict.TIME_LIMIT])
        self.assertEqual(result.verdict, Verdict.WRONG_ANSWER)

    def test_runtime_memory_and_syntax_errors(self) -> None:
        backend = FakeJudge0([{"status": {"id": 11}, "stderr": b64("MemoryError")},
                              {"status": {"id": 11}, "stderr": b64("SyntaxError: invalid syntax")}])
        result = backend.submit("code", "python3", TESTS, Limits())
        self.assertEqual([t.verdict for t in result.tests], [Verdict.MEMORY_LIMIT, Verdict.COMPILATION_ERROR])

    def test_network_error_is_internal_error(self) -> None:
        result = BrokenJudge0([]).submit("code", "python3", TESTS, Limits())
        self.assertEqual(result.verdict, Verdict.INTERNAL_ERROR)

    def test_unsupported_language(self) -> None:
        result = FakeJudge0([]).submit("code", "cobol", TESTS, Limits())
        self.assertEqual(result.verdict, Verdict.INTERNAL_ERROR)

    @override_settings(JUDGE0_URL="")
    def test_requires_url(self) -> None:
        with self.assertRaises(ImproperlyConfigured):
            Judge0Backend()
