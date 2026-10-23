"""User.is_seed: seed_demo akkauntlarini belgilash (mavjud demoNN akkauntlar ham belgilanadi)."""

from django.db import migrations, models


def mark_demo_users(apps, schema_editor) -> None:
    User = apps.get_model("accounts", "User")
    User.objects.filter(username__regex=r"^demo[0-9]+$").update(is_seed=True)


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_login_attempt"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="is_seed",
            field=models.BooleanField(
                db_index=True, default=False,
                help_text="seed_demo yaratgan akkaunt — bosh sahifa statistikasida hisobga olinmaydi.",
                verbose_name="demo/seed akkaunt",
            ),
        ),
        migrations.RunPython(mark_demo_users, migrations.RunPython.noop),
    ]
