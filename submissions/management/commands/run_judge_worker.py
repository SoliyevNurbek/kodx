"""
`manage.py run_judge_worker` — navbatdagi yechimlarni tekshiruvchi worker.

Django veb-jarayonidan ALOHIDA ishga tushiriladi: foydalanuvchi kodi faqat shu yerda,
judge backend (dev: LocalDevBackend, prod: Judge0) orqali bajariladi.
"""

import time

from django.core.management.base import BaseCommand

from contests.services import apply_due_ratings
from judge.backends import get_backend
from submissions.queue import DatabaseQueue, get_queue
from submissions.services import judge_submission


class Command(BaseCommand):
    help = "Judge worker: navbatdagi yechimlarni tekshiradi (Ctrl+C — to'xtatish)."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--once", action="store_true", help="Navbat bo'shaguncha ishlab, chiqib ketish")
        parser.add_argument("--interval", type=float, default=1.0, help="Bo'sh navbatda kutish (sekund)")
        parser.add_argument("--max", type=int, default=0, help="Ko'pi bilan nechta yechim (0 — cheklovsiz)")

    def handle(self, *args, once: bool, interval: float, max: int, **options) -> None:
        queue = get_queue()
        backend = get_backend()
        if isinstance(queue, DatabaseQueue):
            requeued = queue.requeue_stale()
            if requeued:
                self.stdout.write(f"{requeued} ta to'xtab qolgan yechim navbatga qaytarildi.")
        self.stdout.write(self.style.SUCCESS(f"Worker ishga tushdi (backend: {backend.name})."))
        processed = 0
        idle_cycles = 0
        try:
            while not max or processed < max:
                submission = queue.claim_next()
                if submission is None:
                    # Bo'sh paytda: tugagan reytingli kontestlar reytingini hisoblash
                    if idle_cycles % 30 == 0:
                        rated = apply_due_ratings()
                        if rated:
                            self.stdout.write(f"{rated} ta kontest reytingi hisoblandi.")
                    idle_cycles += 1
                    if once:
                        break
                    time.sleep(interval)
                    continue
                idle_cycles = 0
                judge_submission(submission, backend)
                processed += 1
                self.stdout.write(f"#{submission.pk} {submission.problem.slug}: {submission.verdict} "
                                  f"({submission.score} ball, {submission.time_ms} ms)")
        except KeyboardInterrupt:
            self.stdout.write("To'xtatildi.")
        self.stdout.write(f"Jami tekshirildi: {processed}")
