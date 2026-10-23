a, b = input().split()
dx = abs(ord(a[0]) - ord(b[0]))
dy = abs(int(a[1]) - int(b[1]))
print(dx == 1 and dy == 2 or dx == 2 and dy == 1)
