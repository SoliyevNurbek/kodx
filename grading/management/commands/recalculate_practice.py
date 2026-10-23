"""`manage.py recalculate_practice` — barcha foydalanuvchilar mashq statistikasi va nishonlarini qayta hisoblash."""

from django.core.management.base import BaseCommand

from accounts.models import User
from grading.practice import refresh_practice_stats


class Command(BaseCommand):
    help = "Mashq bali, seriya va nishonlarni barcha foydalanuvchilar uchun qayta hisoblaydi."

    def handle(self, *args, **options) -> None:
        count = 0
        for user in User.objects.filter(is_active=True).iterator():
            refresh_practice_stats(user)
            count += 1
        self.stdout.write(self.style.SUCCESS(f"{count} ta foydalanuvchi yangilandi."))
