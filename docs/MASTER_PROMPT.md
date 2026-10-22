# kodx.uz — to‘liq platformani qurish bo‘yicha MASTER TOPSHIRIQ

Avval CLAUDE.md ni to‘liq o‘qi. U loyihaning konteksti, rollari va qoidalari.
Ushbu fayl — bajarish rejasi. 1-bosqich (poydevor: Django, MySQL, rollar, audit) tayyor.

---

## 0. ISHLASH REJIMI — AVTONOM

- **Menga savol berma.** Har noaniqlikda professional standartga mos eng oqilona qarorni o‘zing qabul qil
  va uni `docs/DECISIONS.md` ga yoz: sana, qaror, sabab, muqobil variant.
- Har bosqich sikli:
  1. `git checkout -b stage-N-nomi`
  2. Kod
  3. Migratsiyalar
  4. Testlar (`python manage.py test`) — hammasi o‘tishi shart
  5. `ruff check .` toza
  6. Commit
  7. `main` ga merge
  8. `git push`
  9. Keyingi bosqich
- Har bosqich oxirida `docs/PROGRESS.md` ni yangila: nima qilindi, testlar soni, keyingi qadam.
  Sessiya uzilsa, ish shu fayldan davom ettiriladi.
- Xato chiqsa — o‘zing tahlil qil va tuzat. 3 urinishdan keyin ham hal bo‘lmasa, PROGRESS.md ga
  «bloklangan» deb yoz va keyingi mustaqil vazifaga o‘t.
- Har bosqich oxirida 5–8 qatorlik qisqa hisobot yoz.

## 1. HECH QACHON QILMA (qat’iy chegaralar)

- `.env` ni ekranga chiqarma, o‘qib ko‘rsatma, commit qilma. Har commit’dan oldin `git status` bilan tekshir.
- MySQL `root` dan loyihada foydalanma — faqat `kodx_user`.
- Foydalanuvchi kodini Django veb-jarayonining ichida ishga tushirma (3-bosqichdagi Judge arxitekturasiga qara).
- `git push --force`, tarixni qayta yozish, ma’lumotlarni o‘chiruvchi migratsiyalar — taqiqlanadi.
- Testlarni o‘chirib yoki «skip» qilib o‘tkazib yuborma.

## 2. SUPERUSER

- Superuser’ni o‘zing yarat:
  - login: `nurbek`, roli: `superadmin`.
  - Parol: Python `secrets` bilan tasodifiy 20 belgi. Uni faqat `.env` ga
    `SUPERUSER_INITIAL_PASSWORD=` qatoriga yoz, ekranga chiqarma.
  - Yaratish: `DJANGO_SUPERUSER_PASSWORD` muhit o‘zgaruvchisi bilan
    `createsuperuser --noinput`.
  - `must_change_password=True` qo‘y — birinchi kirishda parol majburan almashtiriladi.
- README’ga yoz: «Boshlang‘ich parol .env dagi SUPERUSER_INITIAL_PASSWORD da; birinchi kirishdan
  keyin almashtiriladi va bu qatorni .env dan o‘chiring».

## 3. ARXITEKTURA QARORLARI (o‘zgartirma)

- **Backend:** Django 5.2, MySQL 8 (utf8mb4).
- **Frontend:**
  - Django shablonlari + HTMX + Tailwind CSS (CDN, keyin build).
  - Kod muharriri: CodeMirror 6 (CDN).
  - Interfeys matnlari — o‘zbekcha (lotin), barcha shablonlarda Django i18n
    (keyin rus/ingliz qo‘shish uchun).
- **Dizayn:**
  - qorong‘i va yorug‘ mavzu;
  - responsiv (375 / 768 / 1440 px);
  - kurs ranglari — fon `#0E1A2E`, aksent `#22D3EE`, oltin `#D9B25F`.
- **Judge (kodni tekshirish) — `judge` ilovasi, adapter naqshi:**
  - `JudgeBackend` interfeysi: `submit(code, lang, tests, limits) → natijalar`.
  - `Judge0Backend` — production uchun (`JUDGE0_URL`, `JUDGE0_TOKEN` .env dan).
  - `LocalDevBackend`:
    - faqat `DEBUG=True` da ishlaydi;
    - alohida jarayonda (subprocess), timeout, xotira chegarasi va vaqtinchalik papka bilan;
    - faqat Python;
    - kodda va README’da «production uchun EMAS» deb belgilansin.
  - Yechimlarni tekshirish — navbat orqali, web so‘rovni bloklamasdan:
    - dev’da DB-asosidagi oddiy navbat + `manage.py run_judge_worker` buyrug‘i;
    - keyin Redis/Celery’ga o‘tish uchun interfeys tayyor tursin.
- **Ruxsatlar:**
  - `RoleRequiredMixin` va `@role_required` — CLAUDE.md dagi 5 daraja.
  - Ob’ekt darajasida: Jury Pro faqat o‘z masalalari, Jury faqat o‘z kontestlari.
  - Har ruxsat uchun test.

## 4. BOSQICHLAR VA QABUL MEZONLARI

### 2-bosqich — Kurs tuzilmasi
- **Modellar:** Course, Module, Lesson, Group, GroupMember.
  - Lesson turlari: dars / loyiha himoyasi / Demo Day.
- **Seed (data migratsiya, qayta ishga tushirsa dublikatsiz):**
  - 1 kurs, 4 modul, 48 dars — nomlar CLAUDE.md dan.
  - 1 ta namunaviy guruh: «Python-1», o‘qituvchisi `nurbek`.
- **Qoidalar:**
  - Guruh va a’zolarni moderator va undan yuqori boshqaradi;
    `Group.teacher` kamida moderator bo‘ladi.
  - O‘quvchi bir nechta guruhda bo‘lishi mumkin, lekin bitta kursda faqat bitta faol guruhda.
- **Mezon:** 48 dars, testlar o‘tadi, admin’da ko‘rinadi.

### 3-bosqich — Vazifalar banki (3 tur)
- **Problem:**
  - type: `code` / `quiz` / `project`;
  - author, difficulty (1–5), points, tags, holat (qoralama → ko‘rib chiqishda → nashr etilgan);
  - shart (Markdown, LaTeX formulalari);
  - kirish/chiqish formati, namunalar;
  - time_limit, memory_limit.
- **TestCase:**
  - kirish va chiqish fayllari `media/tests/` da, bazada faqat yo‘l;
  - namuna yoki yopiq; ball; tartib.
  - Chiqishni solishtirish: aniq, bo‘shliqlarni hisobga olmasdan, sonlar uchun epsilon bilan.
- **Quiz:** QuizQuestion (bitta javob / ko‘p javob / qisqa matn), QuizOption.
- **Project:** baholash rubrikasi (mezon, ball) — JSON yoki alohida model.
- **LessonProblem:**
  - dars ↔ vazifa; turi: sinf ishi / uyga vazifa / qo‘shimcha (challenge);
  - muddat; majburiylik.
- **Import tizimi** — `manage.py import_problems <papka>`:
  - format: `problems/<slug>/problem.yaml`, `statement.md`, `tests/01.in`, `tests/01.out` …
  - Shu formatda `docs/PROBLEM_FORMAT.md` yoz — o‘qituvchi o‘z masalalarini shu yo‘l bilan qo‘shadi.
- **Seed kontent** (data migratsiya, holati «nashr etilgan», muallifi `nurbek`, `is_seed=True` belgisi bilan):
  - **Modul 1–2:**
    - har darsga kamida 3 ta `code` masala (oson / o‘rta / challenge), har birida
      kamida 5 ta test (2 namuna + 3 yopiq);
    - mavzu dars nomiga mos bo‘lsin: arifmetika, if, match-case, for, while, list, saralash,
      dict, satrlar, funksiyalar, fayl mantiqi (stdin orqali), xatolar, OOP — sof mantiq,
      stdin/stdout.
    - Har darsga 5 savollik `quiz`.
  - **Modul 3–4:**
    - har darsga 5 savollik `quiz` va 1 ta `project` topshiriq (GitHub havolasi, rubrika bilan);
    - 12, 24, 36, 48-darslar — loyiha himoyasi topshiriqlari.
  - **Sifat:** har seed masala uchun etalon yechim (`solution.py`) yoz va barcha testlarni
    LocalDevBackend’da avtomatik o‘tkazib tekshir. O‘tmagan seed masala qabul qilinmaydi.
- **Mezon:**
  - 48 darsning har birida vazifalar bor;
  - barcha `code` seed’lar etalon yechimda 100% o‘tadi;
  - import buyrug‘i namunaviy papka bilan ishlaydi.

### 4-bosqich — Yechimlar va avtomatik tekshiruv
- **Modellar:**
  - Submission: user, problem, lesson (ixtiyoriy), contest (ixtiyoriy), til, kod, holat,
    verdict, ball, vaqt, xotira, yaratilgan vaqt.
  - SubmissionResult: har test natijasi.
- **Verdiktlar:** Accepted, Wrong Answer, Time Limit Exceeded, Memory Limit Exceeded,
  Runtime Error, Compilation Error, Internal Error — o‘zbekcha nomlari bilan.
- **Tillar:** Python 3 (MVP). Arxitektura C++/JS qo‘shishga tayyor.
- **Quiz:** javoblar avtomatik baholanadi.
- **Project:**
  - o‘quvchi GitHub havolasini yuboradi;
  - moderator rubrika bo‘yicha baholaydi va izoh yozadi;
  - qayta topshirish mumkin.
- **Cheklovlar:**
  - yechim yuborish rate limit — 1 daqiqada 6 ta;
  - kod hajmi ≤ 64 KB.
- **Ko‘rish huquqlari:**
  - o‘quvchi o‘z urinishlarini ko‘radi;
  - boshqalarning kodini — faqat o‘zi masalani yechgandan keyin yoki kontest tugagandan keyin;
  - moderator va undan yuqori — hammasini.
- **Mezon:** to‘g‘ri / noto‘g‘ri / TLE / RE yechimlar uchun testlar; worker ishlaydi; quiz baholanadi.

### 5-bosqich — Sahifalar (UI)
- **Umumiy sahifalar:**
  - Bosh sahifa: kurs, modullar, statistikalar, top-10.
  - Ro‘yxatdan o‘tish va login; parolni tiklash (email konsolga, dev).
  - Profil:
    - ochiq qism: username, avatar, reyting, yechilganlar soni, faollik kalendari,
      nishonlar (badges);
    - shaxsiy kontaktlar boshqalarga ko‘rinmaydi.
  - Kurs → modul → dars sahifasi: vazifalar ro‘yxati, holati (yechilgan / urinilgan / yangi), muddatlar.
  - Masala sahifasi: shart, namunalar, CodeMirror muharriri, «Yuborish», jonli natija (HTMX polling).
  - Quiz sahifasi; project topshirish sahifasi.
  - «Mening urinishlarim»; urinish tafsiloti (testlar bo‘yicha natija).
- **Rol panellari:**
  - O‘qituvchi (moderator):
    - guruhlar, o‘quvchilar progressi jadvali (dars × o‘quvchi);
    - yechimlar oqimi; project baholash navbati;
    - Jury so‘rovlari, rol berish.
  - Jury Pro: o‘z masalalari — yaratish va tahrirlash (shart, testlar yuklash, etalon yechim
    bilan tekshirish), ko‘rib chiqishga yuborish.
  - Super admin: tizim sozlamalari (sayt nomi, mavzu ranglari, ro‘yxatdan o‘tish yoqilgan/o‘chiq),
    audit jurnali, tizim holati (worker, navbat uzunligi).
- **Mezon:** har sahifa uchun view testlari (ruxsat bor / yo‘q), mobil ko‘rinishda buzilmaydi.

### 6-bosqich — Baholash va reyting
- **Kurs bahosi (har modul 20 ball, sozlanadigan):**
  - davomat 2,5; mustaqil vazifalar 5; test 2,5; loyiha 10.
  - Uyga vazifa muddatidan keyin topshirilsa — sozlanadigan jarima.
  - O‘qituvchi uchun guruh baholari jadvali va CSV eksport.
- **Mashq reytingi (practice):**
  - yechilgan masalalar ballining yig‘indisi (qiyinlikka qarab);
  - kunlik seriya (streak);
  - nishonlar: birinchi yechim, 10/50/100 masala, modul yakunlandi, 7 kunlik seriya va h.k.
- **Kontest reytingi:** Elo / Codeforces uslubidagi hisob (boshlang‘ich 1200), RatingHistory, grafik.
- **Reyting jadvallari:** umumiy, guruh bo‘yicha, kurs bo‘yicha, haftalik; o‘quvchi o‘z o‘rnini ko‘radi.
- **Mezon:** baho va reyting hisobi uchun unit testlar (chekka holatlar bilan).

### 7-bosqich — Kontestlar
- **Contest:**
  - egasi (Jury), boshlanish va davomiylik;
  - turi: ICPC (jarima bilan) yoki IOI (qisman ball);
  - ochiq / guruh uchun / parol bilan; reytingli yoki yo‘q.
- ContestProblem (harf: A, B, C…), ContestParticipant.
- **Jadval (scoreboard):** jonli; oxirgi 30 daqiqada muzlatish (ixtiyoriy);
  kontest tugagach yechimlar ochiladi.
- **Ruxsatlar:**
  - Jury — o‘z kontestlarini to‘liq boshqaradi;
  - moderator — barcha kontestlarni;
  - kontest paytida masalalar faqat ishtirokchilarga ko‘rinadi.
- **Kontestdan keyin:** reytingli bo‘lsa, reyting avtomatik qayta hisoblanadi.
- **Mezon:** ICPC/IOI hisoblash va ruxsatlar testlari; namunaviy kontest seed.

### 8-bosqich — Rollar oqimi va xavfsizlik
- **RoleRequest oqimi UI orqali:** o‘quvchi Jury so‘raydi → moderator tasdiqlaydi.
- **Vaqtinchalik parol:**
  - moderator va undan yuqori o‘quvchiga vaqtinchalik parol beradi;
  - `must_change_password` — keyingi kirishda majburiy almashtirish;
  - harakat audit jurnaliga yoziladi.
- **Super admin uchun:**
  - 2FA (TOTP, django-otp);
  - login urinishlari cheklovi.
- **Ko‘chirmachilik:**
  - bir masaladagi yechimlar o‘xshashligini tekshiruvchi `manage.py check_similarity`;
  - natijalar faqat moderatorga ko‘rinadi.
- **Xavfsizlik sozlamalari:** prod uchun alohida settings:
  - DEBUG o‘chiq; HTTPS cookie;
  - CSP sarlavhalari; xavfsiz fayl yuklash (faqat .in/.out/.txt, hajm chegarasi).
- **Mezon:** xavfsizlik testlari, `manage.py check --deploy` ogohlantirishsiz (prod settings bilan).

### 9-bosqich — Sifat va hujjatlar
- **Test qamrovi:** coverage ≥ 80% (`coverage report`).
- **CI:** GitHub Actions — ruff + testlar (MySQL servis bilan).
- **Ishga tushirish:** `manage.py seed_demo` — 20 ta demo o‘quvchi, urinishlar va reyting
  (faqat DEBUG da).
- **README — to‘liq:** o‘rnatish, rollar, bosqichlar, masala qo‘shish, Judge0’ni ulash,
  serverga joylash rejasi.
- **docs/ papkasi:**
  - `ARCHITECTURE.md` — sxema Mermaid’da;
  - `PROBLEM_FORMAT.md`, `DECISIONS.md`, `PROGRESS.md`, `ROLES.md` (ruxsatlar matritsasi).

## 5. YAKUNIY QABUL (hammasi bajarilganda)

1. O‘quvchi ro‘yxatdan o‘tadi → guruhga qo‘shiladi → 48 darsning istalganidagi masala, test va
   loyihani bajaradi → natija va ball ko‘rinadi → reytingda o‘rni chiqadi.
2. O‘qituvchi guruh progressi va baholarini ko‘radi, loyihalarni baholaydi, CSV eksport qiladi.
3. Jury kontest o‘tkazadi, jadval ishlaydi, reyting yangilanadi.
4. Barcha testlar o‘tadi, coverage ≥ 80%, ruff toza, `.env` hech qachon commit qilinmagan.
5. `docs/PROGRESS.md` da barcha bosqichlar «tayyor» deb belgilangan.

Endi 2-bosqichdan boshla va to‘xtamasdan oxirigacha davom et.
