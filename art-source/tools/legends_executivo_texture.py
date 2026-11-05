"""Page for Babuin's Executivo outfit.

Starts from the hand-painted Jade page (babuin_pagina_256.png): the copied Jade parts (head,
ears, neck, fists, bare feet) keep their texels untouched. Only the islands of the new pieces
(jacket, sleeves, cuffs, trousers) are painted, by projecting the Executivo turnaround onto them
in the A-pose (front / profile / back with a depth test, every triangle of the outfit as an
occluder), with the suit's own 15 colours. Never written over a hand-painted page.

Input: executivo/executivo_uv_tris.json from legends_executivo.dump_triangles (Blender).
Output: babuin_pagina_256_executivo_gerada.png (copy it to ..._executivo.png before painting by
hand; this script never writes that name).
python art-source/tools/legends_executivo_texture.py
"""
import json

import cv2
import numpy as np
from PIL import Image

import legends_texture as lt

EX = lt.SRC / 'executivo'
JADE_PAGE = lt.SRC / 'babuin_pagina_256.png'
OUT = lt.SRC / 'babuin_pagina_256_executivo_gerada.png'


def paint(tris):
    raw = {n: lt.load_view_path(EX / f'executivo_{n}.png') for n in ('frente', 'costas', 'perfil')}
    zb = lt.zbuffers(tris, raw)
    flat, centres = lt.palette(raw)
    images = {n: lt.snap(flat[n], centres) for n in flat}
    # The suit's silhouette has a painted light rim: keep samples 6 px inside the figure.
    invalid = {n: cv2.dilate(lt.masks(raw[n]).astype(np.uint8), np.ones((13, 13), np.uint8)).astype(bool) for n in raw}
    # No new piece is skin: in the profile the fist hangs in front of the thigh, so skin-toned
    # samples (and their outline) are someone else's surface.
    for n in raw:
        hsv = cv2.cvtColor(raw[n], cv2.COLOR_RGB2HSV)
        skin = (hsv[..., 0] >= 5) & (hsv[..., 0] <= 25) & (hsv[..., 1] > 70) & (hsv[..., 2] > 90)
        invalid[n] |= cv2.dilate(skin.astype(np.uint8), np.ones((7, 7), np.uint8)).astype(bool)
    W = lt.WORK
    page = np.zeros((W, W, 3), np.uint8)
    filled = np.zeros((W, W), bool)
    island = np.zeros((W, W), bool)
    for t in tris:
        if not t['new']:
            continue
        co, n = np.array(t['co']), np.array(t['n'])
        uv = np.array(t['uv']) * [W, -W] + [0, W]
        r = lt.raster(uv, (W, W))
        if r is None:
            continue
        xs, ys, bary = r
        island[ys, xs] = True
        pts = bary @ co
        score = {'front': -n[1], 'back': n[1], 'left': n[0], 'right': -n[0]}
        colour = np.zeros((len(xs), 3), np.uint8)
        done = np.zeros(len(xs), bool)
        for v in sorted(score, key=score.get, reverse=True):
            if score[v] < -0.2:
                break
            img_name, hor, dep = lt.VIEWS[v]
            img = images[img_name]
            px, py = lt.to_px(img, hor(pts), pts[:, 2])
            ix = np.clip(px.astype(int), 0, img.shape[1] - 1)
            iy = np.clip(py.astype(int), 0, img.shape[0] - 1)
            visible = dep(pts) <= zb[v][iy, ix] + 0.012
            take = visible & ~invalid[img_name][iy, ix] & ~done
            colour[take] = img[iy[take], ix[take]]
            done |= take
            if done.all():
                break
        page[ys[done], xs[done]] = colour[done]
        filled[ys[done], xs[done]] = True
    # Unseen texels inside the new islands take their nearest painted neighbour.
    _, labels = cv2.distanceTransformWithLabels((~filled).astype(np.uint8), cv2.DIST_L2, 5,
                                                labelType=cv2.DIST_LABEL_PIXEL)
    src = np.zeros((labels.max() + 1, 3), np.uint8)
    src[labels[filled]] = page[filled]
    page = src[labels]
    return page, island, centres


def jade_cloth(rgb):
    """The Jade outfit's greens (a bracelet edge painted on the fist's wrist)."""
    r, g, b = [rgb[..., i].astype(int) for i in range(3)]
    return (g > r + 15) & (g > b + 8)


def compose(page, island, centres, tris):
    """Jade page with the new islands (grown 1 texel, nearest reduction) painted over. The kept
    fists carry a strip of the Jade bracelet's green at the wrist: it becomes skin."""
    jade = np.array(Image.open(JADE_PAGE).convert('RGB'))
    P = lt.PAGE
    hands = np.zeros((P, P), np.uint8)
    for t in tris:
        if t['part'].startswith('hand_'):
            uv = np.array(t['uv']) * [P, -P] + [0, P]
            cv2.fillPoly(hands, [np.round(uv).astype(np.int32)], 1)
    green = jade_cloth(jade) & hands.astype(bool)
    if green.any():
        _, labels = cv2.distanceTransformWithLabels(green.astype(np.uint8), cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
        ok = hands.astype(bool) & ~green
        src = np.zeros((labels.max() + 1, 3), np.uint8)
        src[labels[ok]] = jade[ok]
        jade[green] = src[labels[green]]
    small = cv2.resize(page, (lt.PAGE, lt.PAGE), interpolation=cv2.INTER_NEAREST)
    mask = cv2.resize(island.astype(np.uint8), (lt.PAGE, lt.PAGE), interpolation=cv2.INTER_AREA) > 0
    mask = cv2.dilate(mask.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    out = jade.copy()
    out[mask] = lt.snap(small, centres)[mask]
    return out


if __name__ == '__main__':
    tris = json.loads((EX / 'executivo_uv_tris.json').read_text())
    page, island, centres = paint(tris)
    out = compose(page, island, centres, tris)
    Image.fromarray(out).save(OUT)
    print('page', OUT.name, 'new islands', int(island.sum()), 'texels at work size')
