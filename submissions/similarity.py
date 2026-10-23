"""
Ko'chirmachilikni aniqlash: bir masaladagi yechimlarning o'xshashligi.

Kod tokenlarga ajratiladi (izohlar va bo'shliqlar tashlanadi), o'zgaruvchi nomlari, sonlar va satrlar
umumiy belgiga almashtiriladi — nomlarini o'zgartirib ko'chirilgan kod ham topiladi. Keyin token
ketma-ketliklari `difflib.SequenceMatcher` bilan solishtiriladi (0..1).

Kod BAJARILMAYDI — faqat matn sifatida tahlil qilinadi.
"""

import builtins
import io
import keyword
import tokenize
from difflib import SequenceMatcher
from itertools import combinations

from django.db import transaction
from django.db.models import Max

from judge.types import Verdict

from .models import SimilarityMatch, Submission

SKIP = {tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT,
        tokenize.ENCODING, tokenize.ENDMARKER}
KEEP_NAMES = set(keyword.kwlist) | set(dir(builtins))


def normalize_tokens(code: str) -> list[str]:
    """Python kodini normallashtirilgan tokenlar ro'yxatiga aylantiradi (sintaksis xatosida — so'zlar bo'yicha)."""
    tokens: list[str] = []
    try:
        for token in tokenize.generate_tokens(io.StringIO(code).readline):
            if token.type in SKIP:
                continue
            if token.type == tokenize.NAME:
                tokens.append(token.string if token.string in KEEP_NAMES else "ID")
            elif token.type == tokenize.NUMBER:
                tokens.append("NUM")
            elif token.type == tokenize.STRING or token.type in getattr(tokenize, "FSTRING_TYPES", ()):
                tokens.append("STR")
            else:
                tokens.append(token.string)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return code.split()
    return tokens


def similarity(code_a: str, code_b: str) -> float:
    a, b = normalize_tokens(code_a), normalize_tokens(code_b)
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b, autojunk=False).ratio()


def latest_submissions(problem, contest=None, accepted_only: bool = True) -> list[Submission]:
    """Har foydalanuvchining eng oxirgi (qabul qilingan) yechimi."""
    queryset = Submission.objects.filter(problem=problem)
    if accepted_only:
        queryset = queryset.filter(verdict=Verdict.ACCEPTED)
    if contest is not None:
        queryset = queryset.filter(contest=contest)
    last_ids = queryset.values("user_id").annotate(last=Max("pk")).values_list("last", flat=True)
    return list(Submission.objects.filter(pk__in=list(last_ids)).select_related("user"))


def check_problem(problem, threshold: float = 0.85, contest=None, min_tokens: int = 15) -> list[SimilarityMatch]:
    """
    Masala bo'yicha juftliklarni solishtiradi va `threshold` dan yuqorilarini saqlaydi
    (shu masala bo'yicha eski natijalar almashtiriladi). Juda qisqa yechimlar (masalan, `print(a+b)`)
    tabiiy ravishda o'xshash bo'lgani uchun `min_tokens` dan kichiklari solishtirilmaydi.
    """
    submissions = [s for s in latest_submissions(problem, contest) if len(normalize_tokens(s.code)) >= min_tokens]
    tokens = {s.pk: normalize_tokens(s.code) for s in submissions}
    matches = []
    for a, b in combinations(sorted(submissions, key=lambda s: s.pk), 2):
        score = SequenceMatcher(None, tokens[a.pk], tokens[b.pk], autojunk=False).ratio()
        if score >= threshold:
            matches.append(SimilarityMatch(problem=problem, submission_a=a, submission_b=b, score=round(score, 4)))
    with transaction.atomic():
        SimilarityMatch.objects.filter(problem=problem).delete()
        SimilarityMatch.objects.bulk_create(matches)
    return matches
