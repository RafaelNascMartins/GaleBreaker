"""X12's hair built like Mega Man's (the source of truth for Legends heads): the hair is ONE
shell of long blades from the crown down to the drawn tips, not a cap with spikes glued on.

1. Hairline: for every direction round the head's axis (1 degree), the lowest height down to
   which the head volume's surface is still hair (x12_head: the volume and hair labels that
   match the front, profile and back drawings). It is jagged like the drawings: fringe tips
   over the forehead, sideburns, the zigzag nape. Simplified to its corners (tips and
   notches), each a vertex, HAIR_OUT outside the surface.
2. Shell: the hairline joined to one ring round the upper head (MID_N vertices on the surface)
   and a top vertex at the crown, so every tip ends a blade that runs up to the crown.
3. Underside: the hairline fanned to one point inside the head, so the shell is closed.

Built at the drawing's scale, then x12_face.head_xform (the bigger Legends head).
"""
import numpy as np

import x12_face as xf
import x12_head as xh
import x12_lift as xl

HAIR_OUT = 0.006       # m: the hair stands this far off the volume's surface
DP_EPS = 0.011         # m: hairline simplified this far (in height and arc length)
MID_N = 8              # vertices of the ring above the whole hairline (B)
RING_A, RING_C = 6, 10  # rings near the crown (A) and between B and the hairline (C)
RING_C_AT = 0.45       # C is this far from the hairline (local top) up to B
MID_ABOVE = 0.025      # m: the ring is this far above the hairline's highest point
INNER_DEPTH = 0.09      # m: the underside's apex, this far below the crown (inside the head)
GAP = 2                # slices: a hair run may skip this many non-hair slices (stray pixels)
ARC_R = 0.11           # m: about the head's radius (degrees -> metres for the simplification)


def _dp(pts, eps):
    keep = {0, len(pts) - 1}

    def rec(i, j):
        if j <= i + 1:
            return
        a, b = pts[i], pts[j]
        ab = b - a
        q = pts[i + 1:j] - a
        d = np.abs(ab[0] * q[:, 1] - ab[1] * q[:, 0]) / (np.linalg.norm(ab) + 1e-12)
        k = int(np.argmax(d))
        if d[k] > eps:
            keep.add(i + 1 + k)
            rec(i, i + 1 + k)
            rec(i + 1 + k, j)
    rec(0, len(pts) - 1)
    return sorted(keep)


class Surface:
    """The head volume seen from its vertical axis: radius and hair label per (degree, slice)."""

    def __init__(self, head_front):
        occ, xs, ys, zs, m = xh.head_volume(head_front, xl.HEAD_Z - xh.NECK)
        hair = xh.hair_voxels(occ, xs, ys, zs, m)
        Z, Y, X = np.nonzero(occ)
        self.cx, self.cy = 0.0, float(ys[Y].mean())
        self.zs = zs
        ang = (np.degrees(np.arctan2(xs[X] - self.cx, -(ys[Y] - self.cy))) + 360) % 360
        rad = np.hypot(xs[X] - self.cx, ys[Y] - self.cy)
        a = np.round(ang).astype(int) % 360
        self.r = np.zeros((360, len(zs)))
        self.h = np.zeros((360, len(zs)), bool)
        order = np.argsort(rad)                      # the farthest voxel per cell is written last
        self.r[a[order], Z[order]] = rad[order]
        self.h[a[order], Z[order]] = hair[Z[order], Y[order], X[order]]
        for _ in range(3):                           # fill empty degrees from their neighbours
            nb = np.maximum(np.roll(self.r, 1, 0), np.roll(self.r, -1, 0))
            hb = np.roll(self.h, 1, 0) | np.roll(self.h, -1, 0)
            empty = self.r == 0
            self.r[empty], self.h[empty] = nb[empty], hb[empty]
        self.top = float(zs[Z.max()])

    def point(self, deg, z, out=HAIR_OUT):
        k = int(np.clip(np.searchsorted(self.zs, z), 0, len(self.zs) - 1))
        d = int(round(deg)) % 360
        col = self.r[d]
        if col[k] == 0:                              # above this direction's top: nearest slice
            nz = np.nonzero(col)[0]
            k = nz[np.argmin(np.abs(nz - k))]
        t = np.radians(deg)
        r = col[k] + out
        return np.array([self.cx + r * np.sin(t), self.cy - r * np.cos(t), z])

    def hairline(self):
        """Lowest hair height per degree: from the top down, the run of hair on the surface."""
        zb = np.full(360, self.top)
        for d in range(360):
            col, present = self.h[d][::-1], self.r[d][::-1] > 0
            miss, last = 0, None
            for k in range(len(col)):
                if not present[k]:
                    continue
                if col[k]:
                    last, miss = k, 0
                elif last is not None:
                    miss += 1
                    if miss > GAP:
                        break
            if last is not None:
                zb[d] = self.zs[::-1][last]
        return zb


def _zip(ia, da, ib, db):
    """Triangles between two closed rings of vertex ids ia, ib at directions da, db (degrees,
    increasing): advance the ring whose next vertex comes first round the head."""
    na, nb = len(ia), len(ib)
    A, B = list(da) + [da[0] + 360], list(db) + [db[0] + 360]
    F, i, j = [], 0, 0
    while i < na or j < nb:
        if j == nb or (i < na and A[i + 1] <= B[j + 1]):
            F.append([ia[i % na], ia[(i + 1) % na], ib[j % nb]])
            i += 1
        else:
            F.append([ia[i % na], ib[(j + 1) % nb], ib[j % nb]])
            j += 1
    return F


def hair_shell(head_front):
    s = Surface(head_front)
    zb = s.hairline()
    arc = np.radians(np.arange(361)) * ARC_R
    pts = np.stack([arc, np.r_[zb, zb[0]]], 1)
    keep = [k for k in _dp(pts, DP_EPS) if k < 360]
    n = len(keep)
    # rings from the crown down: A near the top, B above the whole hairline, C halfway from B
    # to the hairline in each direction (above its notches), so the back rounds like the drawing
    z_b = min(zb.max() + MID_ABOVE, s.top - 0.04)
    z_a = (s.top + z_b) / 2 + 0.01
    deg_a = np.arange(RING_A) * 360 / RING_A
    deg_b = np.arange(MID_N) * 360 / MID_N
    deg_c = np.arange(RING_C) * 360 / RING_C
    upper = np.array([zb[(np.arange(d - 15, d + 16) % 360).astype(int)].max() for d in deg_c])
    z_c = upper + (z_b - upper) * RING_C_AT
    top = np.array([s.cx, s.cy, s.top])
    V = [top]
    ia = [len(V) + k for k in range(RING_A)]; V += [s.point(d, z_a) for d in deg_a]
    ib = [len(V) + k for k in range(MID_N)]; V += [s.point(d, z_b) for d in deg_b]
    ic = [len(V) + k for k in range(RING_C)]; V += [s.point(d, z) for d, z in zip(deg_c, z_c)]
    ih = [len(V) + k for k in range(n)]; V += [s.point(d, zb[d]) for d in keep]
    V.append(top - [0, 0, INNER_DEPTH])
    it = len(V) - 1
    V = np.array(V)
    F = [[0, ia[(k + 1) % RING_A], ia[k]] for k in range(RING_A)]
    F += _zip(ia, deg_a, ib, deg_b) + _zip(ib, deg_b, ic, deg_c) + _zip(ic, deg_c, ih, keep)
    for k in range(n):                   # closed underneath: the hairline fanned to a point inside
        F.append([it, ih[k], ih[(k + 1) % n]])
    c = np.array([s.cx, s.cy, (s.top + zb.min()) / 2])
    out = []
    for f in F:
        a, b, d = V[f[0]], V[f[1]], V[f[2]]
        if it not in f and np.cross(b - a, d - a) @ (V[f].mean(0) - c) < 0:
            f = f[::-1]
        out.append(f)
    print(f'  hair: {n} hairline corners, {sum(len(f) - 2 for f in out)} tris')
    return V, out


def hair_parts(head_front):
    V, F = hair_shell(head_front)
    return {'hair': {'bone': 'head', 'tone': 'hair', 'v': xf.head_xform(V).round(4).tolist(), 'f': F}}
