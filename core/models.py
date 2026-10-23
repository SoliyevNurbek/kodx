"""Tizim sozlamalari (super admin boshqaradi)."""

from django.core.validators import RegexValidator
from django.db import models

HEX_COLOR = RegexValidator(r"^#[0-9A-Fa-f]{6}$", "Rang #RRGGBB ko‘rinishida bo‘lishi kerak.")


class SiteSettings(models.Model):
    """Yagona yozuvli (singleton) sayt sozlamalari."""

    site_name = models.CharField("sayt nomi", max_length=100, default="kodx.uz")
    tagline = models.CharField("shior", max_length=200, default="Dasturlash va sun’iy intellekt asoslari")
    color_background = models.CharField("fon rangi", max_length=7, default="#0E1A2E", validators=[HEX_COLOR])
    color_accent = models.CharField("aksent rang", max_length=7, default="#22D3EE", validators=[HEX_COLOR])
    color_gold = models.CharField("oltin rang", max_length=7, default="#D9B25F", validators=[HEX_COLOR])
    registration_enabled = models.BooleanField("ro‘yxatdan o‘tish yoqilgan", default=True)
    hero_author_label = models.CharField("hero: karta sarlavhasi", max_length=60, default="Kurs muallifi:")
    hero_author_name = models.CharField("hero: muallif ismi", max_length=100, default="Nurbek Soliyev")
    hero_author_title = models.CharField("hero: muallif lavozimi", max_length=150,
                                         default="AI (ML, CV, LLM) va Full-Stack dasturchi")
    updated_at = models.DateTimeField("yangilangan", auto_now=True)

    class Meta:
        verbose_name = "sayt sozlamalari"
        verbose_name_plural = "sayt sozlamalari"

    def __str__(self) -> str:
        return self.site_name

    def save(self, *args, **kwargs) -> None:
        self.pk = 1  # doim bitta yozuv
        super().save(*args, **kwargs)

    @classmethod
    def load(cls) -> "SiteSettings":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
