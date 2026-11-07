"""Comparison sheet of a Legends character against its concept and the references.

    python art-source/tools/legends_compare.py x12_modelo <render dir> <region> [out.png]

Uses the renders of legends_blender.compare(prefix, <render dir>, region) and the concept crops
(<NAME>_frente / _perfil / _costas.png in the character's SRC, MPP = HEIGHT / 840 px, top of
the crop at 851 px * MPP). Rows: front, profile, back, 3/4; columns: concept, character,
character wire, Mega Man wire.
"""
import importlib
import sys
from pathlib import Path

import cv2
import numpy as np

import legends_kit as lk

CROP_H = 851
FIGURE_PX = 840


def concept(m, view, z, scale, size):
    img = cv2.imread(str(m.SRC / f'{m.NAME}_{view}.png'))
    if img is None:
        return np.full((size[1], size[0], 3), 40, np.uint8)
    mpp = m.HEIGHT / FIGURE_PX
    top = CROP_H * mpp
    h_m = scale                              # ortho scale = height of the frame in metres
    w_m = scale * size[0] / size[1]
    half_h, half_w = int(h_m / 2 / mpp), int(w_m / 2 / mpp)
    r, c = int((top - z) / mpp), img.shape[1] // 2
    pad = max(half_h, half_w)
    img = np.pad(img, ((pad, pad), (pad, pad), (0, 0)), constant_values=128)
    crop = img[r + pad - half_h:r + pad + half_h, c + pad - half_w:c + pad + half_w]
    return cv2.resize(crop, size)


def sheet(module_name, render_dir, region, out=None):
    m = importlib.import_module(module_name)
    key = m.PREFIX.rstrip('_').lower()
    z, scale = lk.REGIONS[region]
    size = (560, 900) if region == 'corpo' else (700, 700)
    rows = []
    for v in ('frente', 'perfil', 'costas', 'tres4'):
        first = concept(m, v, z, scale, size) if v != 'tres4' else np.full((size[1], size[0], 3), 40, np.uint8)
        cells = [first]
        for name in (f'{region}_{key}_{v}', f'{region}_{key}_{v}_arame', f'{region}_megaman_{v}_arame'):
            im = cv2.imread(str(Path(render_dir) / f'{name}.png'))
            cells.append(cv2.resize(im, size) if im is not None else np.zeros_like(first))
        rows.append(np.hstack(cells))
    img = np.vstack(rows)
    k = 1600 / img.shape[1]
    out = out or str(Path(render_dir) / f'{region}_comparacao.png')
    cv2.imwrite(out, cv2.resize(img, None, fx=k, fy=k, interpolation=cv2.INTER_AREA))
    print('wrote', out)


if __name__ == '__main__':
    sheet(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None)
