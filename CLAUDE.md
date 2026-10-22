# kodx.uz — loyiha konteksti (Claude Code uchun)

## Loyiha nima
kodx.uz — «Dasturlash va sun’iy intellekt asoslari» kursi (muallif: Nurbek Soliyev)
o‘quvchilari kurs masalalari, misollar va uyga vazifalarni yechadigan platforma.
Namuna: Codeforces, Kep.uz, Robocontest, Codewars. Hozircha faqat shu kurs uchun,
keyin boshqa yo‘nalishlar (algoritmlash, frontend, backend, AI) qo‘shiladi.
Foydalanuvchilarning ko‘pchiligi — voyaga yetmagan o‘quvchilar.

## Texnologiyalar
- Python 3.12, Django 5, MySQL 8 (OpenServer, lokal), utf8mb4
- Parol xeshlash: Argon2. Sozlamalar faqat .env dan (python-dotenv)
- Kodni avtomatik tekshirish: keyingi bosqichda Judge0 (alohida xizmat)
- Muhit: Windows, Git Bash. Repo: github.com/SoliyevNurbek/kodx

## Rollar (har yuqori rol pastdagilar huquqini o‘z ichiga oladi)
| Daraja | Rol | Huquqlar |
|---|---|---|
| 1 | user | profil, barcha masalalarga kirish, yechim yuborish, o‘z urinishlari, reyting; boshqalarning yechilgan masalalar sonini ko‘radi |
| 2 | jury | + kontest yaratish va o‘z kontestlari ustidan to‘liq nazorat |
| 3 | jury_pro | + masala va test qo‘shish; faqat O‘ZI qo‘shgan masalalarni tahrirlash/o‘chirish |
| 4 | moderator | + barcha urinishlar, kodlar va testlarni ko‘rish; jury/jury_pro rolini berish; Jury so‘rovlarini tasdiqlash; barcha kontestlar ustidan nazorat; nosozlikni super adminga yuboradi |
| 5 | superadmin | + tizim sozlamalari, dizayn, xatolarni bartaraf etish, barcha rollar |

Hech kim (superadmin ham) foydalanuvchi parolini ko‘ra olmaydi — faqat qayta tiklashga majburlaydi.

## Vazifa turlari
- code — kirish/chiqish testlari bilan avtomatik tekshiriladi (Modul 1–2)
- quiz — test savollari, avtomatik tekshiriladi
- project — GitHub havolasi yuboriladi, o‘qituvchi rubrika bo‘yicha baholaydi (Modul 3–4)

Kurs bahosi va musobaqa reytingi — ALOHIDA hisoblanadi.

## Kurs tuzilmasi (seed ma’lumot: 4 modul, 48 dars)
Modul 1 — Kompyuter, Git va Python asoslari:
1 Kompyuter va ish muhiti · 2 Terminal (CLI) · 3 Git asoslari · 4 GitHub ·
5 Python: birinchi qadamlar · 6 Arifmetika, satrlar, f-string · 7 Mantiqiy ifodalar ·
8 Shartli operatorlar (if) · 9 match-case · 10 for tsikli · 11 while tsikli · 12 Loyiha 1 himoyasi
Modul 2 — Ma’lumot tuzilmalari, funksiyalar, OOP:
13 Ro‘yxatlar (list) · 14 Qidirish, saralash, comprehension · 15 tuple, set, dict ·
16 Satrlar chuqur · 17 Funksiyalar · 18 Fayllar: txt, csv, json · 19 Xatolarni boshqarish ·
20 Modullar, paketlar, pip · 21 OOP: klass va obyekt · 22 Meros va inkapsulyatsiya ·
23 Kod sifati, branch va PR · 24 Loyiha 2 himoyasi
Modul 3 — Web: HTML, CSS, JavaScript:
25 Web va HTML5 · 26 HTML: forma va semantika · 27 CSS3 asoslari ·
28 display, position, CSS o‘zgaruvchilar · 29 Flexbox · 30 CSS Grid · 31 Responsiv dizayn ·
32 JavaScript: DOM va hodisalar · 33 Interaktiv komponentlar · 34 Portfolio loyihalash ·
35 SEO, tezlik va Lighthouse · 36 GitHub Pages va Loyiha 3 himoyasi
Modul 4 — AI, API va Telegram bot:
37 AI, ML va LLM · 38 Prompt engineering · 39 AI bilan kodlash va xavfsizlik ·
40 HTTP va REST API · 41 LLM API · 42 Asinxron dasturlash · 43 Telegram bot: aiogram ·
44 Inline tugmalar, FSM, SQLite · 45 Botga AI integratsiyasi · 46 Sinov va serverga joylash ·
47 README, taqdimot, GitHub va CV · 48 Demo Day

## Ishlash qoidalari
- Har bosqichdan oldin qisqa reja ko‘rsat va tasdiq kut. Noaniq bo‘lsa — so‘ra, taxmin qilma.
- .env ni hech qachon o‘qima, ekranga chiqarma, commit qilma. Parollarni so‘rama —
  ularni egasi terminalda o‘zi kiritadi.
- Loyiha root MySQL foydalanuvchisi bilan ishlamaydi — faqat alohida foydalanuvchi.
- Har yangi funksiya: model → migratsiya → admin → test → commit.
- Kod: PEP 8, docstring, type hints; ilova nomlari inglizcha, interfeys matnlari o‘zbekcha (lotin).
- Har muhim admin harakati audit.AuditLog ga yoziladi.
- Bolalar xavfsizligi: profilda shaxsiy kontaktlar (telefon, email) boshqalarga ko‘rinmaydi;
  boshqalarning yechimi faqat masala yechilgandan yoki kontest tugagandan keyin ochiladi.
- Foydalanuvchi kodini hech qachon Django serverining o‘zida ishga tushirma — faqat
  izolyatsiyalangan tekshiruv xizmati (Judge0) orqali.
- Commit xabarlari o‘zbekcha, aniq. main — doim ishlaydigan holatda; yangi bosqich — alohida branch.

## Bosqichlar (MVP)
1. Poydevor: Django + MySQL + rollar + audit + admin
2. Kurs: Course, Module, Lesson (48 dars seed), Group, GroupMember
3. Masalalar: Problem, TestCase, Tag, LessonProblem (dars va muddat)
4. Yechimlar: Submission, SubmissionResult + Judge0 integratsiyasi
5. Sahifalar: ro‘yxatdan o‘tish, profil, masalalar, yechim yuborish, reyting
6. Kontestlar, Jury/Jury Pro, rating tarixi
7. Quiz va loyiha topshirish, kurs bahosi

Batafsil bajarish rejasi va bosqichlar tartibi: docs/MASTER_PROMPT.md (ustuvor).
Holat: docs/PROGRESS.md · Qarorlar: docs/DECISIONS.md
