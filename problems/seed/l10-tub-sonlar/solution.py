n = int(input())
primes = []
for x in range(2, n + 1):
    is_prime = True
    for p in primes:
        if p * p > x:
            break
        if x % p == 0:
            is_prime = False
            break
    if is_prime:
        primes.append(x)
print(*primes)
