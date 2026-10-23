import math


class Shape:
    def area(self) -> float:
        raise NotImplementedError


class Circle(Shape):
    def __init__(self, r: float) -> None:
        self.r = r

    def area(self) -> float:
        return math.pi * self.r ** 2


class Square(Shape):
    def __init__(self, a: float) -> None:
        self.a = a

    def area(self) -> float:
        return self.a ** 2


class Triangle(Shape):
    def __init__(self, a: float, h: float) -> None:
        self.a = a
        self.h = h

    def area(self) -> float:
        return self.a * self.h / 2


KINDS = {"doira": Circle, "kvadrat": Square, "uchburchak": Triangle}
shapes = []
for _ in range(int(input())):
    kind, *sizes = input().split()
    shapes.append(KINDS[kind](*map(float, sizes)))
print(f"{sum(s.area() for s in shapes):.2f}")
