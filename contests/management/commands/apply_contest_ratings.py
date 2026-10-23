"""`manage.py apply_contest_ratings` — tugagan reytingli kontestlar reytingini hisoblash (cron uchun)."""

from django.core.management.base import BaseCommand

from contests.services import apply_due_ratings


class Command(BaseCommand):
    help = "Tugagan, reytingli kontestlar uchun reytinglarni yangilaydi (judge worker ham buni bajaradi)."

    def handle(self, *args, **options) -> None:
        self.stdout.write(self.style.SUCCESS(f"{apply_due_ratings()} ta kontest reytingi hisoblandi."))
