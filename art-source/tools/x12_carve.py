"""X12's armour parts as cut stones: every drawn facet becomes a cutting plane.

For each view (front, back, profile) the facets are traced (x12_lift.trace, veins removed) and
their corners lifted to 3D with the visual hull's surface seen from that camera. A plane is
fitted to each facet's corners: its orientation is the drawing's, its place the hull's. The
hull voxels are split into parts (by the part label of their front pixel); each part is the
intersection of the half-spaces of its facets' planes, plus its bounding box. That gives closed
convex stones whose faces are the drawn facets' planes and whose edges fall where neighbouring
facets meet. A plane may cut at most CUT of its part's hull (the hull is larger than the
figure, so a little cutting is the concavity the silhouettes can't see; more is a bad plane).

Runs in the DA3 environment (needs scipy):
    C:/Users/Rafael/Tools/da3/venv/Scripts/python.exe art-source/tools/x12_carve.py
Writes art-source/characters/tophia/legends/x12_pecas.json (same format as x12_lift.py).
"""
import json

import cv2
import numpy as np
from scipy.spatial import ConvexHull, HalfspaceIntersection

import x12_lift as xl
from x12_lift import H, MPP, SRC, TOP, W

CUT = 0.04            # max share of a part's hull voxels one facet plane may remove
MIN_FACET = 40        # px: smaller facets don't make planes (rivets, slivers)
PROFILE_W = 440
MAX_GROW = 0.012      # m: the PS1 reduction never moves a surface further than this
PS1_TRIS = 1100       # budget of the PS1 version (the faithful one keeps every drawn plane)


def side_depth():
    """Hull seen from her left (+x camera): largest x per (z, y), on the profile crop grid."""
    d = np.load(SRC / 'x12_casco.npz')
    occ, xs, ys, zs = d['occ'], d['x'], d['y'], d['z']
    vox = float(xs[1] - xs[0])
    ix = np.arange(len(xs))[None, None, :]
    right = np.where(occ, ix, -1).max(2).astype(float)           # [z, y]
    g = np.where(right >= 0, xs[0] + right * vox + vox / 2, np.nan)
    valid = np.isfinite(g)
    _, lab = cv2.distanceTransformWithLabels((~valid).astype(np.uint8), cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    src = np.zeros(lab.max() + 1, int)
    vz, vy = np.nonzero(valid)
    src[lab[vz, vy]] = vz * g.shape[1] + vy
    g = cv2.GaussianBlur(g.ravel()[src[lab]].reshape(g.shape).astype(np.float32), (0, 0), 1.0)
    cols, rows = np.meshgrid(np.arange(PROFILE_W), np.arange(H))
    y = (cols - PROFILE_W / 2) * MPP
    z = TOP - rows * MPP
    return cv2.remap(g, ((y - ys[0]) / vox).astype(np.float32), ((z - zs[0]) / vox).astype(np.float32),
                     cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def lift(view, depth):
    """Facets of one view as (corners 3D, camera direction, colour)."""
    polys, _ = xl.trace(view)
    out = []
    for p in polys:
        px = p['px']
        if cv2.contourArea(px.astype(np.float32)) < MIN_FACET:
            continue
        c = px[:, 0].round().astype(int).clip(0, depth.shape[1] - 1)
        r = px[:, 1].round().astype(int).clip(0, H - 1)
        d = depth[r, c]
        z = TOP - px[:, 1] * MPP
        if view == 'frente':
            P, cam = np.stack([(px[:, 0] - W / 2) * MPP, d, z], 1), np.array([0, -1.0, 0])
        elif view == 'costas':
            P, cam = np.stack([-(px[:, 0] - W / 2) * MPP, d, z], 1), np.array([0, 1.0, 0])
        else:
            P, cam = np.stack([d, (px[:, 0] - PROFILE_W / 2) * MPP, z], 1), np.array([1.0, 0, 0])
        out.append((P, cam, p['lab'], view))
    return out


# Profile facets (xl.trace('perfil') order) of her left arm, which the profile draws in front
# of the torso: pauldron, forearm, wrist cuff, fist. The hull can't tell the arm from the torso
# behind it (one blob from the side), so without this the arm takes the torso's whole depth.
ARM_FACETS_PERFIL = [25, 26, 27, 28, 29, 30, 32, 34, 35, 38, 39, 41, 42, 45,
                     46, 48, 50, 53, 56, 58, 59,
                     66, 67, 68, 69, 70, 72, 73, 75, 82,
                     85, 86, 88, 90, 94, 97, 98, 99, 100, 101, 102, 103, 104, 107, 108, 109, 110, 111, 112]
ARM_PARTS = ('pauldron', 'forearm', 'wrist_cuff', 'fist')


def arm_profile_mask():
    """Her arm's outline in the profile crop. Kept as x12_perfil_braco.png: once written it is
    the source (it can be corrected by hand), the facet list only makes the first one."""
    path = SRC / 'x12_perfil_braco.png'
    if path.exists():
        return cv2.imread(str(path), cv2.IMREAD_GRAYSCALE) > 127
    polys, _ = xl.trace('perfil')
    m = np.zeros((H, PROFILE_W), np.uint8)
    for i in ARM_FACETS_PERFIL:
        cv2.fillPoly(m, [polys[i]['px'].round().astype(np.int32)], 255)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    flood = np.pad(m, 2)
    cv2.floodFill(flood, None, (0, 0), 255)
    m = m | (255 - flood[2:-2, 2:-2])
    cv2.imwrite(str(path), m)
    return m > 127


PROFILE_X = 0.12      # m: the profile's non-arm facets take the front's part at this x
# parts drawn in front of others in the profile: (occluder, occluded); the arm covers all
OCCLUDES = {'thigh': ('skirt',)}


def profile_masks(labels, names):
    """Each part's region in the profile crop: its own profile facets plus what is drawn in
    front of it (the arm over everything, the skirt over the thigh tops). Writes a check image
    x12_perfil_partes.png. The hull can't do it: from the side arm, chest, skirt and thighs are
    one blob, so every part took the depth of all of them."""
    arm = arm_profile_mask()
    polys, _ = xl.trace('perfil')
    own = {n: np.zeros((H, PROFILE_W), np.uint8) for n in names}
    for p in polys:
        z = TOP - p['centre'][1] * MPP
        x = PROFILE_X if z > 0.62 else 0.20          # below the skirt: the leg's axis
        n_id = label_of(np.array([[x, 0, z]]), labels)[0]
        if not n_id:
            continue
        n = names[n_id - 1]
        if n.rsplit('_', 1)[0] in ARM_PARTS:
            continue
        cv2.fillPoly(own[n], [p['px'].round().astype(np.int32)], 1)
    for n in own:
        own[n] = cv2.morphologyEx(own[n], cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8)).astype(bool) & ~arm
    out = {}
    for n in names:
        base = n.rsplit('_', 1)[0] if n.endswith(('_l', '_r')) else n
        if base in ARM_PARTS:
            out[n] = arm
            continue
        key = base + '_l' if n.endswith(('_l', '_r')) else n
        m = own.get(key, own[n]) | arm
        for occ in OCCLUDES.get(base, ()):
            m = m | own.get(occ, np.zeros_like(arm))
        out[n] = cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    rng = np.random.default_rng(3)
    pal = rng.integers(40, 255, (len(names) + 1, 3))
    im = cv2.imread(str(SRC / 'x12_perfil.png')).astype(float)
    vis = im * 0.45
    for i, n in enumerate(names, start=1):
        if n.endswith('_r'):
            continue
        m = own[n] if n in own and own[n].any() else np.zeros_like(arm)
        vis[m] += pal[i] * 0.55
    vis[arm] += np.array([200, 120, 0]) * 0.55
    cv2.imwrite(str(SRC / 'x12_perfil_partes.png'), vis.clip(0, 255).astype(np.uint8))
    profile_masks.own, profile_masks.arm = own, arm      # each part's own drawn region (x12_sculpt)
    return out


def front_labels():
    """Part name per front-crop pixel, from the front facets (nearest facet fills the gaps)."""
    polys, _ = xl.trace('frente')
    names, img = [], np.zeros((H, W), np.int32)
    for p in polys:
        cx = (p['centre'][0] - W / 2) * MPP
        cz = TOP - p['centre'][1] * MPP
        n = xl.part_of(cx, cz, p['lab'])
        if not n:
            continue
        if n not in names:
            names.append(n)
        cv2.fillPoly(img, [p['px'].round().astype(np.int32)], names.index(n) + 1)
    empty = img == 0
    _, lab = cv2.distanceTransformWithLabels(empty.astype(np.uint8), cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    src = np.zeros(lab.max() + 1, int)
    vy, vx = np.nonzero(~empty)
    src[lab[vy, vx]] = vy * W + vx
    return img.ravel()[src[lab]].reshape(img.shape), names


def label_of(P, labels):
    c = ((P[:, 0] / MPP) + W / 2).round().astype(int).clip(0, W - 1)
    r = ((TOP - P[:, 2]) / MPP).round().astype(int).clip(0, H - 1)
    return labels[r, c]


DEFECT = 6.0          # px: a concavity deeper than this splits a part into convex pieces


def convex_pieces(mask, depth=DEFECT, min_px=150):
    """Split a 2D mask into nearly convex pieces: cut from the deepest concavity point to the
    next deepest (or straight across, along the concavity's inward direction), recursively."""
    mask = mask.astype(np.uint8)
    cs, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not cs:
        return []
    c = max(cs, key=cv2.contourArea)
    if cv2.contourArea(c) < min_px:
        return [mask.astype(bool)]
    hull = cv2.convexHull(c, returnPoints=False)
    try:
        defects = cv2.convexityDefects(c, hull)
    except cv2.error:
        defects = None
    if defects is None:
        return [mask.astype(bool)]
    defects = defects[:, 0, :]
    deep = defects[defects[:, 3] / 256.0 > depth]
    if not len(deep):
        return [mask.astype(bool)]
    deep = deep[np.argsort(-deep[:, 3])]
    a = c[deep[0, 2], 0].astype(float)
    if len(deep) > 1:
        b = c[deep[1, 2], 0].astype(float)
    else:
        s0, e0 = c[deep[0, 0], 0].astype(float), c[deep[0, 1], 0].astype(float)
        e = e0 - s0
        n = np.array([e[1], -e[0]]) / max(np.linalg.norm(e), 1e-6)
        if n @ (a - s0) < 0:
            n = -n
        b = a + n * 2000
    cut = mask.copy()
    cv2.line(cut, tuple(int(v) for v in a), tuple(int(v) for v in b), 0, 2)
    n_lab, lab = cv2.connectedComponents(cut)
    if n_lab <= 2:
        return [mask.astype(bool)]
    out = []
    for k in range(1, n_lab):
        piece = lab == k
        if piece.sum() < 20:
            continue
        # give the cut line back to the piece it touches most, so pieces stay flush
        out += convex_pieces(cv2.dilate(piece.astype(np.uint8), np.ones((5, 5), np.uint8)) & mask, depth, min_px)
    return out


def outline_planes(mask2d, to_world, centre, eps=1.0):
    """Half-spaces of the convex outline of a part's 2D mask, extruded along the view axis.
    to_world maps (col, row) -> (a, b) metres on the view plane; returns 2D lines (n, d) with
    n . q <= d inside."""
    cs, _ = cv2.findContours(mask2d.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not cs:
        return []
    pts = np.concatenate(cs)[:, 0, :].astype(np.float32)
    hull = cv2.convexHull(pts)
    hull = cv2.approxPolyDP(hull, eps, True)[:, 0, :]
    q = np.array([to_world(c + 0.5, r + 0.5) for c, r in hull])
    out = []
    for a, b in zip(q, np.roll(q, -1, 0)):
        e = b - a
        if np.linalg.norm(e) < 1e-6:
            continue
        n = np.array([e[1], -e[0]]) / np.linalg.norm(e)
        if n @ (centre - a) > 0:
            n = -n
        out.append((n, float(n @ a)))
    return out


def stone(pv, m, planes_p, vox):
    """One convex stone: front outline prism (mask m), side hull prism, facet planes."""
    if len(pv) < 30:
        return None
    lo, hi = pv.min(0) - 0.05, pv.max(0) + 0.05          # safety box only
    hs = [[*e, -hi[a]] for a, e in enumerate(np.eye(3))] + [[*-e, lo[a]] for a, e in enumerate(np.eye(3))]
    c3 = pv.mean(0)
    for n2, d2 in outline_planes(m, lambda c, r: ((c - W / 2) * MPP, TOP - r * MPP), c3[[0, 2]]):
        hs.append([n2[0], 0, n2[1], -d2])
    yz = np.concatenate([pv[:, [1, 2]] + [sy * vox / 2, sz * vox / 2] for sy in (-1, 1) for sz in (-1, 1)])
    ch2 = ConvexHull(yz)
    loop = yz[ch2.vertices]
    for a, b in zip(loop, np.roll(loop, -1, 0)):
        e = b - a
        n2 = np.array([e[1], -e[0]]) / np.linalg.norm(e)
        if n2 @ (c3[[1, 2]] - a) > 0:
            n2 = -n2
        hs.append([0, n2[0], n2[1], -float(n2 @ a)])
    cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    rim = np.concatenate(cs)[::2, 0, :].astype(float) if cs else np.zeros((0, 2))
    rx = (rim[:, 0] + 0.5 - W / 2) * MPP
    rz = TOP - (rim[:, 1] + 0.5) * MPP
    zs_p = pv[:, 2]
    ry = np.array([np.median(pv[np.abs(zs_p - z) < 0.012, 1]) if (np.abs(zs_p - z) < 0.012).any()
                   else c3[1] for z in rz])
    rim3 = np.stack([rx, ry, rz], 1)
    kept = 0
    for nrm, dd, view, *_ in planes_p:
        proj = pv @ nrm
        dd = max(dd, np.quantile(proj, 1 - CUT))
        if len(rim3):
            dd = max(dd, float((rim3 @ nrm).max()) + 1e-4)
        hs.append([*nrm, -dd])
        kept += 1
    # the 3D convex hull of the part's voxels: the 3/4 views carved the hull's corners, which
    # the two prisms (front x profile) alone would fill back in as a box section
    vh, _ = _voxel_stone(pv, vox)
    hs = np.vstack([np.array(hs), vh])
    inner = pv.mean(0)
    ok = hs[:, :3] @ inner + hs[:, 3] < -1e-4
    hs = hs[ok]
    try:
        hi_ = HalfspaceIntersection(hs, inner)
    except Exception as e:      # noqa: BLE001
        print('fail', e)
        return None
    verts, faces = polytope(hs, inner, hi_)
    return verts, faces, kept, hs, inner


def polytope(hs, inner, hi_=None):
    hi_ = hi_ or HalfspaceIntersection(hs, inner)
    pts = hi_.intersections
    ch = ConvexHull(pts)
    remap = {v: i for i, v in enumerate(ch.vertices)}
    return pts[ch.vertices], [[remap[a] for a in s] for s in ch.simplices]


def _state(hs, inner, removed=None):
    """Growth, tri count (2V - 4 once coplanar triangles merge) and the planes that make a face.
    Growth is how far the stone now pokes out past the removed plane (0 without one)."""
    hi_ = HalfspaceIntersection(hs, inner)
    pts = hi_.intersections
    ch = ConvexHull(pts)
    grow = 0.0 if removed is None else float((pts[ch.vertices] @ removed[:3] + removed[3]).max())
    # a plane is active if some hull vertex lies on it
    on = np.abs(pts[ch.vertices] @ hs[:, :3].T + hs[:, 3]) < 1e-6
    active = on.sum(0) >= 3
    n_v = len(np.unique(np.round(pts[ch.vertices], 6), axis=0))
    return grow, 2 * n_v - 4, active


def reduce_stones(stones, target, max_grow=None):
    max_grow = MAX_GROW if max_grow is None else max_grow
    """PS1 budget: drop, across all stones, the face plane whose removal moves the surface the
    least (how far the stone grows past it), until the total tri count reaches target or the
    next removal would move the surface more than MAX_GROW. Near-coplanar neighbours go first,
    so the big drawn faces and the silhouette stay."""
    import heapq
    st = {}
    for name, (hs, inner) in stones.items():
        keep = np.ones(len(hs), bool)
        keep[:6] = False      # the safety box is never a candidate (and rarely a face)
        vol, tris, active = _state(hs, inner)
        st[name] = dict(hs=hs, inner=inner, alive=np.ones(len(hs), bool), cand=keep, vol=vol, tris=tris)
    total = sum(s['tris'] for s in st.values())

    def best(name):
        s = st[name]
        hs_now = s['hs'][s['alive']]
        idx = np.nonzero(s['alive'])[0]
        _, _, active = _state(hs_now, s['inner'])
        res = None
        for k in np.nonzero(active & s['cand'][idx])[0]:
            m = s['alive'].copy()
            m[idx[k]] = False
            try:
                vol, tris, _ = _state(s['hs'][m], s['inner'], s['hs'][idx[k]])
            except Exception:      # noqa: BLE001
                continue
            if tris >= s['tris']:
                continue
            cost = vol
            if res is None or cost < res[0]:
                res = (cost, int(idx[k]), vol, tris)
        return res
    heap = []
    for name in st:
        b = best(name)
        if b:
            heapq.heappush(heap, (b[0], name, b))
    while total > target and heap:
        _, name, (cost, k, vol, tris) = heapq.heappop(heap)
        if cost > max_grow:
            break
        s = st[name]
        if not s['alive'][k]:
            continue
        s['alive'][k] = False
        total -= s['tris'] - tris
        s['vol'], s['tris'] = vol, tris
        b = best(name)
        if b:
            heapq.heappush(heap, (b[0], name, b))
    print('PS1 tris', total, 'last growth', round(float(cost), 4) if heap else '-')
    if getattr(reduce_stones, 'keep_hs', False):    # x12_sculpt: half-spaces, it builds n-gons
        return {n: (s['hs'][s['alive']], s['inner']) for n, s in st.items()}
    return {n: polytope(s['hs'][s['alive']], s['inner']) for n, s in st.items()}


HAIR_L = 95           # Lab L (0-255) below this a head pixel is hair


def hair_mask(view):
    """Hair of one crop: dark pixels, the largest blob (eyes and brows are not hair)."""
    bgr = cv2.imread(str(SRC / f'x12_{view}.png'))
    L = cv2.cvtColor(xl.clean(bgr), cv2.COLOR_BGR2LAB)[..., 0]
    m = ((L < HAIR_L) & xl.silhouette(bgr)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    return lab == 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA])) if n > 1 else m.astype(bool)


HAIR_SECTORS = 7       # hair stones round the skull (top, fringe, sides, back, nape)
HEAD_GROW = 0.004      # m: the faithful head stones are simplified this far (voxel steps out)


def _mask_hull(mask):
    """Filled convex hull of a mask's largest blob."""
    n, lab, st, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8))
    if n < 2:
        return mask.astype(bool)
    big = (lab == 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))).astype(np.uint8)
    cs, _ = cv2.findContours(big, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    out = np.zeros_like(big)
    cv2.fillPoly(out, [cv2.convexHull(np.concatenate(cs))], 1)
    return out.astype(bool)


KDOP = np.array([d for d in __import__('itertools').product((-1, 0, 1), repeat=3) if any(d)], float)
KDOP /= np.linalg.norm(KDOP, axis=1, keepdims=True)


def _voxel_stone(q, vox, kdop=True):
    """Bounding half-spaces of a point set: a 26-direction k-DOP (few clean faces; the drawn
    facet planes add the rest) or, kdop=False, the exact convex hull (many small faces)."""
    if kdop:
        d = (q @ KDOP.T).max(0) + vox / 2
        return np.hstack([KDOP, -d[:, None]]), q.mean(0)
    pts = np.concatenate([q + np.array([sx, sy, sz]) * vox / 2
                          for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)])
    ch = ConvexHull(pts)
    eq = np.unique(ch.equations.round(5), axis=0)
    return eq, pts.mean(0)


def _cut(hs, inner, q, planes_h, tone, vox, near=0.015):
    """Drawn facet planes (OpenCV tracing of the three views) on a head stone: the facets of
    its tone (hair dark, skin light) whose centre lies on this stone's voxels; each may cut at
    most CUT of them, like the armour."""
    from scipy.spatial import cKDTree
    tree = cKDTree(q)
    n_kept = 0
    for nrm, dd, view, _pc, centre, L in planes_h:
        if (L < HAIR_L) != (tone == 'hair'):
            continue
        if tree.query(centre)[0] > near:
            continue
        proj = q @ nrm
        dd = max(dd, float(np.quantile(proj, 1 - CUT)))
        if (inner @ nrm) >= dd:
            continue
        hs = np.vstack([hs, [*nrm, -dd]])
        n_kept += 1
    print(f'  head {tone}: {n_kept} facet planes')
    return hs, inner


def head_stones(pv, vox, planes_h=()):
    """The head in layers, the Legends way. A skin stone (face and skull: the voxels that are
    skin both in the front and in the profile, i.e. inside the convex outline of the skin in
    each), and hair stones over it: the rest of the head's hull, split by direction from the
    skull's centre into sectors (top, fringe, sides, back, nape). Every stone is convex; the
    hollow between the hair and the face is where the layers meet. Returns {name: (hs, inner,
    tone)} for the plane reduction."""
    rows = int((TOP - xl.HEAD_Z) / MPP) + 1
    skin = {}
    for view, w in (('frente', W), ('perfil', PROFILE_W)):
        bgr = cv2.imread(str(SRC / f'x12_{view}.png'))
        m = xl.silhouette(bgr) & ~hair_mask(view)
        m[rows:] = False
        m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        skin[view] = _mask_hull(m)
    r = ((TOP - pv[:, 2]) / MPP).round().astype(int).clip(0, H - 1)
    fc = (pv[:, 0] / MPP + W / 2).round().astype(int).clip(0, W - 1)
    pc = (pv[:, 1] / MPP + PROFILE_W / 2).round().astype(int).clip(0, PROFILE_W - 1)
    is_skin = skin['frente'][r, fc] & skin['perfil'][r, pc]
    out = {'head_skin': (*_cut(*_voxel_stone(pv[is_skin], vox), pv[is_skin], planes_h, 'skin', vox), 'skin')}
    hair = pv[~is_skin]
    centre = pv[is_skin].mean(0) + [0, 0, 0.03]
    d = hair - centre
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 1e-4)
    _, lab, _ = cv2.kmeans(d.astype(np.float32), HAIR_SECTORS, None, crit, 5, cv2.KMEANS_PP_CENTERS)
    lab = lab.ravel()
    # the skin the drawings show (front and profile, not their convex outlines): no hair stone
    # may cover it, so the face, ears and neck stay visible between the layers
    face = np.zeros(len(pv), bool)
    for view, cols in (('frente', fc), ('perfil', pc)):
        bgr = cv2.imread(str(SRC / f'x12_{view}.png'))
        m = xl.silhouette(bgr) & ~cv2.dilate(hair_mask(view).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
        face |= m[r, cols]
    F = pv[is_skin & face]
    for k in range(HAIR_SECTORS):
        q = hair[lab == k]
        if len(q) < 30:
            continue
        hs, inner = _voxel_stone(q, vox)
        for _ in range(6):            # separating planes until no face point is inside
            inside = F[(F @ hs[:, :3].T + hs[:, 3] <= 0).all(1)]
            if not len(inside):
                break
            n = inside.mean(0) - q.mean(0)
            n /= np.linalg.norm(n)
            d = float((inside @ n).min()) - vox
            q = q[q @ n <= d]
            if len(q) < 30:
                break
            hs = np.vstack([hs, [*n, -d]])
            inner = q.mean(0)
        if len(q) >= 30:
            out[f'head_hair.{k}'] = (*_cut(hs, inner, q, planes_h, 'hair', vox), 'hair')
    return out


def main():
    d = np.load(SRC / 'x12_casco.npz')
    occ, xs, ys, zs = d['occ'], d['x'], d['y'], d['z']
    vox = float(xs[1] - xs[0])
    k, j, i = np.nonzero(occ)
    V = np.stack([xs[i], ys[j], zs[k]], 1)
    labels, names = front_labels()
    vlab = label_of(V, labels)
    # keep each part's largest connected piece: a stray facet label (a skirt plate read as
    # fist) would otherwise stretch the convex stone across the body
    from scipy import ndimage
    grid = np.zeros(occ.shape, np.int32)
    grid[k, j, i] = vlab
    for n_id in range(1, len(names) + 1):
        comp, n = ndimage.label(grid == n_id)
        if n > 1:
            sizes = ndimage.sum(np.ones_like(comp), comp, range(1, n + 1))
            big = 1 + int(np.argmax(sizes))
            grid[(comp > 0) & (comp != big)] = 0
    vlab = grid[k, j, i]
    # every part only where the profile draws it (or something in front of it); she is
    # symmetric, so the right side uses the left's profile
    pmask = profile_masks(labels, names)
    r = ((TOP - V[:, 2]) / MPP).round().astype(int).clip(0, H - 1)
    c = (V[:, 1] / MPP + PROFILE_W / 2).round().astype(int).clip(0, PROFILE_W - 1)
    for n_id, n in enumerate(names, start=1):
        if n == 'head':
            continue
        sel = vlab == n_id
        drop = sel & ~pmask[n][r, c]
        print(f'{n}: {int(drop.sum())} of {int(sel.sum())} voxels outside its profile')
        vlab[drop] = 0
    sil_f = xl.silhouette(cv2.imread(str(SRC / 'x12_frente.png')))
    lab_f = cv2.cvtColor(xl.clean(cv2.imread(str(SRC / 'x12_frente.png'))), cv2.COLOR_BGR2LAB).astype(float)
    sil_b = xl.silhouette(cv2.imread(str(SRC / 'x12_costas.png')))[:, ::-1]   # mirrored to the front's x
    yF, yB = xl.hull_depths()
    facets = lift('frente', yF) + lift('costas', yB) + lift('perfil', side_depth())
    planes = {n: [] for n in names}
    for P, cam, lab, view in facets:
        centre = P.mean(0)
        n_id = label_of(centre[None], labels)[0]
        if n_id == 0:
            continue
        name = names[n_id - 1]
        if view == 'perfil' and not (name.endswith('_l') or not name.endswith('_r')):
            continue        # the profile shows her left side and the middle parts only
        q = P - centre
        _, _, vt = np.linalg.svd(q)
        nrm = vt[2]
        if nrm @ cam < 0:
            nrm = -nrm
        if nrm @ cam < 0.05:
            continue        # seen edge-on: its plane is unreliable
        pc = (int(np.clip((TOP - centre[2]) / MPP, 0, H - 1)), int(np.clip(centre[0] / MPP + W / 2, 0, W - 1)))
        planes[name].append((nrm, float(nrm @ centre), view, pc, centre, lab[0]))
    out, stones = {}, {}
    head_v = V[vlab == names.index('head') + 1] if 'head' in names else None
    for n_id, name in enumerate(names, start=1):
        if name == 'head':
            continue
        mk = ((labels == n_id) & sil_f).astype(np.uint8)
        mk = cv2.morphologyEx(cv2.morphologyEx(mk, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)),
                              cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)).astype(bool) & sil_f
        pieces = convex_pieces(mk, min_px=400)
        if len(pieces) > 1:
            print(f'{name}: {len(pieces)} convex pieces')
        for pi, m in enumerate(pieces):
            pname = name if len(pieces) == 1 else f'{name}.{pi}'
            sel = (vlab == n_id) & m[((TOP - V[:, 2]) / MPP).round().astype(int).clip(0, H - 1),
                                    ((V[:, 0] / MPP) + W / 2).round().astype(int).clip(0, W - 1)]
            res = stone(V[sel], m, [pl for pl in planes[name] if m[pl[3]]], vox)
            if res is None:
                continue
            verts, faces, kept, hs_, inner_ = res
            stones[pname] = (hs_, inner_)
            L, A, B = lab_f[m].mean(0)
            if name == 'head':
                tone = 'hair' if L < 90 else 'skin'
            else:
                tone = 'metal' if np.hypot(A - 128, B - 128) < 18 else 'stone'
            out[pname] = {'bone': xl.bone(name), 'tone': tone, 'v': verts.round(4).tolist(), 'f': faces}
            print(f'{pname:16s} planes {kept:3d} verts {len(verts)}')
    if head_v is not None:
        head = head_stones(head_v, vox, planes['head'])
        clean = reduce_stones({n: (hs_, inner_) for n, (hs_, inner_, _) in head.items()}, 0, HEAD_GROW)
        for n, (verts, faces) in clean.items():
            out[n] = {'bone': 'head', 'tone': head[n][2], 'v': verts.round(4).tolist(), 'f': faces}
            stones[n] = head[n][:2]
            print(f'{n:16s} verts {len(verts)}')
    # faithful: only the voxel steps of those hulls are merged away (HEAD_GROW), drawn planes stay
    for n, (verts, faces) in reduce_stones({n: st for n, st in stones.items() if not n.startswith('head')},
                                           0, HEAD_GROW).items():
        out[n] = dict(out[n], v=verts.round(4).tolist(), f=faces)
    tris = sum(2 * len(p['v']) - 4 for p in out.values())
    (SRC / 'x12_pecas.json').write_text(json.dumps(out))
    print('faithful tris', tris)
    ps1 = {}
    for n, (verts, faces) in reduce_stones(stones, PS1_TRIS).items():
        ps1[n] = dict(out[n], v=verts.round(4).tolist(), f=faces)
    (SRC / 'x12_pecas_ps1.json').write_text(json.dumps(ps1))


if __name__ == '__main__':
    main()
