import sys

lines = sys.stdin.read().split("\n")
totals = {}
for line in lines[1:1 + int(lines[0])]:
    name, score = line.split()
    totals[name] = totals.get(name, 0) + int(score)
ranking = sorted(totals.items(), key=lambda item: (-item[1], item[0]))
place = 0
for index, (name, total) in enumerate(ranking, start=1):
    if index == 1 or total != ranking[index - 2][1]:
        place = index
    print(place, name, total)
