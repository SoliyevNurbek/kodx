name = input().strip()
dot = name.rfind(".")
if dot <= 0 or dot == len(name) - 1:
    print("yo'q")
else:
    print(name[dot + 1:].lower())
