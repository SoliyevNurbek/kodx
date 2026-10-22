c, n = map(int, input().split())
sizes = list(map(int, input().split()))
free = c * 1024
count = 0
for size in sizes:
    if size > free:
        break
    free -= size
    count += 1
print(count, free)
