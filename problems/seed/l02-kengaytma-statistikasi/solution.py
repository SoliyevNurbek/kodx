n = int(input())
counts = {}
for _ in range(n):
    name = input().strip()
    dot = name.rfind(".")
    ext = "-" if dot <= 0 or dot == len(name) - 1 else name[dot + 1:].lower()
    counts[ext] = counts.get(ext, 0) + 1
for ext in sorted(counts):
    print(ext, counts[ext])
