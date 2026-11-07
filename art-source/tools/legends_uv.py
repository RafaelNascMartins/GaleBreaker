"""UV layout of a Legends character, the way the references do it (study, section 10).

    python art-source/tools/legends_uv.py x12_modelo        -> <name>_pecas.json gets 'uv'

Rules measured on Mega Man and Roll:
  - one 256 x 256 body page (the face has its own page of expressions);
  - NO overlaps (the user paints the page by hand: painting one part must never paint another),
    so unlike Mega Man every part, right side included, has its own islands, and faces that
    would fall on each other inside an island are split off;
  - islands placed like the body seen from the front (head on top, her right on the left);
  - big simple islands: a limb unrolled as an open cylinder (seam at the back), a trunk piece
    as front and back, blocky pieces (head, fist, boot) projected per direction (box);
  - about 1-1.5 px/cm, more on the front of the trunk and the hands (UV_DENSITY); faces hidden
    inside other parts (UV_HIDDEN: (part, island) or (part, '*') for both limb caps) almost none.

Each island records (part, key) so legends_paint.py knows which panel paints it: keys are
'cyl', 'cap0'/'cap1' (limb ends), 'front'/'back'/'top'/'bottom' (trunk), and for box parts the
direction '+x', '-x', '+y', '-y', '+z', '-z'.
A part's 'uv' is one [u, v] (0..1, v up) per face corner, in the order of its 'f'.
"""
import importlib
import json
import sys

import cv2
import numpy as np

PAGE = 256
GAP = 2                    # px between islands
DEFAULT_DENSITY = 1.2      # px / cm
HIDDEN_DENSITY = 0.12      # px / cm for faces inside other parts (Mega Man's neck has 0)


# ---------------------------------------------------------------- islands (in metres)
def _axis(P):
    """Main axis of a limb: through its first and last rings (the loft's order)."""
    a = np.linalg.svd(P - P.mean(0))[2][0]
    if abs(a[2]) > 0.5:
        a = a if a[2] < 0 else -a           # down
    elif abs(a[1]) > abs(a[0]):
        a = a if a[1] < 0 else -a           # forward
    return a


def _frame(axis):
    fwd = np.array([0, -1.0, 0]) if abs(axis[1]) < 0.8 else np.array([0, 0, 1.0])
    f = fwd - axis * (fwd @ axis)
    f /= np.linalg.norm(f)
    return f, np.cross(axis, f)


def _normals(P, F):
    out = []
    for f in F:
        n = np.zeros(3)
        for k in range(1, len(f) - 1):
            n += np.cross(P[f[k]] - P[f[0]], P[f[k + 1]] - P[f[0]])
        out.append(n / (np.linalg.norm(n) + 1e-12))
    return np.array(out)


def cyl_islands(P, F):
    """Open cylinder around the limb axis (seam at the back) + one island per end cap."""
    axis = _axis(P)
    fwd, side = _frame(axis)
    c = P.mean(0)
    t = (P - c) @ axis
    N = _normals(P, F)
    radius = np.linalg.norm((P - c) - np.outer(t, axis), axis=1).mean()
    out = {}
    for fi, f in enumerate(F):
        cos = N[fi] @ axis
        if abs(cos) > 0.85:                                  # an end cap
            key = 'cap1' if cos > 0 else 'cap0'
            q = P[f] - c
            out.setdefault(key, {})[fi] = np.stack([q @ side, q @ fwd], 1)
            continue
        q = P[f] - c
        ang = np.arctan2(q @ side, q @ fwd)                 # 0 at the front
        # keep a face on one side of the back seam
        if ang.max() - ang.min() > np.pi:
            ang = np.where(ang < 0, ang + 2 * np.pi, ang)
        out.setdefault('cyl', {})[fi] = np.stack([ang * radius, -(q @ axis)], 1)
    return out


def front_back_islands(P, F):
    """Trunk piece: front (normal y < 0) and back, each projected on x/z; caps on x/y."""
    N = _normals(P, F)
    out = {}
    for fi, f in enumerate(F):
        q = P[f]
        if abs(N[fi][2]) > 0.8:
            key = 'top' if N[fi][2] > 0 else 'bottom'
            out.setdefault(key, {})[fi] = np.stack([q[:, 0], -q[:, 1] if key == 'top' else q[:, 1]], 1)
        elif N[fi][1] < 0:
            out.setdefault('front', {})[fi] = np.stack([q[:, 0], q[:, 2]], 1)
        else:
            out.setdefault('back', {})[fi] = np.stack([-q[:, 0], q[:, 2]], 1)
    return out


DIRS = {'+x': (0, 1), '-x': (0, -1), '+y': (1, 1), '-y': (1, -1), '+z': (2, 1), '-z': (2, -1)}


def box_islands(P, F):
    """Blocky piece: every face goes to the direction its normal points most; each direction is
    projected flat as seen from outside (front -y, sides +-x, back +y, top +z, bottom -z)."""
    N = _normals(P, F)
    out = {}
    for fi, f in enumerate(F):
        k = int(np.argmax(np.abs(N[fi])))
        key = ('+' if N[fi][k] > 0 else '-') + 'xyz'[k]
        q = P[f]
        uv = {'-y': (q[:, 0], q[:, 2]), '+y': (-q[:, 0], q[:, 2]), '+x': (q[:, 1], q[:, 2]),
              '-x': (-q[:, 1], q[:, 2]), '+z': (q[:, 0], -q[:, 1]), '-z': (q[:, 0], q[:, 1])}[key]
        out.setdefault(key, {})[fi] = np.stack(uv, 1)
    return out


METHODS = {'cyl': cyl_islands, 'front_back': front_back_islands, 'box': box_islands}


# ---------------------------------------------------------------- no overlaps
SPLIT_RES = 3000           # px / m when testing faces for overlap inside an island


def split_overlaps(faces):
    """Faces of one island that would land on each other (a fringe over the forehead, both
    seen from the front) go to separate sub-islands: greedy layers, a face joins the first
    layer it doesn't overlap. Returns a list of {face: coords} (the first is the main one)."""
    pts = np.concatenate(list(faces.values()))
    lo = pts.min(0)
    size = np.ceil((pts.max(0) - lo) * SPLIT_RES).astype(int) + 3
    order = sorted(faces, key=lambda fi: -abs(_area2(faces[fi])))
    layers = []
    for fi in order:
        poly = np.round((faces[fi] - lo) * SPLIT_RES).astype(np.int32) + 1
        m = np.zeros((size[1], size[0]), np.uint8)
        cv2.fillPoly(m, [poly], 1)
        m = cv2.erode(m, np.ones((3, 3), np.uint8)).astype(bool)     # shared edges don't count
        for lay in layers:
            if not (lay['mask'] & m).any():
                lay['mask'] |= m
                lay['faces'][fi] = faces[fi]
                break
        else:
            layers.append({'mask': m.copy(), 'faces': {fi: faces[fi]}})
    return [l['faces'] for l in layers]


def _area2(q):
    return sum(q[i, 0] * q[(i + 1) % len(q), 1] - q[(i + 1) % len(q), 0] * q[i, 1] for i in range(len(q)))


# ---------------------------------------------------------------- packing
def target_of(centre):
    """Where an island goes on the page: the body seen from the front (her right on the page's
    left, the head at the top, the feet at the bottom), as page pixel (x, y)."""
    return np.array([PAGE * (0.5 + centre[0] / 1.25), PAGE * (1.86 - centre[2]) / 1.9])


def pack(islands, density, centres):
    """Each island at the free spot nearest its body position (target_of), never overlapping
    another (bounding boxes + GAP). islands: [(id, {face: (k, 2) metres})]. If they don't fit,
    every island shrinks. Returns {id: (offset px, scale px/m, min corner m)}, shrink."""
    boxes = []
    for iid, faces in islands:
        pts = np.concatenate(list(faces.values()))
        boxes.append((iid, pts.min(0), np.ptp(pts, 0)))
    shrink = 1.0
    while True:
        occ = np.zeros((PAGE + 1, PAGE + 1), np.int32)          # summed-area table of used px
        used = np.zeros((PAGE, PAGE), bool)
        place, ok = {}, True
        for iid, lo, size in sorted(boxes, key=lambda b: -np.prod(b[2]) * density[b[0]] ** 2):
            s = density[iid] * 100 * shrink
            w, h = (np.ceil(size * s).astype(int) + 1 + 2 * GAP)
            if w > PAGE or h > PAGE:
                ok = False
                break
            t = target_of(centres[iid]) - np.array([w, h]) / 2
            ys, xs = np.mgrid[0:PAGE - h + 1, 0:PAGE - w + 1]
            free = (occ[ys + h, xs + w] - occ[ys, xs + w] - occ[ys + h, xs] + occ[ys, xs]) == 0
            if not free.any():
                ok = False
                break
            d = (xs - t[0]) ** 2 + (ys - t[1]) ** 2
            d[~free] = 1e18
            y, x = np.unravel_index(int(d.argmin()), d.shape)
            used[y:y + h, x:x + w] = True
            occ[1:, 1:] = used.cumsum(0).cumsum(1)
            place[iid] = (np.array([x + GAP, y + GAP]), s, lo)
        if ok:
            return place, shrink
        shrink *= 0.95


# ---------------------------------------------------------------- character
def layout(module_name):
    """UVs of every part (both sides with their own islands: painting one part never paints
    another), islands placed like the body seen from the front. Each face also gets 'luv':
    its corners in its island before splitting (0..1, top = 0), so panels stay whole."""
    m = importlib.import_module(module_name)
    path = m.SRC / f'{m.NAME}_pecas.json'
    parts = json.loads(path.read_text())
    old = json.loads(path.read_text())
    spec = m.UV_METHOD
    dens = getattr(m, 'UV_DENSITY', {})
    hidden = getattr(m, 'UV_HIDDEN', set())
    base_of = lambda n: n.rsplit('_', 1)[0] if n.endswith(('_l', '_r')) else n
    islands, per_part, centres, density = [], {}, {}, {}
    for name, p in parts.items():
        P, F = np.array(p['v']), p['f']
        isl = METHODS[spec.get(base_of(name), 'cyl')](P, F)
        per_part[name] = {}
        luv = [None] * len(F)
        for key, faces in isl.items():
            pts = np.concatenate(list(faces.values()))
            lo, hi = pts.min(0), pts.max(0)
            for fi, q in faces.items():
                luv[fi] = [[float((a - lo[0]) / max(hi[0] - lo[0], 1e-9)),
                            float((hi[1] - b) / max(hi[1] - lo[1], 1e-9))] for a, b in q]
            for k, sub in enumerate(split_overlaps(faces)):
                sk = key if k == 0 else f'{key}.{k}'
                per_part[name][sk] = sub
                iid = (name, sk)
                islands.append((iid, sub))
                centres[iid] = P[[v for fi in sub for v in F[fi]]].mean(0)
                b = base_of(name)
                h = (b, key) in hidden or ((b, '*') in hidden and key.startswith('cap'))
                density[iid] = HIDDEN_DENSITY if h else dens.get(b, DEFAULT_DENSITY)
        p['luv'] = luv
    place, shrink = pack(islands, density, centres)
    for name, isl in per_part.items():
        uv = [None] * len(parts[name]['f'])
        for key, faces in isl.items():
            off, s, lo = place[(name, key)]
            hi_v = max(q[:, 1].max() for q in faces.values())
            for fi, q in faces.items():
                # page pixels grow downwards: the island's top (higher z) at the top of its box
                px = off + np.stack([q[:, 0] - lo[0], hi_v - q[:, 1]], 1) * s
                uv[fi] = [[float(a / PAGE), float(1 - b / PAGE)] for a, b in px]
        parts[name]['uv'] = uv
        parts[name]['islands'] = {key: [int(i) for i in faces] for key, faces in isl.items()}
    path.write_text(json.dumps(parts))
    transfer_page(m, old, parts)
    n_split = sum(1 for i, _ in islands if '.' in i[1])
    print(f'{len(islands)} islands ({n_split} split off to avoid overlaps), density x{shrink:.2f}')
    return parts


def transfer_page(m, old, new):
    """Carry the page the model uses (possibly painted by hand) from the old UVs to the new
    ones, triangle by triangle (nearest texel), keeping a backup of the old page."""
    from PIL import Image
    page = m.SRC / f'{m.NAME}_pagina_256.png'
    if not page.exists() or not all('uv' in p for p in old.values()):
        return
    src = np.array(Image.open(page).convert('RGB'))
    k = 1
    while (m.SRC / f'{m.NAME}_pagina_256_uv_antiga_{k}.png').exists():
        k += 1
    Image.fromarray(src).save(m.SRC / f'{m.NAME}_pagina_256_uv_antiga_{k}.png')
    out = np.zeros_like(src)
    filled = np.zeros(src.shape[:2], bool)
    for name, p in new.items():
        if name not in old:
            continue
        for fi, f in enumerate(p['f']):
            a, b = np.array(p['uv'][fi]), np.array(old[name]['uv'][fi])
            if len(b) != len(a):
                continue
            for t in range(1, len(f) - 1):
                tri = [0, t, t + 1]
                A = np.stack([a[tri, 0] * PAGE, (1 - a[tri, 1]) * PAGE], 1)
                B = np.stack([b[tri, 0] * PAGE, (1 - b[tri, 1]) * PAGE], 1)
                lo, hi = np.floor(A.min(0)).astype(int), np.ceil(A.max(0)).astype(int)
                gx, gy = np.meshgrid(np.arange(lo[0], hi[0] + 1) + .5, np.arange(lo[1], hi[1] + 1) + .5)
                (x0, y0), (x1, y1), (x2, y2) = A
                d = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
                if abs(d) < 1e-12:
                    continue
                w0 = ((y1 - y2) * (gx - x2) + (x2 - x1) * (gy - y2)) / d
                w1 = ((y2 - y0) * (gx - x2) + (x0 - x2) * (gy - y2)) / d
                w2 = 1 - w0 - w1
                ins = (w0 >= -0.05) & (w1 >= -0.05) & (w2 >= -0.05)
                px, py = (gx[ins] - .5).astype(int), (gy[ins] - .5).astype(int)
                okp = (px >= 0) & (px < PAGE) & (py >= 0) & (py < PAGE)
                sxy = np.stack([w0[ins], w1[ins], w2[ins]], 1) @ B
                sx, sy = sxy[:, 0].astype(int).clip(0, PAGE - 1), sxy[:, 1].astype(int).clip(0, PAGE - 1)
                out[py[okp], px[okp]] = src[sy[okp], sx[okp]]
                filled[py[okp], px[okp]] = True
    _, lab = cv2.distanceTransformWithLabels((~filled).astype(np.uint8), cv2.DIST_L2, 5,
                                             labelType=cv2.DIST_LABEL_PIXEL)
    fill = np.zeros((lab.max() + 1, 3), np.uint8)
    fill[lab[filled]] = out[filled]
    Image.fromarray(fill[lab]).save(page)
    print('page carried to the new UVs (backup', f'{m.NAME}_pagina_256_uv_antiga_{k}.png)')


if __name__ == '__main__':
    layout(sys.argv[1] if len(sys.argv) > 1 else 'x12_modelo')
