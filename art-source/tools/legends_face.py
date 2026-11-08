"""Expression atlas and FaceUV of a Legends character (the face page, like Mega Man's).

    python art-source/tools/legends_face.py x12_modelo

The character module gives EXPRESSIONS (a 6 x 4 sheet of 24 faces, each filled with skin edge
to edge) and FACE_BOX {'x': (x0, x1), 'z': (z0, z1)}: the square on the front of the head that
one cell covers (chin to just above the brows, metres).
Writes <name>_rosto_atlas.png: 6 x 4 cells of 42 px (252 x 168), its own 15-colour palette (a
second PS1 CLUT), the cell's skin transparent so the body page's skin shows. And gives the head
part a 'fuv' (FaceUV): per face corner, its place in FACE_BOX (0..1, v up) for skin faces facing
forward that overlap the box; (-1, -1) elsewhere (the toon shader draws the cell where UV2 >= 0).
"""
import importlib
import json
import sys

import cv2
import numpy as np
from PIL import Image

GRID, CELL, COLOURS = (6, 4), 42, 15
MIN_FRONT = 0.05
SKIN_RANGE = 70           # atlas colours this close to its skin are skin shades


def page_skin(m):
    """Most common colour of the head's skin faces on the body page (the page the model uses)."""
    path = m.SRC / f'{m.NAME}_pecas.json'
    p = json.loads(path.read_text())['head']
    path = m.SRC / f'{m.NAME}_pagina_256.png'
    if not path.exists():                                 # a new outfit: its generated page
        path = m.SRC / f'{m.NAME}_pagina_256_gerada.png'
    page = np.array(Image.open(path).convert('RGB'))
    px = []
    for fi, uv in enumerate(p['uv']):
        if p['ftone'][fi] == 'skin':
            c = np.mean(uv, 0)
            px.append(page[int((1 - c[1]) * 255), int(c[0] * 255)])
    v, n = np.unique(np.array(px), axis=0, return_counts=True)
    return v[n.argmax()].astype(np.float32)


def atlas(m):
    sheet = cv2.cvtColor(cv2.imread(str(m.EXPRESSIONS)), cv2.COLOR_BGR2RGB)
    cols, rows = GRID
    cw, ch = sheet.shape[1] / cols, sheet.shape[0] / rows
    cells = []
    for r in range(rows):
        for c in range(cols):
            cell = sheet[int(r * ch) + 6:int((r + 1) * ch) - 6, int(c * cw) + 6:int((c + 1) * cw) - 6]
            cells.append(cv2.resize(cell, (CELL, CELL), interpolation=cv2.INTER_AREA))
    px = np.concatenate([c.reshape(-1, 3) for c in cells]).astype(np.float32)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.2)
    _, _, centres = cv2.kmeans(px, COLOURS, None, crit, 4, cv2.KMEANS_PP_CENTERS)
    # the cells' skin tones are moved onto the page's skin (same offset for every skin shade, so
    # the painted jaw shadow stays): no seam where the cell meets the page
    cnt = np.zeros(COLOURS)
    for cell in cells:
        d = ((cell[..., None, :].astype(np.float32) - centres) ** 2).sum(-1)
        cnt += np.bincount(d.argmin(-1).ravel(), minlength=COLOURS)
    skin0 = centres[cnt.argmax()].copy()
    target = page_skin(m)
    near = np.linalg.norm(centres - skin0, axis=1) < SKIN_RANGE
    shown = centres.copy()                          # colours written; `centres` still classify
    shown[near] = np.clip(centres[near] + (target - skin0), 0, 255)
    out = np.zeros((rows * CELL, cols * CELL, 4), np.uint8)
    for i, cell in enumerate(cells):
        d = ((cell[..., None, :].astype(np.float32) - centres) ** 2).sum(-1)
        q = shown[d.argmin(-1)].astype(np.uint8)
        values, counts = np.unique(q.reshape(-1, 3), axis=0, return_counts=True)
        skin = values[counts.argmax()]                    # the cell is skin edge to edge
        alpha = np.where((q == skin).all(-1), 0, 255).astype(np.uint8)
        r, c = divmod(i, cols)
        out[r * CELL:(r + 1) * CELL, c * CELL:(c + 1) * CELL] = np.dstack([q, alpha])
    path = m.SRC / f'{m.NAME}_rosto_atlas.png'
    Image.fromarray(out, 'RGBA').save(path)
    print('wrote', path, out.shape[1], 'x', out.shape[0])
    return path


def face_uv(m, parts):
    (x0, x1), (z0, z1) = m.FACE_BOX['x'], m.FACE_BOX['z']
    p = parts['head']
    P = np.array(p['v'])
    fuv, n_on = [], 0
    for fi, f in enumerate(p['f']):
        q = P[f]
        n = np.cross(q[1] - q[0], q[2] - q[0])
        n /= np.linalg.norm(n) + 1e-12
        tone = p['ftone'][fi] if 'ftone' in p else 'skin'
        # the jaw shade (Orsted's under-nose and mouth faces) carries the face too: the atlas skin is
        # transparent, so only the mouth and eyes draw over the shade
        on = (tone in ('skin', 'shade') and -n[1] > MIN_FRONT and q[:, 0].min() < x1 and q[:, 0].max() > x0
              and q[:, 2].min() < z1 and q[:, 2].max() > z0)
        n_on += on
        fuv.append([[float((v[0] - x0) / (x1 - x0)), float((v[2] - z0) / (z1 - z0))] if on else [-1.0, -1.0]
                    for v in q])
    p['fuv'] = fuv
    print('FaceUV on', n_on, 'head faces')
    return parts


def build(module_name):
    m = importlib.import_module(module_name)
    path = m.SRC / f'{m.NAME}_pecas.json'
    parts = face_uv(m, json.loads(path.read_text()))
    path.write_text(json.dumps(parts))
    atlas(m)


if __name__ == '__main__':
    build(sys.argv[1] if len(sys.argv) > 1 else 'x12_modelo')
