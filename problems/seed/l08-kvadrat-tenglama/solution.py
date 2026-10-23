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
