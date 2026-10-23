# Vazifa formati (import uchun)

O‘qituvchi (Jury Pro va undan yuqori) o‘z vazifalarini papka ko‘rinishida tayyorlab, bitta buyruq bilan
platformaga qo‘shadi:

```bash
venv/Scripts/python manage.py import_problems <papka> --author <username> [--status draft|review|published]
```

`<papka>` — bitta vazifa papkasi yoki vazifa papkalari to‘plami. Standart holat — `draft` (qoralama);
nashr etishni moderator bajaradi. Bir xil `slug` bilan qayta import qilinsa, vazifa yangilanadi.
Avval barcha papkalar tekshiriladi — bittasida xato bo‘lsa, hech narsa yozilmaydi.

Tayyor namunalar: [`docs/examples/problems/`](examples/problems/).

## Papka tuzilmasi

```
<slug>/                 # papka nomi = slug: kichik lotin harflari, raqamlar, "-"
  problem.yaml          # metama'lumot (majburiy)
  statement.md          # shart: Markdown, formulalar $...$ yoki $$...$$ (KaTeX)
  solution.py           # etalon yechim (code uchun tavsiya etiladi)
  tests/
    01.in   01.out      # kirish va kutilgan chiqish, UTF-8
    02.in   02.out
    ...
```

Testlar fayl nomi bo‘yicha tartiblanadi. Har bir `.in` uchun `.out` bo‘lishi shart.

## problem.yaml

| Kalit | Majburiy | Standart | Izoh |
|---|---|---|---|
| `title` | ha | — | Nomi |
| `type` | yo‘q | `code` | `code` / `quiz` / `project` |
| `difficulty` | yo‘q | 1 | 1–5 |
| `points` | yo‘q | 100 | Vazifa bali |
| `tags` | yo‘q | `[]` | Teglar ro‘yxati |
| `time_limit` | yo‘q | 1000 | ms (code) |
| `memory_limit` | yo‘q | 256 | MB (code) |
| `checker` | yo‘q | `whitespace` | `exact` — qatorma-qator; `whitespace` — bo‘shliqlar e’tiborsiz; `float` — sonlar `epsilon` bilan |
| `epsilon` | yo‘q | `1e-6` | `float` uchun absolyut yoki nisbiy xato |
| `samples` | yo‘q | `[1, 2]` | Namuna (ochiq) testlar raqamlari; qolganlari yopiq |
| `test_points` | yo‘q | 1 | Har bir test bali |
| `input_format`, `output_format`, `notes` | yo‘q | — | Matnlar |
| `lessons` | yo‘q | — | Darsga biriktirish (pastda) |
| `questions` | quiz uchun | — | Savollar (pastda) |
| `rubric` | project uchun | — | Baholash mezonlari (pastda) |

### lessons

```yaml
lessons:
  - lesson: 8          # dars raqami (1–48)
    kind: classwork    # classwork (sinf ishi) | homework (uyga vazifa) | challenge (qo'shimcha)
    required: true
    order: 1
```

### questions (quiz)

```yaml
questions:
  - text: "Savol matni"
    kind: single            # single — bitta javob, multiple — bir nechta, text — qisqa matn
    points: 1
    options:
      - text: "To'g'ri variant"
        correct: true
      - "Noto'g'ri variant"  # oddiy satr = noto'g'ri variant
    explanation: "Javobdan keyin ko'rsatiladigan izoh"
  - text: "len('abc') = ?"
    kind: text
    answers: ["3", "uch"]   # katta-kichik harf farqlanmaydi
```

`single` savolda aynan bitta, `multiple` da kamida bitta to‘g‘ri variant bo‘lishi kerak.

### rubric (project)

```yaml
rubric:
  - title: Funksionallik
    points: 50
    description: Talablar to'liq bajarilgan
```

## Sifat talablari (tavsiya)

- Kamida 5 ta test: 2 ta namuna + 3 ta yopiq (chekka holatlar, katta kirish).
- `solution.py` barcha testlardan o‘tishi kerak — tekshirish: `manage.py verify_problems --slug <slug>`.
- Chiqishda o‘zbekcha so‘z bo‘lsa, oddiy apostrof (`'`) ishlating va shartda aniq ko‘rsating —
  o‘quvchi klaviaturadan aynan shuni teradi.
- Shartda shaxsiy ma’lumotlar (haqiqiy ism-familiya, telefon) ishlatilmaydi.
