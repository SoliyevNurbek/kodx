"""Judge0Backend — production uchun: kod alohida Judge0 xizmatida bajariladi."""

import base64
import json
import time
import urllib.error
import urllib.request
from typing import Any

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from ..checker import check_output
from ..types import JudgeResult, JudgeTest, Language, Limits, TestOutcome, Verdict, overall_verdict
from .base import JudgeBackend

# Judge0 til identifikatorlari (https://ce.judge0.com/languages)
LANGUAGE_IDS: dict[str, int] = {
    Language.PYTHON3: 71,
    # "cpp17": 54, "javascript": 63 — yangi tillar shu yerga
}

# Judge0 status id → verdikt (3 — dastur muvaffaqiyatli tugadi, keyin chiqishni o'zimiz tekshiramiz)
STATUS_QUEUED = {1, 2}
STATUS_MAP: dict[int, str] = {
    5: Verdict.TIME_LIMIT,
    6: Verdict.COMPILATION_ERROR,
    7: Verdict.RUNTIME_ERROR, 8: Verdict.RUNTIME_ERROR, 9: Verdict.RUNTIME_ERROR,
    10: Verdict.RUNTIME_ERROR, 11: Verdict.RUNTIME_ERROR, 12: Verdict.RUNTIME_ERROR,
    13: Verdict.INTERNAL_ERROR, 14: Verdict.INTERNAL_ERROR,
}


def _b64(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def _unb64(value: str | None) -> str:
    return base64.b64decode(value).decode("utf-8", errors="replace") if value else ""


class Judge0Backend(JudgeBackend):
    """Judge0 API (batch submissions) orqali tekshirish."""

    name = "judge0"

    def __init__(self, url: str | None = None, token: str | None = None,
                 poll_interval: float = 0.5, max_wait: float = 120.0) -> None:
        self.url = (url or getattr(settings, "JUDGE0_URL", "")).rstrip("/")
        self.token = token if token is not None else getattr(settings, "JUDGE0_TOKEN", "")
        self.auth_header = getattr(settings, "JUDGE0_AUTH_HEADER", "X-Auth-Token")
        self.poll_interval = poll_interval
        self.max_wait = max_wait
        if not self.url:
            raise ImproperlyConfigured("JUDGE0_URL sozlanmagan (.env).")

    def supports(self, lang: str) -> bool:
        return lang in LANGUAGE_IDS

    def _request(self, method: str, path: str, body: Any = None) -> Any:
        """Judge0 ga HTTP so'rov (testlarda almashtiriladi)."""
        data = json.dumps(body).encode("utf-8") if body is not None else None
        request = urllib.request.Request(self.url + path, data=data, method=method)
        request.add_header("Content-Type", "application/json")
        if self.token:
            request.add_header(self.auth_header, self.token)
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 - URL .env dan
            return json.loads(response.read().decode("utf-8"))

    def submit(self, code: str, lang: str, tests: list[JudgeTest], limits: Limits) -> JudgeResult:
        if not self.supports(lang):
            return JudgeResult(verdict=Verdict.INTERNAL_ERROR, compile_output=f"Til qo'llab-quvvatlanmaydi: {lang}")
        if not tests:
            return JudgeResult(verdict=Verdict.ACCEPTED)
        seconds = limits.time_ms / 1000
        payload = {"submissions": [{
            "source_code": _b64(code),
            "language_id": LANGUAGE_IDS[lang],
            "stdin": _b64(test.input),
            "cpu_time_limit": seconds,
            "wall_time_limit": seconds * 3,
            "memory_limit": limits.memory_mb * 1024,
        } for test in tests]}
        try:
            created = self._request("POST", "/submissions/batch?base64_encoded=true", payload)
            tokens = [item["token"] for item in created]
            results = self._wait(tokens)
        except (urllib.error.URLError, KeyError, TimeoutError, ValueError) as exc:
            return JudgeResult(verdict=Verdict.INTERNAL_ERROR, compile_output=f"Judge0 xatosi: {exc}")

        outcomes = [self._outcome(test, item, limits) for test, item in zip(tests, results, strict=True)]
        compile_output = next((_unb64(r.get("compile_output")) for r in results if r.get("compile_output")), "")
        return JudgeResult(verdict=overall_verdict(outcomes), tests=outcomes, compile_output=compile_output)

    def _wait(self, tokens: list[str]) -> list[dict]:
        deadline = time.monotonic() + self.max_wait
        fields = "token,stdout,stderr,compile_output,status,time,memory"
        while True:
            data = self._request(
                "GET", f"/submissions/batch?tokens={','.join(tokens)}&base64_encoded=true&fields={fields}")
            results = data["submissions"]
            if all(r["status"]["id"] not in STATUS_QUEUED for r in results):
                return results
            if time.monotonic() > deadline:
                raise TimeoutError("Judge0 javobi kutish vaqtidan oshdi")
            time.sleep(self.poll_interval)

    def _outcome(self, test: JudgeTest, item: dict, limits: Limits) -> TestOutcome:
        status = item["status"]["id"]
        stdout, stderr = _unb64(item.get("stdout")), _unb64(item.get("stderr"))
        memory_kb = int(item.get("memory") or 0)
        outcome = TestOutcome(
            test_id=test.id, verdict=Verdict.ACCEPTED,
            time_ms=int(float(item.get("time") or 0) * 1000), memory_kb=memory_kb,
            output=stdout[:2000], error=stderr[-2000:],
        )
        if status == 3:
            if check_output(stdout, test.expected, limits.checker, limits.epsilon):
                outcome.points = test.points
            else:
                outcome.verdict = Verdict.WRONG_ANSWER
        else:
            verdict = STATUS_MAP.get(status, Verdict.INTERNAL_ERROR)
            if verdict == Verdict.RUNTIME_ERROR and ("MemoryError" in stderr
                                                     or memory_kb >= limits.memory_mb * 1024 * 0.95):
                verdict = Verdict.MEMORY_LIMIT
            if verdict == Verdict.RUNTIME_ERROR and "SyntaxError" in stderr:
                verdict = Verdict.COMPILATION_ERROR
            outcome.verdict = verdict
        return outcome
