"""Palette outfits of a Legends character: a new page from the hand-painted one, recolouring
only the chosen material (by hue and saturation) and keeping everything else (skin, hair,
metal, face). The light/dark bands painted by hand are kept: each recoloured texel takes the
new ramp at its own lightness, so the shading stays exactly where it was painted.

    python art-source/tools/legends_recolor.py x12_modelo obsidiana

The character module gives RECOLOR = {outfit: [rule, ...]}, a rule being
    {'hue': (h0, h1) degrees, 'sat': (s0, s1) 0..1, 'val': (v0, v1) 0..1,
     'ramp': [(lightness 0..1, '#rrggbb'), ...], 'parts': ('prefix', ...) optional}
When colours alone can't tell materials apart (Orsted's blond hair and yellow plates), the rules
work on part islands: <name>_partes_uv.json ({part: [[uv, ...] per face]}, dumped from the body's
UVMap) is rasterised, RECOLOR_KEEP_PARTS (prefixes) are never touched and a rule with 'parts' only
touches those parts.
Writes <name>_pagina_256_<outfit>.png next to the page (same colour count as the source); the page itself
is never touched.
"""
import colorsys
import importlib
import sys

import numpy as np
from PIL import Image

COLOURS = 15


def _hex(c):
    c = c.lstrip('#')
    return np.array([int(c[i:i + 2], 16) for i in (0, 2, 4)], float)


def ramp_colour(stops, x):
    xs = [s[0] for s in stops]
    cs = np.array([_hex(s[1]) for s in stops])
    return np.stack([np.interp(x, xs, cs[:, k]) for k in range(3)], -1)


def part_labels(m, shape):
    """Per-texel part name ('' = none) from the dumped UV islands, grown 2 px for the bleed."""
    import json
    from PIL import ImageDraw, ImageFilter
    path = m.SRC / f'{m.NAME}_partes_uv.json'
    if not path.exists():
        return None
    H, W = shape[:2]
    tris = json.loads(path.read_text())
    names = sorted(tris)
    lab = Image.new('I', (W, H), 0)
    d = ImageDraw.Draw(lab)
    for i, n in enumerate(names, 1):
        for f in tris[n]:
            d.polygon([(u * W, (1 - v) * H) for u, v in f], fill=i, outline=i)
    lab = np.array(lab.convert('L').filter(ImageFilter.MaxFilter(5)) if len(names) < 255 else lab)
    return np.array([''] + names, object)[lab]


def recolor(page, rules, labels=None, keep=()):
    rgb = page.astype(float) / 255
    hsv = np.array([colorsys.rgb_to_hsv(*p) for p in rgb.reshape(-1, 3)]).reshape(rgb.shape)
    out = page.astype(float).copy()
    taken = np.zeros(page.shape[:2], bool)
    if labels is not None and keep:
        taken |= np.vectorize(lambda n: n.startswith(tuple(keep)))(labels)
    for r in rules:
        h = hsv[..., 0] * 360
        h0, h1 = r['hue']
        inh = (h >= h0) & (h <= h1) if h0 <= h1 else (h >= h0) | (h <= h1)
        m = inh & ~taken
        if 'parts' in r and labels is not None:
            m &= np.vectorize(lambda n: n.startswith(tuple(r['parts'])))(labels)
        for key, ch in (('sat', 1), ('val', 2)):
            if key in r:
                lo, hi = r[key]
                m &= (hsv[..., ch] >= lo) & (hsv[..., ch] <= hi)
        if not m.any():
            continue
        v = hsv[..., 2][m]
        lo, hi = np.percentile(v, 2), np.percentile(v, 98)
        x = np.clip((v - lo) / max(hi - lo, 1e-6), 0, 1)        # the material's own light/dark range
        out[m] = ramp_colour(r['ramp'], x)
        taken |= m
    return out.clip(0, 255).astype(np.uint8), taken


def build(module_name, outfit):
    m = importlib.import_module(module_name)
    src = m.SRC / f'{m.NAME}_pagina_256.png'
    page = np.array(Image.open(src).convert('RGB'))
    labels = part_labels(m, page.shape)
    new, taken = recolor(page, m.RECOLOR[outfit], labels, getattr(m, 'RECOLOR_KEEP_PARTS', ()))
    # no requantising: the ramp gives as many tones as the source material had (the hand-painted
    # page sets the colour count), and a fresh 15-colour fit would swallow small details (veins)
    img = Image.fromarray(new)
    path = m.SRC / f'{m.NAME}_pagina_256_{outfit}.png'
    img.save(path)
    img.convert('RGB').resize((1024, 1024), Image.NEAREST).save(m.SRC / f'{m.NAME}_pagina_256_{outfit}_x4.png')
    print('wrote', path, f'{100 * taken.mean():.0f}% of the page recoloured')
    return path


if __name__ == '__main__':
    build(sys.argv[1], sys.argv[2])
