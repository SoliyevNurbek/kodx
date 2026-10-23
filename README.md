# kodx.uz

«Dasturlash va sun’iy intellekt asoslari» kursi o‘quvchilari uchun masalalar, testlar va loyihalarni yechish
platformasi (Codeforces, Kep.uz, Robocontest, Codewars uslubida). Muallif: Nurbek Soliyev.

![CI](https://github.com/SoliyevNurbek/kodx/actions/workflows/ci.yml/badge.svg)

- 48 dars, 4 modul; har darsda vazifalar: **146 ta seed vazifa** — 72 kod masala (etalon yechim bilan tekshirilgan),
  48 test (quiz), 26 loyiha (rubrika bilan).
- Kod avtomatik tekshiriladi (Judge0; dev’da LocalDevBackend), natija bir necha soniyada jonli ko‘rinadi.
- Kurs bahosi (davomat, vazifalar, test, loyiha) va musobaqa reytingi — **alohida**.
- Kontestlar (ICPC/IOI), jonli jadval, Elo reyting, mashq bali, kunlik seriya, nishonlar.
- Rol panellari: o‘qituvchi, Jury, Jury Pro, super admin. Bolalar xavfsizligi birinchi o‘rinda.

Hujjatlar: [Arxitektura](docs/ARCHITECTURE.md) · [Rollar matritsasi](docs/ROLES.md) ·
[Vazifa formati](docs/PROBLEM_FORMAT.md) · [Qarorlar](docs/DECISIONS.md) · [Holat](docs/PROGRESS.md)

## Texnologiyalar

| Qatlam | Tanlov |
|---|---|
| Backend | Python 3.12, Django 5.2, MySQL 8 (utf8mb4, `STRICT_TRANS_TABLES`) |
| Frontend | Django shablonlari, HTMX, Tailwind CSS (CDN), CodeMirror 6, KaTeX; o‘zbekcha (i18n tayyor) |
| Kod tekshiruvi | Judge0 (production), LocalDevBackend (faqat dev), navbat + `run_judge_worker` |
| Xavfsizlik | Argon2, 2FA (TOTP) super admin uchun, CSP nonce, kirish urinishlari cheklovi, audit jurnali |
| Sifat | 270+ test, coverage ≥ 80% (hozir ~95%), ruff, GitHub Actions |

## O‘rnatish (lokal, Windows / OpenServer)

1. Repozitoriy va virtual muhit:

   ```bash
   git clone https://github.com/SoliyevNurbek/kodx.git
   cd kodx
   python -m venv venv
   venv/Scripts/python -m pip install -r requirements-dev.txt   # Linux/macOS: venv/bin/python
   ```

2. MySQL’da baza va alohida foydalanuvchi (loyiha `root` bilan ishlamaydi):

   ```sql
   CREATE DATABASE kodx CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'kodx_user'@'localhost' IDENTIFIED BY '<kuchli-parol>';
   GRANT ALL PRIVILEGES ON kodx.* TO 'kodx_user'@'localhost';
   GRANT ALL PRIVILEGES ON test_kodx.* TO 'kodx_user'@'localhost';  -- testlar uchun
   ```

   OpenServer 6 da MySQL odatda `127.0.1.x` manzilida bo‘ladi — `.env` dagi `DB_HOST` ga yozing.

3. Sozlamalar: `.env.example` dan `.env` nusxasini oling va to‘ldiring (`SECRET_KEY`, `DB_*`).

4. Baza, administrator va ishga tushirish:

   ```bash
   venv/Scripts/python manage.py migrate            # kurs, 146 vazifa, nishonlar, namunaviy kontest
   venv/Scripts/python manage.py init_superuser     # «nurbek» uchun parol .env ga yoziladi
   venv/Scripts/python manage.py runserver
   venv/Scripts/python manage.py run_judge_worker   # alohida terminalda — yechimlarni tekshiradi
   ```

   **Boshlang‘ich parol `.env` dagi `SUPERUSER_INITIAL_PASSWORD` qatorida;** birinchi kirishdan keyin u almashtiriladi
   (majburiy) — keyin bu qatorni `.env` dan o‘chiring. `/panel/` birinchi marta ochilganda autentifikator ilova
   (Google Authenticator, Aegis) bilan 2FA yoqiladi.

5. Demo ma’lumotlar (ixtiyoriy, faqat `DEBUG=True`): `manage.py seed_demo [--students 20] [--reset]`.

6. Testlar va sifat:

   ```bash
   venv/Scripts/python manage.py test
   venv/Scripts/ruff check .
   venv/Scripts/coverage run manage.py test && venv/Scripts/coverage report
   ```

## Bosh sahifa surati

Hero’dagi muallif surati `scripts/make_hero_image.py` bilan yaratiladi (Pillow):

```bash
venv/Scripts/python scripts/make_hero_image.py
```

Natija: `static/img/hero-nurbek.png` (manba), `hero-nurbek-800.webp`, `hero-nurbek-1200.webp` (sifat 85) — har
ishga tushirishda qayta yoziladi. Hozir surat dizayn maketidan (`docs/design/landing-mockup.jfif`) qirqib olinadi.
**Haqiqiy surat** qo‘yish uchun uni `static/img/hero-nurbek-source.png` nomi bilan saqlang va skriptni qayta
ishga tushiring — skript maket o‘rniga shu fayldan foydalanadi (portret, kengligi ≥ 1200 px tavsiya etiladi).
Muallif kartasidagi matnlar: panel → Tizim sozlamalari.

## Rollar

Har yuqori rol pastdagilarning barcha huquqlarini o‘z ichiga oladi (`user.has_role_at_least(Role.JURY)`).
To‘liq matritsa: [docs/ROLES.md](docs/ROLES.md). Koddagi identifikatorlar: `jury`, `jury_pro`.

| Daraja | Rol | Huquqlar |
|---|---|---|
| 1 | user | profil, masalalar, yechim yuborish, o‘z urinishlari, reyting |
| 2 | judge | + kontest yaratish va o‘z kontestlarini boshqarish |
| 3 | judge_pro | + masala va test qo‘shish; faqat o‘z masalalarini tahrirlash |
| 4 | moderator | + barcha urinishlar va testlarni ko‘rish; jury/jury_pro rolini berish; rol so‘rovlarini tasdiqlash; guruhlar, baholar, loyihalarni baholash |
| 5 | superadmin | + tizim sozlamalari, dizayn, audit, barcha rollar (2FA bilan) |

Hech kim (superadmin ham) foydalanuvchi parolini ko‘ra olmaydi — faqat bir martalik vaqtinchalik parol berish
(keyingi kirishda almashtirish majburiy) yoki qayta tiklash mumkin. Muhim harakatlar `audit.AuditLog` ga yoziladi.

## Bosqichlar

| # | Bosqich | Holat |
|---|---|---|
| 1 | Poydevor: Django, MySQL, rollar, audit | ✅ |
| 2 | Kurs tuzilmasi: 48 dars, guruhlar | ✅ |
| 3 | Vazifalar banki: code/quiz/project, import, 146 seed | ✅ |
| 4 | Yechimlar, navbat, worker, quiz va loyiha baholash | ✅ |
| 5 | Sahifalar va rol panellari | ✅ |
| 6 | Kurs bahosi, mashq reytingi, nishonlar, Elo | ✅ |
| 7 | Kontestlar (ICPC/IOI), jonli jadval, reyting | ✅ |
| 8 | Rol so‘rovlari, 2FA, CSP, ko‘chirmachilik, prod sozlamalari | ✅ |
| 9 | Sifat: coverage, CI, seed_demo, hujjatlar | ✅ |

## Masala qo‘shish

- **Panel orqali (Jury Pro):** «Vazifalarim» → «Yangi vazifa» → testlarni yuklash (.in/.out) → «Etalon yechim bilan
  tekshirish» → «Ko‘rib chiqishga». Moderator admin panelda nashr etadi.
- **Papkadan (ko‘p vazifa):** [docs/PROBLEM_FORMAT.md](docs/PROBLEM_FORMAT.md) formatida tayyorlab:

  ```bash
  venv/Scripts/python manage.py import_problems <papka> --author <username> [--status published]
  venv/Scripts/python manage.py verify_problems --slug <slug>    # etalon yechim barcha testlardan o'tadimi
  ```

## Judge0’ni ulash

1. Judge0 ni alohida serverda ishga tushiring (Docker Compose — rasmiy yo‘riqnoma: <https://github.com/judge0/judge0>)
   yoki RapidAPI’dagi Judge0 CE dan foydalaning.
2. `.env`:

   ```ini
   JUDGE_BACKEND=judge0
   JUDGE0_URL=https://judge0.sizning-domen.uz
   JUDGE0_TOKEN=<auth token>
   JUDGE0_AUTH_HEADER=X-Auth-Token        # RapidAPI uchun: X-RapidAPI-Key
   ```

3. Worker’ni qayta ishga tushiring: `manage.py run_judge_worker`. Python 3 — `language_id=71`; yangi tillar
   `judge/backends/judge0.py` dagi `LANGUAGE_IDS` ga qo‘shiladi.

> ⚠️ `LocalDevBackend` — **production uchun EMAS**: u faqat `DEBUG=True` da ishlaydi va haqiqiy sandbox emas.

## Serverga joylash rejasi

1. Ubuntu 24.04 server: Python 3.12, MySQL 8, nginx, Judge0 (alohida server yoki Docker).
2. Kod: `git clone`, `python -m venv venv`, `pip install -r requirements.txt`.
3. `.env`: kuchli `SECRET_KEY`, `DEBUG=False`, `PROD_ALLOWED_HOSTS`, `DB_*`, `JUDGE0_*`, `EMAIL_*`.
4. `DJANGO_SETTINGS_MODULE=config.settings_prod`; tekshiruv:
   `python manage.py check --deploy --settings=config.settings_prod` (ogohlantirishsiz bo‘lishi kerak).
5. `migrate`, `collectstatic`, `init_superuser`.
6. systemd xizmatlari: `gunicorn config.wsgi` (web) va `manage.py run_judge_worker` (worker, `Restart=always`);
   cron: `apply_contest_ratings` (zaxira), kerak bo‘lsa `check_similarity`.
7. nginx: HTTPS (Let’s Encrypt), `/static/` va `/media/` ni to‘g‘ridan-to‘g‘ri berish, `X-Forwarded-Proto`.
8. Zaxira nusxa: kunlik `mysqldump` + `media/` papkasi.
9. Keyingi qadamlar: Tailwind build (CDN o‘rniga), Redis/Celery navbati (`JUDGE_QUEUE`), ru/en tarjimalar.

## Tuzilma

```
config/        sozlamalar (settings.py, settings_prod.py), URL’lar, test runner
accounts/      User (5 rol), RoleRequest, LoginAttempt, ruxsatlar, 2FA, init_superuser
audit/         AuditLog va log_action()
courses/       kurs, modul, 48 dars, guruhlar (seed)
problems/      vazifalar banki, importer, seed/ (146 vazifa), import/verify buyruqlari
judge/         JudgeBackend, LocalDevBackend, Judge0Backend, checker
submissions/   yechimlar, navbat, run_judge_worker, quiz/loyiha baholash, check_similarity
grading/       kurs bahosi, davomat, mashq bali, nishonlar, Elo
contests/      kontestlar, jadval, reyting tarixi
core/          sayt sozlamalari, bosh sahifa, middleware (CSP, 2FA), seed_demo
panel/         o‘qituvchi, Jury, Jury Pro, super admin panellari
templates/     shablonlar; static/ — CSS/JS
tools/seed_gen seed kontent generatori (etalon yechim bilan .out yaratadi)
docs/          arxitektura, rollar, format, qarorlar, holat
```
