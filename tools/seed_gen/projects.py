"""Loyiha topshiriqlari (GitHub havolasi + rubrika): 12, 24 va 25–48-darslar."""
from common import project_problem

SAFETY = ("\n\n> **Xavfsizlik:** loyihada shaxsiy ma’lumotlar (uy manzili, telefon raqami, parollar, "
          "API kalitlar) bo‘lmasin. Maxfiy kalitlar faqat `.env` da, u esa `.gitignore` da.\n")
SUBMIT = ("\n\n## Topshirish\nGitHub repozitoriy havolasini yuboring "
          "(`https://github.com/<foydalanuvchi>/<repo>`). Repozitoriyda `README.md` bo‘lsin.")

# (dars, slug, nomi, vazifa matni, [talablar], [(mezon, ball, tavsif), ...] — oxirgi umumiy mezonlar qo'shiladi)
PROJECTS = [
    (12, "l12-loyiha-1", "Loyiha 1: konsol o‘yini", "Python’da konsol o‘yini yozing: «Sonni top», «Tosh-qaychi-qog‘oz» "
     "yoki «Viktorina» (tanlov sizda).",
     ["`if`, `for`/`while` va `match-case` ishlatilgan", "Foydalanuvchi noto‘g‘ri kiritishi to‘g‘ri qayta ishlanadi",
      "O‘yin tugagach natija (ball) ko‘rsatiladi", "Kod GitHub’da, kamida 5 ta ma’noli commit"],
     [("O‘yin to‘liq ishlaydi", 30, "Barcha qoidalar bajariladi, dastur xatosiz tugaydi"),
      ("Shartlar va tsikllar", 20, "if/elif, for/while, match-case o‘rinli ishlatilgan"),
      ("Kiritishni tekshirish", 15, "Noto‘g‘ri qiymatda dastur to‘xtab qolmaydi")]),
    (24, "l24-loyiha-2", "Loyiha 2: ma’lumotlar bilan ishlovchi dastur", "Konsol ilovasi yozing: «Kundalik vazifalar», "
     "«Shaxsiy kutubxona» yoki «Baholar jurnali». Ma’lumotlar JSON faylda saqlanadi.",
     ["Kamida 2 ta klass (OOP), meros yoki inkapsulyatsiya bilan", "Funksiyalar va modullarga bo‘lingan kod",
      "Ma’lumot JSON faylda saqlanadi va qayta yuklanadi", "Xatolar `try/except` bilan boshqariladi",
      "Ish alohida branch’da, main’ga PR orqali birlashtirilgan"],
     [("Funksionallik", 25, "Qo‘shish, ko‘rish, o‘chirish, saqlash ishlaydi"),
      ("OOP va tuzilma", 20, "Klasslar, meros/inkapsulyatsiya, modullar"),
      ("Fayllar va xatolar", 20, "JSON saqlash, try/except, utf-8")]),
    (25, "l25-vizitka", "Shaxsiy vizitka sahifasi", "Faqat HTML5 da o‘zingiz (yoki o‘ylab topilgan qahramon) "
     "haqida vizitka sahifa yarating.",
     ["To‘g‘ri HTML5 skeleti (`<!DOCTYPE html>`, `lang`, `meta charset`)", "Sarlavhalar, paragraflar, ro‘yxat, havola, rasm",
      "Rasmlarda `alt` atributi"],
     [("HTML tuzilmasi", 35, "To‘g‘ri skelet va teglar ierarxiyasi"),
      ("Kontent elementlari", 20, "Sarlavha, ro‘yxat, havola, rasm"),
      ("Validatsiya", 10, "validator.w3.org da xatosiz")]),
    (26, "l26-royxatdan-otish-formasi", "Ro‘yxatdan o‘tish formasi", "Kurs uchun ro‘yxatdan o‘tish formasini semantik "
     "HTML bilan yarating (ma’lumot hech qayerga yuborilmaydi).",
     ["`<header>`, `<main>`, `<footer>` semantik teglar", "Kamida 5 xil maydon (`text`, `email`, `select`, `radio`, `checkbox`)",
      "Har bir maydonda `<label for>`", "`required`, `minlength` kabi validatsiya atributlari"],
     [("Forma maydonlari", 30, "Turli input turlari to‘g‘ri ishlatilgan"),
      ("Semantika va qulaylik", 25, "Semantik teglar, label, fieldset"),
      ("Brauzer validatsiyasi", 10, "Majburiy maydonlar va formatlar tekshiriladi")]),
    (27, "l27-retsept-sahifasi", "Retsept sahifasi (CSS)", "Sevimli taomingiz retseptini HTML va alohida CSS fayl "
     "bilan bezang.",
     ["Tashqi `style.css` fayl", "Klass selektorlari, ranglar, shriftlar (Google Fonts mumkin)",
      "Box model: margin, padding, border"],
     [("CSS asoslari", 30, "Selektorlar, ranglar, shriftlar"),
      ("Box model", 20, "Bo‘shliqlar va chegaralar o‘rinli"),
      ("Ko‘rinish", 15, "O‘qish qulay, rang kontrasti yetarli")]),
    (28, "l28-kartochkalar", "Mahsulot kartochkalari", "Do‘kon uchun 4–6 ta mahsulot kartochkasi; «Yangi» belgisi "
     "`position` bilan, ranglar CSS o‘zgaruvchilarda.",
     ["`:root` da kamida 3 ta CSS o‘zgaruvchi", "`position: relative/absolute` bilan belgi (badge)",
      "Yopishqoq (`sticky`) sarlavha"],
     [("position", 25, "relative/absolute/sticky to‘g‘ri ishlatilgan"),
      ("CSS o‘zgaruvchilar", 20, "Ranglar va o‘lchamlar o‘zgaruvchilarda"),
      ("display", 20, "block/inline/inline-block farqi to‘g‘ri qo‘llangan")]),
    (29, "l29-navbar-flexbox", "Navigatsiya va galereya (Flexbox)", "Flexbox bilan sayt navigatsiyasi va rasmlar "
     "galereyasini yarating.",
     ["Navbar: logo chapda, menyu o‘ngda (`justify-content: space-between`)", "Galereya `flex-wrap` bilan",
      "Elementlar vertikal markazlangan"],
     [("Flexbox navbar", 30, "To‘g‘ri tekislash va bo‘shliqlar"),
      ("Galereya", 25, "flex-wrap, gap, moslashuvchan o‘lchamlar"),
      ("Tozalik", 10, "Ortiqcha float/position yo‘q")]),
    (30, "l30-grid-maket", "Sahifa maketi (CSS Grid)", "Blog sahifasi maketi: sarlavha, yon panel, asosiy kontent va "
     "pastki qism — CSS Grid bilan.",
     ["`grid-template-areas` yoki `grid-template-columns`", "Kamida bitta element bir nechta ustunni egallaydi",
      "`gap` bilan bo‘shliqlar"],
     [("Grid maket", 35, "Hududlar to‘g‘ri joylashgan"),
      ("Grid xossalari", 20, "fr, repeat, span, gap"),
      ("Kontent", 10, "Maket real kontent bilan to‘ldirilgan")]),
    (31, "l31-responsiv-landing", "Responsiv landing sahifa", "Mobil (375px), planshet (768px) va kompyuter (1440px) "
     "da chiroyli ko‘rinadigan landing sahifa.",
     ["`viewport` meta tegi", "Kamida 2 ta media query (mobile-first)", "Moslashuvchan rasmlar (`max-width: 100%`)"],
     [("Responsivlik", 35, "3 ta o‘lchamda buzilmaydi"),
      ("Media query", 20, "Mobile-first, mantiqiy breakpoint’lar"),
      ("Birliklar", 10, "rem, %, vw o‘rinli")]),
    (32, "l32-todo-js", "Vazifalar ro‘yxati (JavaScript)", "DOM va hodisalar bilan oddiy «To-Do» ilovasi.",
     ["Vazifa qo‘shish, bajarilgan deb belgilash, o‘chirish", "`addEventListener` ishlatilgan",
      "Bo‘sh vazifa qo‘shilmaydi", "`textContent` (innerHTML emas) — xavfsizlik"],
     [("Funksionallik", 30, "Qo‘shish, belgilash, o‘chirish ishlaydi"),
      ("DOM va hodisalar", 25, "querySelector, addEventListener, createElement"),
      ("Xavfsizlik va validatsiya", 10, "textContent, bo‘sh kiritish tekshiruvi")]),
    (33, "l33-komponentlar", "Interaktiv komponentlar", "Uchta komponent yarating: modal oyna, akkordeon (FAQ) va "
     "tablar. Holat `localStorage` da saqlansin (masalan, ochiq tab).",
     ["Modal `Esc` tugmasi bilan yopiladi", "Akkordeon `classList.toggle` bilan", "Tanlangan tab qayta yuklashda saqlanadi"],
     [("Komponentlar", 30, "Uchala komponent to‘g‘ri ishlaydi"),
      ("Qulaylik", 20, "Klaviatura, aria-atributlar, fokus"),
      ("localStorage", 15, "Holat saqlanadi va tiklanadi")]),
    (34, "l34-portfolio-dizayn", "Portfolio dizayni va karkasi", "Shaxsiy portfolio uchun maket (wireframe) chizing va "
     "sahifa karkasini HTML/CSS da yarating.",
     ["Maket rasmi (`docs/wireframe.png`) README’da", "Bo‘limlar: Men haqimda, Ko‘nikmalar, Loyihalar, Aloqa (forma emas, havola)",
      "2–3 rangli palitra va CSS o‘zgaruvchilar", "Shaxsiy manzil va telefon raqami yo‘q"],
     [("Maket va reja", 25, "Wireframe va bo‘limlar rejasi"),
      ("Karkas", 25, "Semantik HTML, Grid/Flexbox"),
      ("Dizayn tizimi", 15, "Palitra, shriftlar, o‘zgaruvchilar")]),
    (35, "l35-lighthouse", "Portfolioni optimallashtirish", "Portfolio sahifangizni Lighthouse bilan tekshiring va "
     "natijani yaxshilang.",
     ["README’da Lighthouse natijasi «oldin» va «keyin» (skrinshot)", "Performance, Accessibility, SEO — har biri ≥ 90",
      "Rasmlar siqilgan (WebP), `alt` va `meta description` bor"],
     [("Lighthouse ballari", 35, "Uchala ko‘rsatkich ≥ 90"),
      ("Optimallashtirish", 20, "Rasmlar, lazy loading, keraksiz kod yo‘q"),
      ("Hisobot", 10, "Oldin/keyin taqqoslash va xulosa")]),
    (36, "l36-loyiha-3", "Loyiha 3 himoyasi: portfolio GitHub Pages’da", "Tayyor portfolio saytini GitHub Pages’ga joylang "
     "va himoya qiling.",
     ["Sayt `https://<foydalanuvchi>.github.io/...` da ochiladi", "Responsiv, kamida bitta JS komponent",
      "Kamida 3 ta loyiha kartochkasi havolalar bilan", "README: tavsif, skrinshot, sayt havolasi"],
     [("Joylashtirilgan sayt", 25, "GitHub Pages’da ishlaydi"),
      ("Sifat", 25, "Responsiv, qulay, Lighthouse ≥ 90"),
      ("Himoya", 15, "Kodni tushuntira oladi, savollarga javob beradi")]),
    (37, "l37-ai-xarita", "AI tushunchalari xaritasi", "AI, ML, deep learning va LLM tushunchalari orasidagi bog‘liqlikni "
     "Markdown hujjatda (Mermaid diagramma bilan) tushuntiring.",
     ["`README.md` da Mermaid diagramma", "Har bir tushunchaga oddiy tilda ta’rif va hayotiy misol",
      "LLM cheklovlari (gallyutsinatsiya, bilim sanasi) bo‘limi", "Manbalar ro‘yxati"],
     [("Tushunchalar", 30, "To‘g‘ri va tushunarli ta’riflar"),
      ("Diagramma", 20, "Mermaid diagramma bog‘liqlikni ko‘rsatadi"),
      ("Tanqidiy fikr", 15, "Cheklovlar va xavfsizlik")]),
    (38, "l38-prompt-kutubxonasi", "Prompt kutubxonasi", "O‘qish va dasturlash uchun 10 ta foydali prompt yozing va "
     "sinab ko‘ring.",
     ["Har bir prompt: maqsad, matn, natija namunasi, xulosa", "Kamida 2 ta few-shot va 2 ta format (JSON/jadval) so‘raydigan prompt",
      "Bitta promptni 3 marta yaxshilash tarixi"],
     [("Promptlar sifati", 30, "Aniq vazifa, kontekst, format"),
      ("Texnikalar", 20, "Rol, few-shot, format, cheklovlar"),
      ("Tahlil", 15, "Natijalar taqqoslangan, xulosalar")]),
    (39, "l39-ai-kod-audit", "AI kodini tekshirish", "AI yordamida kichik Python dastur (masalan, parol generatori) yozing, "
     "keyin uni o‘zingiz tekshirib, xatolarni tuzating.",
     ["Asl AI kodi va tuzatilgan versiya alohida fayllarda", "`AUDIT.md`: topilgan muammolar (kamida 3 ta) va tuzatishlar",
      "Kamida 3 ta `pytest` testi", "Maxfiy ma’lumot kodda yo‘q"],
     [("Audit", 30, "Muammolar to‘g‘ri aniqlangan va asoslangan"),
      ("Tuzatishlar va testlar", 20, "Testlar o‘tadi, kod yaxshilangan"),
      ("Xavfsizlik", 15, "Kiritish tekshiruvi, maxfiy kalitlar yo‘q")]),
    (40, "l40-api-mijoz", "Ochiq API bilan ishlovchi dastur", "Ochiq API’dan (masalan, ob-havo yoki valyuta kursi) "
     "`requests` yordamida ma’lumot olib, chiroyli ko‘rsatuvchi konsol dastur.",
     ["GET so‘rov va JSON javobni tahlil qilish", "Status kod va tarmoq xatolari ushlangan", "API kalit (bo‘lsa) `.env` da"],
     [("API bilan ishlash", 30, "So‘rov, parametrlar, JSON"),
      ("Xatolarni boshqarish", 20, "Status kod, timeout, tarmoq xatosi"),
      ("Natija", 15, "Ma’lumot tushunarli ko‘rsatiladi")]),
    (41, "l41-llm-yordamchi", "LLM API yordamchisi", "LLM API orqali ishlaydigan konsol yordamchi: masalan, matnni "
     "qisqartiruvchi yoki so‘zlarni tushuntiruvchi.",
     ["API kalit faqat `.env` da, `.env.example` repozitoriyda", "Tizim prompti va javob uzunligi cheklovi",
      "Xatolar va limitlar qayta ishlangan", "README’da ishlatish namunasi"],
     [("Integratsiya", 30, "API to‘g‘ri chaqiriladi, javob qayta ishlanadi"),
      ("Prompt va parametrlar", 20, "Tizim prompti, max_tokens, temperature"),
      ("Xavfsizlik", 15, "Kalit himoyalangan, xatolar ushlangan")]),
    (42, "l42-async-yuklovchi", "Asinxron yuklovchi", "Bir nechta URL’dan ma’lumotni `asyncio` bilan parallel yuklab, "
     "sinxron versiya bilan tezligini solishtiring.",
     ["`async def`, `await`, `asyncio.gather` ishlatilgan", "Sinxron va asinxron vaqtlar README’da",
      "Xatoli URL dasturni to‘xtatmaydi"],
     [("Asinxron kod", 30, "To‘g‘ri korutinalar va gather"),
      ("Taqqoslash", 20, "O‘lchov natijalari va xulosa"),
      ("Barqarorlik", 15, "Xatolar va timeout’lar")]),
    (43, "l43-echo-bot", "Birinchi Telegram bot", "aiogram bilan bot: `/start`, `/help` va kamida 2 ta o‘z buyrug‘ingiz.",
     ["Token `.env` da", "Buyruqlar va oddiy matnga javob", "README’da ishga tushirish yo‘riqnomasi"],
     [("Bot ishlaydi", 30, "Buyruqlar to‘g‘ri javob beradi"),
      ("Kod tuzilmasi", 20, "Handler’lar, routerlar, asinxronlik"),
      ("Xavfsizlik", 15, "Token himoyalangan")]),
    (44, "l44-viktorina-bot", "Viktorina bot (inline, FSM, SQLite)", "Inline tugmali viktorina bot: savollar SQLite’da, "
     "foydalanuvchi natijalari saqlanadi.",
     ["Inline tugmalar va callback’lar", "FSM bilan ko‘p bosqichli jarayon", "SQLite, parametrli so‘rovlar",
      "`/top` — eng yaxshi natijalar (faqat ism/taxallus)"],
     [("Inline va FSM", 30, "Tugmalar va holatlar to‘g‘ri ishlaydi"),
      ("Ma’lumotlar bazasi", 20, "Jadvallar, parametrli so‘rovlar"),
      ("Foydalanuvchi tajribasi", 15, "Tushunarli matnlar va xatolar")]),
    (45, "l45-ai-bot", "AI yordamchi bot", "Telegram botga LLM ulang: o‘quvchilarga dars mavzularini tushuntiruvchi yordamchi.",
     ["Xavfsiz tizim prompti (bolalar uchun mos)", "Foydalanuvchi uchun kunlik so‘rovlar limiti",
      "Suhbat tarixi (oxirgi bir necha xabar)", "API xatolarida tushunarli javob"],
     [("AI integratsiyasi", 30, "LLM javoblari botda ishlaydi"),
      ("Xavfsizlik va limitlar", 20, "Tizim prompti, limit, kalitlar"),
      ("Kontekst", 15, "Suhbat tarixi to‘g‘ri saqlanadi")]),
    (46, "l46-botni-joylash", "Botni sinash va serverga joylash", "Botingizga testlar yozing va uni serverga "
     "(yoki bepul platformaga) joylang.",
     ["Kamida 5 ta `pytest` testi", "`requirements.txt`, `.env.example`", "Joylash yo‘riqnomasi README’da",
      "Bot 24/7 ishlaydi (havola yoki skrinshot)"],
     [("Testlar", 25, "Muhim funksiyalar testlangan, testlar o‘tadi"),
      ("Joylash", 25, "Server/platformada ishlaydi"),
      ("Hujjat", 15, "Qadamma-qadam yo‘riqnoma")]),
    (47, "l47-readme-cv", "README, taqdimot va CV", "Eng yaxshi loyihangiz uchun professional README, 5–7 slaydli "
     "taqdimot va bir sahifali CV tayyorlang.",
     ["README: tavsif, skrinshotlar, o‘rnatish, texnologiyalar", "Taqdimot PDF ko‘rinishida repozitoriyda",
      "CV’da shaxsiy kontaktlar o‘rniga GitHub havolasi"],
     [("README", 30, "To‘liq va tushunarli"),
      ("Taqdimot", 20, "Muammo → yechim → natija"),
      ("CV", 15, "Ko‘nikmalar va loyihalar aniq")]),
    (48, "l48-demo-day", "Demo Day: yakuniy loyiha", "Kurs davomidagi bilimlarni birlashtirgan yakuniy loyihani "
     "(veb-sayt + bot yoki AI integratsiyasi) Demo Day’da taqdim eting.",
     ["Ishlaydigan loyiha va jonli demo", "GitHub’da toza tarix, README, testlar", "3 daqiqalik pitch",
      "Savollarga javob"],
     [("Loyiha sifati", 30, "Funksionallik va barqarorlik"),
      ("Texnik chuqurlik", 20, "Kurs mavzularidan foydalanilgan"),
      ("Taqdimot", 15, "Pitch va jonli demo")]),
]

COMMON = [("Kod sifati", 15, "PEP 8 / toza HTML-CSS, tushunarli nomlar, takrorlanmaydigan kod"),
          ("README va Git", 10, "README to‘liq, ma’noli commit’lar"),
          ("Xavfsizlik va mustaqillik", 10, "Maxfiy ma’lumot yo‘q; muallif kodni tushuntira oladi")]

for lesson, slug, title, task, requirements, rubric in PROJECTS:
    body = f"{task}\n\n## Talablar\n" + "\n".join(f"- {r}" for r in requirements) + SUBMIT + SAFETY
    full = rubric + COMMON
    project_problem(slug=slug, title=title, lesson=lesson, statement=body, rubric=full, tags=["loyiha"],
                    difficulty=4 if lesson in (12, 24, 36, 48) else 3)
print(len(PROJECTS), "ta loyiha")
