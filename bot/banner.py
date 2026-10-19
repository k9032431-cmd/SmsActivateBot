"""Баннер главного меню.

Если админ не поставил свою картинку (/setbanner), бот рисует баннер сам — с названием бота.
"""
import io
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ASSETS = Path(__file__).parent / "assets"
W, H = 1280, 640


def _font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(ASSETS / name), size)


def _glow(size, box, color, radius, blur) -> Image.Image:
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle(box, radius, fill=color)
    return layer.filter(ImageFilter.GaussianBlur(blur))


def _tile(img: Image.Image, cx: int, cy: int, s: int, draw_icon) -> None:
    """Глянцевая «иконка приложения» с подсветкой, как на витринах магазинов."""
    box = (cx - s // 2, cy - s // 2, cx + s // 2, cy + s // 2)
    img.alpha_composite(_glow(img.size, box, (40, 140, 255, 150), s // 4, s // 5))
    tile = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    d.rounded_rectangle(box, s // 4, fill=(18, 44, 92, 255), outline=(110, 180, 255, 255), width=max(2, s // 40))
    # блик сверху
    d.rounded_rectangle((box[0] + 6, box[1] + 6, box[2] - 6, cy - s // 8), s // 5, fill=(255, 255, 255, 22))
    img.alpha_composite(tile)
    draw_icon(ImageDraw.Draw(img), cx, cy, s)


def _icon_phone(d: ImageDraw.ImageDraw, cx, cy, s):
    w, h = s * 0.36, s * 0.6
    d.rounded_rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), s // 12, outline=(230, 242, 255), width=s // 22)
    d.rounded_rectangle((cx - w * 0.18, cy - h / 2 + s * 0.05, cx + w * 0.18, cy - h / 2 + s * 0.08), 3, fill=(230, 242, 255))
    d.ellipse((cx - s * 0.03, cy + h / 2 - s * 0.11, cx + s * 0.03, cy + h / 2 - s * 0.05), fill=(230, 242, 255))


def _icon_chat(d: ImageDraw.ImageDraw, cx, cy, s):
    w, h = s * 0.56, s * 0.4
    d.rounded_rectangle((cx - w / 2, cy - h / 2 - s * 0.04, cx + w / 2, cy + h / 2 - s * 0.04), s // 9, outline=(230, 242, 255), width=s // 22)
    d.polygon([(cx - w * 0.25, cy + h / 2 - s * 0.06), (cx - w * 0.38, cy + h / 2 + s * 0.1), (cx - w * 0.05, cy + h / 2 - s * 0.06)],
              fill=(230, 242, 255))
    for i in (-1, 0, 1):
        x = cx + i * s * 0.12
        d.ellipse((x - s * 0.035, cy - s * 0.075, x + s * 0.035, cy - s * 0.005), fill=(230, 242, 255))


def _icon_shield(d: ImageDraw.ImageDraw, cx, cy, s):
    k = s * 0.3
    pts = [(cx, cy - k), (cx + k * 0.85, cy - k * 0.6), (cx + k * 0.75, cy + k * 0.3), (cx, cy + k),
           (cx - k * 0.75, cy + k * 0.3), (cx - k * 0.85, cy - k * 0.6)]
    d.polygon(pts, outline=(230, 242, 255), width=s // 22)
    d.line([(cx - k * 0.35, cy), (cx - k * 0.05, cy + k * 0.3), (cx + k * 0.4, cy - k * 0.3)],
           fill=(230, 242, 255), width=s // 18, joint="curve")


def _icon_globe(d: ImageDraw.ImageDraw, cx, cy, s):
    r = s * 0.28
    width = s // 24
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(230, 242, 255), width=width)
    d.ellipse((cx - r * 0.45, cy - r, cx + r * 0.45, cy + r), outline=(230, 242, 255), width=width)
    d.line([(cx - r, cy), (cx + r, cy)], fill=(230, 242, 255), width=width)


def render(title: str, subtitle: str = "VIRTUAL NUMBERS  ·  SMS") -> bytes:
    rnd = random.Random(42)
    img = Image.new("RGBA", (W, H), (6, 12, 30, 255))

    # фон: радиальное свечение по центру
    bg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(bg)
    for i in range(60, 0, -1):
        r = i * 13
        a = int(110 * (1 - i / 60) ** 1.6)
        d.ellipse((W / 2 - r * 1.4, H * 0.42 - r, W / 2 + r * 1.4, H * 0.42 + r), fill=(20, 90, 220, a))
    img.alpha_composite(bg.filter(ImageFilter.GaussianBlur(30)))

    # звёзды и «облака» внизу
    stars = ImageDraw.Draw(img)
    for _ in range(140):
        x, y, r = rnd.randint(0, W), rnd.randint(0, H), rnd.choice([1, 1, 1, 2])
        stars.ellipse((x - r, y - r, x + r, y + r), fill=(170, 210, 255, rnd.randint(60, 200)))
    fog = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fog)
    for _ in range(26):
        x = rnd.randint(-100, W + 100)
        r = rnd.randint(70, 160)
        fd.ellipse((x - r * 1.6, H - r * 0.7, x + r * 1.6, H + r), fill=(60, 110, 200, 70))
    img.alpha_composite(fog.filter(ImageFilter.GaussianBlur(28)))

    # иконки
    _tile(img, 640, 205, 210, _icon_chat)
    _tile(img, 400, 235, 140, _icon_phone)
    _tile(img, 880, 235, 140, _icon_shield)
    _tile(img, 215, 140, 92, _icon_globe)
    _tile(img, 1065, 140, 92, _icon_phone)

    # заголовок со свечением
    title = title.upper()
    size = 112
    font = _font("InterDisplay-Black.otf", size)
    while font.getlength(title) > W - 160 and size > 40:
        size -= 4
        font = _font("InterDisplay-Black.otf", size)
    tw = font.getlength(title)
    ty = 395
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).text(((W - tw) / 2, ty), title, font=font, fill=(60, 150, 255, 255))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(16)))
    d = ImageDraw.Draw(img)
    d.text(((W - tw) / 2, ty), title, font=font, fill=(240, 247, 255))

    sub_font = _font("InterDisplay-SemiBold.otf", 34)
    sw = sub_font.getlength(subtitle)
    d.text(((W - sw) / 2, ty + size + 22), subtitle, font=sub_font, fill=(150, 195, 255))
    line_y = ty + size + 42
    for sign in (-1, 1):
        x0 = W / 2 + sign * (sw / 2 + 24)
        d.line([(x0, line_y), (x0 + sign * 90, line_y)], fill=(80, 150, 255), width=3)

    out = io.BytesIO()
    img.convert("RGB").save(out, "JPEG", quality=92)
    return out.getvalue()


if __name__ == "__main__":  # python -m bot.banner "Название" — посмотреть баннер
    import sys

    Path("banner_preview.jpg").write_bytes(render(sys.argv[1] if len(sys.argv) > 1 else "SMS Number Bot"))
    print("banner_preview.jpg")
