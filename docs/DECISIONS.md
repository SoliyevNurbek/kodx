# Qarorlar jurnali

Har yozuv: sana · qaror · sabab · muqobil variant.

## 2026-10-23 · Ish rejimi
- **Qaror:** MASTER_PROMPT avtonom bajariladi — bosqichlar orasida tasdiq kutilmaydi.
- **Sabab:** loyiha egasining oxirgi aniq ko‘rsatmasi («savol berma, qarorlarni DECISIONS.md ga yoz»).
  CLAUDE.md dagi «har bosqichdan oldin tasdiq kut» qoidasi shu ko‘rsatma bilan almashtirildi.
- **Muqobil:** har bosqichda to‘xtash — egasi aynan buni bekor qildi.

## 2026-10-23 · MASTER_PROMPT.md joyi
- **Qaror:** fayl loyiha ildizida edi, `docs/MASTER_PROMPT.md` ga ko‘chirildi.
- **Sabab:** topshiriqda `docs/MASTER_PROMPT.md` deb ko‘rsatilgan, barcha hujjatlar `docs/` da.
- **Muqobil:** ildizda qoldirish.

## 2026-10-23 · Superuser yaratish
- **Qaror:** `manage.py init_superuser` buyrug‘i yozildi (parol `secrets` bilan, faqat `.env` dagi
  `SUPERUSER_INITIAL_PASSWORD` ga yoziladi, `must_change_password=True`). Buyruqni loyiha egasi
  o‘zi ishga tushiradi.
- **Sabab:** agentning administrator parolini o‘rnatishi Claude Code xavfsizlik tizimi tomonidan
  bloklandi; CLAUDE.md ham «parollarni egasi o‘zi kiritadi» deydi. Seed migratsiya `nurbek` ni
  ishlatib bo‘lmaydigan parol bilan yaratadi — hech kim kira olmaydi, guruh seed’i ishlaydi.
- **Muqobil:** `createsuperuser` — `nurbek` seed’da allaqachon bor bo‘lgani uchun ishlamaydi.

## 2026-10-23 · Admin panelga kirish (is_staff)
- **Qaror:** `is_staff` roldan avtomatik kelib chiqadi: moderator va undan yuqori (yoki superuser).
  Admin ruxsatlari Django model-permission emas, `RoleAdminMixin` orqali rol darajasiga bog‘langan.
- **Sabab:** CLAUDE.md dagi 5 darajali ierarxiya yagona manba bo‘lsin; qo‘lda permission berish shart emas.
- **Muqobil:** Django guruhlari va permission’lari — ikki parallel tizim, xatoga moyil.

## 2026-10-23 · Moderatorning admin chegaralari
- **Qaror:** moderator faqat o‘zidan past darajadagi foydalanuvchini tahrirlaydi, faqat user/jury/jury_pro
  rolini beradi, foydalanuvchini o‘chira olmaydi, audit jurnalini ko‘rmaydi (u super admin paneli).
  Kurs/modul/darsni moderator ko‘radi, faqat super admin o‘zgartiradi.
- **Sabab:** CLAUDE.md rollar jadvali; kurs tuzilmasi seed bilan boshqariladi.
- **Muqobil:** moderatorga to‘liq admin — ruxsatlar eskalatsiyasi xavfi.

## 2026-10-23 · Guruh qoidalari
- **Qaror:** «bitta kursda bitta faol guruh» `GroupMember.clean()` da tekshiriladi va `save()` da ham
  chaqiriladi (admin, shell, servis — barchasi uchun bir xil).
- **Sabab:** jadvallararo cheklovni MySQL da UNIQUE bilan ifodalab bo‘lmaydi.
- **Muqobil:** denormalizatsiya (`course_id` + `active_flag` ustunlari) — keyin kerak bo‘lsa.

## 2026-10-23 · Dars raqami
- **Qaror:** `Lesson.number` butun kurs bo‘yicha uzluksiz (1–48); DB da `(module, number)` unikal,
  kurs bo‘yicha unikallik `clean()` da.
- **Sabab:** CLAUDE.md dagi numeratsiya; o‘qituvchilar darsni raqami bilan ataydi.

## 2026-10-23 · Lint va qaramliklar
- **Qaror:** ruff (line-length 120, E/F/W/I/B/UP/DJ). Avtomatik generatsiya qilingan `0001_*`
  migratsiyalar tekshiruvdan chiqarilgan. `requirements.txt` — runtime, `requirements-dev.txt` — ruff, coverage.
- **Sabab:** generatsiya qilingan kodni qo‘lda formatlash ma’nosiz.

## 2026-10-23 · README dagi «judge» nomi
- **Qaror:** egasining GitHub’dagi README tahriri (jury → judge, 2–3-qatorlar) o‘zgartirilmasdan
  merge qilindi. Koddagi rol identifikatorlari `jury`/`jury_pro` qoldi.
- **Sabab:** CLAUDE.md va MASTER_PROMPT — ustuvor spetsifikatsiya, ularda `jury`. Koddagi nomni
  o‘zgartirish migratsiya va barcha hujjatlarni o‘zgartirishni talab qiladi; egasining tahriri
  qisman (4-qatorda «jury» qolgan), shuning uchun niyat aniq emas.
- **Muqobil:** butun loyihada `judge` ga o‘tish — egasi xohlasa, `Role` label’larini o‘zgartirish
  yetarli (DB da raqam saqlanadi, migratsiya oddiy).

## 2026-10-23 · Judge arxitekturasi (3-bosqich)
- **Qaror:** `judge` ilovasi — `JudgeBackend.submit(code, lang, tests, limits)`, `LocalDevBackend`, `Judge0Backend`
  (batch API, `urllib`, qo‘shimcha kutubxonasiz). Chiqishni solishtirish har doim bizning `checker` da
  (Judge0 ga `expected_output` yuborilmaydi) — ikkala backend bir xil natija beradi.
- **Sabab:** adapter naqshi (MASTER_PROMPT §3); tekshirish mantiqi bitta joyda.

## 2026-10-23 · LocalDevBackend cheklovlari
- **Qaror:** Windows’da Job Object (xotira chegarasi, faqat 1 jarayon — subprocess/fork taqiqlanadi, eng yuqori
  xotira o‘lchanadi), POSIX’da `setrlimit`. venv’dagi `python.exe` o‘rniga asosiy interpretator
  (`sys._base_executable`) — venv launcher bola jarayon ochadi va Job Object uni bloklaydi; foydali yon ta’sir:
  foydalanuvchi kodi Django va loyiha paketlarini ko‘rmaydi. `-I -X utf8`, minimal env, vaqtinchalik papka.
  Interpretator ishga tushish vaqti (~20 ms) vaqt chegarasiga kiradi.
- **Ruxsat:** `DEBUG=True` yoki test jarayoni (`settings.TESTING`, test runner qo‘yadi). Django test runner
  DEBUG’ni majburan o‘chiradi, shuning uchun alohida belgi kerak bo‘ldi.
- **Muqobil:** Docker sandbox — Windows/OpenServer muhitida og‘ir; production’da Judge0 baribir alohida.

## 2026-10-23 · Float checker
- **Qaror:** `float` rejimida absolyut YOKI nisbiy xato ≤ epsilon (`math.isclose`), son bo‘lmagan tokenlar aniq.
- **Sabab:** Codeforces/Polygon standarti.

## 2026-10-23 · Vazifa ruxsatlari
- **Qaror:** ko‘rish — nashr etilgan hammaga, qoralama muallif va moderator+; yopiq testlar va etalon yechim —
  muallif (Jury Pro) va moderator+; tahrirlash — muallif (agar hali Jury Pro bo‘lsa) va super admin;
  nashr etish — moderator+. Moderator boshqaning vazifasini tahrirlamaydi, faqat holatini o‘zgartiradi.
- **Sabab:** CLAUDE.md: Jury Pro faqat o‘z masalasini, moderator hammasini ko‘radi.

## 2026-10-23 · Seed kontent
- **Qaror:** 146 vazifa (`problems/seed/`, PROBLEM_FORMAT bo‘yicha) — 72 code, 48 quiz, 26 project. Data migratsiya
  umumiy `importer` orqali tarixiy modellar bilan yuklaydi (mavjud bo‘lmagan maydonlar o‘tkazib yuboriladi — kelajakdagi
  model o‘zgarishlari eski migratsiyani buzmaydi). `.out` fayllar etalon yechimdan generatsiya qilingan, namunalar
  qo‘lda yozilgan javob bilan solishtirilgan (`tools/seed_gen/`). Test har safar 72 ta etalon yechimni
  LocalDevBackend’da ishga tushiradi (~12 s).
- **Chiqishdagi o‘zbekcha so‘zlar:** oddiy apostrof (`yo'q`) — o‘quvchi klaviaturadan shuni teradi; matnlarda (shart)
  to‘g‘ri belgilar (o‘, g‘, ’). Iloji boricha chiqish so‘zlarida apostrof ishlatilmagan.
- **Darsga biriktirish:** oson — sinf ishi, o‘rta — uyga vazifa, challenge — qo‘shimcha (majburiy emas);
  quiz — sinf ishi; loyiha — uyga vazifa. Ball: code `difficulty × 100`, quiz 50, loyiha 100.
- **Testlar media’si:** test runner MEDIA_ROOT’ni vaqtinchalik papkaga almashtiradi (seed migratsiya ham u yerga yozadi).
