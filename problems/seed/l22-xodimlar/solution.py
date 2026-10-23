class Employee:
    def __init__(self, name: str, base: int) -> None:
        self.name = name
        self._base = base

    def salary(self) -> int:
        return self._base


class Developer(Employee):
    def salary(self) -> int:
        return self._base * 6 // 5


class Manager(Employee):
    def __init__(self, name: str, base: int, bonus: int) -> None:
        super().__init__(name, base)
        self._bonus = bonus

    def salary(self) -> int:
        return self._base + self._bonus


KINDS = {"xodim": Employee, "dasturchi": Developer, "menejer": Manager}
staff = []
for _ in range(int(input())):
    kind, name, *numbers = input().split()
    staff.append(KINDS[kind](name, *map(int, numbers)))
for person in staff:
    print(person.name, person.salary())
print(f"jami: {sum(p.salary() for p in staff)}")
