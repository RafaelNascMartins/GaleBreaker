"""Segment a flat-shaded low-poly turnaround into its facets and fit straight polygons.

Mean-shift flattens each drawn facet to one colour; facets are the connected areas between
colour edges (Lab gradient) and the dark outline; watershed then splits the edge and outline
pixels between neighbouring facets, so every border is one pixel wide and shared. Each facet
is traced and simplified with approxPolyDP. Writes <view>_facetas.png (straight edges over
the faded drawing) and <view>_facetas.json (polygons in metres, horizontal from the image
centre and z up) for placing vertices.

python art-source/tools/concept_facets.py
"""
import json
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'art-source/characters/kaze/legends'
MPP = 1.9 / 977.0
TOP_Z = 0.95 + 997 * MPP / 2
EDGE = 4.0       # Lab gradient that separates two facets (the back of the head needs it this low)
MIN_AREA = 30    # px; smaller seeds are left for the watershed to absorb
EPS = 1.8        # px; polygon simplification tolerance


def segment(bgr, edge=None, sr=7, dark_l=85, min_area=MIN_AREA):
    edge = EDGE if edge is None else edge
    flat = cv2.pyrMeanShiftFiltering(bgr, sp=6, sr=sr)
    lab = cv2.cvtColor(flat, cv2.COLOR_BGR2LAB).astype(np.float32)
    grad = sum(np.abs(cv2.Sobel(lab[:, :, c], cv2.CV_32F, 1, 0, ksize=1)) +
               np.abs(cv2.Sobel(lab[:, :, c], cv2.CV_32F, 0, 1, ksize=1)) for c in range(3))
    bg = np.abs(flat.astype(int) - flat[3, 3].astype(int)).sum(2) < 30
    # outline pixels; dark outfits (a charcoal suit) need this well below their own tones
    dark = lab[:, :, 0] < dark_l
    seeds = ((grad < edge) & ~dark & ~bg).astype(np.uint8)
    n, comp, stats, _ = cv2.connectedComponentsWithStats(seeds, connectivity=4)
    markers = np.zeros(comp.shape, np.int32)
    keep = [i for i in range(1, n) if stats[i, cv2.CC_STAT_AREA] >= min_area]
    for k, i in enumerate(keep, start=2):
        markers[comp == i] = k
    markers[bg] = 1
    cv2.watershed(flat, markers)
    return markers, flat


def facets(src, mpp=MPP, top_z=TOP_Z, edge=None, sr=7, fade=0.6, dark_l=85, min_area=MIN_AREA):
    """Trace one view crop; metres run from the image centre (horizontal) and down from
    top_z at the top row. Writes <crop>_facetas.png / .json next to the crop."""
    src = Path(src)
    bgr = cv2.imread(str(src))
    markers, flat = segment(bgr, edge, sr, dark_l, min_area)
    h, w = markers.shape
    polys = []
    for k in np.unique(markers):
        if k <= 1:
            continue
        mask = (markers == k).astype(np.uint8)
        # close the 1 px watershed border so neighbouring polygons share their edges
        mask = cv2.dilate(mask, np.ones((3, 3), np.uint8))
        cs, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        c = max(cs, key=cv2.contourArea)
        if cv2.contourArea(c) < min_area:
            continue
        p = cv2.approxPolyDP(c, EPS, True)[:, 0, :]
        colour = cv2.mean(bgr, mask)[:3][::-1]
        polys.append({'colour': [round(v) for v in colour], 'area_px': int(cv2.contourArea(c)),
                      'px': p.tolist(),
                      'm': [[round((x - w / 2) * mpp, 4), round(top_z - y * mpp, 4)] for x, y in p]})
    # fade: how much the drawing is whitened under the traced lines (lower = drawing stronger)
    faded = (bgr * (1 - fade) + 255 * fade).astype(np.uint8)
    big = cv2.resize(faded, (w * 2, h * 2), interpolation=cv2.INTER_NEAREST)
    for p in polys:
        pts = (np.array(p['px']) * 2 + 1).astype(np.int32)
        cv2.polylines(big, [pts], True, (190, 0, 210), 1, cv2.LINE_AA)
        for x, y in pts:
            cv2.circle(big, (int(x), int(y)), 2, (255, 90, 0), -1)
    cv2.imwrite(str(src.with_name(src.stem + '_facetas.png')), big)
    src.with_name(src.stem + '_facetas.json').write_text(json.dumps(polys))
    return len(polys)


if __name__ == '__main__':
    # python concept_facets.py                       -> the Babuin body views
    # python concept_facets.py <crop.png> ... --mpp M --top Z   -> any other crops
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('crops', nargs='*')
    ap.add_argument('--mpp', type=float, default=MPP)
    ap.add_argument('--top', type=float, default=None, help='z of the top row (default: crop height * mpp)')
    # Dark or low-contrast outfits (the charcoal suit): --edge 3.2 --sr 6 --dark 38 --min-area 150
    ap.add_argument('--edge', type=float, default=None, help='Lab gradient between two facets (default EDGE)')
    ap.add_argument('--sr', type=int, default=7, help='mean-shift colour radius')
    ap.add_argument('--dark', type=int, default=85, help='L below which a pixel is outline')
    ap.add_argument('--min-area', type=int, default=MIN_AREA, help='px; smaller facets are dropped')
    ap.add_argument('--fade', type=float, default=0.6, help='how much the drawing is whitened in the overlay')
    a = ap.parse_args()
    if not a.crops:
        for view in ('frente', 'perfil', 'costas'):
            print(view, facets(SRC / f'babuin_{view}.png'), 'facets')
    for crop in a.crops:
        h = cv2.imread(crop).shape[0]
        print(crop, facets(crop, a.mpp, a.top if a.top is not None else h * a.mpp, a.edge, a.sr, a.fade, a.dark, a.min_area), 'facets')
