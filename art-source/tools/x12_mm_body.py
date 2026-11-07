"""X12's body parts on Mega Man's topology (the source of truth for Legends models).

Mega Man (concept-art/referencias/Megaman.obj) is 18 rigid pieces, ~350 triangles below the
head, each a simple symmetric shape with few cuts. Every X12 part takes the matching piece:

    chest <- torso          pauldron <- shoulder     forearm <- forearm    fist <- hand
    skirt <- hips           thigh <- thigh           shin <- shin          boot <- foot

and each of its vertices is moved onto the surface of X12's part (the stones of x12_sculpt,
which match the drawings): along the part's main axis to the same fraction of its length, and
out from the axis in the same direction to the X12 surface, at the same share of Mega Man's
own radius there. Bands with no Mega Man piece (collar, wrist and ankle cuffs) are 8-sided
prisms fitted the same way. Left parts are built and mirrored; central parts are symmetric.
"""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

import x12_face as xf
import x12_lift as xl

# X12 part (left or central) -> Mega Man piece (connected component of Megaman.obj, x > 0 side)
PIECES = {'chest': 1, 'skirt': 11, 'pauldron_l': 8, 'forearm_l': 9, 'fist_l': 10,
          'thigh_l': 15, 'shin_l': 16, 'boot_l': 17}
BANDS = {'collar': 3, 'wrist_cuff_l': 2, 'ankle_cuff_l': 2}     # prism levels
SIDES = 8
AXIS = {'boot_l': 'y', 'forearm_l': 'pca', 'fist_l': 'pca', 'wrist_cuff_l': 'pca'}   # else down


def mm_pieces():
    P, faces = xf.load_obj('Megaman')
    r, c = [], []
    for f, _ in faces:
        for a, b in zip(f, f[1:] + f[:1]):
            r.append(a)
            c.append(b)
    _, lab = connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(len(P), len(P))), directed=False)
    out = {}
    for f, _ in faces:
        out.setdefault(int(lab[f[0]]), []).append(f)
    return P, out


def prism(levels, n=SIDES):
    """A template band: n-sided prism with `levels` rings, capped (unit radius, z 0..1)."""
    a = np.arange(n) * 2 * np.pi / n + np.pi / n
    V = [[np.cos(t), np.sin(t), k / (levels - 1)] for k in range(levels) for t in a]
    F = []
    for k in range(levels - 1):
        for i in range(n):
            j = (i + 1) % n
            F.append([k * n + i, k * n + j, (k + 1) * n + j, (k + 1) * n + i])
    F.append(list(range(n))[::-1])
    F.append(list(range((levels - 1) * n, levels * n)))
    return np.array(V, float), F


def frame(V, axis='pca'):
    """Main axis (down for the trunk and legs, forward for a foot, PCA along an arm) and two
    cross axes (forward and side)."""
    c = V.mean(0)
    if axis == 'z':
        u = np.array([0, 0, -1.0])
    elif axis == 'y':
        u = np.array([0, -1.0, 0])
    else:
        u = np.linalg.svd(V - c)[2][0]
    if abs(u[2]) > 0.5:
        u = u if u[2] < 0 else -u            # down
    elif abs(u[1]) > abs(u[0]):
        u = u if u[1] < 0 else -u            # forward (foot)
    else:
        u = u if u[0] > 0 else -u            # out to her left
    fwd = np.array([0, -1.0, 0]) if abs(u[1]) < 0.8 else np.array([0, 0, 1.0])
    v = fwd - u * (fwd @ u)
    v /= np.linalg.norm(v)
    return c, u, v, np.cross(u, v)


def tris(V, F):
    return np.array([V[[f[0], f[k], f[k + 1]]] for f in F for k in range(1, len(f) - 1)])


def cast(T, o, d):
    """Farthest hit of the ray o + s d (s > 0) on triangles T (n, 3, 3), or None."""
    e1, e2 = T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]
    p = np.cross(d, e2)
    det = (e1 * p).sum(1)
    ok = np.abs(det) > 1e-12
    inv = np.where(ok, 1 / np.where(ok, det, 1), 0)
    s = o - T[:, 0]
    u = (s * p).sum(1) * inv
    q = np.cross(s, e1)
    v = (q * d).sum(1) * inv
    t = (q * e2).sum(1) * inv
    hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0)
    return float(t[hit].max()) if hit.any() else None


def radius(T, Vt, c, u, v, w, t, ang):
    """Distance from the axis point at t to the surface in direction ang (cross-section)."""
    o = c + u * t
    d = v * np.cos(ang) + w * np.sin(ang)
    r = cast(T, o, d)
    if r is None:                            # the axis left the part: the outermost vertex near t
        near = Vt[np.abs((Vt - c) @ u - t) < 0.03]
        r = float(((near - o) @ d).max()) if len(near) else 0.0
    return max(r, 0.0)


def fit(Vs, Fs, Vt, Ft, axis='pca'):
    """Template mesh (Vs, Fs) moved onto the target surface (Vt, Ft)."""
    Ts, Tt = tris(Vs, Fs), tris(Vt, Ft)
    cs, us, vs, ws = frame(Vs, axis)
    ct, ut, vt, wt = frame(Vt, axis)
    ps, pt = (Vs - cs) @ us, (Vt - ct) @ ut
    out = []
    for p in Vs:
        q = p - cs
        f = (q @ us - ps.min()) / max(np.ptp(ps), 1e-9)
        ang = np.arctan2(q @ ws, q @ vs)
        rs = np.hypot(q @ vs, q @ ws)
        Rs = radius(Ts, Vs, cs, us, vs, ws, q @ us, ang)
        k = min(rs / Rs, 1.0) if Rs > 1e-6 else 0.0
        t = pt.min() + f * np.ptp(pt)
        Rt = radius(Tt, Vt, ct, ut, vt, wt, t, ang)
        out.append(ct + ut * t + (vt * np.cos(ang) + wt * np.sin(ang)) * Rt * k)
    return np.array(out)


def target(out, name):
    """X12's stones of a part (all its convex pieces) as one vertex/face soup."""
    V, F = [], []
    for k, p in out.items():
        if k == name or k.startswith(name + '.'):
            off = len(V)
            V += p['v']
            F += [[i + off for i in f] for f in p['f']]
    return (np.array(V), F) if V else (None, None)


def mirror(V, F):
    return V * [-1, 1, 1], [f[::-1] for f in F]


def body_parts(out):
    """New parts replacing X12's stone parts in `out` (the x12_sculpt dict)."""
    P, pieces = mm_pieces()
    new = {}
    jobs = [(n, 'mm', i) for n, i in PIECES.items()] + [(n, 'band', l) for n, l in BANDS.items()]
    for name, kind, arg in jobs:
        Vt, Ft = target(out, name)
        if Vt is None:
            print('  no target', name)
            continue
        if kind == 'mm':
            Fm = pieces[arg]
            ids = sorted({v for f in Fm for v in f})
            remap = {v: i for i, v in enumerate(ids)}
            Vs, Fs = P[ids], [[remap[v] for v in f] for f in Fm]
        else:
            Vs, Fs = prism(arg)
            Vs = Vs * [0.1, 0.1, -0.1]                # down its axis like the targets
            Fs = [f[::-1] for f in Fs]
        V = fit(Vs, Fs, Vt, Ft, AXIS.get(name, 'z'))
        first = next(p for k, p in out.items() if k == name or k.startswith(name + '.'))
        base = name[:-2] if name.endswith('_l') else name
        part = {'bone': first['bone'], 'tone': first.get('tone', 'stone'), 'v': V.round(4).tolist(), 'f': Fs}
        new[name] = part
        if name.endswith('_l'):
            Vm, Fm2 = mirror(V, Fs)
            new[base + '_r'] = dict(part, bone=part['bone'][:-2] + '_r' if part['bone'].endswith('_l') else part['bone'],
                                    v=Vm.round(4).tolist(), f=Fm2)
        print(f'  {name}: {sum(len(f) - 2 for f in Fs)} tris')
    return new


FIT_SKIP = ('collar',)  # bands already sized by their stones


def fit_outline(model, labels, names, sil_f, prows):
    """Width and depth of every part from the drawings, keeping Mega Man's shape: the whole
    part is scaled and moved in x and y (one affine per part) so its extent is the part's
    front outline (x) and its own region in the profile (y), over the part's heights. Right
    parts are the mirrored left ones afterwards."""
    from x12_lift import MPP, TOP, W
    for name, part in model.items():
        if name.endswith('_r') or name.startswith(('head', 'hair', 'neck')) or name in FIT_SKIP:
            continue
        if name not in names or name not in prows:
            continue
        i = names.index(name) + 1
        front = (labels == i) & sil_f
        if name.endswith('_l'):
            front &= (np.arange(W) + 0.5 - W / 2)[None, :] >= 0
        rows, cols = np.nonzero(front)
        if not len(cols):
            continue
        tx0, tx1 = (cols.min() - W / 2) * MPP, (cols.max() + 1 - W / 2) * MPP
        pr = [prows[name][r] for r in range(rows.min(), rows.max() + 1) if r in prows[name]]
        ty0, ty1 = min(p[0] for p in pr), max(p[1] for p in pr)
        V = np.array(part['v'])
        for ax, (t0, t1) in ((0, (tx0, tx1)), (1, (ty0, ty1))):
            c0, c1 = V[:, ax].min(), V[:, ax].max()
            V[:, ax] = t0 + (V[:, ax] - c0) / max(c1 - c0, 1e-6) * (t1 - t0)
        part['v'] = V.round(4).tolist()
        if name.endswith('_l') and name[:-2] + '_r' in model:
            Vm, _ = mirror(V, part['f'])
            model[name[:-2] + '_r']['v'] = Vm.round(4).tolist()
        print(f'  fit {name}: x {tx1 - tx0:.3f} y {ty1 - ty0:.3f}')
