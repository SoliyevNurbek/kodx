"""
LocalDevBackend — FAQAT DEV/TEST UCHUN. PRODUCTION UCHUN EMAS!

Python kodini alohida jarayonda (subprocess) ishga tushiradi: vaqtinchalik papka,
vaqt chegarasi, xotira chegarasi (Windows — Job Object, POSIX — rlimit) va bola
jarayon yaratish taqiqi (Windows). Bu haqiqiy sandbox emas: kod fayl tizimi va
tarmoqqa kira oladi. Production'da faqat Judge0Backend ishlatiladi.

Faqat judge worker'dan chaqiriladi — Django veb-jarayoni ichida hech qachon.
"""

import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from ..checker import check_output
from ..types import JudgeResult, JudgeTest, Language, Limits, TestOutcome, Verdict, overall_verdict
from .base import JudgeBackend

OUTPUT_KEEP_CHARS = 2000  # bazada saqlanadigan chiqish/xato uzunligi
STARTUP_GRACE_S = 1.0  # interpretator ishga tushishi uchun qo'shimcha vaqt (o'ldirishdan oldin)
# POSIX'da RLIMIT_AS virtual xotirani cheklaydi; interpretatorning o'zi ham joy oladi
POSIX_AS_OVERHEAD_MB = 64

IS_WINDOWS = sys.platform == "win32"


@dataclass
class ExecResult:
    """Bitta ishga tushirish natijasi (tekshiruvsiz)."""

    stdout: str
    stderr: str
    returncode: int
    time_ms: int
    peak_bytes: int
    timed_out: bool

    @property
    def ok(self) -> bool:
        return self.returncode == 0 and not self.timed_out


def local_backend_allowed() -> bool:
    """LocalDevBackend faqat DEBUG=True da yoki test jarayonida ruxsat etiladi."""
    return bool(settings.DEBUG or getattr(settings, "TESTING", False))


class _WindowsJob:
    """Windows Job Object: xotira chegarasi, bitta jarayon, eng yuqori xotirani o'lchash."""

    def __init__(self, memory_bytes: int) -> None:
        import ctypes
        from ctypes import wintypes

        self.ctypes = ctypes

        class IoCounters(ctypes.Structure):
            _fields_ = [(name, ctypes.c_ulonglong) for name in (
                "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]

        class BasicLimit(ctypes.Structure):
            _fields_ = [
                ("PerProcessUserTimeLimit", ctypes.c_int64),
                ("PerJobUserTimeLimit", ctypes.c_int64),
                ("LimitFlags", wintypes.DWORD),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t),
                ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD),
            ]

        class ExtendedLimit(ctypes.Structure):
            _fields_ = [
                ("BasicLimitInformation", BasicLimit),
                ("IoInfo", IoCounters),
                ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t),
            ]

        self.ExtendedLimit = ExtendedLimit
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.CreateJobObjectW.restype = wintypes.HANDLE
        k32.CreateJobObjectW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p]
        k32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        k32.QueryInformationJobObject.argtypes = [
            wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p]
        k32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        k32.CloseHandle.argtypes = [wintypes.HANDLE]
        self.k32 = k32

        self.handle = k32.CreateJobObjectW(None, None)
        info = ExtendedLimit()
        job_limit_process_memory, job_limit_active_process, job_limit_kill_on_close = 0x100, 0x8, 0x2000
        info.BasicLimitInformation.LimitFlags = (
            job_limit_process_memory | job_limit_active_process | job_limit_kill_on_close)
        info.BasicLimitInformation.ActiveProcessLimit = 1
        info.ProcessMemoryLimit = memory_bytes
        k32.SetInformationJobObject(self.handle, 9, ctypes.byref(info), ctypes.sizeof(info))

    def assign(self, process: subprocess.Popen) -> None:
        self.k32.AssignProcessToJobObject(self.handle, int(process._handle))  # noqa: SLF001

    def peak_memory_bytes(self) -> int:
        info = self.ExtendedLimit()
        ok = self.k32.QueryInformationJobObject(
            self.handle, 9, self.ctypes.byref(info), self.ctypes.sizeof(info), None)
        return int(info.PeakProcessMemoryUsed) if ok else 0

    def close(self) -> None:
        self.k32.CloseHandle(self.handle)


def _posix_limits(limits: Limits):
    """POSIX: preexec_fn — xotira, CPU vaqti va fayl hajmi chegaralari."""

    def apply() -> None:  # pragma: no cover - Windows'da ishlamaydi
        import resource

        memory = (limits.memory_mb + POSIX_AS_OVERHEAD_MB) * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (memory, memory))
        cpu = int(limits.time_ms / 1000) + 1
        resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu + 1))
        resource.setrlimit(resource.RLIMIT_FSIZE, (16 * 1024 * 1024,) * 2)
        os.setsid()

    return apply


class LocalDevBackend(JudgeBackend):
    """Dev uchun mahalliy Python judge. PRODUCTION UCHUN EMAS."""

    name = "local"

    def __init__(self, python_executable: str | None = None) -> None:
        if not local_backend_allowed():
            raise ImproperlyConfigured("LocalDevBackend faqat DEBUG=True da ishlaydi. Production'da Judge0 ishlating.")
        # Windows venv'dagi python.exe — bola jarayon ochuvchi launcher; Job Object bitta jarayonga
        # ruxsat beradi, shuning uchun asosiy interpretator ishlatiladi (venv paketlari ham ko'rinmaydi).
        self.python = (python_executable or getattr(settings, "JUDGE_PYTHON", "")
                       or getattr(sys, "_base_executable", "") or sys.executable)

    def supports(self, lang: str) -> bool:
        return lang == Language.PYTHON3

    # --- yordamchi metodlar ---

    def _env(self) -> dict[str, str]:
        if IS_WINDOWS:
            return {"SYSTEMROOT": os.environ.get("SYSTEMROOT", r"C:\Windows"), "PATH": ""}
        return {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"}

    def _command(self, *args: str) -> list[str]:
        # -I: izolyatsiya rejimi (PYTHON* o'zgaruvchilari, user site, joriy papka e'tiborsiz)
        # -X utf8: stdin/stdout doim UTF-8
        return [self.python, "-I", "-X", "utf8", *args]

    def _compile_error(self, workdir: Path) -> str:
        """Sintaksis xatosini alohida jarayonda tekshiradi (kod bajarilmaydi)."""
        probe = "import sys; compile(open('solution.py', encoding='utf-8').read(), 'solution.py', 'exec')"
        proc = subprocess.run(self._command("-c", probe), cwd=workdir, env=self._env(),
                              capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15)
        return proc.stderr.strip() if proc.returncode != 0 else ""

    def _execute_in(self, workdir: Path, stdin: str, limits: Limits) -> ExecResult:
        """`workdir/solution.py` ni bir marta ishga tushiradi."""
        memory_bytes = limits.memory_mb * 1024 * 1024
        job = _WindowsJob(memory_bytes) if IS_WINDOWS else None
        kwargs = {}
        if not IS_WINDOWS:  # pragma: no cover
            kwargs["preexec_fn"] = _posix_limits(limits)
        started = time.perf_counter()
        process = subprocess.Popen(
            self._command("solution.py"), cwd=workdir, env=self._env(),
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs,
        )
        if job:
            job.assign(process)
        timed_out = False
        try:
            stdout, stderr = process.communicate(stdin.encode("utf-8"),
                                                 timeout=limits.time_ms / 1000 + STARTUP_GRACE_S)
        except subprocess.TimeoutExpired:
            timed_out = True
            process.kill()
            stdout, stderr = process.communicate()
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        peak = job.peak_memory_bytes() if job else 0
        if job:
            job.close()
        return ExecResult(
            stdout=stdout.decode("utf-8", errors="replace"),
            stderr=stderr.decode("utf-8", errors="replace"),
            returncode=process.returncode, time_ms=elapsed_ms, peak_bytes=peak, timed_out=timed_out,
        )

    def _run_one(self, workdir: Path, test: JudgeTest, limits: Limits) -> TestOutcome:
        run = self._execute_in(workdir, test.input, limits)
        memory_bytes = limits.memory_mb * 1024 * 1024
        outcome = TestOutcome(test_id=test.id, verdict=Verdict.ACCEPTED, time_ms=run.time_ms,
                              memory_kb=run.peak_bytes // 1024, output=run.stdout[:OUTPUT_KEEP_CHARS],
                              error=run.stderr[-OUTPUT_KEEP_CHARS:])
        if run.timed_out or run.time_ms > limits.time_ms:
            outcome.verdict = Verdict.TIME_LIMIT
        elif run.returncode != 0:
            near_limit = run.peak_bytes and run.peak_bytes >= memory_bytes * 0.95
            is_mle = "MemoryError" in run.stderr or near_limit
            outcome.verdict = Verdict.MEMORY_LIMIT if is_mle else Verdict.RUNTIME_ERROR
        elif check_output(run.stdout, test.expected, limits.checker, limits.epsilon):
            outcome.points = test.points
        else:
            outcome.verdict = Verdict.WRONG_ANSWER
        return outcome

    def execute(self, code: str, stdin: str, limits: Limits) -> ExecResult:
        """
        Kodni bitta kirish bilan ishga tushirib, to'liq natijani qaytaradi.

        Etalon yechimdan .out fayllarni yaratish uchun (faqat o'qituvchi/seed asboblari).
        """
        with tempfile.TemporaryDirectory(prefix="kodx-judge-") as tmp:
            workdir = Path(tmp)
            (workdir / "solution.py").write_text(code, encoding="utf-8")
            return self._execute_in(workdir, stdin, limits)

    # --- interfeys ---

    def submit(self, code: str, lang: str, tests: list[JudgeTest], limits: Limits,
               stop_on_failure: bool = False) -> JudgeResult:
        if not self.supports(lang):
            return JudgeResult(verdict=Verdict.INTERNAL_ERROR, compile_output=f"Til qo'llab-quvvatlanmaydi: {lang}")
        with tempfile.TemporaryDirectory(prefix="kodx-judge-") as tmp:
            workdir = Path(tmp)
            (workdir / "solution.py").write_text(code, encoding="utf-8")
            compile_error = self._compile_error(workdir)
            if compile_error:
                return JudgeResult(verdict=Verdict.COMPILATION_ERROR, compile_output=compile_error[-OUTPUT_KEEP_CHARS:])
            outcomes: list[TestOutcome] = []
            for test in tests:
                outcome = self._run_one(workdir, test, limits)
                outcomes.append(outcome)
                if stop_on_failure and outcome.verdict != Verdict.ACCEPTED:
                    break
        return JudgeResult(verdict=overall_verdict(outcomes), tests=outcomes)
