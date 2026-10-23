"""`manage.py import_problems <papka>` — masalalarni papkadan import qilish (docs/PROBLEM_FORMAT.md)."""

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts.models import User
from audit.services import log_action
from problems.importer import ProblemFormatError, import_directory
from problems.models import Problem


class Command(BaseCommand):
    help = "Masalalarni papkadan import qiladi (problem.yaml, statement.md, tests/*.in|*.out)."

    def add_arguments(self, parser) -> None:
        parser.add_argument("path", help="Masala papkasi yoki masala papkalari to'plami")
        parser.add_argument("--author", default="nurbek", help="Muallif username (standart: nurbek)")
        parser.add_argument("--status", default=Problem.Status.DRAFT, choices=Problem.Status.values)

    def handle(self, *args, path: str, author: str, status: str, **options) -> None:
        root = Path(path)
        if not root.is_dir():
            raise CommandError(f"Papka topilmadi: {root}")
        try:
            author_user = User.objects.get(username=author)
        except User.DoesNotExist as exc:
            raise CommandError(f"Foydalanuvchi topilmadi: {author}") from exc
        if not author_user.is_jury_pro:
            raise CommandError("Muallif kamida Jury Pro bo'lishi kerak.")
        try:
            with transaction.atomic():
                results = import_directory(root, author_user, status=status)
        except (ProblemFormatError, KeyError, ValueError) as exc:
            raise CommandError(f"Import xatosi: {exc}") from exc

        for problem, created in results:
            mark = "+" if created else "~"
            self.stdout.write(f"  {mark} {problem.slug} ({problem.get_type_display()})")
        log_action(author_user, "problems_imported", details={
            "path": str(root), "count": len(results), "slugs": [p.slug for p, _ in results][:50],
        })
        self.stdout.write(self.style.SUCCESS(f"{len(results)} ta vazifa import qilindi."))
