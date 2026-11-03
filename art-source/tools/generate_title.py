"""Main menu title set in the golden alphabet (concept-art/ui/tipografia/alfabeto-dourado-v1.png).

The alphabet is a painted sheet, not a font file: glyphs are cut from it by
alpha projection and set with even tracking on a shared baseline.
Writes godot/assets/ui/title/title.png (two lines, transparent, soft shadow).
"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
SHEET = ROOT / "concept-art" / "ui" / "tipografia" / "alfabeto-dourado-v1.png"
OUT = ROOT / "godot" / "assets" / "ui" / "title"
ROW_LETTERS = ["ABCDEFGHIJKLM", "NOPQRSTUV#YZ"]  # '#' is W and X, touching in the sheet
LINES = ["GALE", "BREAKER"]
TRACKING = 0.08  # extra space between letters, in cap heights


def runs(mask):
    out, start = [], None
    for i, v in enumerate(mask):
        if v and start is None:
            start = i
        elif not v and start is not None:
            out.append((start, i))
            start = None
    if start is not None:
        out.append((start, len(mask)))
    return out


def glyphs():
    sheet = Image.open(SHEET).convert("RGBA")
    alpha = np.asarray(sheet.getchannel("A")) > 40
    bands = runs(alpha.any(axis=1))[:2]
    found = {}
    for (y0, y1), letters in zip(bands, ROW_LETTERS):
        for (x0, x1), letter in zip(runs(alpha[y0:y1].any(axis=0)), letters):
            ys = np.where(alpha[y0:y1, x0:x1].any(axis=1))[0]
            box = (x0, y0 + ys[0], x1, y0 + ys[-1] + 1)
            found[letter] = sheet.crop(box)
    return found


def set_line(text, found, cap):
    tiles = [found[c] for c in text]
    gap = int(cap * TRACKING)
    width = sum(t.width for t in tiles) + gap * (len(tiles) - 1)
    line = Image.new("RGBA", (width, cap), (0, 0, 0, 0))
    x = 0
    for t in tiles:
        # Caps sit on the baseline; trim any slight height difference at the top.
        line.alpha_composite(t.crop((0, max(0, t.height - cap), t.width, t.height)), (x, max(0, cap - t.height)))
        x += t.width + gap
    return line


def main():
    found = glyphs()
    cap = max(found[c].height for c in "GALEBRK")
    lines = [set_line(text, found, cap) for text in LINES]
    leading = int(cap * 0.42)
    pad = 24
    width = max(l.width for l in lines) + pad * 2
    height = cap * 2 + leading + pad * 2
    title = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    y = pad
    for line in lines:
        title.alpha_composite(line, (pad, y))
        y += cap + leading
    # Soft dark shadow so the gold reads over the bright beach.
    shadow_alpha = title.getchannel("A").filter(ImageFilter.GaussianBlur(7)).point(lambda v: int(v * 0.55))
    shadow = Image.new("RGBA", title.size, (20, 18, 12, 0))
    shadow.putalpha(shadow_alpha)
    final = Image.new("RGBA", title.size, (0, 0, 0, 0))
    final.alpha_composite(shadow, (3, 4))
    final.alpha_composite(title)
    OUT.mkdir(parents=True, exist_ok=True)
    final.save(OUT / "title.png")
    print("title:", final.size, "cap height", cap)


if __name__ == "__main__":
    main()
