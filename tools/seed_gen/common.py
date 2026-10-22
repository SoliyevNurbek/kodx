"""Seed masala papkalarini yaratish uchun umumiy yordamchilar (scratchpad generator)."""
import os
import sys
import textwrap
from pathlib import Path

ROOT = Path(r"D:\OSPanel\home\kodx")
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.chdir(ROOT)
import django  # noqa: E402

django.setup()

import yaml  # noqa: E402

from judge.backends.local import LocalDevBackend  # noqa: E402
from judge.checker import check_output  # noqa: E402
from judge.types import Limits  # noqa: E402

SEED = ROOT / "problems" / "seed"
BACKEND = LocalDevBackend()
KIND_BY_LEVEL = {0: "classwork", 1: "homework", 2: "challenge"}


def dedent(text: str) -> str:
    return textwrap.dedent(text).strip() + "\n"


def _yaml_dump(data: dict) -> str:
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=100)


def _norm_input(text: str) -> str:
    text = textwrap.dedent(text).lstrip("\n") if text.startswith("\n") else text
    return text if text.endswith("\n") else text + "\n"


def code_problem(*, slug, title, lesson, level, difficulty, tags, statement, input_format, output_format,
                 solution, samples, hidden, checker="whitespace", epsilon=None, time_limit=1000,
                 memory_limit=256, notes=""):
    """level: 0 — oson (sinf ishi), 1 — o'rta (uyga vazifa), 2 — challenge."""
    assert len(samples) >= 2 and len(samples) + len(hidden) >= 5, slug
    folder = SEED / slug
    tests = folder / "tests"
    tests.mkdir(parents=True, exist_ok=True)
    for old in tests.glob("*"):
        old.unlink()
    solution = dedent(solution)
    meta = {
        "title": title, "type": "code", "difficulty": difficulty, "points": difficulty * 100,
        "tags": tags, "time_limit": time_limit, "memory_limit": memory_limit, "checker": checker,
    }
    if epsilon is not None:
        meta["epsilon"] = epsilon
    meta.update({
        "samples": list(range(1, len(samples) + 1)),
        "input_format": dedent(input_format).strip(), "output_format": dedent(output_format).strip(),
    })
    if notes:
        meta["notes"] = dedent(notes).strip()
    meta["lessons"] = [{"lesson": lesson, "kind": KIND_BY_LEVEL[level], "required": level < 2,
                        "order": level + 1}]
    (folder / "problem.yaml").write_text(_yaml_dump(meta), encoding="utf-8", newline="\n")
    (folder / "statement.md").write_text(dedent(statement), encoding="utf-8", newline="\n")
    (folder / "solution.py").write_text(solution, encoding="utf-8", newline="\n")

    limits = Limits(time_ms=time_limit, memory_mb=memory_limit, checker=checker, epsilon=epsilon or 1e-6)
    inputs = [s[0] for s in samples] + list(hidden)
    for index, raw in enumerate(inputs, start=1):
        data = _norm_input(raw)
        run = BACKEND.execute(solution, data, limits)
        assert run.ok, f"{slug} test {index}: yechim xatosi\n{run.stderr}"
        assert run.time_ms < time_limit * 0.6, f"{slug} test {index}: sekin ({run.time_ms} ms)"
        assert run.stdout.strip(), f"{slug} test {index}: bo'sh chiqish"
        if index <= len(samples):
            expected = _norm_input(samples[index - 1][1])
            assert check_output(run.stdout, expected, checker, epsilon or 1e-6), (
                f"{slug} namuna {index}: kutilgan\n{expected!r}\nolingan\n{run.stdout!r}")
        (tests / f"{index:02d}.in").write_text(data, encoding="utf-8", newline="\n")
        (tests / f"{index:02d}.out").write_text(run.stdout.replace("\r\n", "\n"), encoding="utf-8", newline="\n")
    print(f"  ok {slug} ({len(inputs)} test)")


def quiz_problem(*, slug, title, lesson, questions, tags=(), difficulty=1):
    """questions: list of dict(text, kind, options=[(text, correct)], answers=[...], explanation)."""
    assert len(questions) >= 5, slug
    folder = SEED / slug
    folder.mkdir(parents=True, exist_ok=True)
    qs = []
    for q in questions:
        item = {"text": q["text"], "kind": q.get("kind", "single"), "points": q.get("points", 1)}
        if item["kind"] == "text":
            item["answers"] = q["answers"]
        else:
            item["options"] = [{"text": t, "correct": c} for t, c in q["options"]]
            correct = sum(c for _, c in q["options"])
            assert (correct == 1) if item["kind"] == "single" else correct >= 1, (slug, q["text"])
        if q.get("explanation"):
            item["explanation"] = q["explanation"]
        qs.append(item)
    meta = {"title": title, "type": "quiz", "difficulty": difficulty, "points": 50, "tags": list(tags),
            "questions": qs, "lessons": [{"lesson": lesson, "kind": "classwork", "required": True, "order": 10}]}
    (folder / "problem.yaml").write_text(_yaml_dump(meta), encoding="utf-8", newline="\n")
    (folder / "statement.md").write_text(
        f"{lesson}-dars bo‘yicha {len(qs)} ta savol. Har bir to‘g‘ri javob uchun ball beriladi.\n",
        encoding="utf-8", newline="\n")
    print(f"  ok {slug} ({len(qs)} savol)")


def project_problem(*, slug, title, lesson, statement, rubric, tags=(), difficulty=3, points=100):
    """rubric: list of (title, points, description)."""
    assert sum(p for _, p, _ in rubric) == points, (slug, "rubrika yig'indisi")
    folder = SEED / slug
    folder.mkdir(parents=True, exist_ok=True)
    meta = {"title": title, "type": "project", "difficulty": difficulty, "points": points, "tags": list(tags),
            "rubric": [{"title": t, "points": p, "description": d} for t, p, d in rubric],
            "lessons": [{"lesson": lesson, "kind": "homework", "required": True, "order": 20}]}
    (folder / "problem.yaml").write_text(_yaml_dump(meta), encoding="utf-8", newline="\n")
    (folder / "statement.md").write_text(dedent(statement), encoding="utf-8", newline="\n")
    print(f"  ok {slug} (loyiha, {len(rubric)} mezon)")
