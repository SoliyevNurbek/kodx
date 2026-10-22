n = int(input())
hashes = [input().strip() for _ in range(n)]
k = 4
while len({h[:k] for h in hashes}) < n:
    k += 1
print(k)
