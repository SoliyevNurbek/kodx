"""Masala shartini Markdown → xavfsiz HTML ga aylantirish (LaTeX formulalari saqlanadi)."""

import html
import re

import markdown as md
import nh3

# $$...$$ va $...$ formulalari Markdown ishlovidan himoyalanadi va KaTeX (brauzerda) uchun qaytariladi.
MATH_RE = re.compile(r"(\$\$.+?\$\$|\$[^$\n]+?\$)", re.DOTALL)

ALLOWED_TAGS = {
    "p", "br", "hr", "h1", "h2", "h3", "h4", "h5", "h6", "strong", "em", "b", "i", "u", "s", "del",
    "code", "pre", "blockquote", "ul", "ol", "li", "table", "thead", "tbody", "tr", "th", "td",
    "a", "img", "span", "div", "sup", "sub",
}
ALLOWED_ATTRIBUTES = {
    "a": {"href", "title"},
    "img": {"src", "alt", "title"},
    "span": {"class"},
    "div": {"class"},
    "code": {"class"},
    "th": {"align"},
    "td": {"align"},
}


def render_markdown(text: str) -> str:
    """Markdown matnni sanitizatsiya qilingan HTML ga aylantiradi."""
    if not text:
        return ""
    formulas: list[str] = []

    def stash(match: re.Match) -> str:
        formulas.append(match.group(0))
        return f"KODXMATH{len(formulas) - 1}X"

    protected = MATH_RE.sub(stash, text)
    rendered = md.markdown(protected, extensions=["fenced_code", "tables", "sane_lists"])
    for index, formula in enumerate(formulas):
        rendered = rendered.replace(f"KODXMATH{index}X", f'<span class="math">{html.escape(formula)}</span>')
    return nh3.clean(rendered, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES,
                     url_schemes={"http", "https", "mailto"}, link_rel="noopener noreferrer")
