"""
Kontest reytingi — Codeforces uslubidagi Elo (boshlang'ich reyting 1200).

1. Har ishtirokchi uchun kutilgan o'rin: seed_i = 1 + Σ P(j yutadi i), P = 1 / (1 + 10^((r_i - r_j)/400)).
2. Maqsadli o'rin: m_i = √(seed_i · rank_i); m_i ga mos reyting R_i ikkilik qidiruv bilan topiladi.
3. delta_i = (R_i - r_i) / 2; keyin reyting inflyatsiyasini oldini olish uchun tuzatishlar.
"""

import math
from dataclasses import dataclass

INITIAL_RATING = 1200


@dataclass(frozen=True)
class Standing:
    """Kontest natijasi: ishtirokchi, eski reytingi va o'rni (teng o'rinlar bir xil raqam oladi)."""

    key: object
    rating: int
    rank: int


def _win_probability(rating_a: float, rating_b: float) -> float:
    """a ning b dan yuqori o'rin olish ehtimoli."""
    return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400.0))


def _seed(rating: float, others: list[float]) -> float:
    return 1.0 + sum(_win_probability(other, rating) for other in others)


def _rating_for_seed(target: float, others: list[float]) -> float:
    low, high = -2000.0, 6000.0
    for _ in range(60):
        mid = (low + high) / 2
        if _seed(mid, others) < target:
            high = mid  # seed kichik → reyting yuqori; maqsad seed'ga yetish uchun pasaytiramiz
        else:
            low = mid
    return (low + high) / 2


def rating_changes(standings: list[Standing]) -> dict[object, int]:
    """{ishtirokchi: reyting o'zgarishi}. 2 dan kam ishtirokchida o'zgarish yo'q."""
    n = len(standings)
    if n < 2:
        return {s.key: 0 for s in standings}
    ratings = [float(s.rating) for s in standings]
    deltas: list[float] = []
    for index, standing in enumerate(standings):
        others = ratings[:index] + ratings[index + 1:]
        seed = _seed(ratings[index], others)
        target = math.sqrt(seed * standing.rank)
        deltas.append((_rating_for_seed(target, others) - ratings[index]) / 2)

    # 1) Umumiy yig'indi biroz manfiy bo'lsin (inflyatsiya yo'q)
    correction = -sum(deltas) / n - 1
    deltas = [d + correction for d in deltas]
    # 2) Eng kuchli ishtirokchilar yig'indisi 0 atrofida bo'lsin
    top = min(n, int(4 * math.sqrt(n)))
    order = sorted(range(n), key=lambda i: -ratings[i])[:top]
    top_sum = sum(deltas[i] for i in order)
    correction = min(max(-top_sum / top, -10), 0)
    deltas = [d + correction for d in deltas]
    return {s.key: int(round(d)) for s, d in zip(standings, deltas, strict=True)}


def competition_ranks(scores: list[tuple[object, tuple]]) -> list[tuple[object, int]]:
    """
    (kalit, solishtirish_kaliti) ro'yxatidan o'rinlar: kichik kalit — yuqori o'rin;
    teng natijalar bir xil o'rin oladi, keyingisi suriladi (1, 1, 3).
    """
    ordered = sorted(scores, key=lambda item: item[1])
    result: list[tuple[object, int]] = []
    for index, (key, value) in enumerate(ordered, start=1):
        rank = index if index == 1 or value != ordered[index - 2][1] else result[-1][1]
        result.append((key, rank))
    return result
