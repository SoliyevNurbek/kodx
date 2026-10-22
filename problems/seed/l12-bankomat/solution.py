amount = int(input())
if amount % 1000 != 0:
    print("xato")
else:
    total = 0
    for note in (200000, 100000, 50000, 20000, 10000, 5000, 2000, 1000):
        count = amount // note
        if count:
            print(f"{note} x {count}")
            amount -= note * count
            total += count
    print(f"jami: {total}")
