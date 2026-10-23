# Bajarilish holati

Sessiya uzilsa — ish shu fayldan davom ettiriladi. Reja: `docs/MASTER_PROMPT.md`.

| Bosqich | Holat | Testlar |
|---|---|---|
| 1. Poydevor | tayyor | 20 |
| 2. Kurs tuzilmasi | tayyor | 43 |
| 3. Vazifalar banki | tayyor | 96 |
| 4. Yechimlar va tekshiruv | — | |
| 5. Sahifalar (UI) | — | |
| 6. Baholash va reyting | — | |
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
