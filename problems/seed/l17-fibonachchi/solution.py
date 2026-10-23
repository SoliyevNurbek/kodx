MOD = 10 ** 9 + 7


def fib_pair(n: int) -> tuple[int, int]:
    """(F(n), F(n+1)) mod MOD."""
    if n == 0:
        return 0, 1
    a, b = fib_pair(n // 2)
    c = a * (2 * b - a) % MOD
    d = (a * a + b * b) % MOD
    return (d, (c + d) % MOD) if n % 2 else (c, d)


print(fib_pair(int(input()))[0])
