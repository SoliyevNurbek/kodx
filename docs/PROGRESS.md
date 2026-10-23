# Bajarilish holati

Sessiya uzilsa — ish shu fayldan davom ettiriladi. Reja: `docs/MASTER_PROMPT.md`.

| Bosqich | Holat | Testlar |
|---|---|---|
| 1. Poydevor | tayyor | 20 |
| 2. Kurs tuzilmasi | tayyor | 43 |
| 3. Vazifalar banki | tayyor | 96 |
| 4. Yechimlar va tekshiruv | tayyor | 129 |
| 5. Sahifalar (UI) | tayyor | 175 |
| 6. Baholash va reyting | tayyor | 214 |
| 7. Kontestlar | tayyor | 244 |
| 8. Rollar oqimi va xavfsizlik | tayyor | 265 |
| 9. Sifat va hujjatlar | tayyor | 277 |

## Egasi bajarishi kerak bo‘lgan ishlar
- [ ] `venv/Scripts/python manage.py init_superuser` — `nurbek` ga parol o‘rnatadi
  (agent uchun bloklangan, qarang DECISIONS.md). Parol `.env` ning oxirgi qatorida.
- [ ] Birinchi kirishda: parolni almashtirish (majburiy), keyin `/panel/` ochilganda autentifikator ilovada
  (Google Authenticator, Aegis) QR-kodni skanerlab 2FA ni yoqish.

## 2-bosqich — Kurs tuzilmasi (tayyor)
- Course, Module, Lesson (dars / loyiha himoyasi / Demo Day), Group, GroupMember.
- Seed migratsiya: 1 kurs, 4 modul, 48 dars, «Python-1» guruhi (o‘qituvchi `nurbek`), dublikatsiz.
- `accounts.permissions`: `role_required`, `RoleRequiredMixin`, `RoleAdminMixin`.
- `is_staff` roldan kelib chiqadi; moderatorning admin chegaralari.
- Keyingi qadam: 3-bosqich — vazifalar banki.

## 3-bosqich — Vazifalar banki (tayyor)
- `judge`: Verdict/Limits, checker (exact/whitespace/float), JudgeBackend, LocalDevBackend (DEV ONLY), Judge0Backend.
- `problems`: Problem (code/quiz/project, holat, qiyinlik, teglar, limitlar, etalon yechim), TestCase (fayllar
  media/tests/ da), QuizQuestion/QuizOption, RubricCriterion, LessonProblem; ob'ekt ruxsatlari; admin (nashr etish).
- Import: `manage.py import_problems`, `verify_problems`; `docs/PROBLEM_FORMAT.md`, namunalar `docs/examples/problems/`.
- Seed: 146 vazifa (72 code, 48 quiz × 5 savol, 26 loyiha), har darsda vazifa bor; 72 etalon yechim 100% o‘tadi.
  Kontentni o‘zgartirish: `tools/seed_gen/*.py` ni tahrirlab, `cd tools/seed_gen && python <fayl>.py`
  (problems/seed/ qayta yoziladi); bazaga — `import_problems problems/seed --status published`.
- Testlar: 96. Keyingi qadam: 4-bosqich — yechimlar, navbat, worker.

## 4-bosqich — Yechimlar va avtomatik tekshiruv (tayyor)
- Submission, SubmissionResult, QuizAttempt, ProjectSubmission; verdiktlar o‘zbekcha.
- `submissions.services`: create_submission (64 KB, 6/daqiqa), judge_submission, rejudge, grade_quiz,
  submit_project, grade_project, user_solved.
- Navbat: `submissions.queue` (DatabaseQueue); worker: `manage.py run_judge_worker [--once]`.
- Admin: yechimlar (faqat ko‘rish + qayta tekshirish), quiz va loyihalar.
- Testlar: 129. Keyingi qadam: 5-bosqich — UI sahifalari.

## 5-bosqich — Sahifalar (tayyor)
- Ommaviy: bosh sahifa (kurs, modullar, statistika, top-10), ro‘yxatdan o‘tish/kirish/parol tiklash, profil
  (faollik kalendari, nishonlar joyi; email faqat egasiga), kurs → dars (holat, muddatlar), masalalar ro‘yxati.
- Vazifa sahifalari: code (shart, namunalar, KaTeX, CodeMirror, yuborish → HTMX jonli natija), quiz, project.
- Urinishlarim, urinish tafsiloti (testlar bo‘yicha natija, kod ko‘rinishi qoidalari).
- Panellar: o‘qituvchi (guruh progressi dars × o‘quvchi, yechimlar oqimi, loyiha baholash, rol so‘rovlari, rollar),
  Jury Pro (o‘z vazifalari, testlar yuklash, etalon bilan tekshirish, ko‘rib chiqishga yuborish),
  super admin (sayt sozlamalari, audit, tizim holati/worker).
- 46 ta view testi (ruxsat bor/yo‘q matritsasi bilan). Haqiqiy bazada barcha asosiy sahifalar 200.
- Egasi uchun: 375/768/1440 px da vizual ko‘rib chiqish (responsiv klasslar va overflow-x jadvallar ishlatilgan).
- Keyingi qadam: 6-bosqich — baholash va reyting.

## 6-bosqich — Baholash va reyting (tayyor)
- `grading`: GradingPolicy, Attendance, PracticeStats, Badge/UserBadge; seed: 12 nishon, standart siyosat.
- Kurs bahosi (modul × 4 komponent, kechikish jarimasi), guruh baholari jadvali + CSV, davomat sahifasi.
- Mashq bali, kunlik seriya, nishonlar (avtomatik); reyting jadvallari: umumiy/haftalik/guruh/kurs, o‘z o‘rni.
- Elo/CF reyting algoritmi (`grading.rating`), boshlang‘ich 1200.
- 39 yangi test (chekka holatlar). Jami 214. Keyingi qadam: 7-bosqich — kontestlar.

## 7-bosqich — Kontestlar (tayyor)
- Contest (ICPC/IOI, ochiq/guruh/parol, reytingli, muzlatish), ContestProblem, ContestParticipant, RatingHistory;
  `Submission.contest`.
- Sahifalar: kontestlar ro‘yxati, kontest, masala + yuborish, jonli jadval (HTMX), ro‘yxatdan o‘tish.
- Jury paneli: kontest yaratish/tahrirlash, masalalar, ishtirokchilar, reytingni qo‘lda hisoblash.
- Reyting: worker va `apply_contest_ratings` avtomatik; profilda reyting grafigi. Seed: «Kirish kontesti».
- 30 yangi test. Jami 244. Keyingi qadam: 8-bosqich — rollar oqimi va xavfsizlik.

## 8-bosqich — Rollar oqimi va xavfsizlik (tayyor)
- Rol so‘rovi sahifasi (o‘quvchi) + moderator tasdiqlashi; vaqtinchalik parol (bir marta ko‘rsatiladi, majburiy almashtirish).
- Super admin 2FA (TOTP, QR), kirish urinishlari cheklovi (5 / 15 daqiqa), audit.
- `check_similarity` + moderator paneli «O‘xshash yechimlar».
- CSP (nonce), xavfsizlik sarlavhalari; `config/settings_prod.py`, `check --deploy` toza.
- 21 yangi test. Jami 265. Keyingi qadam: 9-bosqich — sifat, CI, seed_demo, hujjatlar.

## 9-bosqich — Sifat va hujjatlar (tayyor)
- Coverage 95% (talab ≥ 80%), ruff toza, GitHub Actions CI (MySQL 8 servisi bilan).
- `seed_demo` (20 demo o‘quvchi, urinishlar, kontest, reyting; faqat DEBUG).
- Yakuniy qabul testlari (`core/test_acceptance.py`): o‘quvchi yo‘li, o‘qituvchi baholari va CSV, Jury kontesti va reyting.
- README to‘liq; `docs/ARCHITECTURE.md` (Mermaid), `docs/ROLES.md` (ruxsatlar matritsasi).

## Yakuniy qabul (MASTER_PROMPT §5)
1. ✅ O‘quvchi ro‘yxatdan o‘tadi → guruhga qo‘shiladi → masala, test, loyiha → ball → reytingda o‘rni (test_1).
2. ✅ O‘qituvchi progress va baholarni ko‘radi, loyihani baholaydi, CSV eksport qiladi (test_2).
3. ✅ Jury kontest o‘tkazadi, jadval ishlaydi, reyting yangilanadi (test_3).
4. ✅ Barcha testlar o‘tadi, coverage ≥ 80% (95%), ruff toza, `.env` hech qachon commit qilinmagan.
5. ✅ Barcha bosqichlar «tayyor».

## Keyingi tavsiyalar (MVP dan keyin)
- Tailwind build (CDN o‘rniga) va CSP’dan `style-src 'unsafe-inline'` ni olib tashlash.
- Production’da Judge0 serverini ko‘tarish; Redis/Celery navbati (`JUDGE_QUEUE`).
- ru/en tarjimalar (`makemessages`), 375/768/1440 px da vizual QA.
