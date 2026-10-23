# Arxitektura

## Umumiy sxema

```mermaid
flowchart LR
    B[Brauzer<br/>Django shablonlari + HTMX + Tailwind<br/>CodeMirror 6, KaTeX] -->|HTTPS| N[nginx]
    N --> W[Django web<br/>gunicorn]
    W <--> DB[(MySQL 8<br/>utf8mb4)]
    W -->|navbatga qo'yish| Q[[Judge navbati<br/>DatabaseQueue]]
    Q --> JW[run_judge_worker<br/>alohida jarayon]
    JW -->|dev| L[LocalDevBackend<br/>subprocess + Job Object / rlimit]
    JW -->|prod| J0[Judge0 xizmati]
    JW <--> DB
    JW -->|bo'sh paytda| R[Kontest reytingi<br/>Elo]
    W --> M[(media/<br/>testlar, avatarlar)]
    JW --> M
```

**Asosiy qoida:** foydalanuvchi kodi hech qachon Django web-jarayonida bajarilmaydi. Web faqat yechimni saqlab
navbatga qo‘yadi; worker uni judge backend orqali tekshiradi, natijani bazaga yozadi, sahifa esa HTMX bilan
har 2 soniyada holatni so‘raydi.

## Yechim hayot sikli

```mermaid
sequenceDiagram
    participant U as O'quvchi
    participant W as Django (web)
    participant D as MySQL
    participant K as Judge worker
    participant J as Judge backend
    U->>W: POST /masalalar/<slug>/yuborish/
    W->>W: tekshiruv (64 KB, 6/daqiqa, ruxsat)
    W->>D: Submission(status=queued)
    W-->>U: 302 → /urinishlar/<id>/
    loop har 2 s (HTMX)
        U->>W: GET /urinishlar/<id>/holat/
        W->>D: holatni o'qish
    end
    K->>D: SELECT … FOR UPDATE SKIP LOCKED → running
    K->>J: submit(code, tests, limits)
    J-->>K: test natijalari
    K->>D: SubmissionResult, verdikt, ball, done
    K->>D: PracticeStats, nishonlar (AC bo'lsa)
```

## Ilovalar

```mermaid
flowchart TB
    accounts[accounts<br/>User, Role, RoleRequest,<br/>LoginAttempt, ruxsatlar] --> audit[audit<br/>AuditLog]
    courses[courses<br/>Course, Module, Lesson,<br/>Group, GroupMember] --> accounts
    problems[problems<br/>Problem, TestCase, Quiz,<br/>Rubric, LessonProblem, importer] --> courses
    judge[judge<br/>JudgeBackend, LocalDev,<br/>Judge0, checker]
    submissions[submissions<br/>Submission, Quiz/Project,<br/>navbat, worker, o'xshashlik] --> problems
    submissions --> judge
    grading[grading<br/>kurs bahosi, davomat,<br/>mashq bali, nishonlar, Elo] --> submissions
    contests[contests<br/>Contest, jadval,<br/>RatingHistory] --> submissions
    contests --> grading
    core[core<br/>SiteSettings, bosh sahifa,<br/>middleware, seed_demo] --> grading
    panel[panel<br/>o'qituvchi, Jury, Jury Pro,<br/>super admin panellari] --> contests
    panel --> core
```

| Ilova | Vazifasi |
|---|---|
| `accounts` | Foydalanuvchi (5 darajali rol), rol so‘rovlari, ruxsat vositalari, kirish cheklovi, 2FA sahifalari |
| `audit` | Muhim harakatlar jurnali (`log_action`) |
| `courses` | Kurs → modul → dars (48), guruhlar |
| `problems` | Vazifalar banki (code/quiz/project), testlar (media’da), import/verify buyruqlari, seed kontent |
| `judge` | Judge adapterlari va chiqishni solishtirish; Django modellarisiz |
| `submissions` | Yechimlar, navbat, worker, quiz va loyiha baholash, statistika, ko‘chirmachilik |
| `grading` | Kurs bahosi (musobaqa reytingidan alohida), davomat, mashq bali, seriya, nishonlar, Elo algoritmi |
| `contests` | Kontestlar (ICPC/IOI), jadval, muzlatish, reyting tarixi |
| `core` | Sayt sozlamalari, bosh sahifa, xavfsizlik middleware’lari (CSP, 2FA, parol), `seed_demo` |
| `panel` | Rol panellari (UI) |

## Ma’lumotlar modeli (asosiy)

```mermaid
erDiagram
    USER ||--o{ SUBMISSION : yuboradi
    USER ||--o{ GROUPMEMBER : a'zo
    GROUP ||--o{ GROUPMEMBER : ""
    COURSE ||--o{ MODULE : ""
    MODULE ||--o{ LESSON : ""
    COURSE ||--o{ GROUP : ""
    LESSON ||--o{ LESSONPROBLEM : ""
    PROBLEM ||--o{ LESSONPROBLEM : ""
    PROBLEM ||--o{ TESTCASE : ""
    PROBLEM ||--o{ QUIZQUESTION : ""
    PROBLEM ||--o{ RUBRICCRITERION : ""
    PROBLEM ||--o{ SUBMISSION : ""
    SUBMISSION ||--o{ SUBMISSIONRESULT : ""
    CONTEST ||--o{ CONTESTPROBLEM : ""
    CONTEST ||--o{ CONTESTPARTICIPANT : ""
    CONTEST ||--o{ SUBMISSION : ""
    CONTEST ||--o{ RATINGHISTORY : ""
    USER ||--|| PRACTICESTATS : ""
    USER ||--o{ USERBADGE : ""
```

## Kengaytirish nuqtalari

- **Yangi til (C++, JS):** `judge.types.Language` + `judge0.LANGUAGE_IDS`; LocalDevBackend faqat Python (dev).
- **Redis/Celery navbati:** `submissions.queue.JudgeQueue` ni amalga oshiruvchi klass va `JUDGE_QUEUE` sozlamasi.
- **Yangi kurs/yo‘nalish:** `Course` + `courses/seed_data.py` uslubida data migratsiya; vazifalar — `import_problems`.
- **Tarjimalar (ru/en):** barcha shablon matnlari `{% translate %}` da; `LANGUAGES` va `locale/` ga qo‘shish.
- **Tailwind build:** CDN o‘rniga build — keyin CSP’dan `style-src 'unsafe-inline'` olib tashlanadi.
