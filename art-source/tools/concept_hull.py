"""Visual hull of a turnaround: the volume that fits the front, profile and back silhouettes.

Each view is an orthographic projection, so a voxel belongs to the figure only if it falls inside
the silhouette in every view: front and back give x at each height, the profile gives y. This
gives the real depth at every height (no guessing), which the painted shading alone can't.
Silhouettes are the whole figure against the grey background (dark metal bands included, unlike
the facet tracer, which treats them as outline).

Limits: a silhouette can't see concavities, and where the A-pose arm hangs in front of the body
in the profile, the torso gets the arm's depth too (the profile only shows their union).

Writes to the crops' folder:
    <prefix>_casco_vistas.png  depth heat from the front, 3/4 and profile, centred on the hips
                               (red = towards the viewer, blue = away), with a legend
    <prefix>_casco.npz         the voxel grid (occ[z, y, x]), voxel size and origin

python art-source/tools/concept_hull.py <frente.png> <perfil.png> <costas.png> --mpp M [--axis-front C] ...
Crops: same scale, feet on the bottom row; front/back centred on the body axis, profile with
front (-y) on the left.
"""
import argparse
from pathlib import Path

import cv2
import numpy as np


def silhouette(path, tol=40):
    bgr = cv2.imread(str(path)).astype(int)
    fg = (np.abs(bgr - bgr[3, 3]).sum(2) > tol).astype(np.uint8)
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    # fill holes (gaps inside the outline). Pad with background first: the gap between the
    # legs only reaches the outside through the bottom row, and a corner pixel of the crop may
    # not be background.
    h, w = fg.shape
    flood = np.pad(fg, 2)
    cv2.floodFill(flood, None, (0, 0), 1)
    fg = fg | (1 - flood[2:-2, 2:-2])
    # drop specks
    n, lab, st, _ = cv2.connectedComponentsWithStats(fg)
    keep = np.zeros_like(fg)
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] > 400:
            keep[lab == i] = 1
    return keep.astype(bool)


def carve(front, side, back, mpp, step=2):
    """occ[z, y, x] at `step` px voxels. Front col -> x (character left = image right); back view
    is mirrored; profile col -> y (front = -y, image left)."""
    H = front.shape[0]
    zs = np.arange(0, H, step)                       # image rows, top first
    xs = np.arange(0, front.shape[1], step)
    ys = np.arange(0, side.shape[1], step)
    F = front[np.ix_(zs, xs)]                        # [z, x]
    B = back[np.ix_(zs, (back.shape[1] - 1 - xs).clip(0, back.shape[1] - 1))]
    P = side[np.ix_(zs, ys)]                         # [z, y]
    occ = F[:, None, :] & B[:, None, :] & P[:, :, None]
    x = (xs - front.shape[1] / 2) * mpp
    y = (ys - side.shape[1] / 2) * mpp
    z = (H - zs) * mpp
    return occ, x, y, z


def surface_points(occ, x, y, z):
    pad = np.pad(occ, 1)
    inner = pad[2:, 1:-1, 1:-1] & pad[:-2, 1:-1, 1:-1] & pad[1:-1, 2:, 1:-1] & pad[1:-1, :-2, 1:-1] & \
        pad[1:-1, 1:-1, 2:] & pad[1:-1, 1:-1, :-2]
    k, j, i = np.nonzero(occ & ~inner)
    return np.stack([x[i], y[j], z[k]], 1)


STOPS = np.array([[230, 40, 20], [240, 220, 40], [40, 220, 240], [30, 50, 230]], np.float32)  # BGR red, yellow, cyan, blue


def colour(t):
    t = np.clip(t, 0, 1) * 3
    i = np.clip(t.astype(int), 0, 2)
    f = (t - i)[..., None]
    c = STOPS[i] * (1 - f) + STOPS[i + 1] * f
    return c[..., ::-1]  # STOPS are RGB-ish written as BGR reversed below


def render(pts, yaw_deg, centre, mpp, size=(700, 900), span=0.30, splat=2):
    """Orthographic z-buffer of the surface points from a camera at `yaw_deg` round z
    (0 = front, looking +y; 90 = from the character's left). Depth heat around `centre`."""
    a = np.radians(yaw_deg)
    right = np.array([np.cos(a), np.sin(a), 0.0])
    fwd = np.array([-np.sin(a), np.cos(a), 0.0])        # camera looks along fwd
    p = pts - centre
    u = p @ right
    d = p @ fwd                                         # bigger = further from the camera
    W, H = size
    px = (u / mpp + W / 2).astype(int)
    py = (H - 20 - (pts[:, 2] / mpp)).astype(int)
    ok = (px >= 0) & (px < W) & (py >= 0) & (py < H)
    px, py, d = px[ok], py[ok], d[ok]
    zbuf = np.full((H, W), np.inf)
    order = np.argsort(-d)                              # far first, near overwrites
    for oy in range(splat):
        for ox in range(splat):
            yy, xx = (py[order] + oy).clip(0, H - 1), (px[order] + ox).clip(0, W - 1)
            zbuf[yy, xx] = d[order]
    hit = np.isfinite(zbuf)
    img = np.full((H, W, 3), 128, np.uint8)
    t = (zbuf + span) / (2 * span)                      # -span (near, red) .. +span (far, blue)
    img[hit] = np.clip(_heat(t[hit]), 0, 255).astype(np.uint8)
    # light edge shading so the volume reads: darken where depth jumps
    gy, gx = np.gradient(np.where(hit, zbuf, 0))
    edge = hit & (np.hypot(gx, gy) > mpp * 6)
    img[edge] = (img[edge] * 0.55).astype(np.uint8)
    return img


def _heat(t):
    """t 0 = near (red) .. 1 = far (blue); returns BGR."""
    rgb = np.array([[220, 30, 30], [245, 215, 40], [40, 215, 235], [35, 60, 225]], np.float32)
    x = np.clip(t, 0, 1) * 3
    i = np.clip(x.astype(int), 0, 2)
    f = (x - i)[:, None]
    c = rgb[i] * (1 - f) + rgb[i + 1] * f
    return c[:, ::-1]


def legend(width, span):
    bar = np.full((70, width, 3), 235, np.uint8)
    x0, x1 = 60, width - 60
    t = np.linspace(0, 1, x1 - x0)
    bar[18:38, x0:x1] = _heat(t)[None].astype(np.uint8)
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(bar, f'perto da camera (-{span*100:.0f} cm)', (x0, 58), font, 0.5, (20, 20, 20), 1, cv2.LINE_AA)
    txt = f'longe (+{span*100:.0f} cm)'
    cv2.putText(bar, txt, (x1 - 8 * len(txt), 58), font, 0.5, (20, 20, 20), 1, cv2.LINE_AA)
    cv2.putText(bar, 'centro do quadril', ((x0 + x1) // 2 - 70, 14), font, 0.45, (20, 20, 20), 1, cv2.LINE_AA)
    return bar


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('front')
    ap.add_argument('side')
    ap.add_argument('back')
    ap.add_argument('--mpp', type=float, required=True)
    ap.add_argument('--hips', type=float, default=0.85, help='z of the hips centre for the heat')
    ap.add_argument('--span', type=float, default=0.30, help='metres from the centre to full red/blue')
    ap.add_argument('--step', type=int, default=2)
    a = ap.parse_args()
    f, s, b = silhouette(a.front), silhouette(a.side), silhouette(a.back)
    occ, x, y, z = carve(f, s, b, a.mpp, a.step)
    pts = surface_points(occ, x, y, z)
    centre = np.array([0.0, 0.0, a.hips])
    vm = a.mpp * a.step / 2  # splat size: points are a.step px apart
    views = []
    for yaw, name in ((0, 'frente'), (35, '3/4'), (90, 'perfil (esquerda)'), (180, 'costas')):
        img = render(pts, yaw, centre, a.mpp, span=a.span, splat=a.step + 1)
        cv2.putText(img, name, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (20, 20, 20), 2, cv2.LINE_AA)
        views.append(img)
    sheet = np.hstack(views)
    sheet = np.vstack([sheet, legend(sheet.shape[1], a.span)])
    prefix = Path(a.front).with_name(Path(a.front).stem.rsplit('_', 1)[0])
    cv2.imwrite(str(prefix) + '_casco_vistas.png', sheet)
    np.savez_compressed(str(prefix) + '_casco.npz', occ=occ, x=x, y=y, z=z)
    print('voxels', int(occ.sum()), 'surface', len(pts), '->', str(prefix) + '_casco_vistas.png')


if __name__ == '__main__':
    main()
