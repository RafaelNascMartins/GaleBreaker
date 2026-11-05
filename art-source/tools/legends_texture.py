"""Paint the Legends-style texture page by projecting the turnaround onto the model.

The model was built to match the front, profile and back views, so each triangle takes its
colours from the view it faces most (front, back, or the profile for both sides), with a depth
test so an arm in front of the torso does not paint the torso. Texels no view can see are
filled from their neighbours. The drawing is first flattened to a 15-colour palette (the PS1
4-bit page), the page is painted at 2x and reduced to 256x256 by nearest pixel.

Parts with a painted panel on babuin-texturas-referencia-psx-v1.png take their colours from
it instead (see Mapper).

Input: babuin_uv_tris.json from legends_babuin.dump_triangles (Blender).
python art-source/tools/legends_texture.py
"""
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'art-source/characters/kaze/legends'
OUT = ROOT / 'godot/assets/characters/kaze/textures'
MPP = 1.9 / 977.0
TOP_Z = 0.95 + 997 * MPP / 2
PAGE, WORK = 256, 512
COLOURS = 15


def load_view(name):
    return load_view_path(SRC / f'babuin_{name}.png')


def masks(img):
    """Background, and the silhouette outline: dark pixels within 5 px of the background.
    Dark lines inside the figure (eyes, brows, creases) are paint and stay."""
    bg = np.abs(img.astype(int) - img[3, 3].astype(int)).sum(2) < 45
    near_bg = cv2.dilate(bg.astype(np.uint8), np.ones((11, 11), np.uint8)).astype(bool)
    outline = near_bg & (img.max(2) < 110)
    return bg | outline


def palette(images, extra=()):
    """15 colours shared by the page: k-means over the flattened drawing (mean shift removes
    the anti-aliasing), like a 4-bit PS1 texture page."""
    flat = {n: cv2.pyrMeanShiftFiltering(cv2.cvtColor(im, cv2.COLOR_RGB2BGR), 4, 12)[..., ::-1].copy() for n, im in images.items()}
    px = np.concatenate([flat[n][~masks(images[n])] for n in flat] + [e.reshape(-1, 3) for e in extra]).astype(np.float32)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.2)
    _, _, centres = cv2.kmeans(px, COLOURS, None, crit, 4, cv2.KMEANS_PP_CENTERS)
    return flat, centres


def snap(rgb, centres):
    d = ((rgb[..., None, :].astype(np.float32) - centres) ** 2).sum(-1)
    return centres[d.argmin(-1)].astype(np.uint8)


PANELS_FILE = ROOT / 'concept-art/characters/babuin/babuin-texturas-referencia-psx-v1.png'
# The reference sheet's panels, row by row (detected on its grey background).
PANEL_NAMES = ['chest_front', 'chest_back', 'skirt_front', 'skirt_back', 'lapel',
               'belt', 'orb', 'sash', 'pants_front', 'pants_back',
               'wrap', 'upper_arm', 'forearm', 'hand_back', 'fist_front',
               'foot_top', 'sole', 'scalp_top', 'head_side', 'neck']


def load_panels():
    im = load_view_path(PANELS_FILE)
    bg = im[2, 2].astype(int)
    mask = (np.abs(im.astype(int) - bg).sum(2) > 30).astype(np.uint8)
    n, _, st, _ = cv2.connectedComponentsWithStats(mask, connectivity=4)
    rects = sorted((tuple(st[i, :4]) for i in range(1, n) if st[i, 4] > 5000), key=lambda r: (round(r[1] / 150), r[0]))
    assert len(rects) == len(PANEL_NAMES), len(rects)
    # Inset 3 px so the panel's own border never bleeds in.
    return im, {k: (x + 3, y + 3, w - 6, h - 6) for k, (x, y, w, h) in zip(PANEL_NAMES, rects)}


def load_view_path(path):
    return cv2.cvtColor(cv2.imread(str(path)), cv2.COLOR_BGR2RGB)


class Mapper:
    """Which panel and where, for points of a part. Faces the turnaround sees poorly (tops,
    soles, sides, insides) and every surface with a painted panel take it from the panel;
    the face, the sides of the head, the ears and the side faces of robe and pants keep the
    projection (the head panel's painted ear would double the modelled one)."""

    def __init__(self, tris):
        self.box = {}
        for t in tris:
            key = self.group(t['part'])
            co = np.array(t['co']) * [self.sign(t['part']), 1, 1]
            lo, hi = self.box.get(key, (co.min(0), co.max(0)))
            self.box[key] = (np.minimum(lo, co.min(0)), np.maximum(hi, co.max(0)))
        for side in 'lr':  # the visible pants run from the robe hem to the cuff
            lo, hi = self.box['pants_' + side]
            self.box['pants_' + side] = (np.array([lo[0], lo[1], 0.403]), np.array([hi[0], hi[1], 0.88]))

    @staticmethod
    def sign(part):
        return -1 if part.endswith('_r') else 1

    @staticmethod
    def group(part):
        base, _, side = part.rpartition('_')
        if side in 'lr' and base:
            return ('pants_' + side) if base in ('thigh', 'shin') else part
        return part

    def planar(self, part, pts, panel, iu, iv, flip=False, v_up=False):
        lo, hi = self.box[self.group(part)]
        u = (pts[:, iu] - lo[iu]) / max(hi[iu] - lo[iu], 1e-6)
        v = (pts[:, iv] - lo[iv]) / max(hi[iv] - lo[iv], 1e-6)
        return panel, (1 - u) if flip else u, v if v_up else 1 - v

    def cyl(self, part, pts, panel):
        lo, hi = self.box[self.group(part)]
        c = (lo + hi) / 2
        ang = np.arctan2(pts[:, 0] - c[0], -(pts[:, 1] - c[1]))
        # Fold the angle (front 0.5, back 0 from both sides): the wrap has no seam.
        return panel, 0.5 - np.abs(ang) / (2 * np.pi), (hi[2] - pts[:, 2]) / max(hi[2] - lo[2], 1e-6)

    def __call__(self, part, pts, n):
        base = part[:-2] if part[-2:] in ('_l', '_r') else part
        pts = pts * [self.sign(part), 1, 1]
        n = n * [self.sign(part), 1, 1]
        front = n[1] <= 0
        side_facing = abs(n[0]) > abs(n[1])
        # Side faces of the robe and pants: the shaded outer strip of the front panel (the
        # profile view mixes in the sash and lapel there).
        if side_facing and base in ('chest', 'skirt', 'thigh', 'shin'):
            panel = {'chest': 'chest_front', 'skirt': 'skirt_front'}.get(base, 'pants_front')
            _, u, v = self.planar(part, pts, panel, 1, 2)
            return panel, 0.12 + 0.18 * u, v
        if base in ('chest', 'skirt'):
            return self.planar(part, pts, f'{base}_front' if front else f'{base}_back', 0, 2, flip=not front)
        if base in ('thigh', 'shin'):
            return self.planar(part, pts, 'pants_front' if front else 'pants_back', 0, 2, flip=not front)
        if base == 'sash':
            return self.planar(part, pts, 'sash', 0, 2)
        if base in ('belt', 'pelvis'):
            return self.cyl(part, pts, 'belt')
        if base == 'orbs':
            r, cx = 0.036, np.sign(pts[:, 0]) * 0.06
            return 'orb', 0.5 + (pts[:, 0] - cx) / (2 * r) * .8, 0.5 - (pts[:, 2] - 1.207) / (2 * r) * .8
        if base == 'wrap':
            return self.cyl(part, pts, 'wrap')
        if base == 'upper_arm':
            return self.cyl(part, pts, 'upper_arm')
        if base in ('forearm', 'calf'):
            return self.cyl(part, pts, 'forearm')
        if base == 'neck':
            return self.cyl(part, pts, 'neck')
        if base == 'hand' and abs(n[1]) >= abs(n[0]):
            return self.planar(part, pts, 'fist_front' if front else 'hand_back', 0, 2, flip=not front)
        if base == 'foot':
            # foot_top panel: instep above, toes in its lower third. The top face takes the
            # instep, the front face of the toes takes the toes, so they are painted once.
            if n[2] > 0.35:
                p, u, v = self.planar(part, pts, 'foot_top', 0, 1)
                return p, u, v * 0.6
            if n[1] < -0.3:
                p, u, v = self.planar(part, pts, 'foot_top', 0, 2)
                return p, u, 0.68 + 0.32 * v
            if n[2] < -0.5:
                return self.planar(part, pts, 'sole', 0, 1)
            # Heel, ankle back and sides: plain shaded skin from the neck panel.
            return self.planar(part, pts, 'neck', 1 if abs(n[0]) > abs(n[1]) else 0, 2)
        if base == 'head':
            if n[2] > 0.55:
                return self.planar(part, pts, 'scalp_top', 0, 1)
            if n[1] < -0.2:   # face and cheeks: plain skin, the expression decal draws the face
                return 'skin', None, None
            if abs(n[0]) > abs(n[1]):
                _, u, v = self.planar(part, pts, 'head_side', 1, 2, flip=n[0] < 0)
                return 'head_side', u * 0.55, v   # the painted ear sits on the panel's right half
        if base == 'ear':
            return 'skin_shade', None, None
        return None


VIEWS = {
    # name: (image, horizontal coordinate from a 3D point, depth (smaller = nearer the viewer))
    'front': ('frente', lambda p: p[..., 0], lambda p: p[..., 1]),
    'back': ('costas', lambda p: -p[..., 0], lambda p: -p[..., 1]),
    'left': ('perfil', lambda p: p[..., 1], lambda p: -p[..., 0]),
    'right': ('perfil', lambda p: p[..., 1], lambda p: p[..., 0]),
}


def to_px(img, h, z):
    return img.shape[1] / 2 + h / MPP, (TOP_Z - z) / MPP


def raster(tri_px, shape):
    """Pixel centres inside a 2D triangle and their barycentrics."""
    (x0, y0), (x1, y1), (x2, y2) = tri_px
    xs = np.arange(max(int(np.floor(min(x0, x1, x2))), 0), min(int(np.ceil(max(x0, x1, x2))) + 1, shape[1]))
    ys = np.arange(max(int(np.floor(min(y0, y1, y2))), 0), min(int(np.ceil(max(y0, y1, y2))) + 1, shape[0]))
    if not len(xs) or not len(ys):
        return None
    gx, gy = np.meshgrid(xs + .5, ys + .5)
    d = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
    if abs(d) < 1e-9:
        return None
    a = ((y1 - y2) * (gx - x2) + (x2 - x1) * (gy - y2)) / d
    b = ((y2 - y0) * (gx - x2) + (x0 - x2) * (gy - y2)) / d
    c = 1 - a - b
    eps = -0.02
    m = (a >= eps) & (b >= eps) & (c >= eps)
    return (gx[m] - .5).astype(int), (gy[m] - .5).astype(int), np.stack([a[m], b[m], c[m]], 1)


def zbuffers(tris, images):
    bufs = {}
    for v, (img_name, hor, dep) in VIEWS.items():
        img = images[img_name]
        zb = np.full(img.shape[:2], np.inf)
        for t in tris:
            co = np.array(t['co'])
            px = [to_px(img, hor(c), c[2]) for c in co]
            r = raster(px, zb.shape)
            if r is None:
                continue
            xs, ys, bary = r
            d = bary @ dep(co)
            np.minimum.at(zb, (ys, xs), d)
        bufs[v] = zb
    return bufs


def paint(tris):
    raw = {n: load_view(n) for n in ('frente', 'costas', 'perfil')}
    zb = zbuffers(tris, raw)
    sheet, rects = load_panels()
    sheet_flat = cv2.pyrMeanShiftFiltering(cv2.cvtColor(sheet, cv2.COLOR_RGB2BGR), 4, 12)[..., ::-1].copy()
    panel_px = [sheet_flat[y:y + h, x:x + w] for x, y, w, h in rects.values()]
    flat, centres = palette(raw, panel_px)
    images = {n: snap(flat[n], centres) for n in flat}
    sheet = snap(sheet_flat, centres)
    invalid = {n: masks(raw[n]) for n in raw}
    mapper = Mapper(tris)
    # Plain skin tones: the most common colour of the neck panel and its darker side.
    nx, ny, nw, nh = rects['neck']
    neck = sheet[ny:ny + nh, nx:nx + nw].reshape(-1, 3)
    tones, counts = np.unique(neck, axis=0, return_counts=True)
    order = counts.argsort()[::-1]
    light, dark = sorted(tones[order[:2]].tolist(), key=sum, reverse=True)
    flat_colour = {'skin': np.array(light), 'skin_shade': np.array(dark)}
    page = np.zeros((WORK, WORK, 3), np.float32)
    filled = np.zeros((WORK, WORK), bool)
    for t in tris:
        co, n = np.array(t['co']), np.array(t['n'])
        uv = np.array(t['uv']) * [WORK, -WORK] + [0, WORK]
        r = raster(uv, (WORK, WORK))
        if r is None:
            continue
        xs, ys, bary = r
        pts = bary @ co
        hit = mapper(t['part'], pts, n)
        if hit is not None and hit[1] is None:
            page[ys, xs] = flat_colour[hit[0]]
            filled[ys, xs] = True
            continue
        if hit is not None:
            name, u, v = hit
            x, y, w, h = rects[name]
            sx = np.clip((x + np.clip(u, 0, 1) * (w - 1)).astype(int), 0, sheet.shape[1] - 1)
            sy = np.clip((y + np.clip(v, 0, 1) * (h - 1)).astype(int), 0, sheet.shape[0] - 1)
            page[ys, xs] = sheet[sy, sx]
            filled[ys, xs] = True
            continue
        score = {'front': -n[1], 'back': n[1], 'left': n[0], 'right': -n[0]}
        colour = np.zeros((len(xs), 3), np.float32)
        done = np.zeros(len(xs), bool)
        for v in sorted(score, key=score.get, reverse=True):
            if score[v] < -0.2:
                break
            img_name, hor, dep = VIEWS[v]
            img = images[img_name]
            px, py = to_px(img, hor(pts), pts[:, 2])
            ix, iy = np.clip(px.astype(int), 0, img.shape[1] - 1), np.clip(py.astype(int), 0, img.shape[0] - 1)
            visible = dep(pts) <= zb[v][iy, ix] + 0.012
            # The drawing's grey background and silhouette outline are not surface colour.
            take = visible & ~invalid[img_name][iy, ix] & ~done
            colour[take] = img[iy[take], ix[take]]
            done |= take
            if done.all():
                break
        page[ys[done], xs[done]] = colour[done]
        filled[ys[done], xs[done]] = True
    # Fill unseen texels and the gutters between islands from their neighbours.
    page8 = page.clip(0, 255).astype(np.uint8)
    # Pad every island outwards with its own edge colour (nearest painted texel), so filtering
    # and mipmaps never pull a neighbouring island's colour across a seam.
    _, labels = cv2.distanceTransformWithLabels((~filled).astype(np.uint8), cv2.DIST_L2, 5,
                                                labelType=cv2.DIST_LABEL_PIXEL)
    src = np.zeros((labels.max() + 1, 3), np.uint8)
    src[labels[filled]] = page8[filled]
    page8 = src[labels]
    return snap(page8, centres), centres


def quantise(page, centres):
    # Nearest-pixel reduction keeps the flat facet colours; an area filter would blend them.
    small = cv2.resize(page, (PAGE, PAGE), interpolation=cv2.INTER_NEAREST)
    pal = Image.new('P', (1, 1))
    pal.putpalette(centres.astype(np.uint8).ravel().tolist() + [0, 0, 0] * (256 - COLOURS))
    return Image.fromarray(small).quantize(palette=pal, dither=Image.Dither.NONE)


EXPRESSIONS = ROOT / 'concept-art/characters/babuin/babuin-expressoes-24-psx-v1.png'
FACE_GRID, FACE_CELL = (6, 4), 42   # 24 cells; 252 x 168 fits a 256 page


def face_atlas():
    """The 24 expressions reduced to 42 px cells with their own 15-colour palette (a second
    CLUT, as on the PS1); the cell's skin becomes transparent so the page's skin shows."""
    sheet = load_view_path(EXPRESSIONS)
    cols, rows = FACE_GRID
    cw, ch = sheet.shape[1] // cols, sheet.shape[0] // rows
    out = np.zeros((rows * FACE_CELL, cols * FACE_CELL, 4), np.uint8)
    cells = []
    for r in range(rows):
        for c in range(cols):
            cell = sheet[r * ch + 4:(r + 1) * ch - 4, c * cw + 4:(c + 1) * cw - 4]
            cells.append(cv2.resize(cell, (FACE_CELL, FACE_CELL), interpolation=cv2.INTER_AREA))
    allpx = np.concatenate([c.reshape(-1, 3) for c in cells]).astype(np.float32)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.2)
    _, _, centres = cv2.kmeans(allpx, COLOURS, None, crit, 4, cv2.KMEANS_PP_CENTERS)
    for i, cell in enumerate(cells):
        q = snap(cell, centres)
        values, counts = np.unique(q.reshape(-1, 3), axis=0, return_counts=True)
        skin = values[counts.argmax()]          # the cell is filled with skin edge to edge
        alpha = np.where((q == skin).all(-1), 0, 255).astype(np.uint8)
        r, c = divmod(i, cols)
        out[r * FACE_CELL:(r + 1) * FACE_CELL, c * FACE_CELL:(c + 1) * FACE_CELL] = np.dstack([q, alpha])
    Image.fromarray(out, 'RGBA').save(SRC / 'babuin_rosto_atlas.png')
    return out.shape


HAND_DIR = SRC / 'mao'
HAND_VIEWS = ('costas', 'perfil', 'palma')
HAND_PAGE = (192, 128)
HAND_CM_PER_PX = 0.045      # the open-hand reference crops (legends_babuin.OPEN_HAND_RINGS)


def hand_page():
    """The open hand's own small page: its three reference views side by side at 128 px tall,
    15 colours. Returns each view's x offset and width on the page (pixels), for the UVs."""
    crops = [load_view_path(HAND_DIR / f'mao_{v}.png') for v in HAND_VIEWS]
    k = HAND_PAGE[1] / crops[0].shape[0]
    page = np.full((HAND_PAGE[1], HAND_PAGE[0], 3), crops[0][3, 3], np.uint8)
    layout, x = {}, 0
    for v, c in zip(HAND_VIEWS, crops):
        w = round(c.shape[1] * k)
        page[:, x:x + w] = cv2.resize(c, (w, HAND_PAGE[1]), interpolation=cv2.INTER_AREA)
        layout[v] = (x, w)
        x += w + 2
    # Grey background -> nearest hand colour, so UV corners on the outline never pick it up.
    # The 2 px dark outline is dropped the same way.
    bg = np.abs(page.astype(int) - crops[0][3, 3].astype(int)).sum(2) < 40
    bg = cv2.dilate(bg.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    _, labels = cv2.distanceTransformWithLabels(bg.astype(np.uint8), cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    src = np.zeros((labels.max() + 1, 3), np.uint8)
    src[labels[~bg]] = page[~bg]
    page = src[labels]
    centres = cv2.kmeans(page.reshape(-1, 3).astype(np.float32), COLOURS, None,
                         (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.2), 4, cv2.KMEANS_PP_CENTERS)[2]
    Image.fromarray(snap(page, centres)).save(SRC / 'babuin_mao_pagina.png')
    meta = {'size': HAND_PAGE, 'scale': k, 'crop_h': crops[0].shape[0], 'cm_per_px': HAND_CM_PER_PX,
            'views': {v: {'x': layout[v][0], 'w': layout[v][1], 'crop_w': c.shape[1]} for v, c in zip(HAND_VIEWS, crops)}}
    (SRC / 'babuin_mao_pagina.json').write_text(json.dumps(meta))
    return meta


if __name__ == '__main__':
    import sys
    if '--hand' in sys.argv:
        print('hand page', hand_page())
        raise SystemExit
    print('face atlas', face_atlas())
    tris = json.loads((SRC / 'babuin_uv_tris.json').read_text())
    page, centres = paint(tris)
    cv2.imwrite(str(SRC / 'babuin_pagina_1024.png'), cv2.cvtColor(page, cv2.COLOR_RGB2BGR))
    q = quantise(page, centres)
    q.save(SRC / 'babuin_pagina_256_gerada.png')  # never over the hand-painted page
    print('colours', len(q.getcolors()), 'size', q.size)
