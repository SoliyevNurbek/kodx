"""Seed: problems/seed/ dagi barcha vazifalar (nashr etilgan, muallif nurbek, is_seed=True)."""

from pathlib import Path
from types import SimpleNamespace

from django.db import migrations

SEED_DIR = Path(__file__).resolve().parent.parent / "seed"


def seed(apps, schema_editor):
    from problems.importer import import_directory

    models = SimpleNamespace(
        Problem=apps.get_model("problems", "Problem"),
        Tag=apps.get_model("problems", "Tag"),
        TestCase=apps.get_model("problems", "TestCase"),
        QuizQuestion=apps.get_model("problems", "QuizQuestion"),
        QuizOption=apps.get_model("problems", "QuizOption"),
        RubricCriterion=apps.get_model("problems", "RubricCriterion"),
        LessonProblem=apps.get_model("problems", "LessonProblem"),
        Lesson=apps.get_model("courses", "Lesson"),
    )
    author = apps.get_model("accounts", "User").objects.get(username="nurbek")
    import_directory(SEED_DIR, author, models=models, status="published", is_seed=True)


class Migration(migrations.Migration):
    dependencies = [
        ("problems", "0001_initial"),
        ("courses", "0002_seed_course"),
    ]

    # Teskari yo'nalishda ma'lumot o'chirilmaydi
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
