def gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a


def lcm(a: int, b: int) -> int:
    return a // gcd(a, b) * b


input()
result = 1
for x in map(int, input().split()):
    result = lcm(result, x)
print(result)
