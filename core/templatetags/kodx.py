"""Shablon yordamchilari."""

from django import template

register = template.Library()


@register.filter
def get_item(mapping, key):
    """{{ dict|get_item:key }}"""
    if mapping is None:
        return None
    return mapping.get(key)


@register.filter
def stars(difficulty: int) -> str:
    """Qiyinlik: ★★★☆☆"""
    difficulty = int(difficulty or 0)
    return "★" * difficulty + "☆" * (5 - difficulty)


@register.simple_tag(takes_context=True)
def query_replace(context, **kwargs) -> str:
    """Joriy GET parametrlarini saqlagan holda bittasini almashtiradi (sahifalash uchun)."""
    params = context["request"].GET.copy()
    for key, value in kwargs.items():
        params[key] = value
    return params.urlencode()
