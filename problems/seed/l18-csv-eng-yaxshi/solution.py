import csv
import sys

best = {}
for row in csv.DictReader(sys.stdin):
    key = (-int(row["ball"]), row["ism"])
    if row["fan"] not in best or key < best[row["fan"]]:
        best[row["fan"]] = key
for subject in sorted(best):
    score, name = best[subject]
    print(subject, name, -score)
