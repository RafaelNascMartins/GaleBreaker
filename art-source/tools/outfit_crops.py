"""Crop an outfit's turnaround (front, profile, back side by side on a flat background) into
<name>_frente / _perfil / _costas.png at the base character's crop scale, so the outfit's joints
fall on the base's (same rig, animations and hitboxes).

    python art-source/tools/outfit_crops.py <turnaround.png> <base crop dir> <base name> <outfit name> [--scale-from z]

Each figure is scaled so its feet-to-`--scale-from` height (default: the whole figure, top of the
head to the soles) matches the base front crop's; with a helmet or a big hat taller than the
base's hair, pass e.g. --scale-from shoulder to match on the shoulder line instead. The body's
middle (hip rows; the profile's mid rows) is centred, the soles sit on the base's ground row.
"""
import sys
from pathlib import Path

import cv2
import numpy as np

SIZES = {'frente': 660, 'perfil': 440, 'costas': 660}
H = 851


def figure_mask(img, tol=30):
    bg = img[5, 5].astype(int)
    fg = (np.abs(img.astype(int) - bg).sum(2) > tol).astype(np.uint8)
    return cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)), bg


def figures(fg, min_w=60):
    cols = fg.any(0)
    runs, inside, start = [], False, 0
    for x, c in enumerate(cols):
        if c and not inside:
            start, inside = x, True
        if not c and inside:
            if x - start > min_w:
                runs.append((start, x))
            inside = False
    if inside:
        runs.append((start, len(cols)))
    return runs


def shoulder_row(m):
    """First row (from the top) where the figure is wider than 60% of its widest row above the
    hips: the shoulder line under a helmet or hat."""
    widths = np.array([np.ptp(np.nonzero(r)[0]) if r.any() else 0 for r in m])
    upper = widths[: int(len(widths) * .45)]
    return int(np.nonzero(upper > .6 * upper.max())[0][0])


def crop(turnaround, base_dir, base_name, name, scale_from='top'):
    src = cv2.imread(str(turnaround))
    fg, bg = figure_mask(src)
    runs = figures(fg)
    assert len(runs) == 3, f'expected 3 figures, found {runs}'
    base = cv2.imread(str(Path(base_dir) / f'{base_name}_frente.png'))
    bfg, _ = figure_mask(base)
    ys = np.nonzero(bfg.any(1))[0]
    top, bottom = ys.min(), ys.max()
    b_ref = shoulder_row(bfg[top:bottom + 1]) if scale_from == 'shoulder' else 0
    out_paths = []
    s_front = None
    for (x0, x1), view in zip(runs, ('frente', 'perfil', 'costas')):
        m = fg[:, x0:x1]
        r = np.nonzero(m.any(1))[0]
        y0, y1 = r.min(), r.max()
        cm = m[y0:y1 + 1]
        if scale_from == 'shoulder':
            if view == 'perfil':                     # the profile has no clear shoulder line
                s = s_front
            else:
                ref = shoulder_row(cm)
                s = (bottom - top - b_ref) / (y1 - y0 - ref)
            if view == 'frente':
                s_front = s
        else:
            s = (bottom - top + 1) / (y1 - y0 + 1)
        img = cv2.resize(src[y0:y1 + 1, x0:x1], None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
        W = SIZES[view]
        out = np.full((H, W, 3), bg, np.uint8)
        band = cm[int(len(cm) * (.4 if view == 'perfil' else .5)):int(len(cm) * (.6 if view == 'perfil' else .55))]
        cx = np.nonzero(band.any(0))[0].mean() * s
        ox = int(round(W / 2 - cx))
        h, w = img.shape[:2]
        oy = bottom + 1 - h                          # soles on the base's ground row
        ya, yb = max(0, oy), min(H, oy + h)
        xa, xb = max(0, ox), min(W, ox + w)
        out[ya:yb, xa:xb] = img[ya - oy:yb - oy, xa - ox:xb - ox]
        path = Path(base_dir) / f'{name}_{view}.png'
        cv2.imwrite(str(path), out)
        out_paths.append(path)
        print(view, 'scale', round(s, 3), 'figure px', y1 - y0 + 1, '->', path.name)
    return out_paths


if __name__ == '__main__':
    a = sys.argv[1:]
    sf = a[a.index('--scale-from') + 1] if '--scale-from' in a else 'top'
    crop(a[0], a[1], a[2], a[3], sf)
