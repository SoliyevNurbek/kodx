ALLOWED = set("abcdefghijklmnopqrstuvwxyz0123456789-_/.")


def is_valid(name: str) -> bool:
    return (
        1 <= len(name) <= 100
        and set(name) <= ALLOWED
        and name[0] not in "-/."
        and name[-1] not in "/."
        and not name.endswith(".lock")
        and ".." not in name
        and "//" not in name
    )


n = int(input())
for _ in range(n):
    print("OK" if is_valid(input()) else "XATO")
