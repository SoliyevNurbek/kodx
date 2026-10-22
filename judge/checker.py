"""Dastur chiqishini kutilgan javob bilan solishtirish."""

import math

from .types import CheckerMode


def _normalize_lines(text: str) -> list[str]:
    """CRLF → LF, qator oxiridagi bo'shliqlar va oxirgi bo'sh qatorlar olib tashlanadi."""
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    while lines and not lines[-1]:
        lines.pop()
    return lines


def _tokens_equal_float(out: str, exp: str, epsilon: float) -> bool:
    """Ikki token teng: son bo'lsa — absolyut yoki nisbiy xato epsilon ichida."""
    if out == exp:
        return True
    try:
        a, b = float(out), float(exp)
    except ValueError:
        return False
    if math.isnan(a) or math.isnan(b):
        return False
    return math.isclose(a, b, rel_tol=epsilon, abs_tol=epsilon)


def check_output(output: str, expected: str, mode: str = CheckerMode.WHITESPACE, epsilon: float = 1e-6) -> bool:
    """
    Chiqish to'g'rimi.

    exact — qatorma-qator (qator oxiridagi bo'shliqlar va oxirgi bo'sh qatorlar e'tiborsiz);
    whitespace — barcha bo'shliq va qator ajratgichlar e'tiborsiz (tokenlar ketma-ketligi);
    float — tokenlar, sonlar `epsilon` aniqlik bilan.
    """
    if mode == CheckerMode.EXACT:
        return _normalize_lines(output) == _normalize_lines(expected)
    out_tokens, exp_tokens = output.split(), expected.split()
    if len(out_tokens) != len(exp_tokens):
        return False
    if mode == CheckerMode.FLOAT:
        return all(_tokens_equal_float(a, b, epsilon) for a, b in zip(out_tokens, exp_tokens, strict=True))
    return out_tokens == exp_tokens
