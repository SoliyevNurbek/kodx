n = int(input())
counts = {"M": 0, "A": 0, "D": 0, "??": 0}
for _ in range(n):
    code = input().split()[0]
    counts[code] += 1
for code in ("M", "A", "D", "??"):
    print(code, counts[code])
