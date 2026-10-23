n = int(input())
balance = 0
for _ in range(n):
    op, raw = input().split()
    try:
        amount = int(raw)
        if amount <= 0:
            raise ValueError
    except ValueError:
        print("xato: summa")
        continue
    if op == "kirim":
        balance += amount
    elif op == "chiqim":
        if amount > balance:
            print("xato: yetarli emas")
        else:
            balance -= amount
    else:
        print("xato: amal")
print(f"balans: {balance}")
