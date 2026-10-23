"""
Bosh sahifa hero surati: maketdan (yoki haqiqiy suratdan) WebP/PNG fayllarini yaratadi.

Ishlatish:  venv/Scripts/python scripts/make_hero_image.py

Manba tanlash:
- static/img/hero-nurbek-source.png mavjud bo'lsa — shu haqiqiy surat butunligicha ishlatiladi;
- aks holda docs/design/landing-mockup.jfif dan muallif tasviri qirqib olinadi.

Natija (har ishga tushirishda qayta yoziladi):
static/img/hero-nurbek.png, hero-nurbek-800.webp, hero-nurbek-1200.webp.
"""

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
MOCKUP = ROOT / "docs" / "design" / "landing-mockup.jfif"
OUT_DIR = ROOT / "static" / "img"
SOURCE = OUT_DIR / "hero-nurbek-source.png"

# Qirqish chegaralari 2752×1536 maket uchun (chap, yuqori, o'ng, past). Chapda — h1 matni (x ≤ 1665),
# o'ngda — hamkor logotiplari va ikonkalar (x ≥ 2400), yuqorida — breadcrumb qatori (y ≤ 186),
# pastda — «KURS MUALLIFI» kartasi (y ≥ 1143) va «Python AI & Web» yozuvi (x ≥ 2440) tushmaydi.
MOCKUP_SIZE = (2752, 1536)
CROP_BOX = (1680, 205, 2390, 1130)
WIDTHS = (800, 1200)
QUALITY = 85


def scaled_box(size: tuple[int, int]) -> tuple[int, int, int, int]:
    """Maket boshqa o'lchamda saqlangan bo'lsa, qirqish chegaralarini mutanosib o'zgartiradi."""
    sx, sy = size[0] / MOCKUP_SIZE[0], size[1] / MOCKUP_SIZE[1]
    left, top, right, bottom = CROP_BOX
    return round(left * sx), round(top * sy), round(right * sx), round(bottom * sy)


def load_portrait() -> tuple[Image.Image, str]:
    """Manba suratni qaytaradi: haqiqiy surat bo'lsa — o'zi, aks holda maketdan kesim."""
    if SOURCE.exists():
        return Image.open(SOURCE).convert("RGB"), SOURCE.name
    mockup = Image.open(MOCKUP).convert("RGB")
    return mockup.crop(scaled_box(mockup.size)), f"{MOCKUP.name} {scaled_box(mockup.size)}"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    portrait, origin = load_portrait()
    portrait.save(OUT_DIR / "hero-nurbek.png", optimize=True)
    for width in WIDTHS:
        height = round(portrait.height * width / portrait.width)
        resized = portrait.resize((width, height), Image.Resampling.LANCZOS)
        resized.save(OUT_DIR / f"hero-nurbek-{width}.webp", "WEBP", quality=QUALITY, method=6)
        print(f"hero-nurbek-{width}.webp: {width}x{height}")
    print(f"Manba: {origin}; asl o'lcham {portrait.width}x{portrait.height}")


if __name__ == "__main__":
    main()
