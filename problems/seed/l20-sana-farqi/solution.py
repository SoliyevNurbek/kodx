from datetime import date

first = date.fromisoformat(input().strip())
second = date.fromisoformat(input().strip())
print(abs((second - first).days))
