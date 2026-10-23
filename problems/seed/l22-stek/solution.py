import sys


class Stack:
    def __init__(self) -> None:
        self._items: list[str] = []

    def push(self, item: str) -> None:
        self._items.append(item)

    def pop(self) -> str:
        return self._items.pop() if self._items else "-"

    def peek(self) -> str:
        return self._items[-1] if self._items else "-"

    def size(self) -> int:
        return len(self._items)


lines = sys.stdin.read().split("\n")
stack = Stack()
out = []
for line in lines[1:1 + int(lines[0])]:
    parts = line.split()
    if parts[0] == "push":
        stack.push(parts[1])
    elif parts[0] == "pop":
        out.append(stack.pop())
    elif parts[0] == "peek":
        out.append(stack.peek())
    else:
        out.append(str(stack.size()))
print("\n".join(out))
