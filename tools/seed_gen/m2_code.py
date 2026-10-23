"""Modul 2 (13–24-darslar) code masalalari."""
import json
import random

from common import code_problem

R = random.Random(2027)


def nums(n: int, lo: int, hi: int) -> str:
    return " ".join(str(R.randint(lo, hi)) for _ in range(n))


# ---------------- 13. Ro'yxatlar (list) ----------------
code_problem(
    slug="l13-max-min", title="Eng katta va eng kichik", lesson=13, level=0, difficulty=1, tags=["list"],
    statement="""
        $n$ ta butun son berilgan. Ularning eng kattasi va eng kichigini chiqaring.
    """,
    input_format="Birinchi qatorda $n$ ($1 \\le n \\le 10^5$), ikkinchi qatorda $n$ ta son ($|a_i| \\le 10^9$).",
    output_format="Ikki son: eng katta va eng kichik.",
    solution="""
        n = int(input())
        a = list(map(int, input().split()))
        print(max(a), min(a))
    """,
    samples=[("5\n3 -1 7 7 0", "7 -1"), ("1\n42", "42 42")],
    hidden=["3\n-5 -5 -5", "100000\n" + nums(100000, -10 ** 9, 10 ** 9), "2\n1000000000 -1000000000"],
)

code_problem(
    slug="l13-ortachadan-katta", title="O‘rtachadan kattalar", lesson=13, level=1, difficulty=2, tags=["list"],
    statement="""
        $n$ ta butun son berilgan. Nechta son ularning o‘rta arifmetigidan **qat’iy katta**?
    """,
    input_format="Birinchi qatorda $n$ ($1 \\le n \\le 10^5$), ikkinchi qatorda $n$ ta son ($|a_i| \\le 10^9$).",
    output_format="Bitta son.",
    notes="Haqiqiy sonlar bilan xatolikka yo‘l qo‘ymaslik uchun $a_i \\cdot n > S$ ni solishtirish mumkin.",
    solution="""
        n = int(input())
        a = list(map(int, input().split()))
        total = sum(a)
        print(sum(1 for x in a if x * n > total))
    """,
    samples=[("5\n1 2 3 4 10", "1"), ("4\n5 5 5 5", "0")],
    hidden=["2\n-1 1", "100000\n" + nums(100000, -10 ** 9, 10 ** 9), "3\n1 1 2"],
)

code_problem(
    slug="l13-siljitish", title="Ro‘yxatni siljitish", lesson=13, level=2, difficulty=3, tags=["list"],
    statement="""
        $n$ ta sondan iborat ro‘yxatni $k$ marta o‘ngga siklik siljiting: har siljishda oxirgi element
        boshiga o‘tadi.
    """,
    input_format="Birinchi qatorda $n$ va $k$ ($1 \\le n \\le 10^5$, $0 \\le k \\le 10^{9}$), ikkinchi qatorda ro‘yxat.",
    output_format="Siljitilgan ro‘yxat bitta qatorda.",
    solution="""
        n, k = map(int, input().split())
        a = input().split()
        k %= n
        print(*(a[n - k:] + a[:n - k]))
    """,
    samples=[("5 2\n1 2 3 4 5", "4 5 1 2 3"), ("3 4\n7 8 9", "9 7 8")],
    hidden=["1 1000000000\n5", "4 0\n1 2 3 4", "100000 999999999\n" + nums(100000, 1, 100)],
)

# ---------------- 14. Qidirish, saralash, comprehension ----------------
code_problem(
    slug="l14-juftlar", title="Juft sonlar saralangan", lesson=14, level=0, difficulty=1,
    tags=["comprehension", "saralash"],
    statement="""
        $n$ ta butun son berilgan. List comprehension yordamida juft sonlarni ajratib, o‘sish tartibida
        chiqaring. Juft son bo‘lmasa, `yo'q` chiqaring (oddiy apostrof bilan).
    """,
    input_format="Birinchi qatorda $n$ ($1 \\le n \\le 10^5$), ikkinchi qatorda sonlar.",
    output_format="Juft sonlar yoki `yo'q`.",
    solution="""
        n = int(input())
        evens = sorted(x for x in map(int, input().split()) if x % 2 == 0)
        print(*evens if evens else ["yo'q"])
    """,
    samples=[("6\n5 2 8 1 4 9", "2 4 8"), ("3\n1 3 5", "yo'q")],
    hidden=["4\n-2 0 -4 3", "100000\n" + nums(100000, -1000, 1000), "1\n0"],
)

_arr = sorted(R.sample(range(1, 10 ** 9), 100000))
_queries = [R.choice(_arr) if R.random() < 0.5 else R.randint(1, 10 ** 9) for _ in range(100000)]
code_problem(
    slug="l14-ikkilik-qidiruv", title="Ikkilik qidiruv", lesson=14, level=1, difficulty=3,
    tags=["qidirish", "ikkilik qidiruv"],
    statement="""
        O‘sish tartibida saralangan $n$ ta turli son va $q$ ta so‘rov berilgan. Har bir so‘rov soni
        ro‘yxatda bo‘lsa, uning tartib raqamini (1 dan boshlab), aks holda $-1$ chiqaring.

        $n$ va $q$ katta — har so‘rov uchun ro‘yxatni boshidan ko‘rib chiqish juda sekin. Ikkilik
        qidiruvdan foydalaning.
    """,
    input_format="""
        $n$; keyingi qatorda $n$ ta son; keyin $q$; keyingi qatorda $q$ ta so‘rov
        ($1 \\le n, q \\le 10^5$, sonlar $\\le 10^9$).
    """,
    output_format="Har bir so‘rov uchun alohida qatorda javob.",
    solution="""
        import sys
        from bisect import bisect_left

        data = sys.stdin.read().split()
        n = int(data[0])
        a = list(map(int, data[1:1 + n]))
        q = int(data[1 + n])
        out = []
        for x in map(int, data[2 + n:2 + n + q]):
            i = bisect_left(a, x)
            out.append(str(i + 1) if i < n and a[i] == x else "-1")
        print("\\n".join(out))
    """,
    samples=[("5\n1 3 5 7 9\n3\n7 1 4", "4\n1\n-1"), ("1\n10\n2\n10 5", "1\n-1")],
    hidden=["3\n2 4 6\n3\n1 7 6",
            f"{len(_arr)}\n{' '.join(map(str, _arr))}\n{len(_queries)}\n{' '.join(map(str, _queries))}",
            "2\n1 1000000000\n2\n1000000000 999999999"],
)

code_problem(
    slug="l14-ikki-yigindi", title="Ikki son yig‘indisi K", lesson=14, level=2, difficulty=4,
    tags=["qidirish", "lug‘at"],
    statement="""
        $n$ ta butun son va $K$ soni berilgan. $i < j$ va $a_i + a_j = K$ bo‘ladigan juftliklar sonini toping.
    """,
    input_format="Birinchi qatorda $n$ va $K$ ($1 \\le n \\le 10^5$, $|K| \\le 2 \\cdot 10^9$), ikkinchi qatorda sonlar.",
    output_format="Juftliklar soni.",
    solution="""
        n, k = map(int, input().split())
        seen = {}
        pairs = 0
        for x in map(int, input().split()):
            pairs += seen.get(k - x, 0)
            seen[x] = seen.get(x, 0) + 1
        print(pairs)
    """,
    samples=[("5 6\n1 5 3 3 2", "2"), ("4 2\n1 1 1 1", "6")],
    hidden=["1 2\n1", "100000 0\n" + nums(100000, -50, 50), "100000 7\n" + nums(100000, 1, 6)],
)

# ---------------- 15. tuple, set, dict ----------------
code_problem(
    slug="l15-noyob", title="Noyob sonlar", lesson=15, level=0, difficulty=1, tags=["set"],
    statement="""
        $n$ ta son berilgan. Ular orasida nechta turli son bor? (`set` dan foydalaning.)
    """,
    input_format="Birinchi qatorda $n$ ($1 \\le n \\le 10^5$), ikkinchi qatorda sonlar.",
    output_format="Turli sonlar soni.",
    solution="""
        input()
        print(len(set(input().split())))
    """,
    samples=[("6\n1 2 2 3 3 3", "3"), ("3\n5 5 5", "1")],
    hidden=["1\n0", "100000\n" + nums(100000, 1, 1000), "5\n1 2 3 4 5"],
)

_words = ["olma", "nok", "uzum", "anor", "behi", "shaftoli", "gilos", "o‘rik"]
code_problem(
    slug="l15-soz-chastotasi", title="So‘zlar chastotasi", lesson=15, level=1, difficulty=2, tags=["dict"],
    statement="""
        Matn berilgan (bir yoki bir necha qator, so‘zlar bo‘shliq bilan ajratilgan). Harflar katta-kichikligi
        farqlanmaydi. Har bir so‘z necha marta uchraganini chiqaring: avval eng ko‘p uchraganlari,
        teng bo‘lsa — alifbo tartibida. So‘zlar kichik harflarda chiqariladi.
    """,
    input_format="Matn (jami 10^5 belgigacha).",
    output_format="Har bir qatorda `so‘z soni`.",
    solution="""
        import sys

        counts = {}
        for word in sys.stdin.read().lower().split():
            counts[word] = counts.get(word, 0) + 1
        for word, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
            print(word, count)
    """,
    samples=[("olma nok olma uzum nok olma", "olma 3\nnok 2\nuzum 1"), ("a b", "a 1\nb 1")],
    hidden=["Salom salom SALOM dunyo",
            "\n".join(" ".join(R.choice(_words) for _ in range(20)) for _ in range(50)),
            "bitta"],
)

code_problem(
    slug="l15-kontaktlar", title="Kontaktlar daftari", lesson=15, level=2, difficulty=3, tags=["dict"],
    statement="""
        Kontaktlar daftari (lug‘at) bilan ishlang. Buyruqlar:

        - `add NOM RAQAM` — kontakt qo‘shish (bor bo‘lsa, raqam yangilanadi);
        - `get NOM` — raqamni chiqarish, kontakt bo‘lmasa `topilmadi`;
        - `del NOM` — kontaktni o‘chirish (bo‘lmasa, hech narsa qilinmaydi).

        Faqat `get` buyruqlari natija chiqaradi. (Masalada barcha ism va raqamlar o‘ylab topilgan.)
    """,
    input_format="Birinchi qatorda $n$ ($1 \\le n \\le 10^5$), keyingi $n$ qatorda buyruqlar.",
    output_format="Har bir `get` uchun natija.",
    solution="""
        import sys

        lines = sys.stdin.read().split("\\n")
        book = {}
        out = []
        for line in lines[1:1 + int(lines[0])]:
            parts = line.split()
            if parts[0] == "add":
                book[parts[1]] = parts[2]
            elif parts[0] == "get":
                out.append(book.get(parts[1], "topilmadi"))
            elif parts[0] == "del":
                book.pop(parts[1], None)
        print("\\n".join(out))
    """,
    samples=[("5\nadd ali 901234567\nget ali\ndel ali\nget ali\nget vali", "901234567\ntopilmadi\ntopilmadi"),
             ("3\nadd a 1\nadd a 2\nget a", "2")],
    hidden=["2\ndel x\nget x", "4\nadd b 5\nadd c 6\ndel b\nget c",
            "100000\n" + "\n".join(
                R.choice([f"add u{R.randint(1, 500)} {R.randint(10 ** 8, 10 ** 9)}", f"get u{R.randint(1, 500)}",
                          f"del u{R.randint(1, 500)}"]) for _ in range(99999)) + "\nget u1"],
)

# ---------------- 16. Satrlar chuqur ----------------
code_problem(
    slug="l16-palindrom", title="Palindrom", lesson=16, level=0, difficulty=1, tags=["satrlar"],
    statement="""
        Satr palindrommi (chapdan va o‘ngdan bir xil o‘qiladimi)? Bo‘shliqlar va harflar katta-kichikligi
        hisobga olinmaydi. `ha` yoki `yo'q` chiqaring.
    """,
    input_format="Bitta qator (uzunligi $10^5$ gacha).",
    output_format="`ha` yoki `yo'q`.",
    solution="""
        s = input().replace(" ", "").lower()
        print("ha" if s == s[::-1] else "yo'q")
    """,
    samples=[("Kiyik", "ha"), ("Python", "yo'q")],
    hidden=["Nok kon", "a", "ab ba c", "x" * 100000],
)

code_problem(
    slug="l16-unlilar", title="Unli harflar", lesson=16, level=1, difficulty=2, tags=["satrlar"],
    statement="""
        Matndagi unli harflar (`a`, `e`, `i`, `o`, `u`, katta-kichikligidan qat’i nazar) sonini toping.
    """,
    input_format="Bitta qator (uzunligi $10^5$ gacha).",
    output_format="Unlilar soni.",
    solution="""
        print(sum(1 for ch in input().lower() if ch in "aeiou"))
    """,
    samples=[("Salom dunyo", "4"), ("xyz", "0")],
    hidden=["AEIOU aeiou", "O‘zbekiston", "".join(R.choice("abcdefghijklmnopqrstuvwxyz ") for _ in range(100000))],
)

code_problem(
    slug="l16-siqish", title="Satrni siqish", lesson=16, level=2, difficulty=3, tags=["satrlar"],
    statement="""
        Satrdagi ketma-ket takrorlangan belgilarni siqing: har bir guruh o‘rniga belgi va (agar 1 dan ko‘p
        bo‘lsa) takrorlanishlar soni yoziladi. Masalan, `aaabcc` → `a3bc2`.
    """,
    input_format="Bitta qator — kichik lotin harflari (uzunligi 1–$10^5$).",
    output_format="Siqilgan satr.",
    solution="""
        s = input().strip()
        parts = []
        i = 0
        while i < len(s):
            j = i
            while j < len(s) and s[j] == s[i]:
                j += 1
            parts.append(s[i] + (str(j - i) if j - i > 1 else ""))
            i = j
        print("".join(parts))
    """,
    samples=[("aaabcc", "a3bc2"), ("abc", "abc")],
    hidden=["zzzzzzzzzzzz", "a", "".join(R.choice("ab") * R.randint(1, 5) for _ in range(20000))],
)

# ---------------- 17. Funksiyalar ----------------
code_problem(
    slug="l17-faktorial", title="Faktorial", lesson=17, level=0, difficulty=1, tags=["funksiyalar"],
    statement="""
        `factorial(n)` funksiyasini yozing va $n!$ ni chiqaring ($0! = 1$).
    """,
    input_format="Bitta son $n$ ($0 \\le n \\le 20$).",
    output_format="$n!$",
    solution="""
        def factorial(n: int) -> int:
            result = 1
            for i in range(2, n + 1):
                result *= i
            return result


        print(factorial(int(input())))
    """,
    samples=[("5", "120"), ("0", "1")],
    hidden=["1", "20", "10"],
)

code_problem(
    slug="l17-ekuk", title="EKUK", lesson=17, level=1, difficulty=2, tags=["funksiyalar", "matematika"],
    statement="""
        $n$ ta natural sonning eng kichik umumiy karralisini (EKUK) toping. `gcd(a, b)` va `lcm(a, b)`
        funksiyalarini o‘zingiz yozing: $\\mathrm{lcm}(a, b) = a \\cdot b / \\gcd(a, b)$.
    """,
    input_format="Birinchi qatorda $n$ ($1 \\le n \\le 100$), ikkinchi qatorda sonlar ($1 \\le a_i \\le 10^6$).",
    output_format="EKUK (u juda katta bo‘lishi mumkin).",
    solution="""
        def gcd(a: int, b: int) -> int:
            while b:
                a, b = b, a % b
            return a


        def lcm(a: int, b: int) -> int:
            return a // gcd(a, b) * b


        input()
        result = 1
        for x in map(int, input().split()):
            result = lcm(result, x)
        print(result)
    """,
    samples=[("3\n4 6 8", "24"), ("2\n7 5", "35")],
    hidden=["1\n1", "100\n" + nums(100, 1, 10 ** 6), "4\n2 3 5 7"],
)

code_problem(
    slug="l17-fibonachchi", title="Katta Fibonachchi", lesson=17, level=2, difficulty=5,
    tags=["funksiyalar", "rekursiya", "matematika"],
    statement="""
        $F_0 = 0$, $F_1 = 1$, $F_n = F_{n-1} + F_{n-2}$. $F_n \\bmod (10^9 + 7)$ ni toping.

        $n$ juda katta, shuning uchun oddiy tsikl yetmaydi. «Tez ikkilash» formulalaridan foydalaning:
        $F_{2k} = F_k (2F_{k+1} - F_k)$, $F_{2k+1} = F_k^2 + F_{k+1}^2$ — rekursiv funksiya yozing.
    """,
    input_format="Bitta son $n$ ($0 \\le n \\le 10^{18}$).",
    output_format="$F_n \\bmod (10^9 + 7)$.",
    solution="""
        MOD = 10 ** 9 + 7


        def fib_pair(n: int) -> tuple[int, int]:
            \"\"\"(F(n), F(n+1)) mod MOD.\"\"\"
            if n == 0:
                return 0, 1
            a, b = fib_pair(n // 2)
            c = a * (2 * b - a) % MOD
            d = (a * a + b * b) % MOD
            return (d, (c + d) % MOD) if n % 2 else (c, d)


        print(fib_pair(int(input()))[0])
    """,
    samples=[("10", "55"), ("1", "1")],
    hidden=["0", "1000000000000000000", "100", "999999999999999999"],
)

# ---------------- 18. Fayllar: txt, csv, json (stdin orqali) ----------------
code_problem(
    slug="l18-csv-yigindi", title="CSV: ballar yig‘indisi", lesson=18, level=0, difficulty=1, tags=["csv", "fayllar"],
    statement="""
        CSV ma’lumot berilgan (fayl o‘rniga standart kirishdan o‘qiladi). Birinchi qator — sarlavha
        `ism,ball`, keyingi qatorlar — ma’lumot. Barcha ballar yig‘indisini chiqaring.
        `csv` modulidan foydalanish tavsiya etiladi: `csv.reader(sys.stdin)`.
    """,
    input_format="Sarlavha va 0 yoki undan ko‘p ma’lumot qatori (1000 tagacha).",
    output_format="Ballar yig‘indisi.",
    solution="""
        import csv
        import sys

        reader = csv.reader(sys.stdin)
        next(reader)
        print(sum(int(row[1]) for row in reader if row))
    """,
    samples=[("ism,ball\nAli,85\nVali,90", "175"), ("ism,ball", "0")],
    hidden=["ism,ball\nA,0", "ism,ball\n" + "\n".join(f"u{i},{R.randint(0, 100)}" for i in range(1000)),
            "ism,ball\n\"Karimov, Ali\",50\nVali,1"],
)

code_problem(
    slug="l18-csv-eng-yaxshi", title="CSV: fan bo‘yicha eng yaxshi", lesson=18, level=1, difficulty=3,
    tags=["csv", "dict"],
    statement="""
        CSV ma’lumot: sarlavha `ism,fan,ball`, keyin qatorlar. Har bir fan bo‘yicha eng yuqori ball olgan
        o‘quvchini toping (ball teng bo‘lsa — ismi alifbo bo‘yicha oldin keladigani).

        Natijani fan nomlari alifbo tartibida, `fan ism ball` ko‘rinishida chiqaring.
    """,
    input_format="Sarlavha va kamida bitta ma’lumot qatori (10^4 tagacha).",
    output_format="Har bir fan uchun bitta qator.",
    solution="""
        import csv
        import sys

        best = {}
        for row in csv.DictReader(sys.stdin):
            key = (-int(row["ball"]), row["ism"])
            if row["fan"] not in best or key < best[row["fan"]]:
                best[row["fan"]] = key
        for subject in sorted(best):
            score, name = best[subject]
            print(subject, name, -score)
    """,
    samples=[("ism,fan,ball\nAli,matematika,90\nVali,fizika,75\nGuli,matematika,95\nSoli,fizika,75",
              "fizika Soli 75\nmatematika Guli 95"),
             ("ism,fan,ball\nA,x,1", "x A 1")],
    hidden=["ism,fan,ball\n" + "\n".join(
                f"o{R.randint(1, 300)},{R.choice(['algebra', 'biologiya', 'kimyo', 'tarix', 'ingliz'])},"
                f"{R.randint(0, 100)}" for _ in range(10000)),
            "ism,fan,ball\nB,f,10\nA,f,10\nC,g,0", "ism,fan,ball\nZ,ona tili,100\nA,ona tili,99"],
)

_students = [{"ism": f"Oquvchi{i}", "baholar": [R.randint(2, 5) for _ in range(R.randint(0, 8))]} for i in range(200)]
code_problem(
    slug="l18-json-ortacha", title="JSON: o‘rtacha baholar", lesson=18, level=2, difficulty=3, tags=["json"],
    statement="""
        Standart kirishda JSON obyekt berilgan:

        ```json
        {"oquvchilar": [{"ism": "Ali", "baholar": [5, 4, 5]}, ...]}
        ```

        Har bir o‘quvchining o‘rtacha bahosini (2 xona aniqlikda) hisoblang. Bahosi yo‘q o‘quvchining
        o‘rtachasi 0. Natijani o‘rtacha baho kamayishi bo‘yicha, teng bo‘lsa — ism bo‘yicha alifbo
        tartibida chiqaring. O‘quvchilar bo‘lmasa, `yo'q` chiqaring.
    """,
    input_format="JSON obyekt (bir necha qatorda bo‘lishi mumkin).",
    output_format="Har bir qatorda `ism o‘rtacha`.",
    solution="""
        import json
        import sys

        data = json.load(sys.stdin)
        rows = []
        for student in data["oquvchilar"]:
            marks = student["baholar"]
            rows.append((-(sum(marks) / len(marks) if marks else 0.0), student["ism"]))
        if not rows:
            print("yo'q")
        for avg, name in sorted(rows):
            print(name, f"{-avg:.2f}")
    """,
    checker="float", epsilon=1e-2,
    samples=[('{"oquvchilar": [{"ism": "Ali", "baholar": [5, 4, 5]}, {"ism": "Vali", "baholar": [5, 5]}]}',
              "Vali 5.00\nAli 4.67"),
             ('{"oquvchilar": []}', "yo'q")],
    hidden=[json.dumps({"oquvchilar": _students}, indent=2),
            '{\n  "oquvchilar": [\n    {"ism": "B", "baholar": []},\n    {"ism": "A", "baholar": [3]}\n  ]\n}',
            '{"oquvchilar": [{"ism": "Yolgiz", "baholar": [2, 3]}]}'],
)

# ---------------- 19. Xatolarni boshqarish ----------------
code_problem(
    slug="l19-xavfsiz-bolish", title="Xavfsiz bo‘lish", lesson=19, level=0, difficulty=1, tags=["try-except"],
    statement="""
        $n$ ta juftlik $a$, $b$ berilgan. Har biri uchun $a // b$ ni chiqaring. $b = 0$ bo‘lsa,
        dastur to‘xtab qolmasligi kerak: `try/except ZeroDivisionError` bilan ushlab, `xato` chiqaring.
    """,
    input_format="Birinchi qatorda $n$ ($1 \\le n \\le 1000$), keyingi $n$ qatorda $a$ va $b$.",
    output_format="Har bir juftlik uchun natija.",
    solution="""
        n = int(input())
        for _ in range(n):
            a, b = map(int, input().split())
            try:
                print(a // b)
            except ZeroDivisionError:
                print("xato")
    """,
    samples=[("3\n7 2\n5 0\n-7 2", "3\nxato\n-4"), ("1\n0 5", "0")],
    hidden=["2\n0 0\n10 -3", "1\n-9 -2","1000\n" + "\n".join(f"{R.randint(-100, 100)} {R.randint(-3, 3)}" for _ in range(1000))],
)

code_problem(
    slug="l19-sonlarni-ajrat", title="Sonlarni ajratib olish", lesson=19, level=1, difficulty=2, tags=["try-except"],
    statement="""
        Bir qatorda bo‘shliq bilan ajratilgan «so‘zlar» berilgan. Ulardan qaysilari butun son ekanini
        `int()` va `try/except ValueError` yordamida aniqlang. Butun sonlar soni va yig‘indisini chiqaring.
    """,
    input_format="Bitta qator (uzunligi $10^5$ gacha).",
    output_format="Ikki son: butun sonlar soni va ularning yig‘indisi.",
    solution="""
        count = total = 0
        for token in input().split():
            try:
                value = int(token)
            except ValueError:
                continue
            count += 1
            total += value
        print(count, total)
    """,
    samples=[("12 abc 5 -3 4.5 x", "3 14"), ("salom dunyo", "0 0")],
    hidden=["+7 -0 007 1e3 0x10", " ".join(R.choice([str(R.randint(-999, 999)), "abc", "1.5", "-"])
                                              for _ in range(10000)), "42"],
)

code_problem(
    slug="l19-bank-hisobi", title="Bank hisobi", lesson=19, level=2, difficulty=3, tags=["try-except", "if"],
    statement="""
        Hisob balansi 0 dan boshlanadi. $n$ ta amal bajariladi:

        - `kirim X` — balansga $X$ qo‘shiladi;
        - `chiqim X` — balansdan $X$ ayriladi.

        Xatolar (amal bajarilmaydi, xabar chiqariladi):

        - $X$ musbat butun son bo‘lmasa — `xato: summa`;
        - chiqimda mablag‘ yetmasa — `xato: yetarli emas`;
        - noma’lum amal — `xato: amal`.

        Oxirida `balans: B` chiqaring.
    """,
    input_format="Birinchi qatorda $n$ ($1 \\le n \\le 10^4$), keyingi $n$ qatorda amallar (ikkita so‘z).",
    output_format="Xato xabarlari va oxirgi balans.",
    solution="""
        n = int(input())
        balance = 0
        for _ in range(n):
            op, raw = input().split()
            try:
                amount = int(raw)
                if amount <= 0:
                    raise ValueError
            except ValueError:
                print("xato: summa")
                continue
            if op == "kirim":
                balance += amount
            elif op == "chiqim":
                if amount > balance:
                    print("xato: yetarli emas")
                else:
                    balance -= amount
            else:
                print("xato: amal")
        print(f"balans: {balance}")
    """,
    samples=[("4\nkirim 100\nchiqim 30\nchiqim 100\nkirim abc", "xato: yetarli emas\nxato: summa\nbalans: 70"),
             ("1\nkirim -5", "xato: summa\nbalans: 0")],
    hidden=["2\nkredit 5\nchiqim 0", "3\nkirim 50\nchiqim 50\nchiqim 1","10000\n" + "\n".join(
        f"{R.choice(['kirim', 'chiqim', 'chiqim', 'boshqa'])} {R.choice([str(R.randint(1, 500)), '-1', 'x', '2.5'])}"
        for _ in range(10000))],
)

# ---------------- 20. Modullar, paketlar, pip ----------------
code_problem(
    slug="l20-ildiz", title="Kvadrat ildiz", lesson=20, level=0, difficulty=1, tags=["modullar", "math"],
    statement="""
        `math` modulining `sqrt` funksiyasi yordamida $\\sqrt{n}$ ni 3 xona aniqlikda chiqaring.
    """,
    input_format="Bitta son $n$ ($0 \\le n \\le 10^{12}$).",
    output_format="$\\sqrt{n}$, 3 xona aniqlikda.",
    solution="""
        import math

        print(f"{math.sqrt(int(input())):.3f}")
    """,
    checker="float", epsilon=1e-3,
    samples=[("16", "4.000"), ("2", "1.414")],
    hidden=["0", "1000000000000", "3"],
)

code_problem(
    slug="l20-sana-farqi", title="Sanalar orasidagi kunlar", lesson=20, level=1, difficulty=2,
    tags=["modullar", "datetime"],
    statement="""
        Ikkita sana `YYYY-MM-DD` ko‘rinishida berilgan. `datetime` modulidan foydalanib, ular orasidagi
        kunlar sonini (musbat) chiqaring.
    """,
    input_format="Ikki qatorda sanalar (1900–2100 yillar).",
    output_format="Kunlar soni.",
    solution="""
        from datetime import date

        first = date.fromisoformat(input().strip())
        second = date.fromisoformat(input().strip())
        print(abs((second - first).days))
    """,
    samples=[("2026-01-01\n2026-12-31", "364"), ("2024-03-01\n2024-02-28", "2")],
    hidden=["2000-01-01\n2000-01-01", "1900-01-01\n2100-12-31", "2026-10-23\n2027-01-01"],
)

code_problem(
    slug="l20-kombinatsiyalar", title="Kombinatsiyalar", lesson=20, level=2, difficulty=3,
    tags=["modullar", "itertools"],
    statement="""
        Turli kichik harflardan iborat satr va $k$ soni berilgan. Harflardan $k$ tadan tuzilgan barcha
        kombinatsiyalarni (har biridagi harflar alifbo tartibida) leksikografik tartibda chiqaring.
        `itertools.combinations` yordam beradi.
    """,
    input_format="Bitta qatorda satr (uzunligi 1–12) va $k$ ($1 \\le k \\le$ satr uzunligi).",
    output_format="Har bir qatorda bitta kombinatsiya.",
    solution="""
        from itertools import combinations

        letters, k = input().split()
        for combo in combinations(sorted(letters), int(k)):
            print("".join(combo))
    """,
    samples=[("abc 2", "ab\nac\nbc"), ("xyz 3", "xyz")],
    hidden=["abcdefghij 5", "dcba 1", "qwertyuiopas 6"],
)

# ---------------- 21. OOP: klass va obyekt ----------------
code_problem(
    slug="l21-tortburchak", title="To‘rtburchak klassi", lesson=21, level=0, difficulty=1, tags=["oop"],
    statement="""
        `Rectangle` klassini yozing: konstruktor kenglik va balandlikni qabul qiladi, `area()` va
        `perimeter()` metodlari bor. Berilgan to‘rtburchakning yuzasi va perimetrini chiqaring.
    """,
    input_format="Bitta qatorda $w$ va $h$ ($1 \\le w, h \\le 10^9$).",
    output_format="Yuza va perimetr.",
    solution="""
        class Rectangle:
            def __init__(self, width: int, height: int) -> None:
                self.width = width
                self.height = height

            def area(self) -> int:
                return self.width * self.height

            def perimeter(self) -> int:
                return 2 * (self.width + self.height)


        rect = Rectangle(*map(int, input().split()))
        print(rect.area(), rect.perimeter())
    """,
    samples=[("3 4", "12 14"), ("1 1", "1 4")],
    hidden=["1000000000 1000000000", "5 1", "7 9"],
)

code_problem(
    slug="l21-vektor", title="Vektor klassi", lesson=21, level=1, difficulty=2, tags=["oop"],
    statement="""
        Ikki o‘lchamli `Vector` klassini yozing. `__add__` metodi vektorlarni qo‘shadi, `dot` metodi skalyar
        ko‘paytmani ($x_1 x_2 + y_1 y_2$) qaytaradi. Ikki vektorning yig‘indisi va skalyar ko‘paytmasini
        chiqaring.
    """,
    input_format="Ikki qatorda vektorlar: $x$ va $y$ ($|x|, |y| \\le 10^9$).",
    output_format="Birinchi qatorda yig‘indi vektor, ikkinchi qatorda skalyar ko‘paytma.",
    solution="""
        class Vector:
            def __init__(self, x: int, y: int) -> None:
                self.x = x
                self.y = y

            def __add__(self, other: "Vector") -> "Vector":
                return Vector(self.x + other.x, self.y + other.y)

            def dot(self, other: "Vector") -> int:
                return self.x * other.x + self.y * other.y


        a = Vector(*map(int, input().split()))
        b = Vector(*map(int, input().split()))
        s = a + b
        print(s.x, s.y)
        print(a.dot(b))
    """,
    samples=[("1 2\n3 4", "4 6\n11"), ("0 0\n5 -5", "5 -5\n0")],
    hidden=["-1000000000 1000000000\n1000000000 1000000000", "3 0\n0 3", "-2 -3\n-4 -5"],
)

code_problem(
    slug="l21-kutubxona", title="Kutubxona", lesson=21, level=2, difficulty=3, tags=["oop", "dict"],
    statement="""
        `Library` klassini yozing va buyruqlarni bajaring (kitob nomlarida bo‘shliq yo‘q):

        - `qosh NOM` — kitob qo‘shish: `qoshildi`, agar bor bo‘lsa — `mavjud`;
        - `ol NOM` — kitobni olish: `berildi`; kitob yo‘q bo‘lsa — `topilmadi`; boshqada bo‘lsa — `band`;
        - `qaytar NOM` — qaytarish: `qaytarildi`; kitob berilmagan bo‘lsa — `xato`;
        - `royxat` — javondagi (berilmagan) kitoblar alifbo tartibida bitta qatorda; bo‘sh bo‘lsa `-`.
    """,
    input_format="Birinchi qatorda $n$ ($1 \\le n \\le 10^4$), keyingi $n$ qatorda buyruqlar.",
    output_format="Har bir buyruq uchun bitta qator.",
    solution="""
        class Library:
            def __init__(self) -> None:
                self.books: dict[str, bool] = {}  # nom -> berilganmi

            def add(self, name: str) -> str:
                if name in self.books:
                    return "mavjud"
                self.books[name] = False
                return "qoshildi"

            def take(self, name: str) -> str:
                if name not in self.books:
                    return "topilmadi"
                if self.books[name]:
                    return "band"
                self.books[name] = True
                return "berildi"

            def give_back(self, name: str) -> str:
                if not self.books.get(name):
                    return "xato"
                self.books[name] = False
                return "qaytarildi"

            def shelf(self) -> str:
                free = sorted(name for name, taken in self.books.items() if not taken)
                return " ".join(free) if free else "-"


        library = Library()
        for _ in range(int(input())):
            parts = input().split()
            match parts:
                case ["qosh", name]:
                    print(library.add(name))
                case ["ol", name]:
                    print(library.take(name))
                case ["qaytar", name]:
                    print(library.give_back(name))
                case ["royxat"]:
                    print(library.shelf())
    """,
    samples=[("6\nqosh Alpomish\nqosh Otamdan_qolgan_dalalar\nol Alpomish\nol Alpomish\nroyxat\nqaytar Alpomish",
              "qoshildi\nqoshildi\nberildi\nband\nOtamdan_qolgan_dalalar\nqaytarildi"),
             ("2\nol X\nroyxat", "topilmadi\n-")],
    hidden=["3\nqosh A\nqosh A\nqaytar A", "4\nqosh B\nqosh A\nol A\nroyxat","5000\n" + "\n".join(
        R.choice([f"qosh k{R.randint(1, 50)}", f"ol k{R.randint(1, 50)}", f"qaytar k{R.randint(1, 50)}", "royxat"])
        for _ in range(5000))],
)

# ---------------- 22. Meros va inkapsulyatsiya ----------------
code_problem(
    slug="l22-shakllar", title="Shakllar yuzasi", lesson=22, level=0, difficulty=2, tags=["oop", "meros"],
    statement="""
        `Shape` asosiy klassi va undan meros oluvchi `Circle`, `Square`, `Triangle` klasslarini yozing —
        har birida `area()` metodi. Barcha shakllar yuzalari yig‘indisini 2 xona aniqlikda chiqaring.

        - `doira r` — $\\pi r^2$ (`math.pi`);
        - `kvadrat a` — $a^2$;
        - `uchburchak a h` — $a \\cdot h / 2$.
    """,
    input_format="Birinchi qatorda $n$ ($1 \\le n \\le 1000$), keyingi qatorlarda shakllar (o‘lchamlar $\\le 1000$).",
    output_format="Yuzalar yig‘indisi.",
    solution="""
        import math


        class Shape:
            def area(self) -> float:
                raise NotImplementedError


        class Circle(Shape):
            def __init__(self, r: float) -> None:
                self.r = r

            def area(self) -> float:
                return math.pi * self.r ** 2


        class Square(Shape):
            def __init__(self, a: float) -> None:
                self.a = a

            def area(self) -> float:
                return self.a ** 2


        class Triangle(Shape):
            def __init__(self, a: float, h: float) -> None:
                self.a = a
                self.h = h

            def area(self) -> float:
                return self.a * self.h / 2


        KINDS = {"doira": Circle, "kvadrat": Square, "uchburchak": Triangle}
        shapes = []
        for _ in range(int(input())):
            kind, *sizes = input().split()
            shapes.append(KINDS[kind](*map(float, sizes)))
        print(f"{sum(s.area() for s in shapes):.2f}")
    """,
    checker="float", epsilon=1e-3,
    samples=[("2\nkvadrat 2\nuchburchak 3 4", "10.00"), ("1\ndoira 1", "3.14")],
    hidden=["3\ndoira 10\nkvadrat 1000\nuchburchak 1 1", "1\nuchburchak 3 3","1000\n" + "\n".join(
        R.choice([f"doira {R.randint(1, 100)}", f"kvadrat {R.randint(1, 100)}",
                  f"uchburchak {R.randint(1, 100)} {R.randint(1, 100)}"]) for _ in range(1000))],
)

code_problem(
    slug="l22-xodimlar", title="Xodimlar maoshi", lesson=22, level=1, difficulty=3, tags=["oop", "meros"],
    statement="""
        `Employee` klassi (ism, asosiy maosh, `salary()` metodi) va undan meros oluvchi klasslar yozing:

        - `xodim NOM M` — maosh $M$;
        - `dasturchi NOM M` — maosh $M + 20\\%$, butun qismi: $M \\cdot 6 // 5$;
        - `menejer NOM M B` — maosh $M + B$ (bonus).

        Har bir xodimni kiritilgan tartibda `ism maosh` ko‘rinishida, oxirida `jami: S` chiqaring.
    """,
    input_format="Birinchi qatorda $n$ ($1 \\le n \\le 1000$), keyingi qatorlarda xodimlar ($M, B \\le 10^9$).",
    output_format="$n$ qator va jami.",
    solution="""
        class Employee:
            def __init__(self, name: str, base: int) -> None:
                self.name = name
                self._base = base

            def salary(self) -> int:
                return self._base


        class Developer(Employee):
            def salary(self) -> int:
                return self._base * 6 // 5


        class Manager(Employee):
            def __init__(self, name: str, base: int, bonus: int) -> None:
                super().__init__(name, base)
                self._bonus = bonus

            def salary(self) -> int:
                return self._base + self._bonus


        KINDS = {"xodim": Employee, "dasturchi": Developer, "menejer": Manager}
        staff = []
        for _ in range(int(input())):
            kind, name, *numbers = input().split()
            staff.append(KINDS[kind](name, *map(int, numbers)))
        for person in staff:
            print(person.name, person.salary())
        print(f"jami: {sum(p.salary() for p in staff)}")
    """,
    samples=[("3\nxodim Ali 1000\ndasturchi Vali 1000\nmenejer Guli 2000 500",
              "Ali 1000\nVali 1200\nGuli 2500\njami: 4700"),
             ("1\ndasturchi X 5", "X 6\njami: 6")],
    hidden=["2\nmenejer A 0 0\nxodim B 1000000000", "1\ndasturchi Y 1000000000","1000\n" + "\n".join(
        R.choice([f"xodim x{i} {R.randint(1, 10 ** 7)}", f"dasturchi d{i} {R.randint(1, 10 ** 7)}",
                  f"menejer m{i} {R.randint(1, 10 ** 7)} {R.randint(0, 10 ** 6)}"]) for i in range(1000))],
)

code_problem(
    slug="l22-stek", title="Stek klassi", lesson=22, level=2, difficulty=3, tags=["oop", "inkapsulyatsiya"],
    statement="""
        Ichki ro‘yxati yashirin (`self._items`) bo‘lgan `Stack` klassini yozing. Buyruqlar:

        - `push X` — $X$ ni qo‘shish (hech narsa chiqarilmaydi);
        - `pop` — yuqoridagi elementni olib tashlash va chiqarish;
        - `peek` — yuqoridagi elementni chiqarish (olib tashlamasdan);
        - `size` — elementlar soni.

        Stek bo‘sh bo‘lganda `pop` va `peek` uchun `-` chiqaring.
    """,
    input_format="Birinchi qatorda $n$ ($1 \\le n \\le 10^5$), keyingi qatorlarda buyruqlar.",
    output_format="`pop`, `peek`, `size` natijalari.",
    solution="""
        import sys


        class Stack:
            def __init__(self) -> None:
                self._items: list[str] = []

            def push(self, item: str) -> None:
                self._items.append(item)

            def pop(self) -> str:
                return self._items.pop() if self._items else "-"

            def peek(self) -> str:
                return self._items[-1] if self._items else "-"

            def size(self) -> int:
                return len(self._items)


        lines = sys.stdin.read().split("\\n")
        stack = Stack()
        out = []
        for line in lines[1:1 + int(lines[0])]:
            parts = line.split()
            if parts[0] == "push":
                stack.push(parts[1])
            elif parts[0] == "pop":
                out.append(stack.pop())
            elif parts[0] == "peek":
                out.append(stack.peek())
            else:
                out.append(str(stack.size()))
        print("\\n".join(out))
    """,
    samples=[("6\npush 5\npush 7\npeek\npop\npop\npop", "7\n7\n5\n-"), ("2\nsize\npush 1", "0")],
    hidden=["3\npeek\npush 0\nsize", "4\npush a\npush b\npop\npeek","100000\n" + "\n".join(
        R.choice([f"push {R.randint(-99, 99)}", "pop", "peek", "size", "push 1"]) for _ in range(99999)) + "\nsize"],
)

# ---------------- 23. Kod sifati, branch va PR ----------------
code_problem(
    slug="l23-snake-case", title="camelCase → snake_case", lesson=23, level=0, difficulty=1,
    tags=["satrlar", "kod sifati"],
    statement="""
        PEP 8 bo‘yicha o‘zgaruvchi nomlari `snake_case` da yoziladi. `camelCase` nomni aylantiring:
        har bir katta harf oldiga (agar u birinchi belgi bo‘lmasa) `_` qo‘yiladi va harf kichik qilinadi.
    """,
    input_format="Bitta qatorda nom (lotin harflari va raqamlar, uzunligi 1–100).",
    output_format="`snake_case` nom.",
    solution="""
        name = input().strip()
        result = []
        for i, ch in enumerate(name):
            if ch.isupper():
                if i > 0:
                    result.append("_")
                result.append(ch.lower())
            else:
                result.append(ch)
        print("".join(result))
    """,
    samples=[("myVariableName", "my_variable_name"), ("x", "x")],
    hidden=["UserProfile", "getHTTPResponse", "item2Count", "already_snake"],
)

_long = "y = " + "1" * 80
code_problem(
    slug="l23-pep8", title="PEP 8 tekshiruvchi", lesson=23, level=1, difficulty=2, tags=["satrlar", "kod sifati"],
    statement="""
        Kichik linter yozing. Kodning har bir qatori uchun (raqamlash 1 dan):

        - uzunligi 79 belgidan oshsa — `i E501`;
        - oxirida bo‘shliq bo‘lsa — `i W291`.

        Ikkala xato bo‘lsa, avval `E501`. Hech qanday xato bo‘lmasa, `toza` chiqaring.
    """,
    input_format="Birinchi qatorda $n$ ($1 \\le n \\le 1000$), keyingi $n$ qatorda kod (bo‘sh qatorlar bo‘lishi mumkin).",
    output_format="Xatolar ro‘yxati yoki `toza`.",
    solution="""
        import sys

        lines = sys.stdin.read().split("\\n")
        n = int(lines[0])
        problems = []
        for number, line in enumerate(lines[1:1 + n], start=1):
            if len(line) > 79:
                problems.append(f"{number} E501")
            if line != line.rstrip():
                problems.append(f"{number} W291")
        print("\\n".join(problems) if problems else "toza")
    """,
    samples=[("3\nx = 1   \nprint(x)\n" + _long, "1 W291\n3 E501"), ("1\npass", "toza")],
    hidden=["2\n" + "a" * 79 + "\n" + "b" * 80 + " ",
            "4\ndef f():\n\n    return 1\t\n",
            "1000\n" + "\n".join("x" * R.randint(0, 90) + R.choice(["", " ", "  "]) for _ in range(1000))],
)

code_problem(
    slug="l23-branch-nomi", title="Branch nomini tekshirish", lesson=23, level=2, difficulty=3,
    tags=["satrlar", "git"],
    statement="""
        Jamoada branch nomlari qoidasi:

        - faqat kichik lotin harflari, raqamlar va `-`, `_`, `/`, `.` belgilari;
        - `-`, `/` yoki `.` bilan boshlanmaydi;
        - `/` yoki `.` bilan, shuningdek `.lock` bilan tugamaydi;
        - `..` va `//` ketma-ketliklari yo‘q;
        - uzunligi 1–100.

        Har bir nom uchun `OK` yoki `XATO` chiqaring.
    """,
    input_format="Birinchi qatorda $n$ ($1 \\le n \\le 1000$), keyingi $n$ qatorda nomlar (bo‘shliq bo‘lishi mumkin).",
    output_format="Har bir nom uchun natija.",
    solution="""
        ALLOWED = set("abcdefghijklmnopqrstuvwxyz0123456789-_/.")


        def is_valid(name: str) -> bool:
            return (
                1 <= len(name) <= 100
                and set(name) <= ALLOWED
                and name[0] not in "-/."
                and name[-1] not in "/."
                and not name.endswith(".lock")
                and ".." not in name
                and "//" not in name
            )


        n = int(input())
        for _ in range(n):
            print("OK" if is_valid(input()) else "XATO")
    """,
    samples=[("4\nfeature/login\nFix bug\nrelease/v1.2\n-hotfix", "OK\nXATO\nOK\nXATO"),
             ("2\nmain\nstage-3-problems", "OK\nOK")],
    hidden=["6\na..b\na//b\nx.lock\nx/\n.hidden\nok_name.v2", "2\n" + "a" * 100 + "\n" + "a" * 101,
            "300\n" + "\n".join("".join(R.choice("ab-/._Z") for _ in range(R.randint(1, 8))) for _ in range(300))],
)

# ---------------- 24. Loyiha 2 himoyasi (takrorlash) ----------------
code_problem(
    slug="l24-anagramma", title="Anagramma", lesson=24, level=0, difficulty=1, tags=["satrlar", "saralash"],
    statement="""
        Ikki so‘z bir xil harflardan (bir xil miqdorda) tuzilganmi? Katta-kichik harf farqlanmaydi.
        `ha` yoki `yo'q` chiqaring.
    """,
    input_format="Ikki qatorda so‘zlar (uzunligi $10^5$ gacha).",
    output_format="`ha` yoki `yo'q`.",
    solution="""
        a = input().strip().lower()
        b = input().strip().lower()
        print("ha" if sorted(a) == sorted(b) else "yo'q")
    """,
    samples=[("listen\nsilent", "ha"), ("olma\nnok", "yo'q")],
    hidden=["Kitob\nbotik", "aab\nabb", "a\na"],
)

code_problem(
    slug="l24-transpoza", title="Matritsani transponirlash", lesson=24, level=1, difficulty=2, tags=["list"],
    statement="""
        $n \\times m$ matritsa berilgan. Uni transponirlang: qatorlar ustunga, ustunlar qatorga aylanadi
        (natija $m \\times n$).
    """,
    input_format="Birinchi qatorda $n$ va $m$ ($1 \\le n, m \\le 300$), keyingi $n$ qatorda $m$ tadan son.",
    output_format="$m$ qator, har birida $n$ ta son.",
    solution="""
        n, m = map(int, input().split())
        matrix = [input().split() for _ in range(n)]
        for row in zip(*matrix):
            print(*row)
    """,
    samples=[("2 3\n1 2 3\n4 5 6", "1 4\n2 5\n3 6"), ("1 1\n7", "7")],
    hidden=["1 4\n1 2 3 4", "300 300\n" + "\n".join(nums(300, -99, 99) for _ in range(300)), "3 1\n1\n2\n3"],
)

code_problem(
    slug="l24-reyting-jadvali", title="Reyting jadvali", lesson=24, level=2, difficulty=3,
    tags=["dict", "saralash"],
    statement="""
        Musobaqa natijalari: har bir qatorda `ism ball` (bitta ism bir necha marta uchrashi mumkin).
        Har bir ishtirokchining jami ballini hisoblang va reyting jadvalini chiqaring: jami ball
        kamayishi bo‘yicha, teng bo‘lsa — ism bo‘yicha alifbo tartibida.

        Ballari teng ishtirokchilar bir xil o‘rinni egallaydi, keyingi o‘rin shunga ko‘ra suriladi
        (masalan: 1, 1, 3). Har bir qatorda `o‘rin ism jami`.
    """,
    input_format="Birinchi qatorda $n$ ($1 \\le n \\le 10^5$), keyingi $n$ qatorda natijalar ($0 \\le$ ball $\\le 100$).",
    output_format="Reyting jadvali.",
    solution="""
        import sys

        lines = sys.stdin.read().split("\\n")
        totals = {}
        for line in lines[1:1 + int(lines[0])]:
            name, score = line.split()
            totals[name] = totals.get(name, 0) + int(score)
        ranking = sorted(totals.items(), key=lambda item: (-item[1], item[0]))
        place = 0
        for index, (name, total) in enumerate(ranking, start=1):
            if index == 1 or total != ranking[index - 2][1]:
                place = index
            print(place, name, total)
    """,
    samples=[("4\nAli 10\nVali 15\nAli 5\nGuli 7", "1 Ali 15\n1 Vali 15\n3 Guli 7"), ("1\nX 0", "1 X 0")],
    hidden=["3\nA 5\nB 5\nC 5", "5\nA 1\nB 2\nC 2\nD 2\nE 0","100000\n" + "\n".join(f"p{R.randint(1, 2000)} {R.randint(0, 100)}"
                                                        for _ in range(100000))],
)
