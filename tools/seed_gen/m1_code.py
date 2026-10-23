"""Modul 1 (1–12-darslar) code masalalari."""
import random

from common import code_problem

R = random.Random(2026)


def hexhash() -> str:
    return "".join(R.choice("0123456789abcdef") for _ in range(40))


# ---------------- 1. Kompyuter va ish muhiti ----------------
code_problem(
    slug="l01-kilobayt", title="Kilobaytdan baytga", lesson=1, level=0, difficulty=1, tags=["arifmetika"],
    statement="""
        Kompyuterda fayl hajmi kilobaytlarda (KB) ko‘rsatilgan. 1 KB = 1024 bayt.
        Fayl hajmini baytlarda chiqaring.
    """,
    input_format="Bitta butun son $K$ ($0 \\le K \\le 10^9$) — hajm kilobaytlarda.",
    output_format="Hajm baytlarda.",
    solution="""
        k = int(input())
        print(k * 1024)
    """,
    samples=[("5", "5120"), ("0", "0")],
    hidden=["1", "1024", "1000000000"],
)

code_problem(
    slug="l01-fayl-kengaytmasi", title="Fayl kengaytmasi", lesson=1, level=1, difficulty=2,
    tags=["satrlar", "fayllar"],
    statement="""
        Fayl nomi berilgan. Uning kengaytmasini (oxirgi nuqtadan keyingi qism) **kichik harflarda** chiqaring.

        Agar nomda nuqta bo‘lmasa, nuqta nomning birinchi belgisi bo‘lsa (masalan, `.gitignore`)
        yoki nuqta oxirgi belgi bo‘lsa — kengaytma yo‘q: `yo'q` chiqaring (oddiy apostrof bilan).
    """,
    input_format="Bitta qatorda fayl nomi (bo‘shliqsiz, uzunligi 1–100).",
    output_format="Kengaytma kichik harflarda yoki `yo'q`.",
    solution="""
        name = input().strip()
        dot = name.rfind(".")
        if dot <= 0 or dot == len(name) - 1:
            print("yo'q")
        else:
            print(name[dot + 1:].lower())
    """,
    samples=[("rasm.PNG", "png"), ("README", "yo'q")],
    hidden=[".gitignore", "arxiv.tar.gz", "hisobot.", "Dars.Py", "a.b"],
)

code_problem(
    slug="l01-disk-joyi", title="Diskdagi bo‘sh joy", lesson=1, level=2, difficulty=3, tags=["tsikl", "arifmetika"],
    statement="""
        Fleshkaning hajmi $C$ gigabayt (1 GB = 1024 MB). Unga $n$ ta fayl **berilgan tartibda** nusxalanadi.
        Agar navbatdagi fayl qolgan joyga sig‘masa, nusxalash shu yerda to‘xtaydi.

        Nechta fayl nusxalanganini va qancha joy (MB) bo‘sh qolganini aniqlang.
    """,
    input_format="""
        Birinchi qatorda $C$ va $n$ ($0 \\le C \\le 1000$, $1 \\le n \\le 1000$).
        Ikkinchi qatorda $n$ ta fayl hajmi (MB, $1 \\le s_i \\le 10^6$).
    """,
    output_format="Ikki son: nusxalangan fayllar soni va bo‘sh qolgan joy (MB).",
    solution="""
        c, n = map(int, input().split())
        sizes = list(map(int, input().split()))
        free = c * 1024
        count = 0
        for size in sizes:
            if size > free:
                break
            free -= size
            count += 1
        print(count, free)
    """,
    samples=[("1 3\n500 400 200", "2 124"), ("2 2\n1024 1024", "2 0")],
    hidden=["0 1\n1", "5 4\n100 6000 1 1",
            "1000 1000\n" + " ".join(str(R.randint(1, 2000)) for _ in range(1000))],
)

# ---------------- 2. Terminal (CLI) ----------------
code_problem(
    slug="l02-toliq-yol", title="To‘liq yo‘l", lesson=2, level=0, difficulty=1, tags=["satrlar", "terminal"],
    statement="""
        Terminalda `pwd` buyrug‘i joriy papkaning to‘liq yo‘lini chiqaradi, masalan `/home/nurbek/kodx`.
        Ildizdan boshlab ichma-ich papkalar nomlari berilgan — to‘liq yo‘lni chiqaring.
        Agar papkalar soni 0 bo‘lsa, javob — ildiz `/`.
    """,
    input_format="Birinchi qatorda $n$ ($0 \\le n \\le 50$). Agar $n > 0$, ikkinchi qatorda $n$ ta papka nomi.",
    output_format="To‘liq yo‘l.",
    solution="""
        import sys

        data = sys.stdin.read().split()
        n = int(data[0])
        print("/" + "/".join(data[1:1 + n]))
    """,
    samples=[("3\nhome nurbek kodx", "/home/nurbek/kodx"), ("0", "/")],
    hidden=["1\nusr", "5\na b c d e", "2\nDocuments Rasmlar"],
)

code_problem(
    slug="l02-cd-buyruqlari", title="cd buyruqlari", lesson=2, level=1, difficulty=2, tags=["satrlar", "terminal"],
    statement="""
        Siz ildiz papkada (`/`) turibsiz. Ketma-ket `cd` buyruqlari bajariladi:

        - `cd NOM` — `NOM` papkasiga kirish;
        - `cd ..` — bir daraja yuqoriga (ildizda bo‘lsangiz, joyida qolasiz);
        - `cd /` — ildizga qaytish.

        Barcha buyruqlardan keyingi to‘liq yo‘lni chiqaring.
    """,
    input_format="Birinchi qatorda $n$ ($1 \\le n \\le 1000$), keyingi $n$ qatorda buyruqlar.",
    output_format="Oxirgi to‘liq yo‘l.",
    solution="""
        n = int(input())
        path = []
        for _ in range(n):
            arg = input().split()[1]
            if arg == "/":
                path = []
            elif arg == "..":
                if path:
                    path.pop()
            else:
                path.append(arg)
        print("/" + "/".join(path))
    """,
    samples=[("4\ncd home\ncd nurbek\ncd ..\ncd kodx", "/home/kodx"), ("3\ncd ..\ncd tmp\ncd /", "/")],
    hidden=["1\ncd ..", "5\ncd a\ncd b\ncd c\ncd ..\ncd d",
            "6\ncd x\ncd /\ncd y\ncd ..\ncd ..\ncd z",
            "200\n" + "\n".join(R.choice(["cd ..", "cd /", f"cd p{R.randint(1, 9)}", f"cd q{R.randint(1, 9)}"])
                                for _ in range(200))],
)

code_problem(
    slug="l02-kengaytma-statistikasi", title="Kengaytmalar statistikasi", lesson=2, level=2, difficulty=3,
    tags=["satrlar", "lug‘at", "terminal"],
    statement="""
        `ls` buyrug‘i papkadagi fayllar ro‘yxatini chiqardi. Har bir kengaytma bo‘yicha fayllar sonini hisoblang.

        Kengaytma — oxirgi nuqtadan keyingi qism, **kichik harflarda**. Nuqta bo‘lmasa, nuqta birinchi yoki
        oxirgi belgi bo‘lsa — kengaytma yo‘q, uni `-` deb hisoblang.

        Natijani kengaytmalar bo‘yicha alifbo tartibida chiqaring (`-` belgisi harflardan oldin keladi).
    """,
    input_format="Birinchi qatorda $n$ ($1 \\le n \\le 10^4$), keyingi $n$ qatorda fayl nomlari.",
    output_format="Har bir qatorda: kengaytma va fayllar soni.",
    solution="""
        n = int(input())
        counts = {}
        for _ in range(n):
            name = input().strip()
            dot = name.rfind(".")
            ext = "-" if dot <= 0 or dot == len(name) - 1 else name[dot + 1:].lower()
            counts[ext] = counts.get(ext, 0) + 1
        for ext in sorted(counts):
            print(ext, counts[ext])
    """,
    samples=[("5\nmain.py\nutils.PY\nREADME\nstyle.css\nindex.html", "- 1\ncss 1\nhtml 1\npy 2"),
             ("2\na.txt\nb.txt", "txt 2")],
    hidden=["3\n.env\nMakefile\nx.", "4\nA.JPG\nb.jpg\nc.Jpg\nd.png",
            "300\n" + "\n".join(f"f{i}." + R.choice(["py", "PY", "md", "txt", "js", "html", ""]) for i in range(300))],
)

# ---------------- 3. Git asoslari ----------------
code_problem(
    slug="l03-commit-xabari", title="Commit xabari uzunligi", lesson=3, level=0, difficulty=1,
    tags=["satrlar", "git"],
    statement="""
        Yaxshi commit xabarining birinchi qatori **50 belgidan oshmasligi** tavsiya etiladi.
        Xabar berilgan (boshi va oxiridagi bo‘shliqlar hisobga olinmaydi). Uzunligi 50 dan oshmasa `OK`,
        aks holda `UZUN` chiqaring.
    """,
    input_format="Bitta qatorda bo‘sh bo‘lmagan commit xabari (uzunligi 200 gacha).",
    output_format="`OK` yoki `UZUN`.",
    solution="""
        message = input().strip()
        print("OK" if len(message) <= 50 else "UZUN")
    """,
    samples=[("Poydevor: Django, MySQL, rollar, audit", "OK"),
             ("Bu juda uzun commit xabari bo'lib, u ellik belgidan oshib ketadi", "UZUN")],
    hidden=["a" * 50, "b" * 51, "x", "   " + "c" * 50 + "   "],
)

code_problem(
    slug="l03-git-status", title="git status hisoboti", lesson=3, level=1, difficulty=2, tags=["satrlar", "git"],
    statement="""
        `git status --short` buyrug‘i har bir fayl uchun holat kodini chiqaradi:
        `M` — o‘zgartirilgan, `A` — qo‘shilgan, `D` — o‘chirilgan, `??` — kuzatilmayotgan (yangi).

        Har bir kod bo‘yicha fayllar sonini `M`, `A`, `D`, `??` tartibida chiqaring.
    """,
    input_format="Birinchi qatorda $n$ ($0 \\le n \\le 1000$), keyingi $n$ qatorda `KOD fayl_nomi`.",
    output_format="To‘rt qator: `M x`, `A y`, `D z`, `?? w`.",
    solution="""
        n = int(input())
        counts = {"M": 0, "A": 0, "D": 0, "??": 0}
        for _ in range(n):
            code = input().split()[0]
            counts[code] += 1
        for code in ("M", "A", "D", "??"):
            print(code, counts[code])
    """,
    samples=[("4\nM app.py\n?? notes.txt\nA README.md\nM models.py", "M 2\nA 1\nD 0\n?? 1"),
             ("0", "M 0\nA 0\nD 0\n?? 0")],
    hidden=["3\nD a\nD b\nD c",
            "100\n" + "\n".join(f"{R.choice(['M', 'A', 'D', '??'])} f{i}.py" for i in range(100)),
            "1\n?? .env.example"],
)

_h2 = ["abcdef1" + "0" * 33, "abcdef2" + "0" * 33]
code_problem(
    slug="l03-qisqa-hash", title="Qisqa commit hash", lesson=3, level=2, difficulty=3, tags=["satrlar", "to‘plam", "git"],
    statement="""
        Git commit’ning to‘liq hash’i 40 ta o‘n oltilik belgidan iborat, lekin odatda uning boshidagi bir nechta
        belgisi (qisqa hash) yetarli bo‘ladi.

        $n$ ta turli hash berilgan. Shunday eng kichik $k \\ge 4$ ni topingki, barcha hash’larning
        birinchi $k$ ta belgisi o‘zaro farq qilsin.
    """,
    input_format="Birinchi qatorda $n$ ($1 \\le n \\le 2000$), keyingi $n$ qatorda 40 belgili hash’lar.",
    output_format="Bitta son $k$.",
    solution="""
        n = int(input())
        hashes = [input().strip() for _ in range(n)]
        k = 4
        while len({h[:k] for h in hashes}) < n:
            k += 1
        print(k)
    """,
    samples=[("3\n" + "\n".join(["abcd" + "1" * 36, "abce" + "2" * 36, "f000" + "3" * 36]), "4"),
             ("2\n" + "\n".join(_h2), "7")],
    hidden=["1\n" + hexhash(), "2000\n" + "\n".join(hexhash() for _ in range(2000)),
            "3\n" + "\n".join(["0123456789" + "a" * 30, "0123456789" + "b" * 30, "f" * 40])],
)

# ---------------- 4. GitHub ----------------
code_problem(
    slug="l04-repo-havolasi", title="Repozitoriy havolasi", lesson=4, level=0, difficulty=1,
    tags=["satrlar", "github"],
    statement="""
        GitHub foydalanuvchi nomi va repozitoriy nomi berilgan. `git clone` uchun havolani
        `https://github.com/<foydalanuvchi>/<repozitoriy>.git` ko‘rinishida chiqaring.
    """,
    input_format="Birinchi qatorda foydalanuvchi nomi, ikkinchi qatorda repozitoriy nomi.",
    output_format="Havola.",
    solution="""
        user = input().strip()
        repo = input().strip()
        print(f"https://github.com/{user}/{repo}.git")
    """,
    samples=[("SoliyevNurbek\nkodx", "https://github.com/SoliyevNurbek/kodx.git"),
             ("alisher\nportfolio", "https://github.com/alisher/portfolio.git")],
    hidden=["a\nb", "dev-team\nweb_site.v2", "Z\nhello-world"],
)

code_problem(
    slug="l04-havola-tahlili", title="Havolani tahlil qilish", lesson=4, level=1, difficulty=2,
    tags=["satrlar", "github"],
    statement="""
        GitHub repozitoriy havolasi quyidagi ko‘rinishlardan birida berilgan:

        - `https://github.com/EGASI/REPO` (oxirida `.git` va/yoki `/` bo‘lishi mumkin);
        - `git@github.com:EGASI/REPO.git`.

        Egasi va repozitoriy nomini alohida qatorlarda chiqaring (`.git` qo‘shimchasisiz).
    """,
    input_format="Bitta qatorda havola.",
    output_format="Birinchi qatorda egasi, ikkinchi qatorda repozitoriy nomi.",
    solution="""
        url = input().strip()
        prefix = "git@github.com:"
        rest = url[len(prefix):] if url.startswith(prefix) else url.split("github.com/", 1)[1]
        rest = rest.strip("/")
        if rest.endswith(".git"):
            rest = rest[:-4]
        owner, repo = rest.split("/")[:2]
        print(owner)
        print(repo)
    """,
    samples=[("https://github.com/SoliyevNurbek/kodx", "SoliyevNurbek\nkodx"),
             ("git@github.com:django/django.git", "django\ndjango")],
    hidden=["https://github.com/a/b.git", "https://github.com/user/repo/", "http://github.com/x-y/z_w.git/",
            "git@github.com:team/bot-v2.git"],
)

code_problem(
    slug="l04-top-repolar", title="Eng mashhur repozitoriylar", lesson=4, level=2, difficulty=3,
    tags=["saralash", "github"],
    statement="""
        $n$ ta repozitoriy nomi va yulduzlar (stars) soni berilgan. Eng ko‘p yulduzli **3 tasini**
        (agar $n < 3$ bo‘lsa — hammasini) chiqaring.

        Yulduzlar soni kamayish tartibida; teng bo‘lsa — nomi alifbo tartibida.
    """,
    input_format="Birinchi qatorda $n$ ($1 \\le n \\le 10^5$), keyingi $n$ qatorda `nom yulduzlar`.",
    output_format="Har bir qatorda `nom yulduzlar`.",
    solution="""
        import sys

        lines = sys.stdin.read().split("\\n")
        n = int(lines[0])
        repos = []
        for line in lines[1:1 + n]:
            name, stars = line.split()
            repos.append((-int(stars), name))
        repos.sort()
        for stars, name in repos[:3]:
            print(name, -stars)
    """,
    samples=[("5\nkodx 120\nportfolio 45\nbot 120\ncalc 3\nblog 80", "bot 120\nkodx 120\nblog 80"),
             ("2\na 1\nb 2", "b 2\na 1")],
    hidden=["1\nsolo 0", "4\nd 5\nc 5\nb 5\na 5",
            "100000\n" + "\n".join(f"r{i} {R.randint(0, 10 ** 6)}" for i in range(100000))],
)

# ---------------- 5. Python: birinchi qadamlar ----------------
code_problem(
    slug="l05-salom", title="Salom!", lesson=5, level=0, difficulty=1, tags=["kirish-chiqish"],
    statement="""
        Foydalanuvchi ismini o‘qing va `Salom, <ism>!` deb chiqaring.
    """,
    input_format="Bitta qatorda ism.",
    output_format="`Salom, <ism>!`",
    solution="""
        name = input().strip()
        print(f"Salom, {name}!")
    """,
    checker="exact",
    samples=[("Ali", "Salom, Ali!"), ("Nodira", "Salom, Nodira!")],
    hidden=["Muhammadali", "X", "Dilnoza"],
)

code_problem(
    slug="l05-ikki-son", title="Ikki son yig‘indisi", lesson=5, level=1, difficulty=1, tags=["kirish-chiqish"],
    statement="""
        Ikkita butun son berilgan. Ularning yig‘indisini chiqaring.
    """,
    input_format="Birinchi qatorda $a$, ikkinchi qatorda $b$ ($|a|, |b| \\le 10^{18}$).",
    output_format="$a + b$",
    solution="""
        a = int(input())
        b = int(input())
        print(a + b)
    """,
    samples=[("2\n3", "5"), ("-10\n4", "-6")],
    hidden=["0\n0", "1000000000000000000\n1000000000000000000", "-5\n5"],
)

code_problem(
    slug="l05-xarid-cheki", title="Xarid cheki", lesson=5, level=2, difficulty=2, tags=["kirish-chiqish"],
    statement="""
        Do‘konda mahsulot nomi, bitta mahsulot narxi va soni kiritiladi. Chekni quyidagi ko‘rinishda chiqaring:

        ```
        Mahsulot: <nomi>
        Soni: <soni>
        Jami: <narx * soni>
        ```
    """,
    input_format="Uch qator: mahsulot nomi, narxi (butun, $\\le 10^9$), soni (butun, $\\le 10^6$).",
    output_format="Uch qatorli chek.",
    solution="""
        name = input().strip()
        price = int(input())
        count = int(input())
        print(f"Mahsulot: {name}")
        print(f"Soni: {count}")
        print(f"Jami: {price * count}")
    """,
    checker="exact",
    samples=[("daftar\n5000\n3", "Mahsulot: daftar\nSoni: 3\nJami: 15000"),
             ("ruchka\n2500\n10", "Mahsulot: ruchka\nSoni: 10\nJami: 25000")],
    hidden=["kitob\n45000\n1", "olma\n0\n100", "noutbuk\n1000000000\n1000000"],
)

# ---------------- 6. Arifmetika, satrlar, f-string ----------------
code_problem(
    slug="l06-raqamlar-yigindisi", title="Raqamlar yig‘indisi", lesson=6, level=0, difficulty=1,
    tags=["arifmetika"],
    statement="""
        Uch xonali son berilgan. Uning raqamlari yig‘indisini **arifmetik amallar** (`//` va `%`) yordamida toping.
    """,
    input_format="Bitta uch xonali son $n$ ($100 \\le n \\le 999$).",
    output_format="Raqamlar yig‘indisi.",
    solution="""
        n = int(input())
        print(n // 100 + n // 10 % 10 + n % 10)
    """,
    samples=[("123", "6"), ("909", "18")],
    hidden=["100", "999", "507"],
)

code_problem(
    slug="l06-vaqt-formati", title="Vaqt formati", lesson=6, level=1, difficulty=2, tags=["arifmetika", "f-string"],
    statement="""
        Sekundlar soni $S$ berilgan. Uni `H:MM:SS` ko‘rinishida chiqaring: soatlar oldiga nol qo‘yilmaydi,
        daqiqa va sekundlar doim ikki xonali.
    """,
    input_format="Bitta son $S$ ($0 \\le S < 10^6$).",
    output_format="`H:MM:SS`",
    solution="""
        s = int(input())
        print(f"{s // 3600}:{s // 60 % 60:02d}:{s % 60:02d}")
    """,
    checker="exact",
    samples=[("3725", "1:02:05"), ("59", "0:00:59")],
    hidden=["0", "86399", "999999", "3600"],
)

code_problem(
    slug="l06-chegirma", title="Chegirmali narx", lesson=6, level=2, difficulty=2, tags=["arifmetika", "f-string"],
    statement="""
        Mahsulot narxi $P$ va chegirma foizi $D$ berilgan. Chegirmadan keyingi narxni
        **verguldan keyin aniq 2 xona** bilan chiqaring (`f"{x:.2f}"`).
    """,
    input_format="Birinchi qatorda $P$ (haqiqiy son, $0 \\le P \\le 10^6$), ikkinchi qatorda $D$ ($0 \\le D \\le 100$).",
    output_format="Yangi narx, 2 xona aniqlikda.",
    solution="""
        price = float(input())
        discount = int(input())
        print(f"{price * (100 - discount) / 100:.2f}")
    """,
    checker="float",
    samples=[("100\n15", "85.00"), ("19.99\n10", "17.99")],
    hidden=["250000\n0", "99.5\n100", "1234.56\n25", "80\n33"],
)

# ---------------- 7. Mantiqiy ifodalar ----------------
code_problem(
    slug="l07-oraliqda", title="Oraliqdami?", lesson=7, level=0, difficulty=1, tags=["mantiqiy ifodalar"],
    statement="""
        Uchta butun son $a$, $x$, $b$ berilgan. $a \\le x \\le b$ shartini tekshiruvchi mantiqiy ifodaning
        qiymatini (`True` yoki `False`) chiqaring.
    """,
    input_format="Bitta qatorda $a$, $x$, $b$ ($|a|, |x|, |b| \\le 10^9$).",
    output_format="`True` yoki `False`.",
    solution="""
        a, x, b = map(int, input().split())
        print(a <= x <= b)
    """,
    samples=[("1 5 10", "True"), ("3 2 8", "False")],
    hidden=["5 5 5", "1 10 10", "10 5 1", "-3 -3 0"],
)

code_problem(
    slug="l07-kabisa-yili", title="Kabisa yili", lesson=7, level=1, difficulty=2, tags=["mantiqiy ifodalar"],
    statement="""
        Yil kabisa bo‘ladi, agar u 4 ga bo‘linsa va 100 ga bo‘linmasa, yoki 400 ga bo‘linsa.
        Bitta mantiqiy ifoda yordamida yil kabisa ekanini aniqlang (`True` yoki `False`).
    """,
    input_format="Bitta son — yil ($1 \\le y \\le 10^5$).",
    output_format="`True` yoki `False`.",
    solution="""
        y = int(input())
        print(y % 4 == 0 and y % 100 != 0 or y % 400 == 0)
    """,
    samples=[("2024", "True"), ("1900", "False")],
    hidden=["2000", "2023", "2400", "4"],
)

code_problem(
    slug="l07-ot-yurishi", title="Ot yurishi", lesson=7, level=2, difficulty=3, tags=["mantiqiy ifodalar"],
    statement="""
        Shaxmat taxtasida ikkita katak berilgan (masalan, `b1` va `c3`). Ot birinchi katakdan ikkinchisiga
        bitta yurishda o‘ta oladimi? `True` yoki `False` chiqaring.

        Ot «G» harfi shaklida yuradi: bir yo‘nalishda 2 katak va unga perpendikulyar yo‘nalishda 1 katak.
    """,
    input_format="Bitta qatorda ikkita katak (`a`–`h` harfi va `1`–`8` raqami).",
    output_format="`True` yoki `False`.",
    solution="""
        a, b = input().split()
        dx = abs(ord(a[0]) - ord(b[0]))
        dy = abs(int(a[1]) - int(b[1]))
        print(dx == 1 and dy == 2 or dx == 2 and dy == 1)
    """,
    samples=[("b1 c3", "True"), ("a1 b2", "False")],
    hidden=["e4 f6", "e4 e6", "h8 g6", "a1 h8", "d4 d4"],
)

# ---------------- 8. Shartli operatorlar (if) ----------------
code_problem(
    slug="l08-ishora", title="Sonning ishorasi", lesson=8, level=0, difficulty=1, tags=["if"],
    statement="""
        Butun son berilgan. Agar u musbat bo‘lsa `musbat`, manfiy bo‘lsa `manfiy`, nolga teng bo‘lsa `nol`
        chiqaring.
    """,
    input_format="Bitta butun son ($|n| \\le 10^{18}$).",
    output_format="`musbat`, `manfiy` yoki `nol`.",
    solution="""
        n = int(input())
        if n > 0:
            print("musbat")
        elif n < 0:
            print("manfiy")
        else:
            print("nol")
    """,
    samples=[("5", "musbat"), ("0", "nol")],
    hidden=["-7", "1000000000000000000", "-1"],
)

code_problem(
    slug="l08-baho", title="Ballni bahoga aylantirish", lesson=8, level=1, difficulty=2, tags=["if"],
    statement="""
        O‘quvchi 0 dan 100 gacha ball to‘pladi. Bahoni aniqlang:

        | Ball | Baho |
        |---|---|
        | 86–100 | 5 |
        | 71–85 | 4 |
        | 56–70 | 3 |
        | 0–55 | 2 |
    """,
    input_format="Bitta butun son — ball ($0 \\le b \\le 100$).",
    output_format="Baho.",
    solution="""
        score = int(input())
        if score >= 86:
            print(5)
        elif score >= 71:
            print(4)
        elif score >= 56:
            print(3)
        else:
            print(2)
    """,
    samples=[("90", "5"), ("70", "3")],
    hidden=["86", "85", "71", "56", "55", "0", "100"],
)

code_problem(
    slug="l08-kvadrat-tenglama", title="Kvadrat tenglama", lesson=8, level=2, difficulty=3, tags=["if", "matematika"],
    statement="""
        $ax^2 + bx + c = 0$ tenglama berilgan ($a \\ne 0$). Uning turli haqiqiy ildizlari sonini chiqaring.
        Ildizlar bo‘lsa, keyingi qatorda ularni o‘sish tartibida, kamida 4 xona aniqlikda chiqaring.

        Diskriminant: $D = b^2 - 4ac$.
    """,
    input_format="Bitta qatorda uchta butun son $a$, $b$, $c$ ($|a|, |b|, |c| \\le 1000$, $a \\ne 0$).",
    output_format="Birinchi qatorda ildizlar soni (0, 1 yoki 2), keyin — ildizlar (agar bo‘lsa).",
    solution="""
        import math

        a, b, c = map(int, input().split())
        d = b * b - 4 * a * c
        if d < 0:
            print(0)
        elif d == 0:
            print(1)
            print(f"{-b / (2 * a):.6f}")
        else:
            r1 = (-b - math.sqrt(d)) / (2 * a)
            r2 = (-b + math.sqrt(d)) / (2 * a)
            low, high = sorted((r1, r2))
            print(2)
            print(f"{low:.6f} {high:.6f}")
    """,
    checker="float", epsilon=1e-4,
    samples=[("1 -3 2", "2\n1.000000 2.000000"), ("1 2 5", "0")],
    hidden=["1 2 1", "2 0 -8", "-1 0 4", "3 1 7", "1 0 0", "7 -1000 3"],
)

# ---------------- 9. match-case ----------------
code_problem(
    slug="l09-hafta-kuni", title="Hafta kuni", lesson=9, level=0, difficulty=1, tags=["match-case"],
    statement="""
        Hafta kunining tartib raqami (1 — dushanba) berilgan. `match-case` yordamida kun nomini chiqaring:
        `Dushanba`, `Seshanba`, `Chorshanba`, `Payshanba`, `Juma`, `Shanba`, `Yakshanba`.
        Raqam 1–7 oralig‘ida bo‘lmasa, `xato` chiqaring.
    """,
    input_format="Bitta butun son.",
    output_format="Kun nomi yoki `xato`.",
    solution="""
        match int(input()):
            case 1:
                print("Dushanba")
            case 2:
                print("Seshanba")
            case 3:
                print("Chorshanba")
            case 4:
                print("Payshanba")
            case 5:
                print("Juma")
            case 6:
                print("Shanba")
            case 7:
                print("Yakshanba")
            case _:
                print("xato")
    """,
    samples=[("1", "Dushanba"), ("8", "xato")],
    hidden=["7", "5", "0", "-3", "3"],
)

code_problem(
    slug="l09-kalkulyator", title="Kalkulyator", lesson=9, level=1, difficulty=2, tags=["match-case"],
    statement="""
        `a amal b` ko‘rinishidagi ifoda berilgan, bu yerda `amal` — `+`, `-`, `*`, `/` yoki `%`.
        Natijani chiqaring:

        - `+`, `-`, `*`, `%` — butun son;
        - `/` — verguldan keyin 2 xona bilan;
        - nolga bo‘lish (`/` yoki `%`) yoki noma’lum amal — `xato`.
    """,
    input_format="Bitta qatorda `a amal b` ($|a|, |b| \\le 10^9$, butun sonlar).",
    output_format="Natija yoki `xato`.",
    solution="""
        a, op, b = input().split()
        a, b = int(a), int(b)
        match op:
            case "+":
                print(a + b)
            case "-":
                print(a - b)
            case "*":
                print(a * b)
            case "/" if b != 0:
                print(f"{a / b:.2f}")
            case "%" if b != 0:
                print(a % b)
            case _:
                print("xato")
    """,
    checker="float",
    samples=[("7 * 6", "42"), ("7 / 2", "3.50")],
    hidden=["5 / 0", "-7 % 3", "10 - 25", "3 ^ 2", "1 / 3", "4 % 0", "1000000000 * 1000000000"],
)

code_problem(
    slug="l09-robot", title="Robot buyruqlari", lesson=9, level=2, difficulty=3, tags=["match-case", "tsikl"],
    statement="""
        Robot $(0, 0)$ nuqtada turibdi. U $n$ ta buyruqni bajaradi, har biri `HARF k` ko‘rinishida:

        - `Y` — yuqoriga $k$ qadam ($y$ ortadi);
        - `P` — pastga $k$ qadam;
        - `C` — chapga $k$ qadam ($x$ kamayadi);
        - `O` — o‘ngga $k$ qadam.

        Robotning oxirgi koordinatalarini va boshlang‘ich nuqtagacha «shahar masofasi»ni
        ($|x| + |y|$) chiqaring.
    """,
    input_format="Birinchi qatorda $n$ ($1 \\le n \\le 10^4$), keyingi $n$ qatorda buyruqlar ($1 \\le k \\le 1000$).",
    output_format="Birinchi qatorda $x$ va $y$, ikkinchi qatorda masofa.",
    solution="""
        n = int(input())
        x = y = 0
        for _ in range(n):
            direction, steps = input().split()
            steps = int(steps)
            match direction:
                case "Y":
                    y += steps
                case "P":
                    y -= steps
                case "C":
                    x -= steps
                case "O":
                    x += steps
        print(x, y)
        print(abs(x) + abs(y))
    """,
    samples=[("4\nY 3\nO 2\nP 1\nC 5", "-3 2\n5"), ("1\nO 10", "10 0\n10")],
    hidden=["2\nY 5\nP 5", "3\nC 1\nC 1\nP 1",
            "10000\n" + "\n".join(f"{R.choice('YPCO')} {R.randint(1, 1000)}" for _ in range(10000))],
)

# ---------------- 10. for tsikli ----------------
code_problem(
    slug="l10-yigindi", title="1 dan n gacha yig‘indi", lesson=10, level=0, difficulty=1, tags=["for"],
    statement="""
        $n$ berilgan. `for` tsikli yordamida $1 + 2 + \\dots + n$ yig‘indisini hisoblang.
    """,
    input_format="Bitta son $n$ ($1 \\le n \\le 10^6$).",
    output_format="Yig‘indi.",
    solution="""
        n = int(input())
        total = 0
        for i in range(1, n + 1):
            total += i
        print(total)
    """,
    samples=[("5", "15"), ("1", "1")],
    hidden=["100", "1000000", "999"],
)

code_problem(
    slug="l10-karra-jadvali", title="Karra jadvali", lesson=10, level=1, difficulty=1, tags=["for", "f-string"],
    statement="""
        $n$ soni uchun karra jadvalini chiqaring: 10 ta qator, har biri `n x i = natija` ko‘rinishida
        ($i$ = 1, 2, …, 10).
    """,
    input_format="Bitta son $n$ ($1 \\le n \\le 1000$).",
    output_format="10 qator.",
    solution="""
        n = int(input())
        for i in range(1, 11):
            print(f"{n} x {i} = {n * i}")
    """,
    checker="exact",
    samples=[("3", "\n".join(f"3 x {i} = {3 * i}" for i in range(1, 11))),
             ("7", "\n".join(f"7 x {i} = {7 * i}" for i in range(1, 11)))],
    hidden=["1", "1000", "12"],
)

code_problem(
    slug="l10-tub-sonlar", title="Tub sonlar", lesson=10, level=2, difficulty=3, tags=["for", "matematika"],
    statement="""
        $n$ dan oshmaydigan barcha tub sonlarni o‘sish tartibida, bo‘shliq bilan ajratib chiqaring.
        Tub son — faqat 1 ga va o‘ziga bo‘linadigan, 1 dan katta natural son.
    """,
    input_format="Bitta son $n$ ($2 \\le n \\le 20000$).",
    output_format="Tub sonlar bitta qatorda.",
    solution="""
        n = int(input())
        primes = []
        for x in range(2, n + 1):
            is_prime = True
            for p in primes:
                if p * p > x:
                    break
                if x % p == 0:
                    is_prime = False
                    break
            if is_prime:
                primes.append(x)
        print(*primes)
    """,
    samples=[("10", "2 3 5 7"), ("2", "2")],
    hidden=["30", "100", "20000", "3"],
)

# ---------------- 11. while tsikli ----------------
code_problem(
    slug="l11-raqamlar-soni", title="Raqamlar soni", lesson=11, level=0, difficulty=1, tags=["while"],
    statement="""
        Manfiy bo‘lmagan butun son berilgan. `while` tsikli yordamida (satrga aylantirmasdan) uning
        raqamlari sonini toping. 0 sonida bitta raqam bor.
    """,
    input_format="Bitta son $n$ ($0 \\le n \\le 10^{18}$).",
    output_format="Raqamlar soni.",
    solution="""
        n = int(input())
        count = 1
        while n >= 10:
            n //= 10
            count += 1
        print(count)
    """,
    samples=[("12345", "5"), ("0", "1")],
    hidden=["9", "10", "1000000000000000000", "999999999999999999"],
)

code_problem(
    slug="l11-teskari-son", title="Teskari son", lesson=11, level=1, difficulty=2, tags=["while"],
    statement="""
        Manfiy bo‘lmagan butun son berilgan. Raqamlarini teskari tartibda yozib hosil bo‘lgan sonni chiqaring
        (boshidagi nollar yozilmaydi: 1200 → 21).
    """,
    input_format="Bitta son $n$ ($0 \\le n \\le 10^{18}$).",
    output_format="Teskari son.",
    solution="""
        n = int(input())
        result = 0
        while n > 0:
            result = result * 10 + n % 10
            n //= 10
        print(result)
    """,
    samples=[("1200", "21"), ("7", "7")],
    hidden=["0", "1000000", "123456789", "1000000000000000000"],
)

code_problem(
    slug="l11-kollats", title="Kollats ketma-ketligi", lesson=11, level=2, difficulty=3, tags=["while"],
    statement="""
        $n$ sonidan boshlab quyidagi amal takrorlanadi: son juft bo‘lsa — 2 ga bo‘linadi, toq bo‘lsa —
        $3n + 1$ ga almashtiriladi. Son 1 ga teng bo‘lguncha nechta qadam kerak?
    """,
    input_format="Bitta son $n$ ($1 \\le n \\le 10^6$).",
    output_format="Qadamlar soni.",
    solution="""
        n = int(input())
        steps = 0
        while n != 1:
            n = n // 2 if n % 2 == 0 else 3 * n + 1
            steps += 1
        print(steps)
    """,
    samples=[("6", "8"), ("1", "0")],
    hidden=["27", "97", "837799", "2"],
)

# ---------------- 12. Loyiha 1 himoyasi (takrorlash) ----------------
code_problem(
    slug="l12-ekub", title="EKUB (Yevklid algoritmi)", lesson=12, level=0, difficulty=2, tags=["while", "matematika"],
    statement="""
        Ikki sonning eng katta umumiy bo‘luvchisini (EKUB) Yevklid algoritmi bilan toping:
        $\\gcd(a, b) = \\gcd(b, a \\bmod b)$, $\\gcd(a, 0) = a$.
    """,
    input_format="Bitta qatorda $a$ va $b$ ($0 \\le a, b \\le 10^{18}$, ikkalasi bir vaqtda 0 emas).",
    output_format="EKUB.",
    solution="""
        a, b = map(int, input().split())
        while b:
            a, b = b, a % b
        print(a)
    """,
    samples=[("12 18", "6"), ("7 13", "1")],
    hidden=["0 5", "1000000000 999999999", "48 180", "1000000000000000000 999999999999999998"],
)

code_problem(
    slug="l12-sonni-top", title="Sonni top o‘yini", lesson=12, level=1, difficulty=2, tags=["while", "if"],
    statement="""
        Kompyuter $s$ sonini o‘yladi. O‘yinchi ketma-ket $n$ ta taxmin aytadi. Har bir taxmin uchun:

        - taxmin $s$ dan katta bo‘lsa — `katta`;
        - kichik bo‘lsa — `kichik`;
        - teng bo‘lsa — `topdingiz` va o‘yin tugaydi (qolgan taxminlar e’tiborsiz qoldiriladi).

        Agar son topilmasa, oxirida `topilmadi` chiqaring.
    """,
    input_format="Birinchi qatorda $s$, ikkinchi qatorda $n$ ($1 \\le n \\le 1000$), uchinchi qatorda $n$ ta taxmin.",
    output_format="Har bir ko‘rib chiqilgan taxmin uchun bitta so‘z.",
    solution="""
        secret = int(input())
        n = int(input())
        guesses = list(map(int, input().split()))
        found = False
        i = 0
        while i < n and not found:
            if guesses[i] > secret:
                print("katta")
            elif guesses[i] < secret:
                print("kichik")
            else:
                print("topdingiz")
                found = True
            i += 1
        if not found:
            print("topilmadi")
    """,
    samples=[("42\n4\n50 30 42 10", "katta\nkichik\ntopdingiz"), ("7\n2\n1 2", "kichik\nkichik\ntopilmadi")],
    hidden=["5\n1\n5", "100\n5\n50 75 88 94 97", "1\n3\n1 1 1"],
)

code_problem(
    slug="l12-bankomat", title="Bankomat", lesson=12, level=2, difficulty=3, tags=["while", "tsikl"],
    statement="""
        Bankomatda 200000, 100000, 50000, 20000, 10000, 5000, 2000 va 1000 so‘mlik kupyuralar bor.
        $A$ so‘mni **eng kam** kupyuralar bilan bering (kattasidan boshlab).

        Har bir ishlatilgan kupyura uchun `nominal x soni` qatorini (kattasidan kichigiga) va oxirida
        `jami: N` qatorini chiqaring. Agar $A$ 1000 ga karrali bo‘lmasa, faqat `xato` chiqaring.
    """,
    input_format="Bitta son $A$ ($1 \\le A \\le 10^9$).",
    output_format="Kupyuralar ro‘yxati va jami, yoki `xato`.",
    solution="""
        amount = int(input())
        if amount % 1000 != 0:
            print("xato")
        else:
            total = 0
            for note in (200000, 100000, 50000, 20000, 10000, 5000, 2000, 1000):
                count = amount // note
                if count:
                    print(f"{note} x {count}")
                    amount -= note * count
                    total += count
            print(f"jami: {total}")
    """,
    samples=[("386000", "200000 x 1\n100000 x 1\n50000 x 1\n20000 x 1\n10000 x 1\n5000 x 1\n1000 x 1\njami: 7"),
             ("1500", "xato")],
    hidden=["1000", "1000000000", "4000", "999999000"],
)
