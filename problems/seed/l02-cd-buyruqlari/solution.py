n = int(input())
path = []
for _ in range(n):
    arg = input().split()[1]
    if arg == "/":
        path = []
    elif arg == "..":
        if path:
            path.pop()
    else:
        path.append(arg)
print("/" + "/".join(path))
