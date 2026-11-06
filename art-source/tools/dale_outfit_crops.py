"""Crop an outfit turnaround of Dale into front / profile / back views at the base model's scale.

The outfit sheets are generated at roughly the same framing as the base turnaround, but not
exactly: each view is scaled so its body silhouette overlaps the base crop best (feet on the same
line, same axis), searched over 0.85-1.15. Writes dale_<outfit>_{frente,perfil,costas}.png next
to the base crops (same 660 x 1002 canvas, so legends_texture's projection works unchanged).

python dale_outfit_crops.py coronel concept-art/characters/dale/dale-coronel-turnaround-psx-v1.png
"""
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'art-source/characters/ignis/legends'
W, H = 660, 1002


def figures(im):
    bg = im[5, 5].astype(int)
    m = (np.abs(im.astype(int) - bg).sum(2) > 40).astype(np.uint8)
    # A drawn ground line joins the figures: drop rows that run across most of the sheet.
    m[m.mean(1) > 0.9] = 0
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    n, comp, st, _ = cv2.connectedComponentsWithStats(m)
    keep = [i for i in range(1, n) if st[i, 4] > 2000]
    # Pieces of one figure (a foot cut off by the ground line) overlap it horizontally: merge them.
    groups = []
    for i in sorted(keep, key=lambda i: -st[i, 4]):
        x0, x1 = st[i, 0], st[i, 0] + st[i, 2]
        for g in groups:
            if x0 < g[2] and x1 > g[1] and st[i, 4] < 20000:
                g[0].append(i); break
        else:
            groups.append([[i], x0, x1, st[i, 4]])
    groups = sorted((g for g in groups if g[3] > 20000), key=lambda g: g[1])
    merged = np.zeros_like(comp)
    for k, g in enumerate(groups, start=1):
        merged[np.isin(comp, g[0])] = k
    return merged, list(range(1, len(groups) + 1)), st


def mask_of(img):
    bg = img[3, 3].astype(int)
    return (np.abs(img.astype(int) - bg).sum(2) > 40)


def place(im, comp, i, scale, axis_row_frac=0.6):
    """The figure i scaled about its feet, centred on its axis, on the W x H canvas."""
    mask = comp == i
    ys, xs = np.nonzero(mask)
    feet = ys.max()
    row = int(ys.min() + (feet - ys.min()) * axis_row_frac)
    r = np.nonzero(mask[row])[0]
    ax = (r.min() + r.max()) / 2
    bgc = np.median(im[0:10, 0:10].reshape(-1, 3), 0)
    src = np.where(mask[..., None], im, bgc).astype(np.uint8)
    # affine: (x, y) -> ((x - ax) * s + W/2, (y - feet) * s + H - 1)
    M = np.float32([[scale, 0, W / 2 - ax * scale], [0, scale, (H - 1) - feet * scale]])
    out = cv2.warpAffine(src, M, (W, H), flags=cv2.INTER_AREA, borderMode=cv2.BORDER_CONSTANT,
                         borderValue=tuple(int(c) for c in bgc))
    return out


def main(outfit, sheet):
    im = cv2.imread(str(ROOT / sheet))
    comp, big, st = figures(im)
    assert len(big) == 3, f'expected 3 figures, found {len(big)}'
    for i, view in zip(big, ('frente', 'perfil', 'costas')):
        base = mask_of(cv2.imread(str(SRC / f'dale_{view}.png')))
        # Compare only the body below the head (hats and hair differ between outfits).
        body = slice(int(H * 0.25), H)
        best = max(np.arange(0.85, 1.151, 0.01),
                   key=lambda s: (lambda m: (m & base)[body].sum() / max(1, (m | base)[body].sum()))(mask_of(place(im, comp, i, s))))
        cv2.imwrite(str(SRC / f'dale_{outfit}_{view}.png'), place(im, comp, i, best))
        print(outfit, view, 'scale', round(float(best), 2))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
