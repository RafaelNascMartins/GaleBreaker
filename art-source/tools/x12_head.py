"""X12's head from the drawings: ONE closed surface, hair or skin per face.

The hair was first made of convex stones (k-means sectors of the head volume, a 26-direction
k-DOP each): a blocky helmet, the nape a separate lump, nothing of the drawn locks. Separate
hair and skin surfaces poke through each other once decimated. Here:

1. Head volume on a 3 mm grid: inside the head's outline in the front, profile and back crops,
   and inside a rounded section per height (superellipse of the row's front width and profile
   depth; flatter in front), so the three outlines don't leave box corners.
2. Each voxel is hair when the view whose surface is nearest draws hair at its pixel, or any
   view that sees it does (the profile's hair behind the ear), except what the front draws as
   face. So the fringe tips, side locks and zigzag nape come from the drawn hair outlines.
3. Surface: the vertices are the drawn corners (outline and hairline of the three views,
   approxPolyDP) lifted onto the volume, plus fill points where no corner is near; spherical
   Delaunay from the head's centre. Each triangle takes the tone of the voxels under it. The exact hairline is
   painted on the texture page from the drawings, as in the Legends models.
"""
import cv2
import numpy as np

import x12_carve as xc
import x12_lift as xl
from x12_lift import H, MPP, SRC, TOP, W

PW = xc.PROFILE_W
VOX = 0.003
POWER = 2.5           # back half: round skull
POWER_FRONT = 5.0     # front half: flat face, the side locks come forward (profile)
CORNER_EPS = 3.0      # px: drawn outlines simplified this far (their corners are the vertices)
FILL = 0.04           # m: a fill vertex where no corner is this near
EAR = 0.02            # m: thickness of the plate kept where the profile draws skin alone
HEAD_TRIS = 1200      # faithful head surface
MERGE = 0.008         # m: corners this close (seen in two views) are one vertex
NECK = 0.03           # m: the head piece goes this far below HEAD_Z into the collar
SEEN = 2              # voxels: this close to a view's surface, the view sees it


HAIR_HI_L, HAIR_HI_CHROMA = 170, 22   # the hair's grey-violet highlights: light but colourless


def hair_mask(view):
    """Hair of one crop: dark pixels and the colourless highlights painted on them (skin,
    collar and iris are coloured), the main blob only. The blob is found after a 7 px opening
    (the lashes and brows that touch a lock are cut off) and then grown back inside the mask
    a few pixels, so the thin lock tips return but the eyes don't."""
    bgr = cv2.imread(str(SRC / f'x12_{view}.png'))
    lab = cv2.cvtColor(xl.clean(bgr), cv2.COLOR_BGR2LAB).astype(float)
    chroma = np.hypot(lab[..., 1] - 128, lab[..., 2] - 128)
    m = ((lab[..., 0] < xc.HAIR_L) | ((lab[..., 0] < HAIR_HI_L) & (chroma < HAIR_HI_CHROMA))) & xl.silhouette(bgr)
    m = m.astype(np.uint8)
    core = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    n, lab_, st, _ = cv2.connectedComponentsWithStats(core)
    if n < 2:
        return m.astype(bool)
    g = (lab_ == 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))).astype(np.uint8)
    for _ in range(5):
        g = cv2.dilate(g, np.ones((3, 3), np.uint8)) & m
    return g.astype(bool)


def _masks():
    out = {}
    for view in ('frente', 'perfil', 'costas'):
        bgr = cv2.imread(str(SRC / f'x12_{view}.png'))
        out[view] = (xl.silhouette(bgr), hair_mask(view))
    return out


def head_volume(head_front, z_low):
    """Voxel centres of the head (bool grid + axes)."""
    m = _masks()
    sil_f, sil_p, sil_b = m['frente'][0], m['perfil'][0], m['costas'][0]
    r_lo = int((TOP - z_low) / MPP)
    rows = np.nonzero(head_front[:r_lo].any(1))[0]
    cols = np.nonzero(head_front[:r_lo].any(0))[0]
    pr = np.nonzero(sil_p[:r_lo].any(0))[0]
    xs = np.arange((cols.min() - W / 2) * MPP, (cols.max() + 1 - W / 2) * MPP, VOX) + VOX / 2
    ys = np.arange((pr.min() - PW / 2) * MPP, (pr.max() + 1 - PW / 2) * MPP, VOX) + VOX / 2
    zs = np.arange(z_low, TOP - rows.min() * MPP, VOX) + VOX / 2
    Z, Y, X = np.meshgrid(zs, ys, xs, indexing='ij')
    r = ((TOP - Z) / MPP).astype(int).clip(0, H - 1)
    cf = (X / MPP + W / 2).astype(int).clip(0, W - 1)
    cb = (-X / MPP + W / 2).astype(int).clip(0, W - 1)
    cp = (Y / MPP + PW / 2).astype(int).clip(0, PW - 1)
    occ = sil_f[r, cf] & sil_b[r, cb] & sil_p[r, cp] & head_front[r, cf]
    ymid = np.zeros(len(zs))
    # rounded section per height: superellipse of the row's extents in x (front) and y (profile)
    for k in range(len(zs)):
        sl = occ[k]
        if not sl.any():
            continue
        yy, xx = np.nonzero(sl)
        x0, x1 = xs[xx].min() - VOX / 2, xs[xx].max() + VOX / 2
        y0, y1 = ys[yy].min() - VOX / 2, ys[yy].max() + VOX / 2
        u = (xs[None, :] - (x0 + x1) / 2) / ((x1 - x0) / 2)
        v = (ys[:, None] - (y0 + y1) / 2) / ((y1 - y0) / 2)
        p = np.where(v < 0, POWER_FRONT, POWER)
        occ[k] &= np.abs(u) ** p + np.abs(v) ** p <= 1
        ymid[k] = (y0 + y1) / 2
    # tone consistency: in the front half, what the front draws as hair and the profile as skin
    # is empty (the sideburns hang beside the ear, behind the cheek, not in front of the jaw);
    # the same for the back half. This gives the V jaw, the thin neck, the sideburns set back.
    hS = m['perfil'][1][r, cp]
    dF = (m['frente'][1] | _dark_outside_face('frente', r_lo))[r, cf]
    hB = m['costas'][1][r, cb]
    front = Y < ymid[:, None, None]
    before = occ.copy()
    occ &= ~(front & dF & ~hS) & ~(~front & hB & ~hS)
    # a profile cell (z, y) emptied by that (the ear: hair in front and back, skin in the
    # profile) keeps a plate EAR thick at the outer side, so the profile outline stays
    lost = before.any(2) & ~occ.any(2)
    xa = np.abs(xs)[None, None, :]
    xmax = np.where(before, xa, -1).max(2, keepdims=True)
    occ |= before & lost[:, :, None] & (xa > xmax - EAR)
    from scipy.ndimage import binary_fill_holes, label
    occ = binary_fill_holes(occ)                    # no hidden cavities inside
    lab, n = label(occ)
    if n > 1:                                       # one piece: the largest
        occ = lab == 1 + int(np.argmax(np.bincount(lab.ravel())[1:]))
    return occ, xs, ys, zs, m


def _dark_outside_face(view, r_low):
    """Dark paint outside the face's convex outline: hair and the neck's shadow beside the
    chin, both behind the jaw (the eyes and brows are inside the outline, not here)."""
    bgr = cv2.imread(str(SRC / f'x12_{view}.png'))
    sil = xl.silhouette(bgr)
    L = cv2.cvtColor(xl.clean(bgr), cv2.COLOR_BGR2LAB)[..., 0]
    skin = (sil & ~hair_mask(view) & (L >= xc.HAIR_L)).astype(np.uint8)
    skin[r_low:] = 0
    skin = cv2.morphologyEx(skin, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    face = xc._mask_hull(skin)
    return (L < xc.HAIR_L) & sil & ~face


def hair_voxels(occ, xs, ys, zs, m):
    """Hair where the nearest view (smallest depth from its surface) draws hair."""
    big = 1e9
    yidx = np.arange(len(ys))[None, :, None]
    yf = np.where(occ, yidx, big).min(1, keepdims=True)          # first voxel from the front
    yb = np.where(occ, yidx, -big).max(1, keepdims=True)
    xidx = np.abs(xs)[None, None, :]
    xm = np.where(occ, xidx, -big).max(2, keepdims=True)          # outer |x| per (z, y)
    dF = (yidx - yf) * VOX
    dB = (yb - yidx) * VOX
    dS = xm - xidx
    view = np.argmin(np.stack(np.broadcast_arrays(dF, dB, dS)), 0)
    Z, Y, X = np.meshgrid(zs, ys, xs, indexing='ij')
    r = ((TOP - Z) / MPP).astype(int).clip(0, H - 1)
    cf = (X / MPP + W / 2).astype(int).clip(0, W - 1)
    cb = (-X / MPP + W / 2).astype(int).clip(0, W - 1)
    cp = (Y / MPP + PW / 2).astype(int).clip(0, PW - 1)
    hF, hB, hS = m['frente'][1][r, cf], m['costas'][1][r, cb], m['perfil'][1][r, cp]
    hair = np.where(view == 0, hF, np.where(view == 1, hB, hS))
    # a voxel on the surface that a view sees as hair is hair even if another view is nearer
    # (behind the ear the back view draws the ear's skin, the profile the hair over it)
    xr = np.where(occ, xs[None, None, :], -big).max(2, keepdims=True)
    xl_ = np.where(occ, xs[None, None, :], big).min(2, keepdims=True)
    xa = xs[None, None, :]
    seen = SEEN * VOX
    over = ((dF < seen) & hF) | ((dB < seen) & hB) | (((xr - xa < seen) | (xa - xl_ < seen)) & hS)
    # ...except the face: what the front draws as skin stays skin (no rims of hair round it)
    hair |= over & ~((dF < seen) & ~hF)
    return occ & hair


def face_tones(P, F, hair, occ, xs, ys, zs):
    """'hair' or 'skin' per triangle: the majority of its sample points in the hair mask of
    the view it faces most (front, back or profile); a triangle unlike all three neighbours
    takes their tone."""
    a, b, c = P[F[:, 0]], P[F[:, 1]], P[F[:, 2]]
    n = np.cross(b - a, c - a)
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    bary = np.array([[1, 1, 1], [4, 1, 1], [1, 4, 1], [1, 1, 4], [2, 2, 1], [1, 2, 2], [2, 1, 2]], float)
    bary /= bary.sum(1, keepdims=True)
    # the view each triangle faces most draws its tone: its sample points in that crop
    masks = {v: hair_mask(v) for v in VIEWS}
    view = np.argmax(np.stack([-n[:, 1], n[:, 1], np.abs(n[:, 0])]), 0)   # front, back, side
    votes = np.zeros(len(F))
    for w in bary:
        q = w[0] * a + w[1] * b + w[2] * c
        r = ((TOP - q[:, 2]) / MPP).astype(int).clip(0, H - 1)
        hf = masks['frente'][r, (q[:, 0] / MPP + W / 2).astype(int).clip(0, W - 1)]
        hb = masks['costas'][r, (-q[:, 0] / MPP + W / 2).astype(int).clip(0, W - 1)]
        hs = masks['perfil'][r, (q[:, 1] / MPP + PW / 2).astype(int).clip(0, PW - 1)]
        h = np.choose(view, [hf, hb, hs])
        votes += np.where(h, 1, -1)
    tone = votes > 0
    edges = {}
    for fi, f in enumerate(F):
        for e in ((f[0], f[1]), (f[1], f[2]), (f[2], f[0])):
            edges.setdefault((min(e), max(e)), []).append(fi)
    nb = [[] for _ in F]
    for fs in edges.values():
        if len(fs) == 2:
            nb[fs[0]].append(fs[1])
            nb[fs[1]].append(fs[0])
    for _ in range(2):
        new = tone.copy()
        for fi, ns in enumerate(nb):
            if ns and all(tone[x] != tone[fi] for x in ns):
                new[fi] = not tone[fi]
        tone = new
    return ['hair' if t else 'skin' for t in tone]


VIEWS = {'frente': W, 'perfil': PW, 'costas': W}


def corners(view, eps_px, r_low, g):
    """Corners of the drawn outlines of one view, above crop row r_low: the head's outline
    (hair tips, jaw, chin, nose: the volume's own projection, so no collar or shoulder) and
    the hair's outline (fringe, sideburns, nape, the ear). Returns [(row, col, outer)]:
    outer = on the head's outline, else on the hair/skin line."""
    head = g.projection(view)
    head[r_low:] = False
    sil = head
    hm = hair_mask(view) & head
    near_bg = cv2.dilate((~sil).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
    out = []
    for mask in (head, hm):
        cs, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        for c in cs:
            if cv2.contourArea(c) < 60:
                continue
            for x, y in cv2.approxPolyDP(c, eps_px, True)[:, 0, :]:
                if y >= r_low - 1:
                    continue           # the cut at the neck: the cap ring closes it
                out.append((int(y), int(x), bool(near_bg[y, x])))
    return out


class Grid:
    def __init__(self, occ, xs, ys, zs):
        self.occ, self.xs, self.ys, self.zs = occ, xs, ys, zs

    def projection(self, view):
        """The volume seen from a view, on the crop's pixel grid."""
        w = VIEWS[view]
        r, c = np.mgrid[0:H, 0:w]
        z = TOP - (r + 0.5) * MPP
        i = ((z - self.zs[0]) / VOX).astype(int)
        if view == 'perfil':
            p, ax0 = self.occ.any(2), self.ys            # [z, y]
            u = (c + 0.5 - PW / 2) * MPP
        else:
            p, ax0 = self.occ.any(1), self.xs            # [z, x]
            u = (c + 0.5 - W / 2) * MPP * (-1 if view == 'costas' else 1)
        j = ((u - ax0[0]) / VOX + 0.5).astype(int)
        ok = (i >= 0) & (i < p.shape[0]) & (j >= 0) & (j < p.shape[1])
        out = np.zeros((H, w), bool)
        out[ok] = p[i[ok], j[ok]]
        return out

    def iz(self, z):
        return int(np.clip(round((z - self.zs[0]) / VOX - 0.5), 0, len(self.zs) - 1))

    def lift(self, view, r, c, outer):
        """3D points of a drawn corner: its depth from the volume (the first voxel the view
        sees there; for a silhouette corner, the middle of the outermost column). A profile
        corner inside the outline is on both sides of the head."""
        z = TOP - (r + 0.5) * MPP
        sl = self.occ[self.iz(z)]                     # [y, x]
        if not sl.any():
            return []
        if view == 'perfil':
            u, line, other = (c + 0.5 - PW / 2) * MPP, self.ys, self.xs
            cols = sl                                  # rows = y index
        else:
            u = (c + 0.5 - W / 2) * MPP * (-1 if view == 'costas' else 1)
            line, other = self.xs, self.ys
            cols = sl.T                                # rows = x index
        has = cols.any(1)
        k = np.nonzero(has)[0]
        j = k[np.argmin(np.abs(line[k] - u))]          # nearest occupied column
        d = other[np.nonzero(cols[j])[0]]
        u = line[j]
        if outer:
            depth = [d.mean()]
        elif view == 'frente':
            depth = [d.min() - VOX / 2]
        elif view == 'costas':
            depth = [d.max() + VOX / 2]
        else:
            depth = [d.max() + VOX / 2, d.min() - VOX / 2]
        if view == 'perfil':
            return [np.array([x, u, z]) for x in depth]
        return [np.array([u, y, z]) for y in depth]

    def ray(self, c, d):
        """Farthest occupied point from c along direction d."""
        t = np.arange(0, 0.3, VOX / 2)
        q = c + t[:, None] * d
        i = ((q[:, 2] - self.zs[0]) / VOX).astype(int)
        j = ((q[:, 1] - self.ys[0]) / VOX).astype(int)
        k = ((q[:, 0] - self.xs[0]) / VOX).astype(int)
        ok = (i >= 0) & (i < len(self.zs)) & (j >= 0) & (j < len(self.ys)) & (k >= 0) & (k < len(self.xs))
        hit = np.zeros(len(t), bool)
        hit[ok] = self.occ[i[ok], j[ok], k[ok]]
        return q[np.nonzero(hit)[0].max()] if hit.any() else None


def surface_mesh(occ, xs, ys, zs, tris, blur=(1.6, 0.7, 0.7)):
    """Marching cubes of the blurred volume (more along z: the per-height sections step from
    one slice to the next), decimated to `tris` (quadric)."""
    from scipy.ndimage import gaussian_filter
    from skimage.measure import marching_cubes
    import fast_simplification
    g = gaussian_filter(np.pad(occ.astype(np.float32), 2), blur)
    v, f, _, _ = marching_cubes(g, 0.5)
    v = v - 2
    P = np.stack([xs[0] + v[:, 2] * VOX, ys[0] + v[:, 1] * VOX, zs[0] + v[:, 0] * VOX], 1)
    P2, F2 = fast_simplification.simplify(P.astype(np.float32), f.astype(np.int32), 1 - tris / len(f))
    return np.asarray(P2, float), np.asarray(F2)


def head_surface(head_front, tris=HEAD_TRIS):
    """The head as the decimated surface of the drawn volume, tone per face from the view it
    faces."""
    occ, xs, ys, zs, m = head_volume(head_front, xl.HEAD_Z - NECK)
    hair = hair_voxels(occ, xs, ys, zs, m)
    P, F = surface_mesh(occ, xs, ys, zs, tris)
    a, b, c = P[F[:, 0]], P[F[:, 1]], P[F[:, 2]]
    if np.einsum('ij,ij->i', a - P.mean(0), np.cross(b - a, c - a)).sum() < 0:
        F = F[:, ::-1]
    tone = face_tones(P, F, hair, occ, xs, ys, zs)
    print(f'  head surface: {len(F)} tris, {tone.count("hair")} hair')
    return P, F, tone


def head_mesh(head_front, eps_px=CORNER_EPS, fill=FILL):
    """The head as one closed surface whose vertices are the drawn corners (outline and
    hairline of the three views) lifted onto the drawn head volume, plus a few fill points
    where no corner is near; triangulated by direction from the head's centre (spherical
    Delaunay), so the hairline corners are shared by hair and skin triangles."""
    occ, xs, ys, zs, m = head_volume(head_front, xl.HEAD_Z - NECK)
    hair = hair_voxels(occ, xs, ys, zs, m)
    g = Grid(occ, xs, ys, zs)
    r_low = int((TOP - zs[0]) / MPP)
    pts = []
    for view in VIEWS:
        for r, c, outer in corners(view, eps_px, r_low, g):
            pts += g.lift(view, r, c, outer)
    Z, Y, X = np.nonzero(occ)
    C = np.array([xs[X].mean(), ys[Y].mean(), zs[Z].mean()])
    # the neck's cut: a ring of 8 at the bottom slice and its centre
    zb = zs[0] + VOX / 2
    for a in np.radians(np.arange(0, 360, 45)):
        q = g.ray(np.array([C[0], C[1], zb]), np.array([np.sin(a), -np.cos(a), 0]))
        if q is not None:
            pts.append(q)
    pts.append(np.array([C[0], C[1], zs[0]]))
    P = []
    for p in pts:                                    # merge corners closer than MERGE
        if all(np.linalg.norm(p - q) >= MERGE for q in P):
            P.append(p)
    n_corner = len(P)
    k = np.arange(400) + 0.5                         # fill: Fibonacci directions
    phi, th = np.arccos(1 - 2 * k / 400), np.pi * (1 + 5 ** 0.5) * k
    for d in np.stack([np.cos(th) * np.sin(phi), np.sin(th) * np.sin(phi), np.cos(phi)], 1):
        q = g.ray(C, d)
        if q is not None and q[2] > zb + VOX and min(np.linalg.norm(q - p) for p in P) >= fill:
            P.append(q)
    P = np.array(P)
    from scipy.spatial import ConvexHull
    u = (P - C) / np.linalg.norm(P - C, axis=1, keepdims=True)
    F = ConvexHull(u).simplices
    a, b, c = u[F[:, 0]], u[F[:, 1]], u[F[:, 2]]
    flip = np.einsum('ij,ij->i', np.cross(b - a, c - a), a + b + c) < 0
    F[flip] = F[flip][:, ::-1]
    tone = face_tones(P, F, hair, occ, xs, ys, zs)
    print(f'  head: {len(P)} vertices ({n_corner} drawn corners), {len(F)} tris, {tone.count("hair")} hair')
    return P, F, tone
