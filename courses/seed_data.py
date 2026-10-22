"""
Kurs tuzilmasining seed ma'lumoti (CLAUDE.md dan).

Faqat oddiy Python ma'lumotlari — data migratsiyalardan xavfsiz import qilinadi.
"""

COURSE = {
    "slug": "dasturlash-va-ai-asoslari",
    "title": "Dasturlash va sun'iy intellekt asoslari",
    "description": "Kompyuter, Git va Python asoslaridan web, AI, API va Telegram botgacha — 48 dars.",
}

# (modul raqami, modul nomi, [(dars raqami, dars nomi), ...])
MODULES: list[tuple[int, str, list[tuple[int, str]]]] = [
    (1, "Kompyuter, Git va Python asoslari", [
        (1, "Kompyuter va ish muhiti"),
        (2, "Terminal (CLI)"),
        (3, "Git asoslari"),
        (4, "GitHub"),
        (5, "Python: birinchi qadamlar"),
        (6, "Arifmetika, satrlar, f-string"),
        (7, "Mantiqiy ifodalar"),
        (8, "Shartli operatorlar (if)"),
        (9, "match-case"),
        (10, "for tsikli"),
        (11, "while tsikli"),
        (12, "Loyiha 1 himoyasi"),
    ]),
    (2, "Ma'lumot tuzilmalari, funksiyalar, OOP", [
        (13, "Ro'yxatlar (list)"),
        (14, "Qidirish, saralash, comprehension"),
        (15, "tuple, set, dict"),
        (16, "Satrlar chuqur"),
        (17, "Funksiyalar"),
        (18, "Fayllar: txt, csv, json"),
        (19, "Xatolarni boshqarish"),
        (20, "Modullar, paketlar, pip"),
        (21, "OOP: klass va obyekt"),
        (22, "Meros va inkapsulyatsiya"),
        (23, "Kod sifati, branch va PR"),
        (24, "Loyiha 2 himoyasi"),
    ]),
    (3, "Web: HTML, CSS, JavaScript", [
        (25, "Web va HTML5"),
        (26, "HTML: forma va semantika"),
        (27, "CSS3 asoslari"),
        (28, "display, position, CSS o'zgaruvchilar"),
        (29, "Flexbox"),
        (30, "CSS Grid"),
        (31, "Responsiv dizayn"),
        (32, "JavaScript: DOM va hodisalar"),
        (33, "Interaktiv komponentlar"),
        (34, "Portfolio loyihalash"),
        (35, "SEO, tezlik va Lighthouse"),
        (36, "GitHub Pages va Loyiha 3 himoyasi"),
    ]),
    (4, "AI, API va Telegram bot", [
        (37, "AI, ML va LLM"),
        (38, "Prompt engineering"),
        (39, "AI bilan kodlash va xavfsizlik"),
        (40, "HTTP va REST API"),
        (41, "LLM API"),
        (42, "Asinxron dasturlash"),
        (43, "Telegram bot: aiogram"),
        (44, "Inline tugmalar, FSM, SQLite"),
        (45, "Botga AI integratsiyasi"),
        (46, "Sinov va serverga joylash"),
        (47, "README, taqdimot, GitHub va CV"),
        (48, "Demo Day"),
    ]),
]

PROJECT_DEFENSE_LESSONS = {12, 24, 36}
DEMO_DAY_LESSONS = {48}

SAMPLE_GROUP = {"name": "Python-1", "teacher_username": "nurbek"}


def lesson_kind(number: int) -> str:
    """Dars raqamiga qarab turini qaytaradi (Lesson.Kind qiymatlari)."""
    if number in DEMO_DAY_LESSONS:
        return "demo_day"
    if number in PROJECT_DEFENSE_LESSONS:
        return "project_defense"
    return "lesson"
