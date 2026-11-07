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


def facets_detail(src, mpp=MPP, top_z=TOP_Z, scale=3, tiles=(2, 3), edge=None, sr=7, dark_l=85,
                  min_area=MIN_AREA, fade=0.6):
    """Finer tracing: the crop is enlarged `scale` times (cubic) and segmented whole, so small
    facets (knuckles, cuff rivet plates, hair locks) survive the minimum area and the polygon
    tolerance keeps more corners. Segmenting the whole enlarged image avoids seams; it is then
    cut into tiles (cols x rows) only to review and count the facets piece by piece at full size.
    Writes <crop>_facetas.json/png like facets() plus <crop>_facetas_t<r><c>.png tiles."""
    src = Path(src)
    bgr0 = cv2.imread(str(src))
    h0, w0 = bgr0.shape[:2]
    bgr = cv2.resize(bgr0, (w0 * scale, h0 * scale), interpolation=cv2.INTER_CUBIC)
    markers, flat = segment(bgr, edge, sr, dark_l, min_area * scale)
    h, w = markers.shape
    cols, rows = tiles
    th, tw = h / rows, w / cols
    polys = []
    for k in np.unique(markers):
        if k <= 1:
            continue
        mask = (markers == k).astype(np.uint8)
        mask = cv2.dilate(mask, np.ones((3, 3), np.uint8))
        cs, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        c = max(cs, key=cv2.contourArea)
        if cv2.contourArea(c) < min_area * scale:
            continue
        p = cv2.approxPolyDP(c, EPS * scale * 0.8, True)[:, 0, :] / scale
        m = cv2.moments(c)
        cx, cy = m['m10'] / max(m['m00'], 1), m['m01'] / max(m['m00'], 1)
        colour = cv2.mean(bgr, mask)[:3][::-1]
        polys.append({'colour': [round(v) for v in colour], 'area_px': round(cv2.contourArea(c) / scale ** 2, 1),
                      'tile': [int(cy // th), int(cx // tw)], 'px': np.round(p, 2).tolist(),
                      'm': [[round((x - w0 / 2) * mpp, 4), round(top_z - y * mpp, 4)] for x, y in p]})
    faded = (bgr * (1 - fade) + 255 * fade).astype(np.uint8)
    lines = faded.copy()
    for q in polys:
        pts = (np.array(q['px']) * scale).astype(np.int32)
        cv2.polylines(lines, [pts], True, (190, 0, 210), 1, cv2.LINE_AA)
        for x, y in pts:
            cv2.circle(lines, (int(x), int(y)), 2, (255, 90, 0), -1)
    counts = {}
    for r in range(rows):
        for c in range(cols):
            y0, y1, x0, x1 = int(r * th), int((r + 1) * th), int(c * tw), int((c + 1) * tw)
            n = sum(1 for q in polys if q['tile'] == [r, c])
            counts[f'{r}{c}'] = n
            tile = lines[y0:y1, x0:x1].copy()
            cv2.putText(tile, f'{r}{c}: {n} facetas', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (20, 20, 20), 2, cv2.LINE_AA)
            cv2.imwrite(str(src.with_name(f'{src.stem}_facetas_t{r}{c}.png')), tile)
    cv2.imwrite(str(src.with_name(src.stem + '_facetas.png')), cv2.resize(lines, (w0 * 2, h0 * 2), interpolation=cv2.INTER_AREA))
    src.with_name(src.stem + '_facetas.json').write_text(json.dumps(polys))
    return len(polys), counts


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
    ap.add_argument('--detail', type=int, default=0, help='enlarge N times and write review tiles (facets_detail)')
    ap.add_argument('--tiles', type=int, nargs=2, default=(2, 3), help='review tiles: cols rows')
    a = ap.parse_args()
    if a.detail:
        for crop in a.crops:
            h = cv2.imread(crop).shape[0]
            print(crop, facets_detail(crop, a.mpp, a.top if a.top is not None else h * a.mpp, a.detail, tuple(a.tiles),
                                      a.edge, a.sr, a.dark, a.min_area, a.fade))
        raise SystemExit
    if not a.crops:
        for view in ('frente', 'perfil', 'costas'):
            print(view, facets(SRC / f'babuin_{view}.png'), 'facets')
    for crop in a.crops:
        h = cv2.imread(crop).shape[0]
        print(crop, facets(crop, a.mpp, a.top if a.top is not None else h * a.mpp, a.edge, a.sr, a.fade, a.dark, a.min_area), 'facets')
