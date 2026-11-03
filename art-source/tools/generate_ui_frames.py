"""UI pieces for the options screen (concept-art/ui/opcoes-*-praia-v2.png).

Run with system Python + Pillow. Writes godot/assets/ui/options/:
  frame.png       ivory card, double jade border, concave corners, raised top tab
  toggle_on.png / toggle_off.png, grabber.png (gold diamond slider handle)
Drawn at 2x and shown scaled down for clean edges.
"""
import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "godot" / "assets" / "ui" / "options"
JADE = (31, 92, 66, 255)
JADE_DARK = (22, 66, 48, 255)
GOLD = (198, 160, 82, 255)
IVORY = (245, 239, 225)

# Card geometry at 2x: canvas, card rectangle, concave corner radius and top tab.
W, H = 2290, 1360
X0, Y0, X1, Y1 = 20, 80, 2270, 1340
R = 46
TAB_L, TAB_R, TAB_H, TAB_S = 880, 1410, 58, 70


def outline(i):
    """Closed outline of the card inset by i px (concave corners, raised tab)."""
    pts = []
    x0, y0, x1, y1 = X0 + i, Y0 + i, X1 - i, Y1 - i
    r = R + i

    def corner(cx, cy, a0, a1):
        # The inset edges cut the arc short: trim it where it meets them.
        trim = math.degrees(math.asin(min(1.0, i / r))) if r > 0 else 0.0
        step = 1 if a1 > a0 else -1
        a0, a1 = a0 + step * trim, a1 - step * trim
        for k in range(13):
            a = math.radians(a0 + (a1 - a0) * k / 12)
            pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))

    # Top-left concave corner (centre on the outer corner), arc from the left edge to the top edge.
    corner(X0, Y0, 90, 0)
    # Top edge with the raised tab and its smooth shoulders.
    top = y0
    tab_top = Y0 - TAB_H + i
    for k in range(17):
        t = k / 16
        e = t * t * (3 - 2 * t)
        pts.append((TAB_L - TAB_S + i * 0.4 + t * TAB_S, top + (tab_top - top) * e))
    for k in range(17):
        t = k / 16
        e = t * t * (3 - 2 * t)
        pts.append((TAB_R - i * 0.4 + t * TAB_S, tab_top + (top - tab_top) * e))
    corner(X1, Y0, 180, 90)
    corner(X1, Y1, 270, 180)
    corner(X0, Y1, 360, 270)
    return pts


def parchment(size, rng):
    img = Image.new("RGB", size, IVORY)
    d = ImageDraw.Draw(img)
    for _ in range(1600):
        x, y = rng.uniform(0, size[0]), rng.uniform(0, size[1])
        r = rng.uniform(6, 40)
        t = rng.uniform(-5, 4)
        c = tuple(int(max(0, min(255, v + t))) for v in IVORY)
        d.ellipse([x - r, y - r, x + r, y + r], fill=c)
    img = img.filter(ImageFilter.GaussianBlur(10))
    # Warm vignette toward the edges.
    vignette = Image.new("L", size, 0)
    vd = ImageDraw.Draw(vignette)
    for k in range(40):
        inset = k * 12
        vd.rectangle([inset, inset, size[0] - inset, size[1] - inset], outline=int(4 * (40 - k)))
    vignette = vignette.filter(ImageFilter.GaussianBlur(60))
    tint = Image.new("RGB", size, (214, 196, 160))
    return Image.composite(tint, img, vignette.point(lambda v: min(v, 90)))


def frame():
    rng = random.Random(5)
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).polygon(outline(0), fill=255)
    card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    card.paste(parchment((W, H), rng), (0, 0), mask)
    d = ImageDraw.Draw(card)
    d.line(outline(0) + [outline(0)[0]], fill=JADE, width=5, joint="curve")
    d.line(outline(14) + [outline(14)[0]], fill=JADE, width=7, joint="curve")
    d.line(outline(26) + [outline(26)[0]], fill=GOLD, width=2, joint="curve")
    # Soft drop shadow under the card.
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).polygon([(x + 6, y + 10) for x, y in outline(0)], fill=(0, 0, 0, 90))
    shadow = shadow.filter(ImageFilter.GaussianBlur(14))
    shadow.alpha_composite(card)
    return shadow


def toggle(on):
    w, h = 132, 72
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    track = JADE if on else (150, 150, 146, 255)
    d.rounded_rectangle([2, 4, w - 2, h - 4], radius=32, fill=track, outline=(255, 255, 255, 60), width=2)
    cx = w - 36 if on else 36
    d.ellipse([cx - 25, h / 2 - 25, cx + 25, h / 2 + 25], fill=(250, 246, 236, 255), outline=(200, 190, 170, 255), width=2)
    return img


def grabber():
    s = 56
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = s / 2
    d.polygon([(c, 4), (s - 4, c), (c, s - 4), (4, c)], fill=(240, 212, 140, 255), outline=(150, 112, 44, 255))
    d.polygon([(c, 14), (s - 14, c), (c, s - 14), (14, c)], fill=(252, 236, 186, 255))
    return img


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    frame().save(OUT / "frame.png")
    # Icons are drawn at 2x and saved at their on-screen size.
    half = lambda img: img.resize((img.width // 2, img.height // 2), Image.Resampling.LANCZOS)
    half(toggle(True)).save(OUT / "toggle_on.png")
    half(toggle(False)).save(OUT / "toggle_off.png")
    half(grabber()).save(OUT / "grabber.png")
    print("ui frames:", sorted(p.name for p in OUT.glob("*.png")))


if __name__ == "__main__":
    main()
