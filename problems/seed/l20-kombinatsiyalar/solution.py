from itertools import combinations

letters, k = input().split()
for combo in combinations(sorted(letters), int(k)):
    print("".join(combo))
