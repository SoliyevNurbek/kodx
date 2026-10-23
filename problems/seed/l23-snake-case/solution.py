name = input().strip()
result = []
for i, ch in enumerate(name):
    if ch.isupper():
        if i > 0:
            result.append("_")
        result.append(ch.lower())
    else:
        result.append(ch)
print("".join(result))
