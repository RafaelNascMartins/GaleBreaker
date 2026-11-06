"""Texture panels of Dale's outfit sheets (20 numbered panels each), cropped to their painted
shape: each panel's grey backdrop and number label are filled from the nearest painted pixel.
Rectangles were read off the sheets (the gutters are too close to the backdrop to detect)."""
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / 'concept-art/characters/dale'
S = 1 / 0.6           # rectangles were measured on a 0.6x preview

SHEETS = {
    'coronel': ('dale-coronel-texturas-20-paineis-psx-v1.png',
                [((5, 170), [(5, 168), (172, 335), (340, 503), (507, 670), (674, 837)]),
                 ((175, 338), [(5, 168), (172, 335), (340, 503), (507, 670), (674, 837)]),
                 ((343, 497), [(5, 168), (172, 335), (340, 503), (507, 670), (674, 837)]),
                 ((503, 668), [(5, 168), (172, 335), (340, 503), (507, 670), (674, 837)])],
                ['jacket_front', 'jacket_back', 'coat_side', 'sleeve_upper', 'sleeve_lower',
                 'shirt', 'vest_front', 'vest_back', 'pants_front', 'pants_back',
                 'pants_side', 'straw_crown', 'straw_brim', 'hat_band', 'boot_shaft',
                 'boot', 'sole', 'cane', 'hands', 'head_side']),
    'physique': ('dale-mens-physique-texturas-20-paineis-psx-v1.png',
                 [((8, 188), [(8, 210), (213, 403), (406, 528), (531, 676), (679, 830)]),
                  ((192, 345), [(8, 210), (213, 371), (374, 523), (526, 676), (679, 830)]),
                  ((350, 500), [(8, 172), (175, 330), (333, 489), (492, 662), (665, 830)]),
                  ((503, 665), [(8, 145), (148, 325), (328, 489), (492, 662), (665, 830)])],
                 ['chest_front', 'chest_back', 'torso_side', 'upper_arm', 'forearm',
                  'hands', 'fist', 'thigh_front', 'thigh_back', 'shin_front',
                  'shin_back', 'foot_top', 'sole', 'shorts_front', 'shorts_back',
                  'shorts_side', 'waistband', 'number', 'mohawk', 'head_side']),
}


def load(outfit, fill=True):
    name, rows, labels = SHEETS[outfit]
    sheet = cv2.cvtColor(cv2.imread(str(DIR / name)), cv2.COLOR_BGR2RGB)
    out, it = {}, iter(labels)
    for (y0, y1), cols in rows:
        for x0, x1 in cols:
            p = sheet[int(y0 * S) + 6:int(y1 * S) - 6, int(x0 * S) + 6:int(x1 * S) - 6].copy()
            label = next(it)
            border = np.concatenate([p[:4].reshape(-1, 3), p[-4:].reshape(-1, 3), p[:, -4:].reshape(-1, 3)])
            grey = border[(border.max(1).astype(int) - border.min(1)) < 18]
            bg = np.median(grey, 0) if len(grey) > 20 else np.array([120, 120, 120])
            # backdrop: close to that grey and itself unsaturated (dark cloth like the shorts is
            # unsaturated too, but much darker than the backdrop)
            sat = p.max(2).astype(int) - p.min(2)
            paint = ~((np.abs(p.astype(int) - bg).sum(2) < 45) & (sat < 20))
            paint[:46, :52] = False                       # the number label
            paint = cv2.morphologyEx(paint.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
            paint = cv2.erode(paint, np.ones((7, 7), np.uint8)).astype(bool)      # drop the anti-aliased rim
            if fill and paint.any():
                ys, xs = np.nonzero(paint)
                p, paint = p[ys.min():ys.max() + 1, xs.min():xs.max() + 1], paint[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
                _, lab = cv2.distanceTransformWithLabels((~paint).astype(np.uint8), cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
                src = np.zeros((lab.max() + 1, 3), np.uint8)
                src[lab[paint]] = p[paint]
                p = src[lab]
            out[label] = cv2.pyrMeanShiftFiltering(cv2.cvtColor(p, cv2.COLOR_RGB2BGR), 4, 12)[..., ::-1].copy()
    return out


if __name__ == '__main__':
    import sys
    for outfit in SHEETS:
        pans = load(outfit)
        tiles = [cv2.resize(pans[k], (150, 130), interpolation=cv2.INTER_NEAREST) for k in SHEETS[outfit][2]]
        grid = np.vstack([np.hstack(tiles[i:i + 5]) for i in range(0, 20, 5)])
        cv2.imwrite(sys.argv[1] + f'/panels_{outfit}.png', grid[..., ::-1])
