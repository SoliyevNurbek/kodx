"""Kontest reytingi boshlang'ich qiymati 1200 (MASTER_PROMPT, 6-bosqich)."""

from django.db import migrations, models


def set_initial_rating(apps, schema_editor):
    # Hali hech qanday kontest o'tkazilmagan — 0 reytingli barcha foydalanuvchilar 1200 oladi
    apps.get_model("accounts", "User").objects.filter(rating=0).update(rating=1200)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="rating",
            field=models.IntegerField(default=1200, verbose_name="kontest reytingi"),
        ),
        migrations.RunPython(set_initial_rating, migrations.RunPython.noop),
    ]
