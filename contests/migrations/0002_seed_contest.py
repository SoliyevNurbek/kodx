"""Seed: namunaviy «Kirish kontesti» (ICPC, ochiq, reytingsiz)."""

from datetime import datetime
from zoneinfo import ZoneInfo

from django.db import migrations

PROBLEMS = [("A", "l06-vaqt-formati"), ("B", "l08-baho"), ("C", "l10-tub-sonlar"), ("D", "l11-kollats")]


def seed(apps, schema_editor):
    Contest = apps.get_model("contests", "Contest")
    ContestProblem = apps.get_model("contests", "ContestProblem")
    Problem = apps.get_model("problems", "Problem")
    owner = apps.get_model("accounts", "User").objects.get(username="nurbek")
    contest, _ = Contest.objects.get_or_create(slug="kirish-kontesti", defaults={
        "title": "Kirish kontesti",
        "description": "Modul 1 mavzulari bo‘yicha birinchi mashq kontesti: vaqt formati, if, for va while.",
        "owner": owner,
        "start_at": datetime(2026, 11, 1, 10, 0, tzinfo=ZoneInfo("Asia/Tashkent")),
        "duration_minutes": 120,
        "scoring": "icpc",
        "freeze_minutes": 30,
        "visibility": "public",
        "is_rated": False,
    })
    for label, slug in PROBLEMS:
        problem = Problem.objects.filter(slug=slug).first()
        if problem:
            ContestProblem.objects.get_or_create(contest=contest, label=label, defaults={"problem": problem})


class Migration(migrations.Migration):
    dependencies = [
        ("contests", "0001_initial"),
        ("problems", "0002_seed_problems"),
    ]

    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
