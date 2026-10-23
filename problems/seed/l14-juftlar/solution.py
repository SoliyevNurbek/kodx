n = int(input())
evens = sorted(x for x in map(int, input().split()) if x % 2 == 0)
print(*evens if evens else ["yo'q"])
