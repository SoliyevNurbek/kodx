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
print("\n".join(out))
