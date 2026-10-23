a, op, b = input().split()
a, b = int(a), int(b)
match op:
    case "+":
        print(a + b)
    case "-":
        print(a - b)
    case "*":
        print(a * b)
    case "/" if b != 0:
        print(f"{a / b:.2f}")
    case "%" if b != 0:
        print(a % b)
    case _:
        print("xato")
