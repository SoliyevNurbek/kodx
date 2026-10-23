count = total = 0
for token in input().split():
    try:
        value = int(token)
    except ValueError:
        continue
    count += 1
    total += value
print(count, total)
