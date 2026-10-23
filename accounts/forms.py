"""Foydalanuvchi formalari."""

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

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


class KodxAuthenticationForm(AuthenticationForm):
    """Kirish formasi: 15 daqiqada 5 ta muvaffaqiyatsiz urinishdan keyin vaqtincha bloklaydi."""

    error_messages = {
        **AuthenticationForm.error_messages,
        "locked": ("Juda ko‘p noto‘g‘ri urinish. 15 daqiqadan keyin qayta urinib ko‘ring "
                   "yoki o‘qituvchingizga murojaat qiling."),
    }

    def clean(self):
        from .services import is_locked_out, record_login_attempt

        username = (self.cleaned_data.get("username") or "").strip()
        if username and is_locked_out(username):
            raise forms.ValidationError(self.error_messages["locked"], code="locked")
        try:
            data = super().clean()
        except forms.ValidationError:
            if username:
                record_login_attempt(username, self.request, success=False)
            raise
        record_login_attempt(username, self.request, success=True)
        return data


class RoleRequestForm(forms.Form):
    requested_role = forms.TypedChoiceField(label="So‘ralayotgan rol", coerce=int)
    reason = forms.CharField(label="Nega bu rol kerak?", widget=forms.Textarea(attrs={"rows": 4}), max_length=1000,
                             help_text="Masalan: maktabda to‘garak olib boraman va kontest o‘tkazmoqchiman.")

    def __init__(self, *args, choices=(), **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["requested_role"].choices = list(choices)
        for field in self.fields.values():
            field.widget.attrs.update(INPUT)


class OTPTokenForm(forms.Form):
    token = forms.RegexField(label="6 xonali kod", regex=r"^\d{6}$", max_length=6,
                             widget=forms.TextInput(attrs={"autocomplete": "one-time-code", "inputmode": "numeric",
                                                           "class": "form-input"}))
