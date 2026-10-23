class Vector:
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

    def __add__(self, other: "Vector") -> "Vector":
        return Vector(self.x + other.x, self.y + other.y)

    def dot(self, other: "Vector") -> int:
        return self.x * other.x + self.y * other.y


a = Vector(*map(int, input().split()))
b = Vector(*map(int, input().split()))
s = a + b
print(s.x, s.y)
print(a.dot(b))
