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

## 2026-10-23 · Yechimlar (4-bosqich)
- **Navbat:** `JudgeQueue` interfeysi + `DatabaseQueue` (`SELECT … FOR UPDATE SKIP LOCKED`, MySQL 8). Bir nechta
  worker parallel ishlashi mumkin. Redis/Celery — `JUDGE_QUEUE` sozlamasini almashtirish orqali.
  Muqobil: Celery hozirdanoq — OpenServer muhitida Redis qo‘shimcha xizmat talab qiladi, MVP uchun ortiqcha.
- **Rate limit:** bazadagi oxirgi 60 soniyadagi yechimlar soni (6 ta). Kesh/Redis shart emas, bir nechta
  web-jarayonda ham to‘g‘ri ishlaydi.
- **Kod hajmi:** 64 KB — UTF-8 baytlarida (belgilarda emas).
- **Ball:** `problem.points × (o‘tgan testlar bali / jami test bali)`, butunga yaxlitlangan (IOI uslubi).
  Yakuniy verdikt — birinchi muvaffaqiyatsiz test verdikti.
- **Quiz:** javoblar savol/variant *tartib raqami* bilan saqlanadi (ID emas) — re-import savollarni qayta yaratsa ham
  eski urinishlar ma’nosini yo‘qotmaydi. `multiple` — to‘plam aynan mos bo‘lsa ball (qisman ball yo‘q).
  `text` — katta-kichik harf va chetdagi bo‘shliqlarsiz.
- **Loyiha:** faqat `https://github.com/<egasi>/<repo>` havolalari; har qayta topshirish — yangi yozuv (tarix saqlanadi);
  moderator «Qayta ishlash kerak» holatini berishi mumkin. «Yechilgan» = kamida bitta «Baholandi».
- **Kod ko‘rinishi:** egasi va moderator+ — doim; boshqalar — o‘zi masalani yechgan bo‘lsa yoki kontest tugagan bo‘lsa.
- **Kontest maydoni:** `Submission.contest` 7-bosqichda (kontest modeli bilan birga) qo‘shiladi; ko‘rinish qoidasi
  allaqachon `_contest_finished()` ilgagi orqali tayyor.
- **Worker:** ishga tushganda 5 daqiqadan eski `running` yechimlarni navbatga qaytaradi; backend xatosi worker’ni
  yiqitmaydi — yechim «Ichki xato» oladi.

## 2026-10-23 · UI (5-bosqich)
- **Tuzilma:** `core` (SiteSettings singleton, bosh sahifa, context processor, majburiy parol almashtirish middleware),
  `panel` (rol panellari); sahifa view'lari tegishli ilovalarda. URL’lar o‘zbekcha (`/masalalar/`, `/urinishlar/`).
- **Frontend:** Tailwind Play CDN (3.4.17), HTMX 2.0.4 (unpkg), CodeMirror 6 (esm.sh, dinamik import),
  KaTeX 0.16.11 (jsdelivr). CodeMirror yuklanmasa, oddiy `<textarea>` ishlaydi (progressiv yaxshilash).
  Mavzu ranglari CSS o‘zgaruvchilarida (`--kx-bg/accent/gold`), super admin paneldan o‘zgaradi; qiymatlar
  `#RRGGBB` validatori bilan (CSS injection’ning oldi olinadi). Inline `on*` handler’lar yo‘q — `data-confirm`,
  `data-autosubmit` (8-bosqichdagi CSP uchun).
- **Jonli natija:** HTMX `hx-trigger="every 2s"` faqat yechim tugamaguncha; tugagach qisman shablon polling’siz qaytadi.
- **Yopiq testlar:** o‘quvchi faqat namunaviy testlardagi chiqish/xatoni ko‘radi; yopiq testlar — faqat verdikt.
- **Etalon yechim bilan tekshirish (Jury Pro paneli):** oddiy yechim sifatida navbatga qo‘yiladi — web jarayonda
  kod bajarilmaydi.
- **Test yuklash:** faqat .in/.out/.txt, ≤ 5 MB, UTF-8 (8-bosqich talabi oldinroq bajarildi).
- **Top-10 / reyting sahifasi:** hozircha yechilgan code masalalar soni; 6-bosqichda mashq bali bilan almashtiriladi.
- **Parolni tiklash:** email konsolga (dev). Emaili yo‘q o‘quvchi — o‘qituvchi orqali (8-bosqich: vaqtinchalik parol).
- **i18n:** barcha shablon matnlari `{% translate %}` ichida, `LANGUAGES=[uz]`, `LOCALE_PATHS` tayyor (ru/en keyin).

## 2026-10-23 · Baholash va reyting (6-bosqich)
- **Kurs bahosi** (`grading.course_grade`, musobaqa reytingidan alohida): modul = davomat + mustaqil vazifalar +
  test + loyiha (standart 2,5 + 5 + 2,5 + 10; `GradingPolicy` da kurs bo‘yicha sozlanadi).
  - Faqat **majburiy** (`is_required`) va nashr etilgan vazifalar; challenge baholanmaydi.
  - Har vazifa — eng yaxshi natija ulushi; muddatdan keyingi topshiriq `late_penalty_percent` ga kamaytiriladi
    (standart 20%). Loyiha — faqat «Baholandi» holati («Qayta ishlash kerak» hisobga olinmaydi).
  - Davomat maxraji — guruhda davomat **olingan** darslar (kelajakdagi darslar jarimaga olib kelmaydi).
  - Decimal, 0,01 gacha yaxlitlash.
- **Mashq bali:** birinchi marta yechilgan vazifalar ballari yig‘indisi (code `difficulty×100`, quiz 50, loyiha 100).
  `PracticeStats` da denormalizatsiya; judge (AC), quiz (100%) va loyiha baholashdan keyin yangilanadi;
  `manage.py recalculate_practice` — to‘liq qayta hisob.
- **Seriya (streak):** *birinchi yechim* sanalari (mahalliy vaqt) bo‘yicha; bugun hali yechmagan o‘quvchining joriy
  seriyasi kechagacha saqlanadi. Muqobil: istalgan AC — eski masalani qayta yechib seriyani «ushlab turish» mumkin bo‘lardi.
- **Nishonlar:** 12 ta (birinchi yechim, 10/50/100, 7/30 kun seriya, 5 challenge, birinchi loyiha, 4 ta modul).
  Qoidalar kodda (`grading.practice.BADGES`), seed migratsiya bilan bazaga yoziladi; berish idempotent.
- **Kontest reytingi:** Codeforces uslubidagi Elo (`grading.rating`): kutilgan o‘rin → maqsadli reyting (ikkilik qidiruv),
  delta/2, inflyatsiyaga qarshi tuzatishlar. Boshlang‘ich 1200 — `User.rating` default o‘zgartirildi va mavjud 0 lar
  1200 ga ko‘chirildi (1-bosqichdagi «0» qarori MASTER_PROMPT bilan almashtirildi). `RatingHistory` modeli kontest
  modeliga FK bo‘lgani uchun 7-bosqichda (kontestlar bilan) qo‘shiladi; profil shabloni unga tayyor.
- **Reyting jadvallari:** umumiy, haftalik (oxirgi 7 kunda birinchi yechimlar), guruh, kurs; teng ball — bir xil o‘rin.
- **Davomat:** o‘qituvchi panelida dars bo‘yicha belgilanadi (audit). CSV eksport UTF-8 BOM bilan (Excel uchun).

## 2026-10-23 · Kontestlar (7-bosqich)
- **ICPC:** o‘rin — yechilganlar soni (kamayish), keyin jarima (o‘sish). Jarima = birinchi AC daqiqasi +
  `penalty_minutes` × undan oldingi noto‘g‘ri urinishlar; CE va IE jarima bermaydi; AC dan keyingi urinishlar e’tiborsiz.
  Har masalani birinchi yechgan ishtirokchi belgilanadi.
- **IOI:** har masala bo‘yicha eng yaxshi ball, kontest masalasi baliga moslashtirilgan
  (`cp.points × submission.score / problem.points`).
- **Teng natija** — bir xil o‘rin (1, 1, 3). Faqat ro‘yxatdan o‘tgan ishtirokchilar va kontest vaqtidagi yechimlar.
- **Muzlatish:** oxirgi `freeze_minutes` da boshqaruvchi bo‘lmaganlar uchun muzlatishdan keyingi yechimlar «?» (kutilmoqda);
  kontest tugashi bilan avtomatik ochiladi. Boshqaruvchi (egasi/moderator) doim jonli jadvalni ko‘radi.
- **Ko‘rinish:** ochiq / guruh (faqat faol a’zolar) / parol (Argon2 xesh, `make_password`). Masalalar: boshlanishdan
  oldin — faqat boshqaruvchiga; kontest paytida — ishtirokchilarga; tugagach — kontestni ko‘ra oladigan hammaga.
  Kontestga qoralama masala qo‘shish mumkin — `create_submission(contest=...)` masala ko‘rinishini kontest qoidalari
  bo‘yicha tekshiradi.
- **Kontest masalasini qo‘shish:** foydalanuvchi ko‘ra oladigan code masala (nashr etilgan yoki o‘z qoralamasi; moderator — hammasi).
  Yechim yuborilgan masalani olib tashlash taqiqlangan (natijalar buzilmasligi uchun).
- **Reytingli kontest:** `is_rated` ni faqat moderator yoqadi (Jury formasida o‘chirilgan).
- **Reyting avtomatik:** judge worker bo‘sh paytda (har 30 sikl) va `manage.py apply_contest_ratings` (cron) —
  tugagan, reytingli, navbatda tekshirilmagan yechimi qolmagan kontestlar. Kamida bitta yechim yuborganlar hisoblanadi.
  `select_for_update` bilan bir martalik; `RatingHistory` — profilda SVG grafik.
- **Jonli jadval:** HTMX har 15 soniyada (faqat kontest davomida).
- **Seed:** «Kirish kontesti» (2026-11-01 10:00, ICPC, 120 daqiqa, 30 daqiqa muzlatish, A–D modul 1 masalalari).

## 2026-10-23 · Rollar oqimi va xavfsizlik (8-bosqich)
- **Rol so‘rovi UI:** o‘quvchi profil → «Rol so‘rash» (Jury; Jury → Jury Pro), sabab bilan; bir vaqtda bitta kutilayotgan
  so‘rov; moderator panelda tasdiqlaydi (audit).
- **Vaqtinchalik parol:** moderator+ o‘zidan past darajadagi foydalanuvchiga beradi. Parol tizim tomonidan generatsiya
  qilinadi (chalkash belgilarsiz), **faqat bir marta** shu javobda ko‘rsatiladi (`Cache-Control: no-store`), bazada —
  faqat xesh, auditga parol yozilmaydi; `must_change_password=True`. CLAUDE.md dagi «hech kim parolni ko‘ra olmaydi»
  qoidasi saqlanadi: foydalanuvchining *o‘z* paroli hech qachon ko‘rinmaydi — bu yangi bir martalik parol.
  Admin paneldagi «parolni o‘rnatish» sahifasi yopiqligicha qoladi.
- **2FA (TOTP, django-otp):** super admin `/panel/` va `/admin/` ga faqat 2FA tasdiqlangan sessiyada kiradi; qurilma
  bo‘lmasa — QR (SVG, server tomonida) bilan ulash sahifasi. django-otp throttling’i (noto‘g‘ri koddan keyin kutish) yoqiq.
  Testlarda boshqa super admin testlari `KODX_REQUIRE_SUPERADMIN_2FA=False` bilan, 2FA oqimi alohida testlangan.
  ⚠️ Egasi: `nurbek` birinchi kirishda telefonda autentifikator ilova bilan QR-kodni skanerlaydi.
- **Kirish cheklovi:** barcha foydalanuvchilar uchun — 15 daqiqada 5 ta xato urinish → vaqtincha blok (to‘g‘ri parol ham
  qabul qilinmaydi); muvaffaqiyatli kirish hisobni yangilaydi; vaqtinchalik parol berilganda blok olib tashlanadi;
  super admin akkauntiga xato urinishlar auditga yoziladi. Hisob bazada (`LoginAttempt`), kesh shart emas.
  Muqobil: django-axes — qo‘shimcha qaramlik, oddiy ehtiyoj uchun ortiqcha.
- **Ko‘chirmachilik:** `manage.py check_similarity [--problem] [--contest] [--threshold 0.85]` — har foydalanuvchining
  oxirgi qabul qilingan yechimi; Python `tokenize` bilan normallashtirish (izohlar olib tashlanadi, nomlar/sonlar/satrlar
  umumiy belgiga) + `SequenceMatcher`; 15 tokendan qisqa yechimlar solishtirilmaydi. Natijalar faqat moderator panelida.
  Kod bajarilmaydi.
- **CSP:** har so‘rovga nonce; `script-src` da `unsafe-inline`/`unsafe-eval` yo‘q; ruxsat etilgan CDN’lar aniq ro‘yxatda;
  `style-src 'unsafe-inline'` — Tailwind Play CDN uslublarni dinamik qo‘shgani uchun (Tailwind build’ga o‘tilganda olib
  tashlanadi). `frame-ancestors 'none'`, `X-Frame-Options: DENY`, `nosniff`, `Referrer-Policy: same-origin`.
- **Prod sozlamalari:** `config/settings_prod.py` — DEBUG o‘chiq, HTTPS redirect, HSTS (1 yil, preload), Secure/HttpOnly
  cookie’lar, nginx orqasida `X-Forwarded-Proto`, Judge0 majburiy, SMTP. `check --deploy` ogohlantirishsiz (test bilan).
- **Fayl yuklash:** test fayllari .in/.out/.txt, ≤ 5 MB, UTF-8 (5-bosqich); avatar ≤ 2 MB, ImageField (Pillow tekshiradi);
  `FILE_UPLOAD_MAX_MEMORY_SIZE`/`DATA_UPLOAD_MAX_MEMORY_SIZE` chegaralari.

## 2026-10-23 · Sifat va hujjatlar (9-bosqich)
- **CI (GitHub Actions):** Ubuntu 24.04 + MySQL 8.0 servisi; `kodx_user` (MYSQL_USER) — loyiha root bilan ishlamaydi,
  root faqat CI konteynerida `test_kodx` ga GRANT berish uchun. venv majburiy: LocalDevBackend foydalanuvchi kodini
  asosiy interpretatorda (venv paketlarisiz) ishga tushiradi. Qadamlar: ruff, `makemigrations --check`, testlar,
  `coverage report --fail-under=80`, `check --deploy` (prod sozlamalari).
- **Coverage:** `config/settings_prod.py`, migratsiyalar, testlar va `tools/` hisobga olinmaydi. Natija ~95%.
- **seed_demo:** faqat DEBUG (yoki testda); `demo` prefiksli foydalanuvchilar, standart holatda kirib bo‘lmaydi
  (`--password` bilan umumiy parol); determinik (`--seed`); `--reset` faqat demo ma’lumotlarni o‘chiradi. Yechimlar
  sintetik (judge’siz) — demo jadvallar uchun. Egasining dev bazasida bir marta ishga tushirildi (20 o‘quvchi).
- **POSIX xotira chegarasi:** `RLIMIT_AS` = limit + 64 MB (interpretatorning virtual xotirasi uchun zaxira).
- **Admin `date_hierarchy` olib tashlandi:** MySQL vaqt zonasi jadvallari yuklanmagan serverlarda (OpenServer odatda)
  `CONVERT_TZ` NULL qaytaradi va sahifa yiqiladi. Statistikalar ham shu sababli Python’da hisoblanadi.
- **README dagi rol nomlari:** egasining `judge`/`judge_pro` tahriri saqlandi; koddagi identifikatorlar izohda ko‘rsatildi.

## 2026-10-23 · Landing hero (branch `landing-hero`)
- **Maket:** `docs/design/landing-mockup.jfif` haqiqiy o‘lchami 2752×1536 (vazifadagi 2576×1438 emas). Muallif surati
  `scripts/make_hero_image.py` bilan qirqildi: **x 1680–2390, y 205–1130** (710×925). Chap chegara h1 matni («…sala»,
  x ≤ 1665), o‘ng — ICPC/IT Park logotiplari va ikonkalar (x ≥ 2400), past — «KURS MUALLIFI» kartasi (y ≥ 1143),
  yuqori — breadcrumb qatori (y ≤ 186). Chap yelkaning bir qismi kesildi — logotip/matn tushmasligi ustun.
  Koordinatalar maket boshqa o‘lchamda saqlansa mutanosib o‘zgaradi.
- **Upscale:** kesim 710 px kenglikda, 1200w WebP LANCZOS bilan kattalashtiriladi (sifati 800w dan yaxshi emas).
  Haqiqiy surat `static/img/hero-nurbek-source.png` qo‘yilsa, skript uni butunligicha ishlatadi.
- **Egasining sidebar ishi:** ishchi nusxadagi commit qilinmagan sidebar/sahifa dizayni («Sidebar o‘zgarmaydi»)
  branch’ning birinchi commit’i sifatida saqlandi; landing maketi ham shu commit’da.
- **«Panel» havolasi** sidebar’da faqat moderator+ ga ko‘rinadi (avval jury/jury_pro ham). Jury/Jury Pro panelga
  `/panel/` orqali kirish huquqini saqlaydi — faqat havola yashirildi.
- **Statistika:** seed hisobi uchun `User.is_seed` maydoni qo‘shildi (`seed_demo` belgilaydi; migratsiya mavjud
  `demoNN` akkauntlarni belgilaydi). `is_seed` akkauntlar va ularning yechimlari hisoblanmaydi. `Problem.is_seed`
  (kursning seed vazifalari) — haqiqiy kontent, «vazifalar» ga kiradi; faqat `published`. Kesh — 10 daqiqa
  (`kodx:site_counters`, standart LocMem kesh).
- **Kicker** matni `site.tagline` dan olinadi (standart qiymati — «Dasturlash va sun’iy intellekt asoslari»,
  CSS bilan katta harf). Muallif kartasi matnlari — `SiteSettings.hero_author_*` (panel → Tizim sozlamalari va admin).
- **«Kursni boshlash»:** mehmon → ro‘yxatdan o‘tish (o‘chirilgan bo‘lsa — kirish); kirgan → kurs sahifasi
  (kurs yo‘q bo‘lsa — masalalar). «1-dars BEPUL!» — bitta, CTA o‘ramida absolute; 1-dars yo‘q bo‘lsa ko‘rinmaydi.
- **h1 o‘lchami:** spetsifikatsiyadagi `clamp(2.5rem, 1rem + 4vw, 4.5rem)` sidebar bilan chap ustunga sig‘maydi
  («Dasturlashni» 4.5rem da ~480 px), shuning uchun `min(clamp(…), 9.2cqi)` (≥ 768px, majburiy 2 qator) va
  `min(clamp(…), 14cqi)` (telefon, erkin o‘tish) — ustun kengligiga nisbatan cheklov.
- **Mavzular:** hero chap qismi yorug‘ mavzuda och fon + to‘q matn (oltin #8A6417, cyan raqam #0E7490 — kontrast
  ≥ 5:1), qorong‘ida maketdagidek to‘q ko‘k. O‘ng «sahna» ikkala mavzuda to‘q (surat foni). Tokenlar —
  `static/css/hero.css` boshida (`--hero-*`), brend ranglari sayt sozlamalaridan (`--kx-*`).
- **Hamkor logotiplari** (ICPC, IT Park) va «Python AI & Web» yozuvi qo‘shilmadi; ikonkalar (Python, VS Code, GitHub,
  AI) — inline SVG. Bosh sahifadagi modullar/Top-10 blokidagi yorug‘ mavzuda ko‘rinmay qolgan oq matnlar tuzatildi.
