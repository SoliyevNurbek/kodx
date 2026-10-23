secret = int(input())
n = int(input())
guesses = list(map(int, input().split()))
found = False
i = 0
while i < n and not found:
    if guesses[i] > secret:
        print("katta")
    elif guesses[i] < secret:
        print("kichik")
    else:
        print("topdingiz")
        found = True
    i += 1
if not found:
    print("topilmadi")
