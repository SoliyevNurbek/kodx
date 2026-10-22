n = int(input())
x = y = 0
for _ in range(n):
    direction, steps = input().split()
    steps = int(steps)
    match direction:
        case "Y":
            y += steps
        case "P":
            y -= steps
        case "C":
            x -= steps
        case "O":
            x += steps
print(x, y)
print(abs(x) + abs(y))
