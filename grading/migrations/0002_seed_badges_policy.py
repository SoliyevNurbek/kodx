"""Seed: nishonlar va seed kurs uchun standart baholash siyosati."""

from django.db import migrations

from grading.practice import BADGES


def seed(apps, schema_editor):
    Badge = apps.get_model("grading", "Badge")
    GradingPolicy = apps.get_model("grading", "GradingPolicy")
    Course = apps.get_model("courses", "Course")
    for order, (code, name, description, icon) in enumerate(BADGES, start=1):
        Badge.objects.update_or_create(code=code, defaults={
            "name": name, "description": description, "icon": icon, "order": order})
    for course in Course.objects.all():
        GradingPolicy.objects.get_or_create(course=course)


class Migration(migrations.Migration):
    dependencies = [
        ("grading", "0001_initial"),
        ("courses", "0002_seed_course"),
    ]

    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
