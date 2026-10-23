n, k = map(int, input().split())
a = input().split()
k %= n
print(*(a[n - k:] + a[:n - k]))
