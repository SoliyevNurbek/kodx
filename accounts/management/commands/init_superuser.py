"""
Boshlang'ich superuser (`nurbek`) ni tayyorlaydi.

Parol `secrets` bilan yaratiladi, faqat .env dagi SUPERUSER_INITIAL_PASSWORD
qatoriga yoziladi va ekranga chiqarilmaydi. Foydalanuvchi birinchi kirishda
parolni almashtirishga majbur (must_change_password=True).
"""

import secrets
import string

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from accounts.models import Role, User
from audit.services import log_action

ENV_KEY = "SUPERUSER_INITIAL_PASSWORD"


def generate_password(length: int = 20) -> str:
    """Katta/kichik harf va raqam qatnashgan tasodifiy parol."""
    alphabet = string.ascii_letters + string.digits + "-_!@#%"
    while True:
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        if (any(c.islower() for c in password) and any(c.isupper() for c in password)
                and any(c.isdigit() for c in password)):
            return password


class Command(BaseCommand):
    help = "nurbek superuserini yaratadi/yangilaydi; parol faqat .env ga yoziladi."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--username", default="nurbek")

    def handle(self, *args, username: str, **options) -> None:
        env_path = settings.BASE_DIR / ".env"
        if not env_path.exists():
            raise CommandError(".env topilmadi.")

        password = generate_password()
        user, created = User.objects.get_or_create(username=username)
        user.role = Role.SUPERADMIN
        user.is_superuser = True
        user.is_active = True
        user.must_change_password = True
        user.set_password(password)
        user.save()

        with env_path.open("a", encoding="utf-8") as fh:
            fh.write(
                "\n# Boshlang'ich superuser paroli — birinchi kirishdan keyin bu qatorni o'chiring\n"
                f"{ENV_KEY}={password}\n"
            )
        log_action(None, "superuser_initialized", user, {"created": created})
        state = "yaratildi" if created else "yangilandi"
        self.stdout.write(self.style.SUCCESS(
            f"'{username}' {state}. Parol .env dagi {ENV_KEY} qatorida (oxirgi qator)."
        ))
