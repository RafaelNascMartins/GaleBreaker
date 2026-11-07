"""Multi-view depth of a turnaround with Depth Anything 3: one consistent point cloud of the
figure from all its views, with the camera of each view estimated by the model.

The turnaround views are cut apart (one image per figure, grey background kept), fed together
to DA3, and every pixel of the figure (silhouette against the background) is lifted to 3D with
the predicted depth and camera. The cloud is written as a .ply (colours from the concept) for
Blender, plus the raw prediction.

Runs in its own environment (PyTorch + DA3, outside the project):
    C:/Users/Rafael/Tools/da3/venv/Scripts/python.exe art-source/tools/concept_da3.py \
        <out_dir> <sheet.png> [<sheet.png> ...] [--model depth-anything/DA3-BASE]
"""
import argparse
import json
from pathlib import Path

import cv2
import numpy as np


def split_views(sheet, tol=40, gap=15, margin=24):
    """Cut a sheet of figures standing side by side into one image per figure."""
    bgr = cv2.imread(str(sheet))
    bg = bgr[5, 5].astype(int)
    fg = (np.abs(bgr.astype(int) - bg).sum(2) > tol)
    cols = np.nonzero(fg.any(0))[0]
    runs, s, p = [], cols[0], cols[0]
    for x in cols[1:]:
        if x > p + gap:
            runs.append((s, p))
            s = x
        p = x
    runs.append((s, p))
    out = []
    for a, b in runs:
        if b - a < 60:
            continue
        rows = np.nonzero(fg[:, a:b + 1].any(1))[0]
        y0, y1 = max(rows[0] - margin, 0), min(rows[-1] + margin, bgr.shape[0])
        x0, x1 = max(a - margin, 0), min(b + margin, bgr.shape[1])
        out.append(bgr[y0:y1, x0:x1].copy())
    return out


CANVAS = (720, 960)      # w, h of every view fed to DA3 (it crops all views to the smallest)
FIG_H = 840              # px, figure height on the canvas
GROUND = 900             # canvas row of the soles
HEIGHT_M = 1.80          # figure height in metres (top of the hair)


def normalise(view, tol=40):
    """Scale a figure to FIG_H px, sit its soles on GROUND and its body axis on the canvas
    centre. Axis: centre of both shins (rows 70-80 % down the figure), where nothing else sticks
    out in any view."""
    fg = (np.abs(view.astype(int) - view[3, 3].astype(int)).sum(2) > tol)
    rows = np.nonzero(fg.any(1))[0]
    top, bot = rows[0], rows[-1]
    k = FIG_H / (bot - top + 1)
    band = fg[int(top + .70 * (bot - top)):int(top + .80 * (bot - top))]
    cols = np.nonzero(band.any(0))[0]
    axis = (cols[0] + cols[-1]) / 2
    W, H = CANVAS
    M = np.float32([[k, 0, W / 2 - axis * k], [0, k, GROUND - bot * k]])
    return cv2.warpAffine(view, M, (W, H), flags=cv2.INTER_AREA, borderMode=cv2.BORDER_CONSTANT,
                          borderValue=[int(c) for c in view[3, 3]])


def cameras(yaws, dist=20.0):
    """Near-orthographic cameras round the figure (OpenCV w2c and K on the canvas). World is
    Blender's: +X character left, -Y front, +Z up. yaw 0 = front, 90 = from her left side,
    180 = back, 270 = from her right."""
    mpp = HEIGHT_M / FIG_H
    W, H = CANVAS
    f = dist / mpp
    K = np.array([[f, 0, W / 2], [0, f, GROUND - 0.0 / mpp], [0, 0, 1]], np.float64)
    # principal point row at z = 0 (soles); the camera sits at z = 0 too, so rows are heights
    exts, ixts = [], []
    for yaw in yaws:
        t = np.radians(yaw)
        right = np.array([np.cos(t), np.sin(t), 0])
        fwd = np.array([-np.sin(t), np.cos(t), 0])
        down = np.array([0, 0, -1.0])
        R = np.stack([right, down, fwd])             # rows: camera axes in world
        C = -fwd * dist                              # camera centre
        E = np.vstack([np.hstack([R, (-R @ C)[:, None]]), [0, 0, 0, 1]])   # DA3 wants 4x4
        exts.append(E)
        ixts.append(K.copy())
    return np.array(exts, np.float32), np.array(ixts, np.float32)


def silhouette(bgr, tol=40):
    fg = (np.abs(bgr.astype(int) - bgr[3, 3].astype(int)).sum(2) > tol).astype(np.uint8)
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    fg = cv2.erode(fg, np.ones((3, 3), np.uint8))   # drop the anti-aliased rim (mixed depth)
    return fg.astype(bool)


def write_ply(path, pts, rgb):
    with open(path, 'wb') as f:
        f.write((f'ply\nformat binary_little_endian 1.0\nelement vertex {len(pts)}\n'
                 'property float x\nproperty float y\nproperty float z\n'
                 'property uchar red\nproperty uchar green\nproperty uchar blue\nend_header\n').encode())
        rec = np.zeros(len(pts), dtype=[('p', '<f4', 3), ('c', 'u1', 3)])
        rec['p'], rec['c'] = pts, rgb
        f.write(rec.tobytes())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out')
    ap.add_argument('sheets', nargs='+')
    ap.add_argument('--model', default='depth-anything/DA3-BASE')
    ap.add_argument('--res', type=int, default=504)
    ap.add_argument('--yaws', type=float, nargs='*', default=None,
                    help='known camera yaw per view (deg): front 0, her left 90, back 180, her right 270')
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    views = []
    for sheet in a.sheets:
        for i, v in enumerate(split_views(sheet)):
            name = f'{Path(sheet).stem}_{i}'
            views.append((name, normalise(v) if a.yaws else v))
    for n, v in views:
        cv2.imwrite(str(out / f'in_{n}.png'), v)
    print('views', [n for n, _ in views])

    import torch
    from depth_anything_3.api import DepthAnything3
    model = DepthAnything3.from_pretrained(a.model).to(torch.device('cuda'))
    rgb_in = [cv2.cvtColor(v, cv2.COLOR_BGR2RGB) for _, v in views]
    with torch.no_grad():
        if a.yaws:
            assert len(a.yaws) == len(views), f'{len(views)} views, {len(a.yaws)} yaws'
            E, K = cameras(a.yaws)
            pred = model.inference(rgb_in, extrinsics=E, intrinsics=K, process_res=a.res)
        else:
            pred = model.inference(rgb_in, process_res=a.res)
    imgs, depth, conf = pred.processed_images, pred.depth, pred.conf
    ext, ixt = pred.extrinsics, pred.intrinsics
    np.savez_compressed(out / 'da3_pred.npz', depth=depth, conf=conf, extrinsics=ext, intrinsics=ixt, images=imgs,
                        names=np.array([n for n, _ in views]))

    all_p, all_c, all_v = [], [], []
    cams = []
    for i, (name, _) in enumerate(views):
        h, w = depth[i].shape
        img = imgs[i]
        mask = silhouette(cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        ys, xs = np.nonzero(mask)
        d = depth[i][ys, xs]
        K = ixt[i]
        cam = np.stack([(xs - K[0, 2]) / K[0, 0] * d, (ys - K[1, 2]) / K[1, 1] * d, d], 1)
        E = ext[i] if ext[i].shape == (4, 4) else np.vstack([ext[i], [0, 0, 0, 1]])   # world -> camera (OpenCV)
        Ei = np.linalg.inv(E)
        world = cam @ Ei[:3, :3].T + Ei[:3, 3]
        all_p.append(world)
        all_c.append(img[ys, xs])
        all_v.append(np.full(len(world), i))
        cams.append({'name': name, 'centre': Ei[:3, 3].round(4).tolist(),
                     'forward': Ei[:3, 2].round(4).tolist(), 'fx': float(K[0, 0]), 'size': [w, h],
                     'depth_median': float(np.median(d)), 'conf_median': float(np.median(conf[i][ys, xs]))})
    pts, col, vid = np.concatenate(all_p), np.concatenate(all_c), np.concatenate(all_v)
    write_ply(out / 'da3_nuvem.ply', pts.astype(np.float32), col.astype(np.uint8))
    np.save(out / 'da3_nuvem_view.npy', vid.astype(np.int8))
    (out / 'da3_cameras.json').write_text(json.dumps(cams, indent=1))
    for c in cams:
        print(c['name'], 'cam', c['centre'], 'fwd', c['forward'], 'depth', round(c['depth_median'], 3))
    print('points', len(pts))


if __name__ == '__main__':
    main()
