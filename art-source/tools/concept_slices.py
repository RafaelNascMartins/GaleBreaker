"""Measure a character turnaround into horizontal rings per body part.

Reads the front and profile crops (same scale, feet on the ground row), slices every
centimetre, keeps the extents of the pixels that belong to each part, then keeps only the
heights where the outline changes direction (Douglas-Peucker, `TOL` metres). Writes
rings as (z, x0, x1, y0, y1) for legends_babuin.py, which builds them in Blender.

python art-source/tools/concept_slices.py
"""
import colorsys
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'art-source/characters/kaze/legends'
MPP = 1.9 / 977.0          # metres per pixel; the figure is 977 px tall in the front crop
TOP_Z = 0.95 + 997 * MPP / 2  # matches the reference empties in Blender (centre z 0.95)
TOL = 0.015
# Limbs carry the most readable outline corners (knee, calf, deltoid), so they keep more rings.
PART_TOL = {'upper_arm': .008, 'forearm': .008, 'fist': .008, 'thigh': .007, 'shin': .007, 'calf': .01, 'foot': .01, 'head': .01}


def classify(rgb):
    h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in rgb))
    if s < 0.12 and v > 0.6:
        return 'bg'
    if v < 0.33:
        return 'line'
    if 0.02 < h < 0.12 and s > 0.3:
        return 'skin'
    return 'cloth'


class View:
    def __init__(self, path):
        im = Image.open(path).convert('RGB')
        self.w, self.h = im.size
        px = im.load()
        self.cls = [[classify(px[x, y]) for x in range(self.w)] for y in range(self.h)]

    def extent(self, z, lo, hi, kinds):
        """Horizontal extent (metres from the image centre) of `kinds` pixels within [lo, hi]."""
        y = round((TOP_Z - z) / MPP)
        if not 0 <= y < self.h:
            return None
        row = self.cls[y]
        xs = [x for x in range(self.w) if lo <= (x - self.w / 2) * MPP <= hi
              and (row[x] in kinds or (row[x] == 'line' and 'line' in kinds))]
        if not xs:
            return None
        return ((xs[0] - self.w / 2) * MPP, (xs[-1] + 1 - self.w / 2) * MPP)


# Dark jade shading reads as outline, so cloth always includes the line class.
ANY, SKIN, CLOTH = ('skin', 'cloth', 'line'), ('skin',), ('cloth', 'line')
# part: z range, front window and kinds, side window and kinds
PARTS = {
    'head': ((1.555, 1.888), (-.2, .2, ANY), (-.3, .3, ANY)),
    'chest': ((1.25, 1.525), (-.16, .16, CLOTH), (-.3, .3, ANY)),
    'belt': ((1.165, 1.25), (-.16, .16, CLOTH), (-.3, .3, ANY)),
    'skirt': ((0.87, 1.165), (-.245, .245, CLOTH), (-.3, .3, ANY)),
    'upper_arm': ((1.215, 1.52), (.13, .6, SKIN), (-.08, .25, SKIN)),
    'forearm': ((1.15, 1.215), (.15, .6, SKIN), (-.08, .25, SKIN)),
    'wrap': ((0.985, 1.17), (.22, .6, ANY), None),
    'fist': ((0.83, 1.0), (.26, .6, SKIN), (-.1, .25, SKIN)),
    'thigh': ((0.60, 0.80), (0.0, .3, ANY), (-.3, .3, ANY)),
    'shin': ((0.395, 0.60), (0.0, .3, ANY), (-.3, .3, ANY)),
    'calf': ((0.13, 0.40), (0.0, .3, SKIN), (-.3, .3, SKIN)),
    'foot': ((0.01, 0.16), (0.0, .4, SKIN), (-.3, .3, SKIN)),
}
EAR_BAND = (1.595, 1.73)


def despike(rows):
    """3-row median per column: drops one-row spikes from outlines touching the window."""
    out = [r[:] for r in rows]
    for i in range(1, len(rows) - 1):
        for c in range(1, 5):
            out[i][c] = sorted(rows[j][c] for j in (i - 1, i, i + 1))[1]
    return out


def simplify(rows, tol):
    """Keep the rows needed so linear interpolation stays within tol on every column."""
    keep = {0, len(rows) - 1}

    def split(i, j):
        worst, at = 0.0, None
        for k in range(i + 1, j):
            t = (rows[k][0] - rows[i][0]) / (rows[j][0] - rows[i][0])
            err = max(abs(rows[k][c] - (rows[i][c] + (rows[j][c] - rows[i][c]) * t)) for c in range(1, 5))
            if err > worst:
                worst, at = err, k
        if at is not None and worst > tol:
            keep.add(at)
            split(i, at)
            split(at, j)

    split(0, len(rows) - 1)
    return [rows[i] for i in sorted(keep)]


def measure():
    front, side = View(SRC / 'babuin_frente.png'), View(SRC / 'babuin_perfil.png')
    out = {}
    for name, ((z0, z1), fw, sw) in PARTS.items():
        rows = []
        for i in range(round(z0 * 100), round(z1 * 100) + 1):
            z = i / 100
            f = front.extent(z, *fw)
            s = side.extent(z, *sw) if sw else (-0.015, 0.19)  # wraps merge with the robe in profile
            if f and s:
                rows.append([z, f[0], f[1], s[0], s[1]])
        if name == 'head':
            # The ears join the head outline in front view; bridge the cheek across the ear band.
            lo = next(r for r in rows if r[0] >= EAR_BAND[0])
            hi = next(r for r in reversed(rows) if r[0] <= EAR_BAND[1])
            ear = []
            for r in rows:
                if EAR_BAND[0] < r[0] < EAR_BAND[1]:
                    t = (r[0] - lo[0]) / (hi[0] - lo[0])
                    ear.append([r[0], r[2]])
                    r[1] = lo[1] + (hi[1] - lo[1]) * t
                    r[2] = lo[2] + (hi[2] - lo[2]) * t
            out['ear'] = [[z, x] for z, x in ear]
        out[name] = [[round(v, 4) for v in r] for r in simplify(despike(rows), PART_TOL.get(name, TOL))]
    return out


if __name__ == '__main__':
    data = measure()
    (SRC / 'babuin_slices.json').write_text(json.dumps(data, indent=1))
    for k, v in data.items():
        print(k, len(v), 'rings' if k != 'ear' else 'rows')
