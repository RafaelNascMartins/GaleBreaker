"""Fuse the visual hull of all turnaround views with Depth Anything 3's per-view relief.

The hull (silhouettes from every view, orthographic cameras round z) is the largest volume
that fits the drawings: true scale, but blind to concavities and to which part is in front.
DA3's per-view depth knows the order of the parts (the near arm in front of the torso, the gaps
between plates) but not the scale. So, per view, the DA3 depth is fitted to the hull's near
surface (depth = a + b * da3 + c * row; the row term removes the "photo seen from above" ramp)
and then carves the hull: voxels clearly in front of the fitted surface are removed.

Input: the out_dir of concept_da3.py run with --yaws (normalised canvas views in_*.png and
da3_pred.npz). Writes to out_dir:
    casco_da3_vistas.png   depth heat of the fused volume from each view and 3/4 (red near)
    casco_da3.npz          the voxel grid occ[z, y, x] + axes, and the hull before carving

python art-source/tools/concept_fuse.py <out_dir> --yaws 0 90 180 55 235
"""
import argparse
from pathlib import Path

import cv2
import numpy as np

CANVAS = (720, 960)
FIG_H = 840
GROUND = 900
HEIGHT_M = 1.80
MPP = HEIGHT_M / FIG_H
VOXEL = 0.006


def silhouette(bgr, tol=40):
    fg = (np.abs(bgr.astype(int) - bgr[3, 3].astype(int)).sum(2) > tol).astype(np.uint8)
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    flood = np.pad(fg, 2)
    cv2.floodFill(flood, None, (0, 0), 1)
    return (fg | (1 - flood[2:-2, 2:-2])).astype(bool)


def axes(yaw):
    t = np.radians(yaw)
    return np.array([np.cos(t), np.sin(t), 0.0]), np.array([-np.sin(t), np.cos(t), 0.0])  # right, fwd


def project(p, yaw):
    right, fwd = axes(yaw)
    u = p @ right / MPP + CANVAS[0] / 2
    v = GROUND - p[:, 2] / MPP
    return u, v, p @ fwd           # depth: bigger = further from this camera


def zbuffer(p, yaw, splat=None):
    # each voxel covers voxel/MPP px; splat a bit more so the projection has no holes
    splat = splat or int(np.ceil(VOXEL / MPP)) + 1
    u, v, d = project(p, yaw)
    ui, vi = np.round(u).astype(int), np.round(v).astype(int)
    W, H = CANVAS
    z = np.full((H, W), np.inf)
    for oy in range(-splat // 2, splat - splat // 2):
        for ox in range(-splat // 2, splat - splat // 2):
            uu, vv = (ui + ox).clip(0, W - 1), (vi + oy).clip(0, H - 1)
            np.minimum.at(z, (vv, uu), d)
    return z


def heat(t):
    """0 = near (red) .. 1 = far (blue), BGR."""
    rgb = np.array([[220, 30, 30], [245, 215, 40], [40, 215, 235], [35, 60, 225]], np.float32)
    x = np.clip(t, 0, 1) * 3
    i = np.clip(x.astype(int), 0, 2)
    f = (x - i)[..., None]
    return (rgb[i] * (1 - f) + rgb[i + 1] * f)[..., ::-1]


def render(p, yaw, title, span=0.30):
    z = zbuffer(p, yaw)
    hit = np.isfinite(z)
    img = np.full(z.shape + (3,), 128, np.uint8)
    img[hit] = heat((z[hit] + span) / (2 * span)).astype(np.uint8)
    gy, gx = np.gradient(np.where(hit, z, 0))
    edge = hit & (np.hypot(gx, gy) > 0.012)
    img[edge] = (img[edge] * 0.55).astype(np.uint8)
    cv2.putText(img, title, (16, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (20, 20, 20), 2, cv2.LINE_AA)
    return img[40:920]


def fit_yaw(P, sil, guess, span=30, step=2):
    """Yaw of a view whose angle the image generator only roughly followed: the one where the
    hull of the reliable views (front, profile, back), projected, best matches the drawn
    silhouette (IoU). That hull is larger than the figure, so the score peaks a little low,
    but at the right angle."""
    best = (-1, guess)
    for yaw in np.arange(guess - span, guess + span + 1e-6, step):
        proj = np.isfinite(zbuffer(P, yaw))
        iou = (proj & sil).sum() / max((proj | sil).sum(), 1)
        best = max(best, (iou, float(yaw)))
    return best[1], best[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out')
    ap.add_argument('--yaws', type=float, nargs='+', required=True)
    ap.add_argument('--voxel', type=float, default=0.006)
    ap.add_argument('--votes', type=int, default=None, help='views a voxel must be inside (default all but one)')
    ap.add_argument('--tol', type=float, default=0.03, help='m in front of the DA3 surface before carving')
    ap.add_argument('--no-carve', action='store_true')
    ap.add_argument('--mesh', default=None, help='write the fused volume as an .obj (marching cubes)')
    ap.add_argument('--fit-yaws', action='store_true', help='refine the yaw of every view after the first three')
    a = ap.parse_args()
    out = Path(a.out)
    pred = np.load(out / 'da3_pred.npz')
    names = list(pred['names'])
    assert len(names) == len(a.yaws)
    views = [cv2.imread(str(out / f'in_{n}.png')) for n in names]
    sils = [silhouette(v) for v in views]

    # voxel centres
    global VOXEL
    s = VOXEL = a.voxel
    xs = np.arange(-0.70, 0.70, s)
    ys = np.arange(-0.70, 0.70, s)
    zs = np.arange(0.0, HEIGHT_M + 0.05, s)
    Z, Y, X = np.meshgrid(zs, ys, xs, indexing='ij')
    P = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1).astype(np.float32)
    W, H = CANVAS
    yaws = list(a.yaws)
    if a.fit_yaws and len(sils) > 3:
        base = np.ones(len(P), bool)
        for sil, yaw in list(zip(sils, yaws))[:3]:
            u, v, _ = project(P, yaw)
            ui, vi = np.round(u).astype(int).clip(0, W - 1), np.round(v).astype(int).clip(0, H - 1)
            base &= sil[vi, ui]
        def inside(i):
            u, v, _ = project(P, yaws[i])
            ui, vi = np.round(u).astype(int).clip(0, W - 1), np.round(v).astype(int).clip(0, H - 1)
            return sils[i][vi, ui]
        for i in range(3, len(sils)):         # first pass against the three reliable views
            yaws[i] = fit_yaw(P[base], sils[i], yaws[i])[0]
        for it in range(2):                   # then each against the hull of all the others
            for i in range(3, len(sils)):
                others = base.copy()
                for j in range(3, len(sils)):
                    if j != i:
                        others &= inside(j)
                yaw, iou = fit_yaw(P[others], sils[i], yaws[i], span=16, step=2)
                yaw, iou = fit_yaw(P[others], sils[i], yaw, span=2, step=0.5)
                print(f'pass {it}', names[i], 'yaw', yaw, 'IoU', round(float(iou), 3))
                yaws[i] = yaw
    a.yaws = yaws
    votes = np.zeros(len(P), np.int8)
    for sil, yaw in zip(sils, a.yaws):
        u, v, _ = project(P, yaw)
        ui, vi = np.round(u).astype(int), np.round(v).astype(int)
        ok = (ui >= 0) & (ui < W) & (vi >= 0) & (vi < H)
        inside = np.zeros(len(P), bool)
        inside[ok] = sil[vi[ok], ui[ok]]
        votes += inside
    need = a.votes if a.votes is not None else len(sils) - 1
    hull = votes >= need
    # the front, profile and back are the reliable views: a voxel must be inside all three
    for sil, yaw in list(zip(sils, a.yaws))[:3]:
        u, v, _ = project(P, yaw)
        ui, vi = np.round(u).astype(int).clip(0, W - 1), np.round(v).astype(int).clip(0, H - 1)
        hull &= sil[vi, ui]
    occ = hull.copy()
    print('hull voxels', int(hull.sum()))

    if not a.no_carve:
        D = pred['depth']
        conf = pred['conf']
        for i, (sil, yaw) in enumerate(zip(sils, a.yaws)):
            da = cv2.resize(D[i], CANVAS, interpolation=cv2.INTER_LINEAR)
            cf = cv2.resize(conf[i], CANVAS, interpolation=cv2.INTER_LINEAR)
            zb = zbuffer(P[occ], yaw)                    # hull near surface from this view
            m = sil & np.isfinite(zb) & (cf > np.percentile(cf[sil], 20))
            m = cv2.erode(m.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
            vv, uu = np.nonzero(m)
            A = np.stack([np.ones(len(vv)), da[m], vv * MPP], 1)
            y = zb[m]
            w = np.ones(len(y))
            for _ in range(6):                               # robust (IRLS) fit
                coef = np.linalg.lstsq(A * w[:, None], y * w, rcond=None)[0]
                r = y - A @ coef
                sc = np.median(np.abs(r)) * 1.5 + 1e-4
                w = 1 / np.maximum(1, np.abs(r) / sc)
            if coef[1] <= 0:
                print(names[i], 'relief upside down, skipped', np.round(coef, 3))
                continue
            fit = coef[0] + coef[1] * da + coef[2] * (np.arange(H)[:, None] * MPP)
            # carve: voxels in front of the fitted surface by more than tol
            u, v, d = project(P, yaw)
            ui, vi = np.round(u).astype(int).clip(0, W - 1), np.round(v).astype(int).clip(0, H - 1)
            ahead = occ & sil[vi, ui] & (d < fit[vi, ui] - a.tol) & (cf[vi, ui] > np.percentile(cf[sil], 20))
            occ &= ~ahead
            print(names[i], 'fit a,b,c', np.round(coef, 3), 'resid', round(float(np.median(np.abs(r))), 4),
                  'carved', int(ahead.sum()))
    print('fused voxels', int(occ.sum()))
    np.savez_compressed(out / 'casco_da3.npz', occ=occ.reshape(Z.shape), hull=hull.reshape(Z.shape),
                        x=xs, y=ys, z=zs)
    if a.mesh:
        from skimage import measure
        vol = occ.reshape(Z.shape).astype(np.float32)
        vol = np.pad(vol, 1)
        verts, faces, _, _ = measure.marching_cubes(vol, 0.5, spacing=(s, s, s))
        verts = verts - s                                   # undo the pad
        xyz = np.stack([verts[:, 2] + xs[0], verts[:, 1] + ys[0], verts[:, 0] + zs[0]], 1)
        with open(a.mesh, 'w') as f:
            f.write('# visual hull, metres, Blender axes (+X her left, -Y front, +Z up)\n')
            f.writelines(f'v {x:.4f} {y:.4f} {z:.4f}\n' for x, y, z in xyz)
            f.writelines(f'f {c + 1} {b + 1} {a_ + 1}\n' for a_, b, c in faces)
        print('mesh', a.mesh, len(xyz), 'verts', len(faces), 'tris')
    print('yaws', [round(y, 1) for y in a.yaws])
    pts_h, pts_f = P[hull], P[occ]
    rows = []
    for pts, label in ((pts_h, 'so casco'), (pts_f, 'casco + DA3')):
        rows.append(np.hstack([render(pts, yaw, f'{label} {int(yaw)}') for yaw in (0, 35, 90, 180, 235)]))
    cv2.imwrite(str(out / 'casco_da3_vistas.png'), np.vstack(rows))


if __name__ == '__main__':
    main()
