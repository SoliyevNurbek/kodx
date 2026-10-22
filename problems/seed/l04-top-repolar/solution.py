import sys

lines = sys.stdin.read().split("\n")
n = int(lines[0])
repos = []
for line in lines[1:1 + n]:
    name, stars = line.split()
    repos.append((-int(stars), name))
repos.sort()
for stars, name in repos[:3]:
    print(name, -stars)
