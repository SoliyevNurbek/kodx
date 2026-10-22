# Bajarilish holati

Sessiya uzilsa — ish shu fayldan davom ettiriladi. Reja: `docs/MASTER_PROMPT.md`.

| Bosqich | Holat | Testlar |
|---|---|---|
| 1. Poydevor | tayyor | 20 |
| 2. Kurs tuzilmasi | tayyor | 43 |
| 3. Vazifalar banki | jarayonda (branch stage-3-problems) | |
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

## 3-bosqich — Vazifalar banki (JARAYONDA, `stage-3-problems` branch)
Tayyor:
- `judge` ilovasi: types (Verdict, Limits…), checker (exact/whitespace/float), JudgeBackend,
  LocalDevBackend (Windows Job Object: xotira + 1 jarayon; venv o‘rniga asosiy python), Judge0Backend.
  Qo‘lda tekshirildi: AC/WA/TLE/RE/MLE/CE, UTF-8, subprocess taqiqlangan, django import qilinmaydi.
- `problems` modellari + 0001 migratsiya, admin, markdown.py (nh3 + LaTeX himoyasi),
  importer.py, `import_problems`, `verify_problems`; config/test_runner.py (vaqtinchalik MEDIA_ROOT).
- Seed generator: `tools/seed_gen/` (common.py, m1_code.py). Modul 1 — 36 code masala tayyor
  (`problems/seed/`), har biri etalon yechimda o‘tadi.
Qolgan:
1. `tools/seed_gen/m2_code.py` — 13–24-darslar, 36 code masala (reja: max-min, ortachadan katta,
   siljitish; juftlar, ikkilik qidiruv, ikki yig‘indi; noyob, so‘z chastotasi, telefon kitobi;
   palindrom, unlilar, siqish; faktorial, EKUK, fibonachchi (fast doubling); csv yig‘indi,
   csv eng yaxshi, json; xavfsiz bo‘lish, son tekshir, bank hisob; math ildiz, sana farqi,
   kombinatsiyalar; to‘rtburchak, vektor, kutubxona; shakllar yuzi, xodimlar maoshi, stek;
   snake_case, pep8 qator, branch nomi; anagramma, transpoza, reyting jadvali).
2. 48 ta quiz (5 savol), 24 ta project (25–48) + 12, 24-darslar loyiha himoyasi.
3. `problems/migrations/0002_seed_problems.py` (importer + tarixiy modellar, status=published, is_seed).
4. Testlar: judge (checker, local, judge0 mock), importer, ruxsatlar, seed sifati (har dars vazifali,
   code ≥5 test/2 namuna, etalon 100%). `docs/PROBLEM_FORMAT.md`. DECISIONS: chiqishda ASCII apostrof,
   float checker (abs/rel 1e-6), LocalDevBackend TESTING da ham ruxsat, moderator nashr etadi.
5. ruff, commit, merge, push → 4-bosqich.
