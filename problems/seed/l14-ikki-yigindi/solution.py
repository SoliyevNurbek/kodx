n, k = map(int, input().split())
seen = {}
pairs = 0
for x in map(int, input().split()):
    pairs += seen.get(k - x, 0)
    seen[x] = seen.get(x, 0) + 1
print(pairs)
