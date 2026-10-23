import json
import sys

data = json.load(sys.stdin)
rows = []
for student in data["oquvchilar"]:
    marks = student["baholar"]
    rows.append((-(sum(marks) / len(marks) if marks else 0.0), student["ism"]))
if not rows:
    print("yo'q")
for avg, name in sorted(rows):
    print(name, f"{-avg:.2f}")
