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
| 7. Kontestlar | — | |
| 8. Rollar oqimi va xavfsizlik | — | |
| 9. Sifat va hujjatlar | — | |

## Egasi bajarishi kerak bo‘lgan ishlar
- [ ] `venv/Scripts/python manage.py init_superuser` — `nurbek` ga parol o‘rnatadi
  (agent uchun bloklangan, qarang DECISIONS.md). Parol `.env` ning oxirgi qatorida.

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
