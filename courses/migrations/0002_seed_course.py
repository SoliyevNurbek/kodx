"""Seed: 1 kurs, 4 modul, 48 dars va «Python-1» namunaviy guruhi (dublikatsiz)."""

from django.contrib.auth.hashers import make_password
from django.db import migrations

from courses import seed_data


def get_seed_teacher(apps):
    """`nurbek` ni topadi yoki ishlatib bo'lmaydigan parol bilan yaratadi."""
    User = apps.get_model("accounts", "User")
    user, created = User.objects.get_or_create(
        username=seed_data.SAMPLE_GROUP["teacher_username"],
        defaults={
            "password": make_password(None),  # kirib bo'lmaydi; `changepassword` yoki init_superuser
            "role": 5,
            "is_staff": True,
            "is_superuser": True,
        },
    )
    return user


def seed(apps, schema_editor):
    Course = apps.get_model("courses", "Course")
    Module = apps.get_model("courses", "Module")
    Lesson = apps.get_model("courses", "Lesson")
    Group = apps.get_model("courses", "Group")

    course, _ = Course.objects.update_or_create(
        slug=seed_data.COURSE["slug"],
        defaults={"title": seed_data.COURSE["title"], "description": seed_data.COURSE["description"]},
    )
    for number, title, lessons in seed_data.MODULES:
        module, _ = Module.objects.update_or_create(course=course, number=number, defaults={"title": title})
        for lesson_number, lesson_title in lessons:
            Lesson.objects.update_or_create(
                module=module,
                number=lesson_number,
                defaults={"title": lesson_title, "kind": seed_data.lesson_kind(lesson_number)},
            )

    Group.objects.get_or_create(
        course=course,
        name=seed_data.SAMPLE_GROUP["name"],
        defaults={"teacher": get_seed_teacher(apps)},
    )


class Migration(migrations.Migration):
    dependencies = [
        ("courses", "0001_initial"),
        ("accounts", "0001_initial"),
    ]

    # Teskari yo'nalishda ma'lumot o'chirilmaydi (ma'lumot yo'qotmaslik uchun)
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
