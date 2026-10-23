n = int(input())
for _ in range(n):
    a, b = map(int, input().split())
    try:
        print(a // b)
    except ZeroDivisionError:
        print("xato")
