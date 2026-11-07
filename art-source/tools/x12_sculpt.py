"""X12's armour stones from the DRAWINGS only (no visual hull).

The hull of the silhouettes was the source of most trouble: from the side, arm, chest, skirt and
thighs are one blob, so every part took the depth of all of them, and its voxel steps made
dozens of sliver faces. Here every number comes from a drawn outline or facet:

1. Volume: each part (convex piece of its front outline) at each height is a rounded section,
   a superellipse with the part's front width (front crop) and the part's own depth in the
   profile (x12_perfil_partes: the part's profile facets; an end hidden behind the arm reaches
   the arm's outline).
2. Facets: every traced facet of the front, back and profile is lifted onto those sections and
   becomes a plane (orientation from its lifted corners). Near-coplanar planes of one stone
   are merged into one.
3. Stone = front outline prism x profile outline prism x facet planes; each facet plane may
   cut at most CUT of the stone's volume and never the front outline's rim.
4. Faces under MIN_FACE are dropped with the plane that made them (no slivers): one drawn
   facet, one face.
5. The head: one piece (face, ears, hair) modelled by hand on the Legends references (x12_cabeca.py).

Runs in the DA3 environment (scipy):
    PYTHONPATH=art-source/tools C:/Users/Rafael/Tools/da3/venv/Scripts/python.exe art-source/tools/x12_sculpt.py
Writes x12_pecas.json (faithful) and x12_pecas_ps1.json (PS1 budget) in the X12 folder.
"""
import json

import cv2
import numpy as np
from scipy.spatial import ConvexHull, HalfspaceIntersection

import x12_carve as xc
import x12_face as xf
import x12_mm_body as xb
import x12_cabeca as xcab
import x12_tronco as xtr
import x12_braco as xbr
import x12_perna as xpe
import x12_lift as xl
from x12_lift import H, MPP, SRC, TOP, W

PW = xc.PROFILE_W
STEP = 0.006           # m between volume samples
POWER = 2.5            # superellipse section: 2 = ellipse, higher = boxier (stone plates)
CUT = 0.04             # max share of a stone's volume one facet plane may remove
MIN_FACET = 40         # px^2: smaller traced facets make no plane
MIN_FACE = 2.0e-4      # m^2 (~1.4 cm square): smaller faces are dropped with their plane
MIN_WIDTH = 0.008      # m: faces thinner than this (slivers) go too
CLEAN_GROW = 0.015     # m: the sliver cleanup never grows a stone more than this
MIN_EDGE = 0.008       # m: corners closer than this are merged (no fans of tiny edges)
MERGE_DEG, MERGE_D = 8.0, 0.008   # planes this close in angle and offset become one
OUTLINE_EPS = 3.0      # px: outline polygons simplified this far
PS1_TRIS, PS1_GROW = 1000, 0.025


def section(u):
    return np.clip(1 - np.abs(u) ** POWER, 0, 1) ** (1 / POWER)


def extent(row):
    c = np.nonzero(row)[0]
    return (int(c.min()), int(c.max()) + 1) if len(c) else None


def profile_rows(own, allowed, arm):
    """Per crop row: the part's depth (y0, y1) in metres, from its own profile region; an end
    that touches the arm (hidden behind it) reaches the allowed region's outline there."""
    out = {}
    for r in range(H):
        e, a = extent(own[r]), extent(allowed[r])
        if e is None:
            if a is None:
                continue
            e = a
        else:
            c0, c1 = e
            if a and c0 >= 3 and arm[r, c0 - 3]:
                c0 = a[0]
            if a and c1 <= PW - 3 and arm[r, c1 + 2]:
                c1 = a[1]
            e = (c0, c1)
        out[r] = ((e[0] - PW / 2) * MPP, (e[1] - PW / 2) * MPP)
    return out


def front_rows(m):
    out = {}
    for r in np.nonzero(m.any(1))[0]:
        e = extent(m[r])
        out[int(r)] = ((e[0] - W / 2) * MPP, (e[1] - W / 2) * MPP)
    return out


def piece_points(m, prow):
    """Samples of the rounded volume of one front piece."""
    pts = []
    fr = front_rows(m)
    for r, (x0, x1) in fr.items():
        if r % 2 or r not in prow:
            continue
        y0, y1 = prow[r]
        xc_, a, yc, b = (x0 + x1) / 2, (x1 - x0) / 2, (y0 + y1) / 2, (y1 - y0) / 2
        z = TOP - (r + 0.5) * MPP
        cols = np.nonzero(m[r])[0][::2]
        x = (cols + 0.5 - W / 2) * MPP
        s = section((x - xc_) / max(a, 1e-6))
        for xi, si in zip(x, s):
            n = max(1, int(np.ceil(2 * b * si / STEP)))
            for y in np.linspace(yc - b * si, yc + b * si, n + 1):
                pts.append((xi, y, z))
    return np.array(pts)


def fill_nearest(g):
    valid = np.isfinite(g)
    if not valid.any():
        return g
    _, lab = cv2.distanceTransformWithLabels((~valid).astype(np.uint8), cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    src = np.zeros(lab.max() + 1, int)
    vy, vx = np.nonzero(valid)
    src[lab[vy, vx]] = vy * g.shape[1] + vx
    return g.ravel()[src[lab]].reshape(g.shape)


def plane_area(hs, inner):
    """Polytope of hs and the face area of every plane (0 if it makes no face)."""
    hi = HalfspaceIntersection(hs, inner)
    pts = hi.intersections
    ch = ConvexHull(pts)
    area = np.zeros(len(hs))
    for simp, eq in zip(ch.simplices, ch.equations):
        a, b, c = pts[simp]
        t = 0.5 * np.linalg.norm(np.cross(b - a, c - a))
        j = int(np.argmin(np.abs(hs[:, :3] @ eq[:3] - 1) + np.abs(hs[:, 3] - eq[3])))
        area[j] += t
    return pts, ch, area


def face_width(hs, pts, area):
    """2 * area / perimeter of each plane's face: about the face's narrow width (slivers ~0)."""
    w = np.full(len(hs), np.inf)
    for j in np.nonzero(area > 0)[0]:
        on = pts[np.abs(pts @ hs[j, :3] + hs[j, 3]) < 1e-6]
        if len(on) < 3:
            continue
        n = hs[j, :3]
        u = np.cross(n, [1, 0, 0] if abs(n[0]) < 0.9 else [0, 1, 0])
        u /= np.linalg.norm(u)
        v = np.cross(n, u)
        q = np.stack([on @ u, on @ v], 1)
        try:
            per = ConvexHull(q).area          # 2D: .area is the perimeter
        except Exception:      # noqa: BLE001
            continue
        w[j] = 2 * area[j] / max(per, 1e-9)
    return w


def _try_drop(hs, inner, j, max_grow):
    """hs without plane j, if the stone then pokes out past it by at most max_grow."""
    h2 = np.delete(hs, j, 0)
    try:
        pts = HalfspaceIntersection(h2, inner).intersections
    except Exception:      # noqa: BLE001
        return None
    if not np.isfinite(pts).all() or (pts @ hs[j, :3] + hs[j, 3]).max() > max_grow:
        return None
    return h2


def clean_small(hs, inner, protect=6, min_face=MIN_FACE, min_width=MIN_WIDTH, max_grow=CLEAN_GROW):
    """Drop planes that make slivers: faces under min_face or thinner than min_width, and
    planes that split two corners closer than MIN_EDGE. A plane goes only if the stone then
    grows past it by at most max_grow (an outline plane under a small face stays: removing it
    would let the stone swell to the safety box). The first `protect` (the box) always stay."""
    from scipy.spatial import cKDTree
    hs = np.asarray(hs, float)
    keep = set()
    for _ in range(600):
        pts, _, area = plane_area(hs, inner)
        cand = (np.arange(len(hs)) >= protect) & np.array([j not in keep for j in range(len(hs))])
        dead = cand & (area == 0)
        if dead.any():
            hs = hs[~dead]
            keep = {j - int(dead[:j].sum()) for j in keep}
            continue
        width = face_width(hs, pts, area)
        bad = cand & ((area < min_face) | (width < min_width))
        if not bad.any():
            v = np.unique(pts.round(7), axis=0)
            pairs = cKDTree(v).query_pairs(MIN_EDGE, output_type='ndarray')
            if len(pairs):
                on = np.abs(v @ hs[:, :3].T + hs[:, 3]) < 1e-6
                bad = (on[pairs[:, 0]] ^ on[pairs[:, 1]]).any(0) & cand & (area > 0)
        if not bad.any():
            break
        order = np.nonzero(bad)[0][np.argsort(area[bad])]
        for j in order:
            h2 = _try_drop(hs, inner, j, max_grow)
            if h2 is not None:
                hs = h2
                keep = {k - (k > j) for k in keep}
                break
            keep.add(int(j))
        else:
            break
    return hs


def ngons(hs, inner):
    """The stone as one polygon per plane (corners in order, outward), not triangles."""
    pts = HalfspaceIntersection(hs, inner).intersections
    v = np.unique(pts.round(6), axis=0)
    faces = []
    for h in hs:
        on = np.nonzero(np.abs(v @ h[:3] + h[3]) < 1e-5)[0]
        if len(on) < 3:
            continue
        n = h[:3]
        c = v[on].mean(0)
        u = np.cross(n, [1, 0, 0] if abs(n[0]) < 0.9 else [0, 1, 0])
        u /= np.linalg.norm(u)
        w = np.cross(n, u)
        ang = np.arctan2((v[on] - c) @ w, (v[on] - c) @ u)
        faces.append([int(i) for i in on[np.argsort(ang)]])
    return v, faces


def merge_planes(planes):
    """Greedy: planes within MERGE_DEG and MERGE_D of each other become their mean."""
    groups = []
    for n, d in planes:
        for g in groups:
            if np.degrees(np.arccos(np.clip(n @ g['n'], -1, 1))) < MERGE_DEG and abs(d - g['d']) < MERGE_D:
                k = g['k']
                g['n'] = (g['n'] * k + n) / np.linalg.norm(g['n'] * k + n)
                g['d'] = (g['d'] * k + d) / (k + 1)
                g['k'] = k + 1
                break
        else:
            groups.append({'n': n, 'd': d, 'k': 1})
    return [(g['n'], g['d']) for g in groups]


def box(pts, pad=0.05):
    lo, hi = pts.min(0) - pad, pts.max(0) + pad
    return [[*e, -hi[a]] for a, e in enumerate(np.eye(3))] + [[*-e, lo[a]] for a, e in enumerate(np.eye(3))]


def stone(pts, m, planes):
    """Convex stone of one piece: safety box, front outline prism, profile outline prism (of
    the piece's rounded volume), merged facet planes (CUT-limited, rim kept)."""
    if len(pts) < 30:
        return None
    c3 = pts.mean(0)
    hs = box(pts)
    for n2, d2 in xc.outline_planes(m, lambda c, r: ((c - W / 2) * MPP, TOP - r * MPP), c3[[0, 2]], OUTLINE_EPS):
        hs.append([n2[0], 0, n2[1], -d2])
    yz = (np.stack([pts[:, 1] / MPP + PW / 2, (TOP - pts[:, 2]) / MPP], 1)).astype(np.float32)
    loop = cv2.approxPolyDP(cv2.convexHull(yz), OUTLINE_EPS, True)[:, 0, :]
    loop = np.stack([(loop[:, 0] - PW / 2) * MPP, TOP - loop[:, 1] * MPP], 1)
    for a, b in zip(loop, np.roll(loop, -1, 0)):
        e = b - a
        if np.linalg.norm(e) < 1e-6:
            continue
        n2 = np.array([e[1], -e[0]]) / np.linalg.norm(e)
        if n2 @ (c3[[1, 2]] - a) > 0:
            n2 = -n2
        hs.append([0, n2[0], n2[1], -float(n2 @ a)])
    cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    rim = np.concatenate(cs)[::3, 0, :].astype(float)
    rz = TOP - (rim[:, 1] + 0.5) * MPP
    near = [np.abs(pts[:, 2] - z) < 0.008 for z in rz]
    rim3 = np.array([[(c + 0.5 - W / 2) * MPP, np.median(pts[k, 1]), z]
                     for (c, _), z, k in zip(rim, rz, near) if k.any()])
    kept = 0
    for nrm, dd in merge_planes(planes):
        dd = max(dd, float(np.quantile(pts @ nrm, 1 - CUT)))
        if len(rim3):
            dd = max(dd, float((rim3 @ nrm).max()) + 1e-4)
        hs.append([*nrm, -dd])
        kept += 1
    hs = np.array(hs)
    hs = hs[hs[:, :3] @ c3 + hs[:, 3] < -1e-4]
    try:
        hs = clean_small(hs, c3)
    except Exception as e:      # noqa: BLE001
        print('  fail', e)
        return None
    return hs, c3, kept


def main():
    labels, names = xc.front_labels()
    allowed = xc.profile_masks(labels, names)
    own, arm = xc.profile_masks.own, xc.profile_masks.arm
    sil_f = xl.silhouette(cv2.imread(str(SRC / 'x12_frente.png')))
    lab_f = cv2.cvtColor(xl.clean(cv2.imread(str(SRC / 'x12_frente.png'))), cv2.COLOR_BGR2LAB).astype(float)

    def key(n):
        b = n.rsplit('_', 1)[0] if n.endswith(('_l', '_r')) else n
        return b + '_l' if n.endswith(('_l', '_r')) else n

    # pieces and their volumes
    pieces = []          # (pname, part, mask, prow, points)
    prows = {}
    for n_id, name in enumerate(names, start=1):
        k = key(name)
        own_k = arm if k.rsplit('_', 1)[0] in xc.ARM_PARTS else own.get(k, np.zeros((H, PW), bool))
        prows[name] = profile_rows(own_k, allowed[name], arm)
        mk = ((labels == n_id) & sil_f).astype(np.uint8)
        mk = cv2.morphologyEx(cv2.morphologyEx(mk, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)),
                              cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)).astype(bool) & sil_f
        parts = [mk] if name == 'head' else xc.convex_pieces(mk, min_px=400)
        for pi, m in enumerate(parts):
            pname = name if len(parts) == 1 else f'{name}.{pi}'
            pieces.append((pname, name, m, prows[name], piece_points(m, prows[name])))

    # depth maps for lifting the facets: front/back y per front pixel, outer x per profile pixel
    yF = np.full((H, W), np.nan)
    yB = np.full((H, W), np.nan)
    for _, _, m, prow, _ in pieces:
        for r, (x0, x1) in front_rows(m).items():
            if r not in prow:
                continue
            y0, y1 = prow[r]
            cols = np.nonzero(m[r])[0]
            s = section(((cols + 0.5 - W / 2) * MPP - (x0 + x1) / 2) / max((x1 - x0) / 2, 1e-6))
            yF[r, cols] = (y0 + y1) / 2 - (y1 - y0) / 2 * s
            yB[r, cols] = (y0 + y1) / 2 + (y1 - y0) / 2 * s
    xS = np.full((H, PW), np.nan)
    pid = np.zeros((H, PW), np.int32)          # part id per profile pixel
    left = {n: (labels == i) & sil_f & ((np.arange(W) + 0.5 - W / 2)[None, :] >= 0)
            for i, n in enumerate(names, start=1)}
    arm_front = np.zeros((H, W), bool)
    for n in names:
        if n.endswith('_l') and n.rsplit('_', 1)[0] in xc.ARM_PARTS:
            arm_front |= left[n]
    for i, n in enumerate(names, start=1):
        if n.endswith('_r'):
            continue
        is_arm = n.rsplit('_', 1)[0] in xc.ARM_PARTS
        if is_arm:
            continue
        reg = own.get(n, np.zeros((H, PW), bool))
        fm = left[n] if n.endswith('_l') else (labels == i) & sil_f
        fr = front_rows(fm)
        pr = prows[n]
        for r in np.nonzero(reg.any(1))[0]:
            if r not in fr or r not in pr:
                continue
            (x0, x1), (y0, y1) = fr[r], pr[r]
            cols = np.nonzero(reg[r])[0]
            s = section(((cols + 0.5 - PW / 2) * MPP - (y0 + y1) / 2) / max((y1 - y0) / 2, 1e-6))
            xc_ = 0.0 if not n.endswith('_l') else (x0 + x1) / 2
            half = x1 if not n.endswith('_l') else (x1 - x0) / 2
            xS[r, cols] = xc_ + half * s
            pid[r, cols] = i
    fa = front_rows(arm_front)
    ar = profile_rows(arm, arm, arm)
    for r in np.nonzero(arm.any(1))[0]:
        if r not in fa or r not in ar:
            continue
        (x0, x1), (y0, y1) = fa[r], ar[r]
        cols = np.nonzero(arm[r])[0]
        s = section(((cols + 0.5 - PW / 2) * MPP - (y0 + y1) / 2) / max((y1 - y0) / 2, 1e-6))
        xS[r, cols] = (x0 + x1) / 2 + (x1 - x0) / 2 * s
        pid[r, cols] = -1                       # arm: part from the front label at the lifted x
    yF, yB, xS = fill_nearest(yF), fill_nearest(yB), fill_nearest(xS)

    # facet planes
    planes = {p[0]: [] for p in pieces}
    piece_masks = [(p[0], p[1], p[2]) for p in pieces]
    head_planes = []
    for P, cam, lab, view in xc.lift('frente', yF) + xc.lift('costas', yB) + xc.lift('perfil', xS):
        centre = P.mean(0)
        if view == 'perfil':
            r = int(np.clip((TOP - centre[2]) / MPP, 0, H - 1))
            c = int(np.clip(centre[1] / MPP + PW / 2, 0, PW - 1))
            if pid[r, c] == 0:
                continue
        q = P - centre
        _, _, vt = np.linalg.svd(q)
        nrm = vt[2]
        if nrm @ cam < 0:
            nrm = -nrm
        if nrm @ cam < 0.05:
            continue
        n_id = xc.label_of(centre[None], labels)[0]
        if not n_id:
            continue
        name = names[n_id - 1]
        if name == 'head':
            pc = (int(np.clip((TOP - centre[2]) / MPP, 0, H - 1)), int(np.clip(centre[0] / MPP + W / 2, 0, W - 1)))
            head_planes.append((nrm, float(nrm @ centre), view, pc, centre, lab[0]))
            continue
        fr_, fc_ = int(np.clip((TOP - centre[2]) / MPP, 0, H - 1)), int(np.clip(centre[0] / MPP + W / 2, 0, W - 1))
        for pname, part, m in piece_masks:
            if part == name and m[fr_, fc_]:
                planes[pname].append((nrm, float(nrm @ centre)))
                break

    out, stones, head_ps1 = {}, {}, {}
    for pname, part, m, prow, pts in pieces:
        if part == 'head':
            # the head modelled by hand on the Legends references (x12_cabeca.py)
            for dst in (out, head_ps1):
                dst['head'] = xcab.head_part()
                dst['neck'] = xf.neck_part()
            continue
        res = stone(pts, m, planes[pname])
        if res is None:
            print(pname, 'no stone')
            continue
        hs, inner, kept = res
        verts, faces = ngons(hs, inner)
        L, A, B = lab_f[m].mean(0)
        tone = 'metal' if np.hypot(A - 128, B - 128) < 18 else 'stone'
        out[pname] = {'bone': xl.bone(part), 'tone': tone, 'v': verts.round(4).tolist(), 'f': faces}
        stones[pname] = (hs, inner)

    # report: faces per part (one per live plane) against the concept count
    per = {}
    for n, (hs, inner) in stones.items():
        _, _, area = plane_area(hs, inner)
        base = n.split('.')[0]
        base = base.rsplit('_', 1)[0] if base.endswith(('_l', '_r')) else base
        base = 'head' if base.startswith('head') else base
        f = per.setdefault(base, [0, 0])
        f[0] += int((area > 0).sum())
        f[1] += 2 * len(xc.polytope(hs, inner)[0]) - 4
    for n, p in out.items():
        if n.startswith('head'):
            per[n] = [len(p['f']), len(p['f'])]
    for b, (nf, nt) in per.items():
        print(f'{b:12s} faces {nf:4d} tris {nt:4d}')
    tris = sum(len(f) - 2 for p in out.values() for f in p['f'])
    print('faithful tris', tris, 'faces', sum(len(p['f']) for p in out.values()))
    # the stones (drawn shapes) are kept for reference; the model is Mega Man's topology on them
    (SRC / 'x12_pecas_pedras.json').write_text(json.dumps(out))
    model = {k: p for k, p in out.items() if k.startswith(('head', 'hair', 'neck'))}
    model.update(xb.body_parts(out))
    xb.fit_outline(model, labels, names, sil_f, prows)
    model.update(xtr.parts())           # trunk modelled by hand (x12_tronco.py)
    model.update(xbr.parts())           # arms modelled by hand (x12_braco.py)
    model.update(xpe.parts())           # skirt, legs, boots by hand (x12_perna.py)
    print('model tris', sum(len(f) - 2 for p in model.values() for f in p['f']))
    (SRC / 'x12_pecas.json').write_text(json.dumps(model))
    (SRC / 'x12_pecas_ps1.json').write_text(json.dumps(model))

if __name__ == '__main__':
    main()
