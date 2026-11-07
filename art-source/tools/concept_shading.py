"""Read the painted light on a traced turnaround view: which facets face the light, which turn
away, and the depth that follows from that.

The concepts are flat-shaded with one key light, so a facet's tone against the brightest tone of
its own material gives the angle between its normal and the light (Lambert with ambient):
    ratio = amb + (1 - amb) * max(0, n . L)
1. Facets (concept_facets.segment) are grouped by material (k-means on their mean a*b* and L*),
   each material's albedo is its brightest facet tone.
2. The light: facets on the silhouette edge have a known normal (the outline's outward normal,
   lying in the image plane), so their ratios fit L in the image plane; L toward the viewer
   follows from |L| = 1.
3. Each facet's normal lies on the cone around L given by its ratio; the one closest to an
   "inflated silhouette" prior (normals bending out toward the outline) is kept.
4. The normals are integrated (Frankot-Chellappa) into a relative depth map, in metres.

Writes next to the crop:
    <crop>_luz.png          facet tone over its material albedo (heat, light arrow)
    <crop>_normais.png      estimated normals (RGB = x right, y up, z toward the viewer)
    <crop>_profundidade.png depth heat (red near the viewer, blue far), same colours as the
                            silhouettes capture
    <crop>_relevo.json      per facet: material, ratio, view-space normal, mean depth (m)

python art-source/tools/concept_shading.py <crop.png> ... --mpp M
"""
import json
from pathlib import Path

import cv2
import numpy as np

from concept_facets import segment, MPP


def facet_table(bgr, markers):
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    ids = [k for k in np.unique(markers) if k > 1]
    rows = []
    for k in ids:
        m = markers == k
        if m.sum() < 20:
            continue
        rows.append((k, lab[m].mean(0), int(m.sum())))
    return rows


def materials(rows, n):
    """k-means on chroma (a*, b*) plus a little lightness, so shades of one paint stay together
    while black hair, grey metal and white bands split off."""
    feats = np.array([[r[1][1], r[1][2], r[1][0] * 0.35] for r in rows], np.float32)
    n = min(n, len(rows))
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
    w = np.array([r[2] for r in rows], np.float32)
    # weight big facets by repeating them a little
    rep = np.repeat(feats, np.clip((w / w.mean()).astype(int), 1, 6), axis=0)
    _, _, centres = cv2.kmeans(rep, n, None, crit, 8, cv2.KMEANS_PP_CENTERS)
    lab = ((feats[:, None, :] - centres[None]) ** 2).sum(2).argmin(1)
    return lab


def inflated_prior(mask, mpp):
    """Normals of the silhouette 'inflated' like a balloon: flat toward the viewer in the
    middle, turning to the image plane at the outline. Image axes: x right, y down."""
    d = cv2.distanceTransform(mask.astype(np.uint8), cv2.DIST_L2, 5)
    h = np.sqrt(np.maximum(d, 0) * 6.0)          # px; a round bulge near the outline
    h = cv2.GaussianBlur(h, (0, 0), 3)
    gy, gx = np.gradient(h)
    n = np.dstack([-gx, gy, np.ones_like(h)])     # view: x right, y up, z toward viewer
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return n


MIDAS = Path(r'C:/Users/Rafael/Tools/midas/model-small.onnx')
_net = None


def midas(bgr, mask):
    """MiDaS v2.1 small through cv2.dnn: relative nearness (bigger = closer), 0 outside the
    figure. The crop is padded to a square on the background colour so it is not stretched."""
    global _net
    if _net is None:
        _net = cv2.dnn.readNet(str(MIDAS))
    h, w = mask.shape
    s = max(h, w)
    sq = np.full((s, s, 3), bgr[3, 3], np.uint8)
    oy, ox = (s - h) // 2, (s - w) // 2
    sq[oy:oy + h, ox:ox + w] = bgr
    blob = cv2.dnn.blobFromImage(sq, 1 / 255.0, (256, 256), (123.675, 116.28, 103.53), swapRB=True)
    blob /= np.array([0.229, 0.224, 0.225], np.float32).reshape(1, 3, 1, 1)
    _net.setInput(blob)
    out = _net.forward()[0]
    if out.ndim == 3:
        out = out[0]
    d = cv2.resize(out, (s, s), interpolation=cv2.INTER_CUBIC)[oy:oy + h, ox:ox + w]
    d = (d - d[mask].min()) / max(np.ptp(d[mask]), 1e-6)
    d[~mask] = 0
    return d.astype(np.float32)


def detrend_rows(d, mask, win=15):
    """Remove the per-row level (MiDaS reads a standing figure as a photo looking down: feet
    near, head far). In an A-pose the body's middle sits at one depth at every height, so the
    row median is set to zero, smoothed over `win` rows to keep real steps between parts."""
    med = np.zeros(d.shape[0])
    for r in range(d.shape[0]):
        v = d[r][mask[r]]
        med[r] = np.median(v) if len(v) else np.nan
    ok = np.isfinite(med)
    med = np.interp(np.arange(len(med)), np.nonzero(ok)[0], med[ok]) if ok.any() else med
    med = np.convolve(np.pad(med, win, mode='edge'), np.ones(2 * win + 1) / (2 * win + 1), 'valid')
    out = d - med[:, None]
    out[~mask] = 0
    return out


def extent_rows(mask, mpp):
    """Width (m) of the silhouette per row: the other view's depth at that height."""
    xs = np.arange(mask.shape[1])
    out = np.full(mask.shape[0], np.nan)
    for r in range(mask.shape[0]):
        c = xs[mask[r]]
        if len(c) > 3:
            out[r] = (c.max() - c.min() + 1) * mpp
    return out


def scale_to(near, mask, target, mpp):
    """One scale for the nearness map so that its range per row matches `target` (the depth
    the other view measures at that height); median of the row ratios, ignores arms/gaps."""
    k = []
    for r in range(mask.shape[0]):
        v = near[r][mask[r]]
        if len(v) > 10 and np.isfinite(target[r]) and np.ptp(v) > 1e-3:
            k.append(target[r] / np.ptp(v))
    return float(np.median(k)) if k else 0.3


def edge_normals(mask):
    """Outward 2D normal (view x right, y up) at silhouette pixels."""
    blur = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 2.0)
    gy, gx = np.gradient(blur)
    edge = mask & (cv2.erode(mask.astype(np.uint8), np.ones((3, 3), np.uint8)) == 0)
    return edge, -gx, gy


def integrate(p, q, mask):
    """Frankot-Chellappa: depth z with dz/dx = p, dz/dy = q (image axes, px units)."""
    h, w = p.shape
    P, Q = (np.pad(a * mask, ((h // 2, h // 2), (w // 2, w // 2))) for a in (p, q))
    H, W = P.shape
    wx = np.fft.fftfreq(W) * 2 * np.pi
    wy = np.fft.fftfreq(H) * 2 * np.pi
    WX, WY = np.meshgrid(wx, wy)
    den = WX ** 2 + WY ** 2
    den[0, 0] = 1
    Z = (-1j * WX * np.fft.fft2(P) - 1j * WY * np.fft.fft2(Q)) / den
    Z[0, 0] = 0
    z = np.real(np.fft.ifft2(Z))[h // 2:h // 2 + h, w // 2:w // 2 + w]
    return z


def heat(values, mask, lo, hi):
    """Blue (low) - cyan - yellow - red (high), grey background."""
    t = np.clip((values - lo) / max(hi - lo, 1e-6), 0, 1)
    stops = np.array([[255, 60, 30], [230, 200, 40], [40, 220, 240], [20, 40, 230]], np.float32)  # BGR blue..red
    x = t * 3
    i = np.clip(x.astype(int), 0, 2)
    f = (x - i)[..., None]
    col = stops[i] * (1 - f) + stops[i + 1] * f
    out = np.full(values.shape + (3,), 128, np.uint8)
    out[mask] = col[mask].astype(np.uint8)
    return out


def shade(crop, mpp=MPP, n_materials=5, edge=None, sr=7, dark_l=85, min_area=30, other=None, light=None, use_midas=False):
    """other: the crop at 90 degrees (profile for the front, front for the profile), whose
    widths give the depth scale. light: force the light direction (view x right, y up, z out)."""
    crop = Path(crop)
    bgr = cv2.imread(str(crop))
    markers, flat = segment(bgr, edge, sr, dark_l, min_area)
    mask = markers > 1
    rows = facet_table(bgr, markers)
    mat = materials(rows, n_materials)
    albedo = {}
    for (k, lab, area), m in zip(rows, mat):
        albedo.setdefault(m, []).append(lab[0])
    albedo = {m: np.percentile(v, 95) for m, v in albedo.items()}
    ratio = {k: min(1.0, lab[0] / max(albedo[m], 1)) for (k, lab, _), m in zip(rows, mat)}
    amb = float(np.percentile(list(ratio.values()), 3))

    # Light in the image plane from the outline facets: ratio = amb + (1-amb)(Lx nx + Ly ny).
    edge_px, ex, ey = edge_normals(mask)
    A, b = [], []
    for k, _, _ in rows:
        sel = edge_px & (markers == k)
        if sel.sum() < 6:
            continue
        nx, ny = ex[sel].mean(), ey[sel].mean()
        ln = np.hypot(nx, ny)
        if ln < 1e-6:
            continue
        A.append([nx / ln, ny / ln])
        b.append((ratio[k] - amb) / (1 - amb))
    lxy = np.linalg.lstsq(np.array(A), np.array(b), rcond=None)[0] if A else np.zeros(2)
    if np.linalg.norm(lxy) > 0.95:
        lxy *= 0.95 / np.linalg.norm(lxy)
    L = np.array([lxy[0], lxy[1], np.sqrt(1 - lxy @ lxy)])

    if light is not None:
        L = np.array(light, float) / np.linalg.norm(light)
    near = None
    # MiDaS (2026-11-06 test on X12): reads the figure as a photo looking down and, once that
    # ramp is removed, is nearly flat on flat-shaded art - kept as an option, off by default.
    if use_midas and MIDAS.exists():
        near = detrend_rows(midas(bgr, mask), mask)
        near = (near - near[mask].min()) / max(np.ptp(near[mask]), 1e-6)
        near[~mask] = 0
        target = None
        if other:
            om = segment(cv2.imread(str(other)), edge, sr, dark_l, min_area)[0] > 1
            t = extent_rows(om, mpp)
            target = np.interp(np.arange(mask.shape[0]), np.arange(len(t)), t) if len(t) != mask.shape[0] else t
        k = scale_to(near, mask, target, mpp) if target is not None else 0.3
        zm = near * k / mpp                     # px toward the viewer
        zm = cv2.GaussianBlur(zm, (0, 0), 2)
        gy, gx = np.gradient(zm)
        prior = np.dstack([-gx, gy, np.ones_like(zm)])
        prior /= np.linalg.norm(prior, axis=2, keepdims=True)
        bl = inflated_prior(mask, mpp)
        prior[~mask] = bl[~mask]
    else:
        prior = inflated_prior(mask, mpp)
    normal = np.zeros(bgr.shape[:2] + (3,), np.float32)
    out = []
    for (k, lab, area), m in zip(rows, mat):
        sel = markers == k
        n0 = prior[sel].mean(0)
        n0 /= np.linalg.norm(n0)
        c = np.clip((ratio[k] - amb) / (1 - amb), 0, 1)
        if c <= 0.02:
            # in shadow: keep the prior, turned away from the light until n.L <= 0
            n = n0 - max(0.0, n0 @ L) * L
        else:
            u = n0 - (n0 @ L) * L
            u = u / np.linalg.norm(u) if np.linalg.norm(u) > 1e-6 else np.array([0, 0, 1.0])
            n = c * L + np.sqrt(1 - c * c) * u
        if n[2] < 0.05:       # a visible facet faces the viewer
            n[2] = 0.05
        n /= np.linalg.norm(n)
        normal[sel] = n
        ys, xs = np.nonzero(sel)
        out.append({'id': int(k), 'material': int(m), 'ratio': round(float(ratio[k]), 3),
                    'normal': [round(float(v), 3) for v in n],
                    'centre_px': [round(float(xs.mean()), 1), round(float(ys.mean()), 1)], 'area_px': area})

    nz = np.maximum(normal[..., 2], 0.05)
    p = -normal[..., 0] / nz          # dz/dx (x right)
    q = normal[..., 1] / nz           # dz/dy_image (image y is down, view y up)
    z = detrend_rows(integrate(p, q, mask) * mpp, mask)   # metres toward the viewer
    for f in out:
        f['depth_m'] = round(float(z[markers == f['id']].mean()), 4)

    # Overlays (2x, NEAREST, like the facet overlay).
    rimg = np.zeros(bgr.shape[:2], np.float32)
    for k, r in ratio.items():
        rimg[markers == k] = r
    luz = heat(rimg, mask, amb, 1.0)
    c0 = np.array([40, 40])
    cv2.arrowedLine(luz, tuple(int(v) for v in c0), tuple(int(v) for v in c0 + np.array([L[0], -L[1]]) * 30), (255, 255, 255), 2, tipLength=0.3)
    nimg = np.full(bgr.shape, 128, np.uint8)
    nimg[mask] = ((normal[mask][:, [2, 1, 0]] * 0.5 + 0.5) * 255).astype(np.uint8)   # BGR <- (z, y, x)
    lo, hi = np.percentile(z[mask], [2, 98])
    prof = heat(z, mask, lo, hi)
    lines = (markers == -1)
    views = [(luz, 'luz'), (nimg, 'normais'), (prof, 'profundidade')]
    if near is not None:
        views.append((heat(near, mask, 0, 1), 'midas'))
    for img, name in views:
        img = img.copy()
        img[lines] = (40, 40, 40)
        big = cv2.resize(img, (img.shape[1] * 2, img.shape[0] * 2), interpolation=cv2.INTER_NEAREST)
        cv2.imwrite(str(crop.with_name(crop.stem + f'_{name}.png')), big)
    crop.with_name(crop.stem + '_relevo.json').write_text(json.dumps(
        {'light': [round(float(v), 3) for v in L], 'ambient': round(amb, 3), 'mpp': mpp,
         'depth_range_m': [round(float(lo), 3), round(float(hi), 3)], 'facets': out}))
    return L, amb, (lo, hi)


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('crops', nargs='+')
    ap.add_argument('--mpp', type=float, default=MPP)
    ap.add_argument('--materials', type=int, default=5)
    ap.add_argument('--edge', type=float, default=None)
    ap.add_argument('--sr', type=int, default=7)
    ap.add_argument('--dark', type=int, default=85)
    ap.add_argument('--other', nargs='*', default=None, help='the 90-degree crop for each crop (depth scale)')
    ap.add_argument('--midas', action='store_true', help='use the MiDaS depth as the shape prior')
    ap.add_argument('--light', type=float, nargs=3, default=None, help='force light x y z (view space)')
    a = ap.parse_args()
    for i, c in enumerate(a.crops):
        o = a.other[i] if a.other and i < len(a.other) else None
        L, amb, rng = shade(c, a.mpp, a.materials, a.edge, a.sr, a.dark, other=o, light=a.light, use_midas=a.midas)
        print(c, 'light', np.round(L, 2), 'ambient', round(amb, 2), 'depth', np.round(rng, 3))
