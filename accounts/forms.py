"""Foydalanuvchi formalari."""

from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User

INPUT = {"class": "form-input"}


class RegistrationForm(UserCreationForm):
    """Ro'yxatdan o'tish. Telefon so'ralmaydi, email ixtiyoriy (bolalar xavfsizligi)."""

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email")
        help_texts = {"email": "Ixtiyoriy — faqat parolni tiklash uchun. Hech kimga ko‘rinmaydi."}

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update(INPUT)
        self.fields["email"].required = False

    def clean_email(self) -> str | None:
        email = self.cleaned_data.get("email") or None
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Bu email allaqachon ishlatilgan.")
        return email


class ProfileForm(forms.ModelForm):
    """O'z profilini tahrirlash."""

    class Meta:
        model = User
        fields = ("first_name", "last_name", "bio", "avatar", "email")
        widgets = {"bio": forms.Textarea(attrs={"rows": 4})}
        help_texts = {"email": "Ixtiyoriy. Boshqalarga ko‘rinmaydi."}

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != "avatar":
                field.widget.attrs.update(INPUT)

    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar")
        if avatar and hasattr(avatar, "size") and avatar.size > 2 * 1024 * 1024:
            raise forms.ValidationError("Avatar hajmi 2 MB dan oshmasligi kerak.")
        return avatar

    def clean_email(self) -> str | None:
        email = self.cleaned_data.get("email") or None
        if email and User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Bu email allaqachon ishlatilgan.")
        return email
