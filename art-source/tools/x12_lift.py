"""Lift X12's drawn facets into 3D on her visual hull: the front and back of every armour part
are the concept's own facets, so they match it face for face.

1. Clean each crop (front, back): amber veins are paint, not shape - inpainted away.
2. Trace the facets at 3x (concept_facets.segment) and fit polygons; merge corners closer than
   MERGE px, so neighbouring facets share their vertices.
3. Give each corner its depth from the hull (x12_casco.npz): the hull's front surface for the
   front view, its back surface for the back view (seen from each camera, smoothed one voxel).
4. Assign every facet to a part (head excluded: it is modelled apart) by where it sits.
5. Per part: front shell + back shell, closed by a side strip zipped along the part's outline
   (both shells' rims are projected on the front outline and merged by position along it).

Writes art-source/characters/tophia/legends/x12_pecas.json:
    {part: {'bone', 'v': [[x, y, z]], 'f': [[i, ...]]}}  world metres, Blender axes

python art-source/tools/x12_lift.py
"""
import json
from pathlib import Path

import cv2
import numpy as np

from concept_facets import segment

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'art-source/characters/tophia/legends'
MPP = 1.8 / 840
W, H = 660, 851
TOP = H * MPP
SCALE = 3
MERGE = 2.6          # px (crop scale): corners this close become one vertex
MIN_AREA = 50        # px (crop scale): smaller facets are absorbed by their neighbours
EPS = 1.6            # px polygon tolerance (crop scale)
HEAD_Z = 1.468


# ---------------------------------------------------------------- 1-2. facets
def clean(bgr):
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    vein = (hsv[:, :, 0] >= 14) & (hsv[:, :, 0] <= 32) & (hsv[:, :, 1] > 120) & (hsv[:, :, 2] > 190)
    rows = np.arange(H)[:, None]
    vein &= rows > (TOP - HEAD_Z) / MPP                       # the face keeps its skin tones
    vein = cv2.dilate(vein.astype(np.uint8), np.ones((5, 5), np.uint8))
    return cv2.inpaint(bgr, vein, 4, cv2.INPAINT_TELEA)


def trace(view):
    bgr = clean(cv2.imread(str(SRC / f'x12_{view}.png')))
    # each crop at its own size (the profile is 440 px wide, not W): px stay in crop pixels
    big = cv2.resize(bgr, (bgr.shape[1] * SCALE, bgr.shape[0] * SCALE), interpolation=cv2.INTER_CUBIC)
    markers, _ = segment(big, None, 7, 40, MIN_AREA * SCALE * SCALE // 2)
    lab = cv2.cvtColor(big, cv2.COLOR_BGR2LAB)
    polys = []
    for k in np.unique(markers):
        if k <= 1:
            continue
        mask = (markers == k).astype(np.uint8)
        mask = cv2.dilate(mask, np.ones((3, 3), np.uint8))
        cs, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        c = max(cs, key=cv2.contourArea)
        if cv2.contourArea(c) < MIN_AREA * SCALE * SCALE * 0.3:
            continue
        p = cv2.approxPolyDP(c, EPS * SCALE, True)[:, 0, :] / SCALE
        if len(p) < 3:
            continue
        m = mask.astype(bool)
        polys.append({'px': p, 'lab': lab[m].mean(0), 'centre': p.mean(0)})
    return polys, bgr


def silhouette(bgr, tol=40):
    fg = (np.abs(bgr.astype(int) - bgr[3, 3].astype(int)).sum(2) > tol).astype(np.uint8)
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    flood = np.pad(fg, 2)
    cv2.floodFill(flood, None, (0, 0), 1)
    return (fg | (1 - flood[2:-2, 2:-2])).astype(bool)


def merge_corners(polys, r=MERGE):
    """Greedy clustering of all corners; returns vertex array (px) and facets as index lists."""
    pts = np.concatenate([p['px'] for p in polys])
    owner = np.concatenate([[i] * len(p['px']) for i, p in enumerate(polys)])
    order = np.argsort(pts[:, 1] * 10000 + pts[:, 0])
    label = -np.ones(len(pts), int)
    centres = []
    grid = {}
    for n in order:
        x, y = pts[n]
        gx, gy = int(x // r), int(y // r)
        best, bd = -1, r
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for c in grid.get((gx + dx, gy + dy), []):
                    d = np.hypot(*(centres[c][0] - pts[n]))
                    if d < bd:
                        best, bd = c, d
        if best < 0:
            best = len(centres)
            centres.append([pts[n].copy(), 1])
            grid.setdefault((gx, gy), []).append(best)
        else:
            c = centres[best]
            c[0] = (c[0] * c[1] + pts[n]) / (c[1] + 1)
            c[1] += 1
        label[n] = best
    V = np.array([c[0] for c in centres])
    faces, start = [], 0
    for i, p in enumerate(polys):
        ids = label[start:start + len(p['px'])]
        start += len(p['px'])
        f = [int(v) for j, v in enumerate(ids) if v != ids[j - 1]]
        faces.append(f if len(set(f)) >= 3 else None)
    return V, faces


# ---------------------------------------------------------------- 3. depth from the hull
def hull_depths():
    d = np.load(SRC / 'x12_casco.npz')
    occ, xs, ys, zs = d['occ'], d['x'], d['y'], d['z']
    any_y = occ.any(1)                                        # [z, x]
    iy = np.arange(len(ys))[None, :, None]
    front = np.where(occ, iy, 10 ** 6).min(1).astype(float)
    back = np.where(occ, iy, -1).max(1).astype(float)
    vox = float(xs[1] - xs[0])
    yF = np.where(any_y, ys[0] + front * vox, np.nan)
    yB = np.where(any_y, ys[0] + back * vox + vox, np.nan)
    yF -= vox / 2

    def to_crop(grid, mirror):
        """Sample a [z, x] hull map on the crop's pixel grid (fill outside by nearest)."""
        valid = np.isfinite(grid)
        g = grid.copy()
        if (~valid).any():
            _, lab = cv2.distanceTransformWithLabels((~valid).astype(np.uint8), cv2.DIST_L2, 5,
                                                     labelType=cv2.DIST_LABEL_PIXEL)
            src = np.zeros(lab.max() + 1, int)
            vz, vx = np.nonzero(valid)
            src[lab[vz, vx]] = vz * grid.shape[1] + vx
            g = g.ravel()[src[lab]].reshape(grid.shape)
        g = cv2.GaussianBlur(g.astype(np.float32), (0, 0), 1.0)
        cols, rows = np.meshgrid(np.arange(W), np.arange(H))
        x = (cols - W / 2) * MPP * (-1 if mirror else 1)
        z = TOP - rows * MPP
        fx = (x - xs[0]) / vox
        fz = (z - zs[0]) / vox
        return cv2.remap(g, fx.astype(np.float32), fz.astype(np.float32), cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_REPLICATE)
    return to_crop(yF, False), to_crop(yB, True)


# ---------------------------------------------------------------- 4. parts
ARM0, ARM1 = np.array([0.325, 1.205]), np.array([0.475, 0.925])      # (|x|, z) elbow -> wrist


def part_of(x, z, lab):
    ax = abs(x)
    s = 'l' if x > 0 else 'r'
    metal = lab[1] < 136 and lab[2] < 136 and lab[0] < 150           # grey: cuffs, collar ring
    if z >= HEAD_Z:
        return 'head'
    if z > 1.375 and ax < 0.135:
        return 'collar'
    if z > 1.185 and ax > 0.135 and ((ax - 0.25) / 0.135) ** 2 + ((z - 1.32) / 0.14) ** 2 < 1.15:
        return 'pauldron_' + s
    if z > 1.115 and ax < 0.165:
        return 'chest'
    if ax > 0.2 and z > 0.86:
        t = np.clip(((np.array([ax, z]) - ARM0) @ (ARM1 - ARM0)) / ((ARM1 - ARM0) @ (ARM1 - ARM0)), 0, 1.2)
        if ax > 0.17 + (1.12 - z) * 0.65 or z > 1.12:
            if metal and t > 0.7:
                return 'wrist_cuff_' + s
            if t > 0.92 and z < 0.95:
                return 'fist_' + s
            return 'forearm_' + s
    if ax > 0.33 and 0.6 < z < 0.95:          # (the wide soles are not fists)
        return 'fist_' + s
    if z > 0.765 and ax < 0.16 + max(0.0, 1.12 - z) * 0.62:
        return 'skirt'
    if z > 0.60:
        return 'thigh_' + s
    if z > 0.31:
        return 'shin_' + s
    if z > 0.215 and metal:
        return 'ankle_cuff_' + s
    if z > 0.215:
        return 'shin_' + s
    return 'boot_' + s


BONES = {'head': 'head', 'collar': 'chest', 'chest': 'chest', 'skirt': 'hips', 'pauldron': 'upper_arm', 'forearm': 'forearm',
         'wrist_cuff': 'forearm', 'fist': 'hand', 'thigh': 'thigh', 'shin': 'shin', 'ankle_cuff': 'shin', 'boot': 'foot'}


def bone(part):
    if part.endswith(('_l', '_r')):
        return BONES[part[:-2]] + part[-2:]
    return BONES[part]


# ---------------------------------------------------------------- 5. shells and strip
def view_data(view, depth):
    polys, bgr = trace(view)
    V, faces = merge_corners(polys)
    mirror = view == 'costas'
    xs = (V[:, 0] - W / 2) * MPP * (-1 if mirror else 1)
    zs = TOP - V[:, 1] * MPP
    ci, ri = V[:, 0].round().astype(int).clip(0, W - 1), V[:, 1].round().astype(int).clip(0, H - 1)
    ys = depth[ri, ci]
    P = np.stack([xs, ys, zs], 1)
    parts = {}
    for p, f in zip(polys, faces):
        if f is None:
            continue
        cx = (p['centre'][0] - W / 2) * MPP * (-1 if mirror else 1)
        cz = TOP - p['centre'][1] * MPP
        name = part_of(cx, cz, p['lab'])
        if name:
            parts.setdefault(name, []).append(f)
    return P, parts, len(polys)


def boundary_loop(faces):
    """Outer boundary of a set of faces (edges used once), as the longest closed loop."""
    count = {}
    for f in faces:
        for a, b in zip(f, f[1:] + f[:1]):
            key = (min(a, b), max(a, b))
            count[key] = count.get(key, 0) + 1
    nxt = {}
    for f in faces:
        for a, b in zip(f, f[1:] + f[:1]):
            if count[(min(a, b), max(a, b))] == 1:
                nxt.setdefault(a, []).append(b)
    loops, seen = [], set()
    for s in list(nxt):
        if s in seen:
            continue
        loop, v = [s], s
        seen.add(s)
        while True:
            cand = [w for w in nxt.get(v, []) if w not in seen or (w == s and len(loop) > 2)]
            if not cand:
                break
            v = cand[0]
            if v == s:
                break
            loop.append(v)
            seen.add(v)
        loops.append(loop)
    return max(loops, key=len) if loops else []


def _arc_param(loop_pts, pts):
    """Position (0..1) of each point along a closed polyline: the nearest point on it."""
    seg_a, seg_b = loop_pts, np.roll(loop_pts, -1, 0)
    d = seg_b - seg_a
    ln = np.linalg.norm(d, axis=1)
    cum = np.concatenate([[0], np.cumsum(ln)])
    total = cum[-1]
    out = []
    for q in pts:
        t = np.clip(((q - seg_a) * d).sum(1) / np.maximum(ln ** 2, 1e-12), 0, 1)
        proj = seg_a + t[:, None] * d
        k = int(np.linalg.norm(proj - q, axis=1).argmin())
        out.append((cum[k] + t[k] * ln[k]) / total)
    return np.array(out)


def zip_strip(front_loop, back_loop, Pf, Pb, base_b):
    """Triangles joining the two rims. The front rim (in its own order) is the outline; every
    back-rim vertex is placed on it by its nearest point (x, z), then the two sequences are
    merged by position along the outline - this holds for concave outlines (skirt, legs)."""
    outline = Pf[front_loop][:, [0, 2]]
    sf = _arc_param(outline, outline)
    sb = _arc_param(outline, Pb[back_loop][:, [0, 2]])
    of, ob = np.argsort(sf), np.argsort(sb)
    F = [front_loop[i] for i in of]
    B = [back_loop[i] + base_b for i in ob]
    sf, sb = sf[of], sb[ob]
    nf, nb = len(F), len(B)
    # start both at the back vertex nearest the first front vertex
    tris = []
    i = j = 0
    while i < nf or j < nb:
        fi, bj = F[i % nf], B[j % nb]
        fa = sf[(i + 1) % nf] + (1 if i + 1 >= nf else 0)
        ba = sb[(j + 1) % nb] + (1 if j + 1 >= nb else 0)
        if j >= nb or (i < nf and fa <= ba):
            tris.append([fi, F[(i + 1) % nf], bj])
            i += 1
        else:
            tris.append([fi, B[(j + 1) % nb], bj])
            j += 1
    return tris


def main():
    yF, yB = hull_depths()
    Pf, parts_f, nf = view_data('frente', yF)
    Pb, parts_b, nb = view_data('costas', yB)
    print('facets front', nf, 'back', nb)
    out = {}
    for name in sorted(set(parts_f) | set(parts_b)):
        ff, fb = parts_f.get(name, []), parts_b.get(name, [])
        if not ff or not fb:
            print('skip', name, 'front', len(ff), 'back', len(fb))
            continue
        used_f = sorted({v for f in ff for v in f})
        used_b = sorted({v for f in fb for v in f})
        mf = {v: i for i, v in enumerate(used_f)}
        mb = {v: i for i, v in enumerate(used_b)}
        vf, vb = Pf[used_f], Pb[used_b]
        faces = [[mf[v] for v in f] for f in ff] + [[len(vf) + mb[v] for v in f] for f in fb]
        lf = [mf[v] for v in boundary_loop(ff)]
        lb = [mb[v] for v in boundary_loop(fb)]
        faces += zip_strip(lf, lb, vf, vb, len(vf))
        out[name] = {'bone': bone(name), 'v': np.concatenate([vf, vb]).round(4).tolist(), 'f': faces}
        print(f'{name:14s} front {len(ff):3d} back {len(fb):3d} facets, rim {len(lf)}/{len(lb)}')
    (SRC / 'x12_pecas.json').write_text(json.dumps(out))


if __name__ == '__main__':
    main()
