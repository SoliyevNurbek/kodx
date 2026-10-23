n = int(input())
a = list(map(int, input().split()))
total = sum(a)
print(sum(1 for x in a if x * n > total))
