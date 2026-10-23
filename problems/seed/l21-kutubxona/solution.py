class Library:
    def __init__(self) -> None:
        self.books: dict[str, bool] = {}  # nom -> berilganmi

    def add(self, name: str) -> str:
        if name in self.books:
            return "mavjud"
        self.books[name] = False
        return "qoshildi"

    def take(self, name: str) -> str:
        if name not in self.books:
            return "topilmadi"
        if self.books[name]:
            return "band"
        self.books[name] = True
        return "berildi"

    def give_back(self, name: str) -> str:
        if not self.books.get(name):
            return "xato"
        self.books[name] = False
        return "qaytarildi"

    def shelf(self) -> str:
        free = sorted(name for name, taken in self.books.items() if not taken)
        return " ".join(free) if free else "-"


library = Library()
for _ in range(int(input())):
    parts = input().split()
    match parts:
        case ["qosh", name]:
            print(library.add(name))
        case ["ol", name]:
            print(library.take(name))
        case ["qaytar", name]:
            print(library.give_back(name))
        case ["royxat"]:
            print(library.shelf())
