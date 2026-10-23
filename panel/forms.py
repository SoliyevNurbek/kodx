"""Panel formalari: vazifa, test yuklash, loyiha baholash, tizim sozlamalari."""

from pathlib import Path

from django import forms

from contests.models import Contest
from core.models import SiteSettings
from problems.models import Problem

INPUT = {"class": "form-input"}
TEST_EXTENSIONS = {".in", ".out", ".txt"}
MAX_TEST_FILE_BYTES = 5 * 1024 * 1024


def _style(form: forms.Form) -> None:
    for field in form.fields.values():
        if not isinstance(field.widget, forms.CheckboxInput | forms.CheckboxSelectMultiple | forms.FileInput):
            field.widget.attrs.setdefault("class", "form-input")


class ProblemForm(forms.ModelForm):
    """Jury Pro uchun vazifa formasi (holat va muallif bu yerda o'zgarmaydi)."""

    class Meta:
        model = Problem
        fields = ("title", "slug", "type", "difficulty", "points", "tags", "statement", "input_format",
                  "output_format", "notes", "time_limit", "memory_limit", "checker", "float_epsilon",
                  "reference_solution")
        widgets = {
            "statement": forms.Textarea(attrs={"rows": 10}),
            "input_format": forms.Textarea(attrs={"rows": 2}),
            "output_format": forms.Textarea(attrs={"rows": 2}),
            "notes": forms.Textarea(attrs={"rows": 2}),
            "reference_solution": forms.Textarea(attrs={"rows": 10, "class": "form-input font-mono"}),
            "tags": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["slug"].disabled = True  # test fayllari yo'li slug'ga bog'liq
        _style(self)


def validate_test_file(upload) -> None:
    """Faqat .in/.out/.txt, ≤ 5 MB, UTF-8 matn."""
    if Path(upload.name).suffix.lower() not in TEST_EXTENSIONS:
        raise forms.ValidationError("Faqat .in, .out yoki .txt fayllar.")
    if upload.size > MAX_TEST_FILE_BYTES:
        raise forms.ValidationError("Fayl hajmi 5 MB dan oshmasligi kerak.")
    head = upload.read(MAX_TEST_FILE_BYTES + 1)
    upload.seek(0)
    try:
        head.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise forms.ValidationError("Fayl UTF-8 matn bo‘lishi kerak.") from exc


class TestUploadForm(forms.Form):
    input_file = forms.FileField(label="Kirish fayli (.in)", validators=[validate_test_file])
    output_file = forms.FileField(label="Chiqish fayli (.out)", validators=[validate_test_file])
    is_sample = forms.BooleanField(label="Namuna (ochiq test)", required=False)
    points = forms.IntegerField(label="Ball", min_value=0, max_value=1000, initial=1)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        _style(self)


class GradeForm(forms.Form):
    """Rubrika bo'yicha baholash: har mezon uchun alohida maydon."""

    feedback = forms.CharField(label="Izoh", widget=forms.Textarea(attrs={"rows": 4}), required=False)
    needs_revision = forms.BooleanField(label="Qayta ishlashga qaytarish", required=False)

    def __init__(self, *args, rubric=(), **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.rubric = list(rubric)
        for criterion in self.rubric:
            self.fields[f"c{criterion.order}"] = forms.IntegerField(
                label=f"{criterion.title} (0–{criterion.max_points})", min_value=0,
                max_value=criterion.max_points, initial=0, help_text=criterion.description)
        _style(self)

    def scores(self) -> dict[str, int]:
        return {str(c.order): self.cleaned_data[f"c{c.order}"] for c in self.rubric}


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = ("site_name", "tagline", "color_background", "color_accent", "color_gold", "registration_enabled")
        widgets = {
            "color_background": forms.TextInput(attrs={"type": "color"}),
            "color_accent": forms.TextInput(attrs={"type": "color"}),
            "color_gold": forms.TextInput(attrs={"type": "color"}),
        }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        _style(self)


class ContestForm(forms.ModelForm):
    """Kontest formasi. Parol ochiq ko'rinishda saqlanmaydi — faqat xesh."""

    password = forms.CharField(label="Kontest paroli", required=False, widget=forms.PasswordInput(render_value=False),
                               help_text="Faqat «Parol bilan» ko‘rinishda. Bo‘sh qoldirilsa — eski parol saqlanadi.")

    class Meta:
        model = Contest
        fields = ("title", "slug", "description", "start_at", "duration_minutes", "scoring", "penalty_minutes",
                  "freeze_minutes", "visibility", "group", "is_rated")
        widgets = {
            "start_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, user=None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["start_at"].input_formats = ["%Y-%m-%dT%H:%M"]
        if self.instance.pk:
            self.fields["slug"].disabled = True
        if user is not None and not user.is_moderator:
            # Reytingga ta'sir qiluvchi kontestni faqat moderator belgilaydi
            self.fields["is_rated"].disabled = True
        _style(self)

    def clean(self):
        data = super().clean()
        if data.get("visibility") == Contest.Visibility.PASSWORD and not data.get("password") \
                and not self.instance.password_hash:
            self.add_error("password", "Parolli kontest uchun parol kiriting.")
        return data

    def save(self, commit: bool = True):
        contest = super().save(commit=False)
        if self.cleaned_data.get("password"):
            contest.set_password(self.cleaned_data["password"])
        if contest.visibility != Contest.Visibility.PASSWORD:
            contest.password_hash = ""
        if commit:
            contest.save()
        return contest


class ContestProblemForm(forms.Form):
    slug = forms.SlugField(label="Masala slug")
    label = forms.CharField(label="Harf", max_length=3)
    points = forms.IntegerField(label="Ball (IOI)", min_value=1, max_value=10000, initial=100)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        _style(self)
