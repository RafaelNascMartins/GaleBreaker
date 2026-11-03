"""Expression atlas for the flat faces of the generated fighters (see model_rig.flat_face).

Output: godot/assets/characters/<id>/textures/face.png, a 4 x 2 grid of 512 px cells with a
transparent background. Each cell covers the same front square of the head (rig_joints.json
"face": x in [-half, half], z from decal_bottom), so any cell can be repainted by hand as long as the
features stay where the neutral cell puts them. Cell order (FaceExpression in fighter_view.gd):
  0 neutral   1 blink   2 shout (attacks)   3 hurt
  4 KO        5 victory 6 effort (guard)    7 focus (elemental / ultimate)

Shapes are traced from concept-art/characters/<id>/<id>-lowpoly-anime-v3-frente.png, in "concept
pixels" of a 4x zoom of the face (eye level at y = 260, face centre at x = 497).

Usage: python art-source/tools/generate_faces.py [fighter_id]
"""
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
CELL = 512
SS = 4  # supersampling
GRID = (4, 2)
CENTRE_X = 497
EYE_Y = 260
# Concept pixels -> cell pixels (0.0004 m per concept pixel; the cell spans 0.24 m).
SCALE = 0.0004 / 0.24 * CELL
EYE_CELL_Y = 219.7
# Eyes and brows sit closer to the nose than in the concept: the model's face is wider.
EYE_SHIFT = 30

SKIN = (200, 158, 110)
SKIN_SHADOW = (178, 124, 82)
INK = (28, 20, 18)
BROW = (27, 44, 36)
IRIS_DARK = (58, 32, 22)
IRIS = (112, 66, 42)
IRIS_LIGHT = (150, 98, 64)
LIP = (138, 86, 58)
MOUTH = (92, 30, 30)
TONGUE = (178, 82, 78)
TEETH = (246, 240, 228)
WHITE = (250, 248, 244)


def to_cell(x, y, mirror=None):
    """mirror: None for centred features (nose, mouth), False/True for the left/right eye side."""
    if mirror is not None:
        x += EYE_SHIFT
    if mirror:
        x = 2 * CENTRE_X - x
    return ((CELL / 2 + (x - CENTRE_X) * SCALE) * SS, (EYE_CELL_Y + (y - EYE_Y) * SCALE) * SS)


def pts(points, mirror=None):
    return [to_cell(x, y, mirror) for x, y in points]


def width(w):
    return max(1, int(round(w * SCALE * SS)))


def ellipse_box(cx, cy, rx, ry, mirror=None):
    (x, y) = to_cell(cx, cy, mirror)
    return [x - rx * SCALE * SS, y - ry * SCALE * SS, x + rx * SCALE * SS, y + ry * SCALE * SS]


def arc(cx, cy, rx, ry, a0, a1, steps=24):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / steps)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / steps))) for i in range(steps + 1)]


def line(d, points, w, colour, mirror=None):
    p = pts(points, mirror)
    d.line(p, fill=colour, width=width(w), joint="curve")
    r = width(w) / 2
    for x, y in (p[0], p[-1]):
        d.ellipse([x - r, y - r, x + r, y + r], fill=colour)


# --- features (screen-left side; the right side is mirrored) ---------------------------------

BROW_NEUTRAL = [(228, 120), (262, 78), (330, 88), (405, 112), (437, 182), (400, 152), (330, 124)]
BROW_ANGRY = [(232, 104), (262, 70), (330, 92), (410, 132), (447, 205), (402, 176), (330, 128)]
BROW_WORRIED = [(232, 140), (258, 112), (330, 92), (405, 66), (430, 90), (400, 108), (330, 126)]
BROW_RELAXED = [(228, 112), (262, 74), (330, 80), (405, 98), (430, 140), (398, 128), (330, 112)]
SCLERA = [(270, 212), (395, 205), (406, 250), (396, 326), (330, 336), (290, 326)]


def brow(d, shape, mirror, shadow=True):
    if shadow:
        d.polygon(pts([(300, 128), (405, 154), (440, 196), (420, 204), (380, 172), (300, 144)], mirror), fill=SKIN_SHADOW)
    d.polygon(pts(shape, mirror), fill=BROW)


def open_eye(img, d, mirror, lid=0.0, iris_scale=1.0, look=0.0):
    """lid: 0 = open, up to ~0.5 = upper lid lowered (narrowed eyes)."""
    top = 205 + (326 - 205) * lid
    sclera = [(270, max(212, top)), (395, top), (406, max(250, top + 20)), (396, 326), (330, 336), (290, 326)]
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).polygon(pts(sclera, mirror), fill=255)
    layer = Image.new("RGBA", img.size, (*SKIN, 0))
    ld = ImageDraw.Draw(layer)
    ld.polygon(pts(sclera, mirror), fill=WHITE)
    ix = 355 + look
    ld.ellipse(ellipse_box(ix, 262, 42 * iris_scale, 72 * iris_scale, mirror), fill=IRIS)
    ld.ellipse(ellipse_box(ix, 292, 30 * iris_scale, 30 * iris_scale, mirror), fill=IRIS_LIGHT)
    ld.ellipse(ellipse_box(ix, 244, 24 * iris_scale, 44 * iris_scale, mirror), fill=IRIS_DARK)
    ld.ellipse(ellipse_box(ix + 14, 226, 9, 11, mirror), fill=WHITE)
    ld.ellipse(ellipse_box(ix - 16, 300, 5, 5, mirror), fill=WHITE)
    img.alpha_composite(Image.composite(layer, Image.new("RGBA", img.size, (*SKIN, 0)), mask))
    line(d, [(245, top - 13), (290, top - 23), (350, top - 23), (400, top - 13), (415, top + 7)], 16, INK, mirror)
    line(d, [(245, top - 13), (258, top + 17)], 10, INK, mirror)
    line(d, [(302, 332), (394, 330)], 7, IRIS_DARK, mirror)


def closed_eye(d, mirror, happy=False):
    if happy:  # ^ ^
        line(d, arc(335, 280, 72, 46, 200, 340), 15, INK, mirror)
    else:  # gentle closed lid
        line(d, arc(335, 236, 76, 52, 25, 155), 14, INK, mirror)
        line(d, [(258, 270), (246, 262)], 9, INK, mirror)


def squeezed_eye(d, mirror):  # > <
    line(d, [(268, 220), (392, 262), (272, 312)], 15, INK, mirror)


def ko_eye(d, mirror):  # X
    line(d, [(282, 214), (392, 318)], 15, INK, mirror)
    line(d, [(392, 214), (282, 318)], 15, INK, mirror)


def nose(d):
    d.polygon(pts([(487, 360), (500, 362), (497, 402), (490, 398)]), fill=SKIN_SHADOW)


def smile(d, wide=False):
    if wide:
        points = [(398, 448), (440, 470), (497, 478), (554, 470), (596, 448)]
    else:
        points = [(403, 460), (450, 473), (497, 476), (544, 472), (585, 455)]
    line(d, points, 8, LIP)


def open_mouth(d, top, bottom, half_w, teeth=True, tongue=True, grin=False, grimace=False):
    if grin:  # flat top, round bottom
        shape = [(CENTRE_X - half_w, top), (CENTRE_X + half_w, top)] + arc(CENTRE_X, top, half_w, bottom - top, 0, 180)
    elif grimace:  # round top, flat bottom
        shape = [(CENTRE_X - half_w, bottom), (CENTRE_X + half_w, bottom)] + arc(CENTRE_X, bottom, half_w, bottom - top, 0, -180)
    else:
        shape = arc(CENTRE_X, (top + bottom) / 2, half_w, (bottom - top) / 2, 0, 360, 32)
    d.polygon(pts(shape), fill=MOUTH)
    if tongue:
        d.ellipse(ellipse_box(CENTRE_X, bottom - (bottom - top) * 0.22, half_w * 0.62, (bottom - top) * 0.26), fill=TONGUE)
    if teeth:
        d.polygon(pts([(CENTRE_X - half_w * 0.78, top + 4), (CENTRE_X + half_w * 0.78, top + 4),
                       (CENTRE_X + half_w * 0.7, top + (bottom - top) * 0.24), (CENTRE_X - half_w * 0.7, top + (bottom - top) * 0.24)]), fill=TEETH)
    d.line(pts(shape + shape[:1]), fill=INK, width=width(6), joint="curve")


def gritted(d):
    box = [(430, 446), (564, 446), (556, 492), (438, 492)]
    d.polygon(pts(box), fill=TEETH)
    for x in (464, 497, 530):
        d.line(pts([(x, 448), (x, 490)]), fill=(150, 130, 120), width=width(4))
    d.line(pts([(434, 469), (560, 469)]), fill=(150, 130, 120), width=width(4))
    d.line(pts(box + box[:1]), fill=INK, width=width(7), joint="curve")


def flat_mouth(d):
    line(d, [(430, 470), (497, 466), (564, 470)], 9, LIP)


# --- expressions ----------------------------------------------------------------------------

def neutral(img, d):
    for m in (False, True):
        brow(d, BROW_NEUTRAL, m)
        open_eye(img, d, m)
    nose(d)
    smile(d)


def blink(img, d):
    for m in (False, True):
        brow(d, BROW_NEUTRAL, m)
        closed_eye(d, m)
    nose(d)
    smile(d)


def shout(img, d):
    for m in (False, True):
        brow(d, BROW_ANGRY, m)
        open_eye(img, d, m, lid=0.28, iris_scale=0.82)
    nose(d)
    open_mouth(d, 430, 520, 66)


def hurt(img, d):
    for m in (False, True):
        brow(d, BROW_WORRIED, m, shadow=False)
        squeezed_eye(d, m)
    nose(d)
    open_mouth(d, 446, 496, 70, tongue=False, grimace=True)


def ko(img, d):
    for m in (False, True):
        brow(d, BROW_WORRIED, m, shadow=False)
        ko_eye(d, m)
    nose(d)
    open_mouth(d, 448, 500, 30, teeth=False)


def victory(img, d):
    for m in (False, True):
        brow(d, BROW_RELAXED, m, shadow=False)
        closed_eye(d, m, happy=True)
    nose(d)
    open_mouth(d, 446, 512, 80, tongue=True, grin=True)


def effort(img, d):
    for m in (False, True):
        brow(d, BROW_ANGRY, m)
        open_eye(img, d, m, lid=0.36, iris_scale=0.8)
    nose(d)
    gritted(d)


def focus(img, d):
    for m in (False, True):
        brow(d, BROW_ANGRY, m)
        open_eye(img, d, m, lid=0.12, iris_scale=0.62)
    nose(d)
    flat_mouth(d)


EXPRESSIONS = [neutral, blink, shout, hurt, ko, victory, effort, focus]


def main(fid):
    atlas = Image.new("RGBA", (CELL * GRID[0], CELL * GRID[1]), (*SKIN, 0))
    for i, draw in enumerate(EXPRESSIONS):
        cell = Image.new("RGBA", (CELL * SS, CELL * SS), (*SKIN, 0))
        draw(cell, ImageDraw.Draw(cell))
        atlas.paste(cell.resize((CELL, CELL), Image.LANCZOS), ((i % GRID[0]) * CELL, (i // GRID[0]) * CELL))
    out = ROOT / "godot" / "assets" / "characters" / fid / "textures" / "face.png"
    atlas.save(out)
    print("face atlas:", out.relative_to(ROOT), atlas.size)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "kaze")
