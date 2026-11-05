"""Dale's Legends page (256, 15 colours) projected from the turnaround, and his face atlas.

Same method as legends_texture.py (Babuin): each triangle takes the view it faces most, with a
depth test. The profile's arm hides the torso, belt, hips and thighs, so those parts only use
the front and back views. The face square is plain skin on the page; the expressions come from
the atlas through FaceUV.

Input: dale_uv_tris.json (legends_dale.dump_triangles). python art-source/tools/dale_texture.py
"""
import json

import cv2
import numpy as np
from PIL import Image

import legends_texture as lt

SRC = lt.ROOT / 'art-source/characters/ignis/legends'
lt.MPP = 2.05 / 933
lt.TOP_Z = 1002 * lt.MPP
HIDDEN_SIDE = {'chest', 'belt', 'buckle', 'pelvis', 'thigh_l', 'thigh_r', 'neck'}
EXPRESSIONS = lt.ROOT / 'concept-art/characters/dale/dale-expressoes-24-psx-v1.png'


PANELS_FILE = lt.ROOT / 'concept-art/characters/dale/dale-texturas-20-paineis-psx-v1.png'
# Panel rectangles, row by row (the gutters are too faint to detect reliably).
PANEL_ROWS = [(12, 302, [(12, 315), (330, 633), (647, 842), (856, 1118), (1132, 1390)]),
              (318, 585, [(12, 315), (330, 582), (597, 855), (870, 1128), (1143, 1390)]),
              (600, 823, [(12, 288), (302, 562), (577, 842), (858, 1127), (1141, 1390)]),
              (840, 1106, [(12, 327), (342, 560), (575, 838), (854, 1112), (1127, 1390)])]
PANEL_NAMES = ['chest_front', 'chest_back', 'torso_side', 'upper_arm', 'forearm',
               'hands', 'fist', 'jeans_front', 'jeans_back', 'jeans_side',
               'jeans_hem', 'belt', 'buckle', 'hat_crown', 'hat_brim',
               'boot', 'sole', 'head_side', 'head_back', 'neck']
PANEL_BG = np.array([58, 40, 32])


def load_panels():
    """Each panel cropped to its painted shape: the dark brown backdrop and the number label
    are filled from the nearest painted pixel, so a mapped face never shows them."""
    sheet = lt.load_view_path(PANELS_FILE)
    out, names = {}, iter(PANEL_NAMES)
    for y0, y1, cols in PANEL_ROWS:
        for x0, x1 in cols:
            p = sheet[y0 + 4:y1 - 4, x0 + 4:x1 - 4].copy()
            paint = (np.abs(p.astype(int) - PANEL_BG).sum(2) > 90) & (p.max(2) > 110)
            paint[:36, :40] = False                                  # the number label
            paint = cv2.morphologyEx(paint.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)).astype(bool)
            ys, xs = np.nonzero(paint)
            p, paint = p[ys.min():ys.max() + 1, xs.min():xs.max() + 1], paint[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
            _, labels = cv2.distanceTransformWithLabels((~paint).astype(np.uint8), cv2.DIST_L2, 5,
                                                        labelType=cv2.DIST_LABEL_PIXEL)
            src = np.zeros((labels.max() + 1, 3), np.uint8)
            src[labels[paint]] = p[paint]
            out[next(names)] = cv2.pyrMeanShiftFiltering(cv2.cvtColor(src[labels], cv2.COLOR_RGB2BGR), 4, 12)[..., ::-1].copy()
    # The belt's leather is as dark as the panel backdrop, so paint the strip from its colours:
    # brown leather with a darker edge and three denim loops per repeat.
    belt = np.zeros((16, 96, 3), np.uint8)
    belt[:] = (124, 67, 39)
    belt[:2] = belt[-2:] = (92, 48, 28)
    for x in (10, 42, 74):
        belt[:, x:x + 8] = (68, 89, 130)
    out['belt'] = belt
    return out


def _axis(points):
    c = points.mean(0)
    _, _, vt = np.linalg.svd(points - c)
    a = vt[0] if vt[0][2] < 0 else -vt[0]              # pointing down the limb
    t = (points - c) @ a
    return c, a, t.min(), t.max()


class PanelMap:
    """Panel and (u, v) in [0, 1] for points of a part, or None to keep the projection.
    Limbs wrap their panel around the limb with the front at the centre and the back folded
    onto it (u = 0.5 + 0.5 sin angle), so no seam shows anywhere."""

    def __init__(self, tris):
        pts = {}
        for t in tris:
            pts.setdefault(t['part'], []).extend(t['co'])
        self.frame = {k: _axis(np.array(v)) for k, v in pts.items()}

    def wrap(self, part, p):
        c, a, t0, t1 = self.frame[part]
        r = p - c
        t = r @ a
        r = r - np.outer(t, a)
        front = np.array([0, -1, 0]) - a * (-a[1])
        front /= np.linalg.norm(front)
        side = np.cross(a, front)
        ang = np.arctan2(r @ side, r @ front)
        return 0.5 + 0.36 * np.sin(ang), (t - t0) / (t1 - t0)

    def __call__(self, part, p, n):
        x, y, z = p[:, 0], p[:, 1], p[:, 2]
        ax = abs(x) if part.endswith('_r') or part in ('chest', 'pelvis') else x
        front, side_face, up = -n[1], abs(n[0]), n[2]
        base = part.rsplit('_', 1)[0] if part[-2:] in ('_l', '_r') else part
        if base == 'chest':
            if side_face > max(abs(n[1]), 0.55):
                return 'torso_side', (y + .2) / .47 if n[0] < 0 else (.27 - y) / .47, (1.72 - z) / .54
            return ('chest_front' if front > 0 else 'chest_back'), (x * np.sign(front) + .25) / .5, (1.72 - z) / .54
        if base in ('upper_arm', 'forearm'):
            return (base,) + self.wrap(part, p)
        if base == 'hand':
            u, v = self.wrap(part, p)
            return ('fist' if front > .3 else 'hands'), (u * .5 if front <= .3 else u), v
        if base in ('pelvis', 'thigh', 'shin'):
            cx = 0.11 + (1.0 - np.clip(z, .2, 1.0)) * 0.15        # the legs splay out
            lx = np.abs(x) - cx
            v = (1.12 - z) / .92
            if side_face > abs(n[1]) and base != 'pelvis':
                return 'jeans_side', (y + .15) / .38, v
            if front > 0:
                if base == 'pelvis':                             # both pockets and the fly
                    return 'jeans_front', (x + .215) / .43, v
                return 'jeans_front', .5 + lx / .3, v
            return 'jeans_back', .5 - lx / .3, v
        if base == 'belt':
            ang = np.arctan2(x, -(y - .02))
            return 'belt', (ang / np.pi) % 1.0, (1.195 - z) / .08
        if base == 'buckle':
            return 'buckle', (x + .07) / .14, (1.19 - z) / .065
        if base == 'hat':
            if np.hypot(x, y - .045).max() < .14 and z.min() > 1.96:
                ang = np.arctan2(x, -(y - .045))
                return 'hat_crown', 0.5 + 0.5 * np.sin(ang), (2.145 - z) / .17
            u = (x + .29) / .58
            vv = (y + .23) / .54
            return 'hat_brim', u, (vv * .5 if up > 0 else .5 + vv * .5)
        if base == 'foot':
            if up < -.5:
                return 'sole', (ax - .105) / .295, (y + .245) / .465
            if side_face > abs(n[1]):
                return 'boot', .5 + .5 * (y + .245) / .465, (.25 - z) / .25
            return 'boot', .5 * (ax - .105) / .295, (.25 - z) / .25
        return None


def paint(tris):
    raw = {n: lt.load_view_path(SRC / f'dale_{n}.png') for n in ('frente', 'costas', 'perfil')}
    zb = lt.zbuffers(tris, raw)
    panels = load_panels()
    flat, centres = lt.palette(raw, list(panels.values()))
    images = {n: lt.snap(flat[n], centres) for n in flat}
    panels = {k: lt.snap(v, centres) for k, v in panels.items()}
    pmap = PanelMap(tris)
    invalid = {n: lt.masks(raw[n]) for n in raw}
    W = lt.WORK
    fx, fy = lt.to_px(images['frente'], 0.085, 1.80)          # cheek, beside the nose
    skin = images['frente'][int(fy), int(fx)]
    page = np.zeros((W, W, 3), np.float32)
    filled = np.zeros((W, W), bool)
    for t in tris:
        co, n = np.array(t['co']), np.array(t['n'])
        uv = np.array(t['uv']) * [W, -W] + [0, W]
        r = lt.raster(uv, (W, W))
        if r is None:
            continue
        xs, ys, bary = r
        if t['face']:
            page[ys, xs] = skin
            filled[ys, xs] = True
            continue
        pts = bary @ co
        hit = pmap(t['part'], pts, n)
        if hit is not None:
            name, u, v = hit
            img = panels[name]
            u = np.broadcast_to(np.clip(u, 0, 1), (len(xs),))
            v = np.broadcast_to(np.clip(v, 0, 1), (len(xs),))
            page[ys, xs] = img[(v * (img.shape[0] - 1)).astype(int), (u * (img.shape[1] - 1)).astype(int)]
            filled[ys, xs] = True
            continue
        score ={'front': -n[1], 'back': n[1], 'left': n[0], 'right': -n[0]}
        if t['part'] in HIDDEN_SIDE:
            score['left'] = score['right'] = -9
        colour = np.zeros((len(xs), 3), np.float32)
        done = np.zeros(len(xs), bool)
        for v in sorted(score, key=score.get, reverse=True):
            if score[v] < -0.5:
                break
            img_name, hor, dep = lt.VIEWS[v]
            img = images[img_name]
            px, py = lt.to_px(img, hor(pts), pts[:, 2])
            ix, iy = np.clip(px.astype(int), 0, img.shape[1] - 1), np.clip(py.astype(int), 0, img.shape[0] - 1)
            visible = dep(pts) <= zb[v][iy, ix] + 0.03
            take = visible & ~invalid[img_name][iy, ix] & ~done
            if t['part'] in HIDDEN_SIDE:
                take = ~invalid[img_name][iy, ix] & ~done
            colour[take] = img[iy[take], ix[take]]
            done |= take
            if done.all():
                break
        page[ys[done], xs[done]] = colour[done]
        filled[ys[done], xs[done]] = True
    page8 = page.clip(0, 255).astype(np.uint8)
    _, labels = cv2.distanceTransformWithLabels((~filled).astype(np.uint8), cv2.DIST_L2, 5,
                                                labelType=cv2.DIST_LABEL_PIXEL)
    src = np.zeros((labels.max() + 1, 3), np.uint8)
    src[labels[filled]] = page8[filled]
    return lt.snap(src[labels], centres), centres


# Looking left / right (cells 17, 18): the drawn pupils barely move, so shift them in the cell.
LOOK_SHIFT = {16: -3, 17: 3}


def face_atlas():
    sheet = lt.load_view_path(EXPRESSIONS)
    cols, rows = lt.FACE_GRID
    C = lt.FACE_CELL
    cw, ch = sheet.shape[1] // cols, sheet.shape[0] // rows
    cells = []
    for r in range(rows):
        for c in range(cols):
            cell = sheet[r * ch + 5:(r + 1) * ch - 5, c * cw + 5:(c + 1) * cw - 5]
            cells.append(cv2.resize(cell, (C, C), interpolation=cv2.INTER_AREA))
    allpx = np.concatenate([c.reshape(-1, 3) for c in cells]).astype(np.float32)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.2)
    _, _, centres = cv2.kmeans(allpx, lt.COLOURS, None, crit, 4, cv2.KMEANS_PP_CENTERS)
    out = np.zeros((rows * C, cols * C, 4), np.uint8)
    for i, cell in enumerate(cells):
        q = lt.snap(cell, centres)
        values, counts = np.unique(q.reshape(-1, 3), axis=0, return_counts=True)
        # Skin: the most common sunburned red (the beard is often the most common colour, and
        # must stay opaque - the page under the face square is plain skin).
        reds = [(c, v) for v, c in zip(values, counts) if v[0] > 150 and int(v[0]) - int(v[1]) > 60]
        skin = max(reds, key=lambda t: t[0])[1] if reds else values[counts.argmax()]
        if False and i in LOOK_SHIFT:
            # Pupils: the darkest pixels in the eye band (upper half), moved sideways over white.
            band = q[: C // 2]
            dark = band.sum(-1) < 120
            white = band.sum(-1) > 600
            ys, xs = np.nonzero(dark & (cv2.dilate(white.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0))
            colour = band[ys, xs].copy()
            near_white = band[white][0] if white.any() else skin
            band[ys, xs] = near_white
            band[ys, np.clip(xs + LOOK_SHIFT[i], 0, C - 1)] = colour
        # Fully opaque: the cells cover the whole face square, so the (hand-painted) page under it
        # never shows; Babuin's atlas cuts the skin out because his page is plain skin there.
        alpha = np.full(q.shape[:2], 255, np.uint8)
        r, c = divmod(i, cols)
        out[r * C:(r + 1) * C, c * C:(c + 1) * C] = np.dstack([q, alpha])
    Image.fromarray(out, 'RGBA').save(SRC / 'dale_rosto_atlas.png')
    return out.shape


if __name__ == '__main__':
    import sys
    if '--face' in sys.argv:          # only the expression atlas (never touches the pages)
        print('face', face_atlas())
        raise SystemExit
    tris = json.loads((SRC / 'dale_uv_tris.json').read_text())
    page, centres = paint(tris)
    # Never over the hand-painted page (dale_pagina_256.png, Texture Paint in Blender): the
    # generator only writes *_gerada.png; copy it over by hand when starting a page anew.
    Image.fromarray(page).save(SRC / 'dale_pagina_1024_gerada.png')
    lt.quantise(page, centres).convert('RGB').save(SRC / 'dale_pagina_256_gerada.png')
    print('page ok', face_atlas())
