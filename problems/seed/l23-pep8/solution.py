import sys

lines = sys.stdin.read().split("\n")
n = int(lines[0])
problems = []
for number, line in enumerate(lines[1:1 + n], start=1):
    if len(line) > 79:
        problems.append(f"{number} E501")
    if line != line.rstrip():
        problems.append(f"{number} W291")
print("\n".join(problems) if problems else "toza")
