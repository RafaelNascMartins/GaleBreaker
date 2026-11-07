"""Measure X12's rigid parts from her visual hull (concept_fuse.py, 5 views).

Each part is a region of the hull with an axis (vertical for the head, torso, skirt and legs;
along the A-pose limb for the arm). The region is sliced across the axis every voxel; each slice
becomes an octagon from its extent in 8 directions (support function at 0, 45, ... 315 degrees):
the 8-sided ring of the Legends style, exact for a convex section. Ring heights are kept where
the section changes (Douglas-Peucker on the 8 extents, TOL metres) and then moved onto the
nearest facet line of the detailed front tracing (x12_frente_facetas.json), so ring edges run
along drawn facet edges. Central parts are made symmetric; left parts are mirrored in Blender.

Writes art-source/characters/tophia/legends/x12_aneis.json:
    {part: {'bone', 'mirror', 'rings': [[[x, y, z] * 8], ...]}}   world metres, Blender axes

python art-source/tools/x12_measure.py
"""
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'art-source/characters/tophia/legends'
TOL = 0.025         # m; below this the voxel noise (6 mm) reads as shape
SNAP = 0.015
TUCK = 0.01          # m each end of a part goes into its neighbour          # m: a ring moves onto a facet line this close
DIRS = np.array([[np.cos(a), np.sin(a)] for a in np.radians(np.arange(0, 360, 45))])

# Parts: name, bone, axis (p0 -> p1, metres), region test on voxel centres (x, y, z),
# mirror (left part, copied to the right in Blender), central (made symmetric).
ARM0, ARM1 = np.array([0.325, 0.0, 1.205]), np.array([0.475, 0.0, 0.925])   # elbow -> wrist
FIST0, FIST1 = np.array([0.475, 0.0, 0.925]), np.array([0.535, 0.0, 0.675])


def _near_axis(p, a, b, r):
    ab = b - a
    t = np.clip(((p - a) @ ab) / (ab @ ab), -0.05, 1.05)
    return np.linalg.norm(p - (a + t[:, None] * ab), axis=1) < r


PARTS = [
    ('head', 'head', (0, 0, 1.465), (0, 0, 1.82), lambda p: p[:, 2] >= 1.465, False, True),
    ('collar', 'chest', (0, 0, 1.38), (0, 0, 1.465), lambda p: (p[:, 2] >= 1.38) & (np.abs(p[:, 0]) < .14), False, True),
    ('chest', 'chest', (0, 0, 1.12), (0, 0, 1.38), lambda p: (np.abs(p[:, 0]) < .155), False, True),
    # the skirt flares (front 0.135 at the waist, 0.29 at the hem): a straight cut would take in the forearm
    ('skirt', 'hips', (0, 0, 0.765), (0, 0, 1.12), lambda p: np.abs(p[:, 0]) < .15 + np.maximum(0, 1.12 - p[:, 2]) * .6, False, True),
    ('pauldron_l', 'upper_arm_l', (0.25, 0, 1.19), (0.25, 0, 1.45),
     lambda p: (p[:, 0] > .135) & (p[:, 0] < .40), True, False),
    ('forearm_l', 'forearm_l', tuple(ARM0 + (ARM0 - ARM1) * .06), tuple(ARM0 + (ARM1 - ARM0) * .80),
     lambda p: (p[:, 0] > .18) & _near_axis(p, ARM0, ARM1, .16), True, False),
    ('wrist_cuff_l', 'forearm_l', tuple(ARM0 + (ARM1 - ARM0) * .78), tuple(ARM1 + (FIST1 - FIST0) * .08),
     lambda p: (p[:, 0] > .18) & _near_axis(p, ARM0, FIST0, .16), True, False),
    ('fist_l', 'hand_l', tuple(FIST0 + (FIST1 - FIST0) * .04), tuple(FIST1),
     lambda p: (p[:, 0] > .33) & _near_axis(p, FIST0, FIST1, .16), True, False),
    ('thigh_l', 'thigh_l', (0.135, 0, 0.60), (0.135, 0, 0.80), lambda p: (p[:, 0] > 0) & (p[:, 0] < .32), True, False),
    ('shin_l', 'shin_l', (0.185, 0, 0.30), (0.185, 0, 0.63), lambda p: (p[:, 0] > 0) & (p[:, 0] < .36), True, False),
    ('ankle_cuff_l', 'shin_l', (0.215, 0, 0.215), (0.215, 0, 0.31), lambda p: (p[:, 0] > 0) & (p[:, 0] < .40), True, False),
    ('boot_l', 'foot_l', (0.24, 0, 0.0), (0.24, 0, 0.235), lambda p: (p[:, 0] > 0) & (p[:, 0] < .45), True, False),
]


def frame(p0, p1):
    z = (p1 - p0) / np.linalg.norm(p1 - p0)
    side = np.array([1.0, 0, 0])
    x = side - z * (side @ z)
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    if y[1] < 0:
        x, y = -x, -y
    return x, y, z


def octagon(sup):
    """Vertices where neighbouring support lines (n_k . p = h_k) meet."""
    out = []
    for k in range(8):
        n1, n2 = DIRS[k], DIRS[(k + 1) % 8]
        out.append(np.linalg.solve(np.array([n1, n2]), np.array([sup[k], sup[(k + 1) % 8]])))
    return np.array(out)


def dp_keep(ts, S, tol):
    keep = {0, len(ts) - 1}

    def rec(i, j):
        if j <= i + 1:
            return
        f = (ts[i + 1:j] - ts[i]) / (ts[j] - ts[i])
        lin = S[i] + f[:, None] * (S[j] - S[i])
        err = np.abs(S[i + 1:j] - lin).max(1)
        k = int(err.argmax())
        if err[k] > tol:
            keep.add(i + 1 + k)
            rec(i, i + 1 + k)
            rec(i + 1 + k, j)
    rec(0, len(ts) - 1)
    return sorted(keep)


def facet_lines(mpp=1.8 / 840):
    """Heights (m) of the near-horizontal facet edges in the detailed front tracing."""
    zs = []
    for f in json.loads((SRC / 'x12_frente_facetas.json').read_text()):
        m = np.array(f['m'])
        for a, b in zip(m, np.roll(m, -1, 0)):
            if abs(b[0] - a[0]) > 0.02 and abs(b[1] - a[1]) < 0.4 * abs(b[0] - a[0]):
                zs.append(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2))
    return np.array(zs)


def main():
    d = np.load(SRC / 'x12_casco.npz')
    occ, xs, ys, zs = d['occ'], d['x'], d['y'], d['z']
    vox = float(xs[1] - xs[0])
    k, j, i = np.nonzero(occ)
    P = np.stack([xs[i], ys[j], zs[k]], 1)
    lines = facet_lines()
    out = {}
    for name, bone, p0, p1, region, mirror, central in PARTS:
        p0, p1 = np.array(p0, float), np.array(p1, float)
        q = P[region(P)]
        fx, fy, fz = frame(p0, p1)
        L = np.linalg.norm(p1 - p0)
        rel = q - p0
        t = rel @ fz
        q = q[(t >= -1e-6) & (t <= L + 1e-6)]
        rel = q - p0
        t, u, v = rel @ fz, rel @ fx, rel @ fy
        ts, S = [], []
        for tc in np.arange(vox / 2, L, vox):
            sel = np.abs(t - tc) <= vox / 2
            if sel.sum() < 6:
                continue
            uv = np.stack([u[sel], v[sel]], 1)
            sup = (uv @ DIRS.T).max(0) + vox / 2
            if central:      # mirror x: direction angle a -> 180 - a, i.e. k -> (4 - k) % 8
                sup = (sup + sup[[(4 - kk) % 8 for kk in range(8)]]) / 2
            ts.append(tc)
            S.append(sup)
        ts, S = np.array(ts), np.array(S)
        # smooth along the axis (median of 5 slices) so single-voxel steps don't make rings
        Sm = S.copy()
        for n in range(len(S)):
            Sm[n] = np.median(S[max(0, n - 2):n + 3], axis=0)
        S = Sm
        idx = dp_keep(ts, S, TOL)
        # snap inner rings to the facet lines crossing this part (vertical parts only)
        rings = []
        for n, ii in enumerate(idx):
            tc = ts[ii]
            if 0 < n < len(idx) - 1 and abs(fz[2]) > 0.99:
                c = p0 + fz * tc
                near = lines[np.abs(lines[:, 0] - c[0]) < 0.25]
                if len(near):
                    dz = near[:, 1] - c[2]
                    m = np.abs(dz).argmin()
                    if abs(dz[m]) < SNAP:
                        tc = tc + dz[m]
                        ii = int(np.abs(ts - tc).argmin())
            oc = octagon(S[ii])
            # end rings reach the slab's outer face plus a tuck into the neighbour, so parts
            # that meet (head/collar/chest/skirt, limb joints) leave no gap
            if n == 0:
                tc = tc - vox / 2 - TUCK
            elif n == len(idx) - 1:
                tc = tc + vox / 2 + TUCK
            c = p0 + fz * tc
            rings.append([(c + fx * a + fy * b).round(4).tolist() for a, b in oc])
        # cap rings at the very ends of the part
        out[name] = {'bone': bone, 'mirror': mirror, 'rings': rings}
        print(f'{name:13s} {len(rings)} rings (of {len(ts)} slices)')
    (SRC / 'x12_aneis.json').write_text(json.dumps(out, indent=0))


if __name__ == '__main__':
    main()
