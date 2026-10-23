"""`manage.py check_similarity` — bir masaladagi yechimlar o'xshashligini tekshirish (ko'chirmachilik)."""

from django.core.management.base import BaseCommand, CommandError

from contests.models import Contest
from problems.models import Problem
from submissions.similarity import check_problem


class Command(BaseCommand):
    help = "Qabul qilingan yechimlarni juftma-juft solishtiradi; natijalar faqat moderator panelida ko'rinadi."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--problem", action="append", help="Masala slug (bir necha marta berish mumkin)")
        parser.add_argument("--contest", help="Kontest slug — faqat shu kontest yechimlari, barcha masalalari")
        parser.add_argument("--threshold", type=float, default=0.85, help="O'xshashlik chegarasi (0–1)")

    def handle(self, *args, problem, contest, threshold, **options) -> None:
        if not 0 < threshold <= 1:
            raise CommandError("--threshold 0 va 1 oralig'ida bo'lishi kerak.")
        contest_obj = None
        if contest:
            contest_obj = Contest.objects.filter(slug=contest).first()
            if contest_obj is None:
                raise CommandError(f"Kontest topilmadi: {contest}")
            problems = Problem.objects.filter(contest_links__contest=contest_obj)
        else:
            problems = Problem.objects.filter(type=Problem.Type.CODE, submissions__isnull=False).distinct()
        if problem:
            problems = problems.filter(slug__in=problem)
        total = 0
        for item in problems:
            matches = check_problem(item, threshold, contest_obj)
            total += len(matches)
            if matches:
                self.stdout.write(f"{item.slug}: {len(matches)} ta o'xshash juftlik")
        self.stdout.write(self.style.SUCCESS(f"Tekshirildi: {problems.count()} masala, {total} ta shubhali juftlik."))
