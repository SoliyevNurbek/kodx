"""
Judge navbati. Web so'rov yechimni faqat navbatga qo'yadi, tekshirish — alohida
`manage.py run_judge_worker` jarayonida.

Hozir: bazaga asoslangan navbat (Submission.status). Keyin Redis/Celery'ga o'tish uchun
`JudgeQueue` interfeysini amalga oshiruvchi yangi klass yozish va JUDGE_QUEUE ni o'zgartirish yetarli.
"""

from abc import ABC, abstractmethod
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.module_loading import import_string

from .models import Submission


class JudgeQueue(ABC):
    """Navbat interfeysi."""

    @abstractmethod
    def enqueue(self, submission: Submission) -> None:
        """Yechimni tekshiruvga qo'yadi."""

    @abstractmethod
    def claim_next(self) -> Submission | None:
        """Navbatdagi yechimni oladi va 'running' deb belgilaydi (boshqa worker olmasligi uchun)."""

    @abstractmethod
    def size(self) -> int:
        """Navbat uzunligi."""


class DatabaseQueue(JudgeQueue):
    """MySQL'dagi Submission.status maydoniga asoslangan oddiy navbat (SKIP LOCKED bilan)."""

    def enqueue(self, submission: Submission) -> None:
        if submission.status != Submission.Status.QUEUED:
            submission.status = Submission.Status.QUEUED
            submission.save(update_fields=["status"])

    def claim_next(self) -> Submission | None:
        with transaction.atomic():
            submission = (
                Submission.objects.select_for_update(skip_locked=True)
                .filter(status=Submission.Status.QUEUED)
                .order_by("created_at", "pk")
                .first()
            )
            if submission is None:
                return None
            submission.status = Submission.Status.RUNNING
            submission.judge_attempts += 1
            submission.save(update_fields=["status", "judge_attempts"])
            return submission

    def size(self) -> int:
        return Submission.objects.filter(status=Submission.Status.QUEUED).count()

    def requeue_stale(self, older_than: timedelta = timedelta(minutes=5)) -> int:
        """Worker to'xtab qolgan 'running' yechimlarni navbatga qaytaradi."""
        stale = Submission.objects.filter(status=Submission.Status.RUNNING,
                                          created_at__lt=timezone.now() - older_than)
        return stale.update(status=Submission.Status.QUEUED)


def get_queue() -> JudgeQueue:
    """Sozlamadagi (JUDGE_QUEUE) navbat klassi."""
    path = getattr(settings, "JUDGE_QUEUE", "submissions.queue.DatabaseQueue")
    return import_string(path)()
