"""Judge backend interfeysi (adapter naqshi)."""

from abc import ABC, abstractmethod

from ..types import JudgeResult, JudgeTest, Limits


class JudgeBackend(ABC):
    """
    Kodni izolyatsiyalangan muhitda tekshiruvchi backend.

    Backend Django veb-jarayonidan EMAS, faqat judge worker'dan chaqiriladi.
    """

    name: str = "base"

    @abstractmethod
    def submit(self, code: str, lang: str, tests: list[JudgeTest], limits: Limits) -> JudgeResult:
        """Kodni barcha testlarda ishga tushiradi va natijani qaytaradi."""

    def supports(self, lang: str) -> bool:
        """Backend shu tilni qo'llab-quvvatlaydimi."""
        return True
