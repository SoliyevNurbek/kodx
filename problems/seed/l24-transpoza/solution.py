n, m = map(int, input().split())
matrix = [input().split() for _ in range(n)]
for row in zip(*matrix):
    print(*row)
