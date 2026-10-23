"""Kontestlar sahifalari (to'liq funksionallik — 7-bosqich)."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def contest_list(request: HttpRequest) -> HttpResponse:
    return render(request, "contests/contest_list.html", {"contests": []})
