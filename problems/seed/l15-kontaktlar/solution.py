import sys

lines = sys.stdin.read().split("\n")
book = {}
out = []
for line in lines[1:1 + int(lines[0])]:
    parts = line.split()
    if parts[0] == "add":
        book[parts[1]] = parts[2]
    elif parts[0] == "get":
        out.append(book.get(parts[1], "topilmadi"))
    elif parts[0] == "del":
        book.pop(parts[1], None)
print("\n".join(out))
