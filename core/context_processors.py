"""Barcha shablonlarga sayt sozlamalarini uzatadi."""

from django.http import HttpRequest

from .models import SiteSettings


def site(request: HttpRequest) -> dict:
    return {"site": SiteSettings.load()}
