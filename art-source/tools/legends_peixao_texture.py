"""Page for Babuin's Peixão outfit, painted from the costume's panel sheet.

The costume's turnaround is drawn with a bigger hood and a lower shoulder line than the rig, so
projecting the drawing would land colours on the wrong pieces. Instead every new piece takes its
panel from babuin-peixao-texturas-referencia-v1.png (like legends_texture.Mapper), placed by the
piece's A-pose bounding box on the plane its face looks along. The Jade fists and feet are
repainted as the costume's gloves and booties; the head, ears and neck keep the hand-painted
Jade texels. Also writes the open hand's page recoloured as a glove.

Input: peixao/peixao_uv_tris.json from legends_executivo.dump_triangles (Blender).
Output: babuin_pagina_256_peixao_gerada.png and babuin_mao_pagina_peixao.png (never over a
hand-painted page).
python art-source/tools/legends_peixao_texture.py
"""
import json

import cv2
import numpy as np
from PIL import Image

import legends_texture as lt

PX = lt.SRC / 'peixao'
SHEET = lt.ROOT / 'concept-art/characters/babuin/babuin-peixao-texturas-referencia-v1.png'
JADE_PAGE = lt.SRC / 'babuin_pagina_256.png'
OUT = lt.SRC / 'babuin_pagina_256_peixao_gerada.png'
HAND_OUT = lt.SRC / 'babuin_mao_pagina_peixao.png'

# Panel grid (row, col) on the sheet.
P = {
    'hood_front': (0, 0), 'hood_top': (0, 1), 'hood_back': (0, 2), 'lip': (0, 3), 'belly': (0, 4),
    'back': (0, 5), 'fin_fan': (1, 0), 'plain': (1, 1), 'forearm': (1, 2), 'glove_back': (1, 3),
    'glove_palm': (1, 4), 'thigh': (1, 5), 'shin': (2, 0), 'boot': (2, 1), 'band': (2, 2),
    'fin_a': (2, 3), 'fin_b': (2, 4), 'fin_v': (2, 5),
}
# part -> {facing: panel}; facing is front / back / side / top; '*' for any.
PANELS = {
    'hood': {'back': 'hood_back', '*': 'plain'},
    'lip': {'*': 'lip'},
    'dorsal': {'*': 'fin_v'}, 'tail': {'*': 'fin_v'},
    'side_fin': {'*': 'fin_fan'}, 'arm_fin': {'*': 'fin_a'},
    'suit_top': {'front': 'belly', 'back': 'back', '*': 'plain'},
    'suit_low': {'front': 'belly', 'back': 'back', '*': 'plain'},
    'upper_arm': {'*': 'plain'}, 'forearm': {'*': 'forearm'}, 'cuff': {'*': 'band'},
    'thigh': {'*': 'thigh'}, 'shin': {'*': 'shin'}, 'boot_cuff': {'*': 'band'},
    'hand': {'front': 'glove_palm', '*': 'glove_back'}, 'foot': {'*': 'boot'},
}
FLAT = {'eye': 'eye', 'pupil': 'pupil'}
# Pieces whose box is shared, so one panel spans them (the belly egg runs over both halves).
GROUPS = {'suit_top': 'suit', 'suit_low': 'suit'}


def panels():
    sheet = np.array(Image.open(SHEET).convert('RGB'))
    bg = np.abs(sheet.astype(int) - sheet[3, 3].astype(int)).sum(2) < 30
    def spans(filled):
        out, start = [], None
        for i, f in enumerate(filled):
            if f and start is None:
                start = i
            if not f and start is not None:
                if i - start > 40:
                    out.append((start, i))
                start = None
        if start is not None:
            out.append((start, len(filled)))
        return out
    rows = spans((~bg).mean(1) > .3)
    cols = spans((~bg).mean(0) > .3)
    assert len(rows) == 3 and len(cols) == 6, (rows, cols)
    flat = cv2.pyrMeanShiftFiltering(cv2.cvtColor(sheet, cv2.COLOR_RGB2BGR), 4, 10)[..., ::-1].copy()
    crops = {k: flat[rows[r][0] + 4:rows[r][1] - 4, cols[c][0] + 4:cols[c][1] - 4] for k, (r, c) in P.items()}
    return crops


def kind(part):
    k = part[:-2] if part[-2:] in ('_l', '_r') else part
    return k


def facing(n):
    ax = int(np.argmax(np.abs(n)))
    if ax == 2:
        return 'top'
    if ax == 1:
        return 'front' if n[1] < 0 else 'back'
    return 'side'


def boxes(tris):
    out = {}
    for t in tris:
        key = GROUPS.get(kind(t['part']), t['part'])
        co = np.array(t['co'])
        lo, hi = out.get(key, (co.min(0), co.max(0)))
        out[key] = (np.minimum(lo, co.min(0)), np.maximum(hi, co.max(0)))
    return out


def paint(tris):
    crops = panels()
    eye = crops['hood_top']
    # eye white and pupil: the lightest and darkest colours of the eye panel
    flat_px = eye.reshape(-1, 3).astype(int)
    lum = flat_px.sum(1)
    flats = {'eye': flat_px[lum.argmax()], 'pupil': flat_px[lum.argmin()]}
    allpx = np.concatenate([c.reshape(-1, 3) for c in crops.values()]).astype(np.float32)
    centres = cv2.kmeans(allpx, lt.COLOURS, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, .2),
                         4, cv2.KMEANS_PP_CENTERS)[2]
    box = boxes(tris)
    W = lt.WORK
    page = np.zeros((W, W, 3), np.uint8)
    painted = np.zeros((W, W), bool)
    for t in tris:
        k = kind(t['part'])
        if k not in PANELS and k not in FLAT:
            continue
        uv = np.array(t['uv']) * [W, -W] + [0, W]
        r = lt.raster(uv, (W, W))
        if r is None:
            continue
        xs, ys, bary = r
        painted[ys, xs] = True
        if k in FLAT:
            page[ys, xs] = flats[FLAT[k]]
            continue
        n = np.array(t['n'])
        f = facing(n)
        table = PANELS[k]
        crop = crops[table.get(f, table['*'])]
        lo, hi = box[GROUPS.get(k, t['part'])]
        size = np.maximum(hi - lo, 1e-4)
        q = (bary @ np.array(t['co']) - lo) / size          # 0..1 in the piece's box
        sx = 1 if t['part'].endswith('_r') else 0
        if f in ('front', 'back'):
            u, v = q[:, 0], 1 - q[:, 2]
            if f == 'back':
                u = 1 - u
        elif f == 'side':
            u, v = (q[:, 1] if n[0] > 0 else 1 - q[:, 1]), 1 - q[:, 2]
        else:
            u, v = q[:, 0], q[:, 1]
        if k in ('side_fin', 'arm_fin', 'dorsal', 'tail'):      # fins: spread from the root
            u, v = (q[:, 0] if k in ('side_fin', 'arm_fin') else q[:, 1]), 1 - q[:, 2]
            if sx:
                u = 1 - u
        h, w = crop.shape[:2]
        page[ys, xs] = crop[np.clip((v * (h - 1)).astype(int), 0, h - 1), np.clip((u * (w - 1)).astype(int), 0, w - 1)]
    return page, painted, centres


def compose(page, painted, centres):
    jade = np.array(Image.open(JADE_PAGE).convert('RGB'))
    small = lt.snap(cv2.resize(page, (lt.PAGE, lt.PAGE), interpolation=cv2.INTER_NEAREST), centres)
    mask = cv2.resize(painted.astype(np.uint8), (lt.PAGE, lt.PAGE), interpolation=cv2.INTER_AREA) > 0
    mask = cv2.dilate(mask.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    out = jade.copy()
    out[mask] = small[mask]
    return out


def glove_hand(centres):
    """The open hand's page as a teal glove: each texel's brightness picks a shade of the
    glove panel's ramp."""
    hand = np.array(Image.open(lt.SRC / 'babuin_mao_pagina.png').convert('RGB'))
    glove = panels()['glove_back'].reshape(-1, 3)
    ramp = glove[np.argsort(glove.sum(1))]
    lum = hand.astype(float).mean(2)
    t = (lum - lum.min()) / max(1, lum.max() - lum.min())
    out = ramp[np.clip((t * (len(ramp) - 1)).astype(int), 0, len(ramp) - 1)]
    return lt.snap(out.astype(np.uint8), centres)


if __name__ == '__main__':
    tris = json.loads((PX / 'peixao_uv_tris.json').read_text())
    page, painted, centres = paint(tris)
    Image.fromarray(compose(page, painted, centres)).save(OUT)
    Image.fromarray(glove_hand(centres)).save(HAND_OUT)
    print('page', OUT.name, 'hand', HAND_OUT.name)
