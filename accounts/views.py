"""Ro'yxatdan o'tish, profil, parol, rol so'rovi va ikki bosqichli himoya sahifalari."""

import base64

import qrcode
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.core.exceptions import ValidationError
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django_otp import login as otp_login
from django_otp import match_token
from django_otp.plugins.otp_totp.models import TOTPDevice
from qrcode.image.svg import SvgPathImage

from audit.services import log_action
from core.models import SiteSettings
from submissions.stats import activity_calendar, solved_ids

from .forms import OTPTokenForm, ProfileForm, RegistrationForm, RoleRequestForm
from .models import RoleRequest, User
from .services import create_role_request, record_login_attempt, requestable_roles


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
        "rating_history": list(person.rating_history.select_related("contest").order_by("created_at")),
    }
    context["rating_points"] = _rating_polyline(context["rating_history"])
    return render(request, "accounts/profile.html", context)


def _rating_polyline(history: list, width: int = 300, height: int = 100) -> str:
    """Reyting tarixi uchun SVG polyline nuqtalari (boshlang'ich reyting + har kontestdan keyingi)."""
    if not history:
        return ""
    values = [history[0].old_rating] + [h.new_rating for h in history]
    low, high = min(values), max(values)
    span = max(high - low, 1)
    step = width / (len(values) - 1)
    return " ".join(f"{i * step:.1f},{height - 5 - (v - low) / span * (height - 10):.1f}"
                    for i, v in enumerate(values))


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


@login_required
def role_request(request: HttpRequest) -> HttpResponse:
    """O'quvchi Jury / Jury Pro rolini so'raydi; moderator panelda tasdiqlaydi."""
    choices = requestable_roles(request.user)
    form = RoleRequestForm(request.POST or None, choices=choices)
    if request.method == "POST" and form.is_valid():
        try:
            create_role_request(request.user, form.cleaned_data["requested_role"], form.cleaned_data["reason"])
        except ValidationError as exc:
            messages.error(request, "; ".join(exc.messages))
        else:
            messages.success(request, "So‘rov yuborildi. Moderator ko‘rib chiqqach, natija shu yerda ko‘rinadi.")
            return redirect("role_request")
    history = request.user.role_requests.select_related("reviewed_by")[:10]
    pending = any(r.status == RoleRequest.Status.PENDING for r in history)
    return render(request, "accounts/role_request.html",
                  {"form": form, "history": history, "pending": pending, "can_request": bool(choices)})


def _otp_redirect_target(request: HttpRequest) -> str:
    target = request.POST.get("next") or request.GET.get("next") or ""
    return target if url_has_allowed_host_and_scheme(target, {request.get_host()}) and target else "/panel/"


@login_required
def two_factor_setup(request: HttpRequest) -> HttpResponse:
    """TOTP qurilmasini ulash: QR-kodni ilovada skanerlab, 6 xonali kodni tasdiqlash."""
    if TOTPDevice.objects.filter(user=request.user, confirmed=True).exists():
        return redirect(f"{reverse('two_factor_verify')}?next={_otp_redirect_target(request)}")
    device, _ = TOTPDevice.objects.get_or_create(user=request.user, confirmed=False, defaults={"name": "kodx"})
    form = OTPTokenForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if device.verify_token(form.cleaned_data["token"]):
            device.confirmed = True
            device.save(update_fields=["confirmed"])
            otp_login(request, device)
            log_action(request.user, "two_factor_enabled", request.user, request=request)
            messages.success(request, "Ikki bosqichli himoya yoqildi.")
            return redirect(_otp_redirect_target(request))
        form.add_error("token", "Kod noto‘g‘ri yoki eskirgan.")
    qr_svg = qrcode.make(device.config_url, image_factory=SvgPathImage).to_string(encoding="unicode")
    secret = base64.b32encode(device.bin_key).decode("ascii")
    return render(request, "accounts/two_factor_setup.html",
                  {"form": form, "qr_svg": qr_svg, "secret": secret, "next": _otp_redirect_target(request)})


@login_required
def two_factor_verify(request: HttpRequest) -> HttpResponse:
    """Sessiya uchun TOTP kodini tasdiqlash."""
    form = OTPTokenForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        device = match_token(request.user, form.cleaned_data["token"])
        if device is not None:
            otp_login(request, device)
            return redirect(_otp_redirect_target(request))
        record_login_attempt(request.user.username, request, success=False)
        form.add_error("token", "Kod noto‘g‘ri yoki eskirgan.")
    return render(request, "accounts/two_factor_verify.html", {"form": form, "next": _otp_redirect_target(request)})
