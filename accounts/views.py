"""Ro'yxatdan o'tish, profil va parol sahifalari."""

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy

from audit.services import log_action
from core.models import SiteSettings
from submissions.stats import activity_calendar, solved_ids

from .forms import ProfileForm, RegistrationForm
from .models import User


def register(request: HttpRequest) -> HttpResponse:
    """Ro'yxatdan o'tish (super admin o'chirib qo'yishi mumkin)."""
    if not SiteSettings.load().registration_enabled:
        return render(request, "accounts/register_closed.html", status=403)
    if request.user.is_authenticated:
        return redirect("home")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        log_action(user, "user_registered", user, request=request)
        login(request, user)
        messages.success(request, "Xush kelibsiz! Birinchi masalani yechib ko‘ring.")
        return redirect("home")
    return render(request, "accounts/register.html", {"form": form})


def profile(request: HttpRequest, username: str) -> HttpResponse:
    """
    Ochiq profil: username, avatar, reyting, yechilganlar, faollik, nishonlar.
    Shaxsiy kontaktlar (email) faqat egasiga ko'rinadi.
    """
    person = get_object_or_404(User, username=username)
    if not person.is_active:
        raise Http404
    context = {
        "person": person,
        "is_owner": request.user.is_authenticated and request.user.pk == person.pk,
        "solved_count": len(solved_ids(person)),
        "calendar": activity_calendar(person),
        "badges": list(person.badges.select_related("badge")),
        "practice": getattr(person, "practice", None),
        "rating_history": list(person.rating_history.select_related("contest").order_by("created_at"))
        if hasattr(person, "rating_history") else [],
    }
    return render(request, "accounts/profile.html", context)


@login_required
def profile_edit(request: HttpRequest) -> HttpResponse:
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profil saqlandi.")
        return redirect("profile", request.user.username)
    return render(request, "accounts/profile_edit.html", {"form": form})


class KodxPasswordChangeView(PasswordChangeView):
    """Parolni almashtirish; majburiy almashtirish belgisini olib tashlaydi."""

    template_name = "registration/password_change_form.html"
    success_url = reverse_lazy("password_change_done")

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.request.user
        if user.must_change_password:
            user.must_change_password = False
            user.save(update_fields=["must_change_password"])
        log_action(user, "password_changed", user, request=self.request)
        return response
