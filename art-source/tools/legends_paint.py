"""Paint a Legends character's 256 x 256 body page from its texture panels and concept views.

    python art-source/tools/legends_paint.py x12_modelo

Needs the UVs of legends_uv.py. The character module gives:
    PANELS       the panel sheet (numbered panels on a flat grey background, row by row)
    PAINT        {(part, island) or (part, '*'): source}; the part name without _l/_r, or with
                 it for one side only. A source is one of
                   ('panel', n[, (x0, y0, x1, y1) crop as fractions][, 'mirror'])
                   ('view', 'frente' | 'perfil' | 'costas'[, 'only'])   projection of the concept
                     crop ('only': keep the pixels near the face's own tone, e.g. hair without
                     the skin around it; 'hair': the character's HAIR_MASK(view) decides per
                     texel, hair projected and the rest flat skin, for the head)
                   ('tone', 'stone' | 'metal' | 'skin' | 'hair')   flat colour
                   ('ftone', {tone: source})   by the face's tone (e.g. face skin flat, hair projected)
                 Panels are cropped to the painted part by PANEL_CROP {n: (x0, y0, x1, y1)}
                 (their dark background left out), or by the source's own crop, or 'full'. Limb cylinders take the panel as their front, folded
                 round to the back.
                 Islands without an entry are projected from the view they face.
    FACE_PAINT   {(part, face index): source}: one face painted apart from its island
    PAGE_COLOURS optional colour count of the page (default 15, one PS1 CLUT)
    TONE_PANEL   {tone: (panel, crop)}: where the flat colours are sampled (most common colour)
    PANEL_FILL   {panel: tone}: the panel's dark background (flooded from its border) painted with that tone;
                 PANEL_FILL_ALL (r, g, b): also every texel of that colour (a sheet whose panels sit on its grey)
    COPY_FROM    (module, [parts]): those parts are painted from the other module's page, face by face
                 (an outfit keeps the base's hand-painted head); same part names and faces
A panel source may add ('turn', t): a limb cylinder's panel turned t of a turn round the limb, and
'wrap': the panel goes once round the limb (not folded), e.g. a stripe or a tattoo on one side.
('band', u0, u1, tone) paints a stripe of a tone on the island (u across it; round a limb 0.5 is the front);
('vband', v0, v1, tone) a ring (v down the island; down a limb from its top).
A TONE_PANEL value may also be a '#rrggbb' colour. Writes <name>_pagina_256_gerada.png (indexed, 15 colours: one PS1 palette) and a 4x preview;
<name>_pagina_256.png, the page the model uses and the user paints in Blender, is created from
it only when missing, never overwritten; `legends_paint.py merge <module> part:island ...`
copies chosen islands (part:island, part:*, or faces part:f12,f13) of the generated page into it (the rest of the hand painting stays);
`legends_paint.py sym <module> [-x] part:island ...` mirrors symmetric islands of it (her left half kept, or -x), and part_l>part_r copies a limb's painting
onto its mirror face by face.
The page is painted at WORK px and reduced with nearest sampling (flat facets stay flat).
"""
import importlib
import json
import sys

import cv2
import numpy as np
from PIL import Image

PAGE, WORK = 256, 1024
COLOURS = 15
VIEW_DIR = {'-y': 'frente', '+y': 'costas', '+x': 'perfil', '-x': 'perfil'}
FIGURE_PX, CROP_H = 840, 851


# ---------------------------------------------------------------- sources
def load_rgb(path):
    return cv2.cvtColor(cv2.imread(str(path)), cv2.COLOR_BGR2RGB)


def panels(spec):
    """Numbered panels: a sheet path (numbered from 1) or a list of (sheet path, first number),
    for sheets made later (e.g. panels 21-24)."""
    if not isinstance(spec, (list, tuple)):
        spec = [(spec, 1)]
    out = {}
    for path, first in spec:
        out.update({first - 1 + k: p for k, p in _sheet(path).items()})
    return out


def _runs(filled, min_len):
    """(start, length) of the runs of True at least min_len long."""
    out, start = [], None
    for i, f in enumerate(list(filled) + [False]):
        if f and start is None:
            start = i
        elif not f and start is not None:
            if i - start >= min_len:
                out.append((start, i - start))
            start = None
    return out


def _grid(mask, dark):
    """Panel rectangles (x, y, w, h): the connected shapes of the mask; a shape much bigger than
    the typical panel (panels a few px apart joined by a stray pixel) is cut along the rows and
    columns inside it that carry no dark panel background."""
    n, _, st, _ = cv2.connectedComponentsWithStats(mask, connectivity=4)
    rects = [tuple(int(v) for v in st[i, :4]) for i in range(1, n) if st[i, 4] > 0.01 * mask.size / 20]
    area = np.median([w * h for _, _, w, h in rects])
    out = []
    for x, y, w, h in rects:
        if w * h < 1.8 * area:
            out.append((x, y, w, h))
            continue
        d = dark[y:y + h, x:x + w]
        side = int(np.sqrt(area))
        for ry, rh in _runs(d.mean(1) > 0.03, side // 3):
            band = d[ry:ry + rh]
            for rx, rw in _runs(band.mean(0) > 0.03, side // 3):
                out.append((x + rx, y + ry, rw, rh))
    keep = []                                       # a cut panel may repeat one found on its own;
    out = [r for r in out if r[2] * r[3] > 0.3 * area]   # a dark panel's stray bits are not panels
    for r in sorted(out, key=lambda r: -r[2] * r[3]):   # the whole panel wins over a piece inside it
        ix = lambda a, b: max(0, min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0])) * max(0, min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1]))
        if all(ix(r, k) < 0.5 * min(r[2] * r[3], k[2] * k[3]) for k in keep):
            keep.append(r)
    return keep


def _sheet(path):
    """Panels of one sheet (1-based, row by row), inset 4 px from their borders; the number
    tag in the top-left corner is covered with the panel's own colour."""
    im = load_rgb(path)
    bg = im[2, 2].astype(int)
    mask = (np.abs(im.astype(int) - bg).sum(2) > 60).astype(np.uint8)   # noisy grey gaps stay gaps
    rects = _grid(mask, (im.max(2) < 90).astype(np.uint8))
    h0 = np.median([r[3] for r in rects])
    rects = sorted(rects, key=lambda r: (round(r[1] / h0), r[0]))
    out = {}
    for k, (x, y, w, h) in enumerate(rects, start=1):
        p = im[y + 4:y + h - 4, x + 4:x + w - 4].copy()
        tag = p[:int(h * 0.13), :int(w * 0.13)]
        below = p[int(h * 0.13):int(h * 0.2), :int(w * 0.13)].reshape(-1, 3)
        tag[:] = np.median(below, 0)
        out[k] = p
    return out


def views(m):
    return {v: load_rgb(m.SRC / f'{m.NAME}_{v}.png') for v in ('frente', 'perfil', 'costas')}


def background(img):
    """Grey background and the dark silhouette outline next to it (not surface colour)."""
    bg = np.abs(img.astype(int) - img[3, 3].astype(int)).sum(2) < 45
    near = cv2.dilate(bg.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)
    return bg | (near & (img.max(2) < 110))


def project(img, invalid, view, P, mpp):
    """Colours of 3D points seen in a concept crop (orthographic, as the crops are drawn)."""
    top = CROP_H * mpp
    h = {'frente': P[:, 0], 'costas': -P[:, 0], 'perfil': P[:, 1]}[view]
    c = (img.shape[1] / 2 + h / mpp).astype(int).clip(0, img.shape[1] - 1)
    r = ((top - P[:, 2]) / mpp).astype(int).clip(0, img.shape[0] - 1)
    ok = ~invalid[r, c]
    return img[r, c], ok


# ---------------------------------------------------------------- raster
def raster(tri, shape):
    (x0, y0), (x1, y1), (x2, y2) = tri
    xs = np.arange(max(int(np.floor(min(x0, x1, x2))), 0), min(int(np.ceil(max(x0, x1, x2))) + 1, shape[1]))
    ys = np.arange(max(int(np.floor(min(y0, y1, y2))), 0), min(int(np.ceil(max(y0, y1, y2))) + 1, shape[0]))
    if not len(xs) or not len(ys):
        return None
    gx, gy = np.meshgrid(xs + .5, ys + .5)
    d = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
    if abs(d) < 1e-12:
        return None
    a = ((y1 - y2) * (gx - x2) + (x2 - x1) * (gy - y2)) / d
    b = ((y2 - y0) * (gx - x2) + (x0 - x2) * (gy - y2)) / d
    c = 1 - a - b
    m = (a >= -0.03) & (b >= -0.03) & (c >= -0.03)
    return (gx[m] - .5).astype(int), (gy[m] - .5).astype(int), np.stack([a[m], b[m], c[m]], 1)


def source_for(table, name, key):
    base = name[:-2] if name.endswith(('_l', '_r')) else name
    for k in ((name, key), (name, '*'), (base, key), (base, '*')):
        if k in table:
            return table[k]
    return None


def fill_background(img, tone, tone_panel, flat, sheet_grey=None):
    """The panel's dark background (the colour of its corners, flooded in from the border) painted
    with a tone, so a crop that reaches past the drawn part never brings dark into the island."""
    v = tone_panel[tone]
    if isinstance(v, str):
        colour = np.array([int(v[i:i + 2], 16) for i in (1, 3, 5)], np.uint8)
    else:
        n, c = v
        src = flat[n]
        colour = common_colour(src[int(c[1] * src.shape[0]):int(c[3] * src.shape[0]),
                                   int(c[0] * src.shape[1]):int(c[2] * src.shape[1])])
    out = img.copy()
    h, w = img.shape[:2]
    mask = np.zeros((h + 2, w + 2), np.uint8)
    for x, y in ((2, 2), (w - 3, 2), (2, h - 3), (w - 3, h - 3), (w // 2, h - 3), (w // 2, 2)):
        if not mask[y + 1, x + 1] and np.abs(img[y, x].astype(int) - img[2, 2].astype(int)).sum() < 40:
            cv2.floodFill(out, mask, (x, y), (0, 0, 0), (24, 24, 24), (24, 24, 24),   # fixed range: no creeping over soft edges
                          4 | cv2.FLOODFILL_MASK_ONLY | cv2.FLOODFILL_FIXED_RANGE | (255 << 8))
    out[mask[1:-1, 1:-1] > 0] = colour
    if sheet_grey is not None:                      # panels on a grey sheet: the grey between parts too
        g = img.astype(int)
        out[(np.abs(g - np.array(sheet_grey)).sum(2) < 80) & (np.ptp(g, axis=2) < 14)] = colour   # its greys, not coloured texels
    return out


def common_colour(img):
    v, c = np.unique(img.reshape(-1, 3), axis=0, return_counts=True)
    return v[c.argmax()]


# ---------------------------------------------------------------- page
def paint(module_name):
    m = importlib.import_module(module_name)
    parts = json.loads((m.SRC / f'{m.NAME}_pecas.json').read_text())
    mpp = m.HEIGHT / FIGURE_PX
    pan = panels(m.PANELS)
    flat = {k: cv2.pyrMeanShiftFiltering(p[..., ::-1], 4, 12)[..., ::-1].copy() for k, p in pan.items()}
    vw = views(m)
    vflat = {k: cv2.pyrMeanShiftFiltering(v[..., ::-1], 4, 12)[..., ::-1].copy() for k, v in vw.items()}
    invalid = {k: background(v) for k, v in vw.items()}
    hair = {k: m.HAIR_MASK(k) for k in vw} if hasattr(m, 'HAIR_MASK') else {}
    sheet_grey = getattr(m, 'PANEL_FILL_ALL', None)    # (r, g, b): every texel of the sheet's grey, not only the border
    for n, tone in getattr(m, 'PANEL_FILL', {}).items():
        flat[n] = fill_background(flat[n], tone, m.TONE_PANEL, flat, sheet_grey)
    tones = {t: (np.array([int(v[i:i + 2], 16) for i in (1, 3, 5)], np.uint8) if isinstance(v, str) else
                 common_colour(flat[v[0]][int(v[1][1] * flat[v[0]].shape[0]):int(v[1][3] * flat[v[0]].shape[0]),
                                          int(v[1][0] * flat[v[0]].shape[1]):int(v[1][2] * flat[v[0]].shape[1])]))
             for t, v in m.TONE_PANEL.items()}
    copy = {}
    if hasattr(m, 'COPY_FROM'):
        sm = importlib.import_module(m.COPY_FROM[0])
        src_parts = json.loads((sm.SRC / f'{sm.NAME}_pecas.json').read_text())
        src_page = np.array(Image.open(sm.SRC / f'{sm.NAME}_pagina_256.png').convert('RGB'))
        copy = {n: src_parts[n]['uv'] for n in m.COPY_FROM[1]}
    page = np.zeros((WORK, WORK, 3), np.uint8)
    filled = np.zeros((WORK, WORK), bool)
    done = set()
    for name, p in parts.items():
        P, F, UV = np.array(p['v']), p['f'], p['uv']
        key_of = {fi: k for k, fs in p['islands'].items() for fi in fs}
        for fi, f in enumerate(F):
            uv = np.array(UV[fi])
            sig = (tuple(np.round(uv.ravel(), 5)))
            if sig in done:                                 # a right limb reusing the left's UVs
                continue
            done.add(sig)
            key = key_of[fi].split('.')[0]               # a split-off sub-island paints as its island
            if name.endswith('_r') and key in ('+x', '-x'):  # the mirrored side: outer is -x
                key = '-x' if key == '+x' else '+x'
            src = getattr(m, 'FACE_PAINT', {}).get((name, fi)) or source_for(m.PAINT, name, key)
            if src is not None and src[0] == 'ftone':          # by the face's tone (skin / hair)
                src = src[1].get(p['ftone'][fi])
            if src is None and key in VIEW_DIR:
                src = ('view', VIEW_DIR[key])
            if src is None:
                src = ('tone', p.get('tone', 'stone') if 'ftone' not in p else p['ftone'][fi])
            luv = np.array(p['luv'][fi]) if 'luv' in p else None
            for k in range(1, len(f) - 1):
                tri = [0, k, k + 1]
                px = np.stack([uv[tri, 0] * WORK, (1 - uv[tri, 1]) * WORK], 1)
                r = raster(px, (WORK, WORK))
                if r is None or not len(r[0]):
                    # a face too small to cover a pixel still paints the one at its centre, so it
                    # never takes a neighbouring island's colour
                    c = px.mean(0).astype(int).clip(0, WORK - 1)
                    r = (np.array([c[0]]), np.array([c[1]]), np.array([[1 / 3, 1 / 3, 1 / 3]]))
                xs, ys, bary = r
                if name in copy:                            # the other page, same face
                    q = bary @ np.array(copy[name][fi])[tri]
                    sx = (q[:, 0] * PAGE).astype(int).clip(0, PAGE - 1)
                    sy = ((1 - q[:, 1]) * PAGE).astype(int).clip(0, PAGE - 1)
                    page[ys, xs] = src_page[sy, sx]
                elif src[0] == 'tone':
                    tone = src[1]
                    if 'ftone' in p and p['ftone'][fi] in tones:
                        tone = p['ftone'][fi] if src[1] in ('stone', 'metal') else tone
                    page[ys, xs] = tones[tone]
                elif src[0] == 'view':
                    pts = bary @ P[[f[i] for i in tri]]
                    col, ok = project(vflat[src[1]], invalid[src[1]], src[1], pts, mpp)
                    if 'hair' in src[2:]:                       # drawn hair mask decides per texel
                        hm = hair[src[1]]
                        top = CROP_H * mpp
                        h = {'frente': pts[:, 0], 'costas': -pts[:, 0], 'perfil': pts[:, 1]}[src[1]]
                        cc = (hm.shape[1] / 2 + h / mpp).astype(int).clip(0, hm.shape[1] - 1)
                        rr = ((top - pts[:, 2]) / mpp).astype(int).clip(0, hm.shape[0] - 1)
                        inside = hm[rr, cc]
                        col[~inside] = tones['skin']
                        col[inside & ~ok] = tones['hair']
                        ok[:] = True
                    if 'only' in src[2:] and 'ftone' in p:     # keep only this face's own tone
                        own = tones[p['ftone'][fi]].astype(float)
                        dist = np.abs(col.astype(float) - own).sum(1)
                        ok &= dist < 150
                    if 'ftone' in p and p['ftone'][fi] in tones:
                        col[~ok] = tones[p['ftone'][fi]]
                    else:
                        col[~ok] = tones.get(p.get('tone', 'stone'), col[~ok].mean(0) if (~ok).any() else 0)
                    page[ys, xs] = col
                else:
                    n = src[1]
                    crop = next((a for a in src[2:] if isinstance(a, tuple) and len(a) == 4), None)
                    if crop is None:
                        crop = (0, 0, 1, 1) if 'full' in src[2:] else getattr(m, 'PANEL_CROP', {}).get(n, (0, 0, 1, 1))
                    mirror = 'mirror' in src[2:]
                    q = bary @ luv[tri]                       # position in the whole island
                    u, v = q[:, 0], q[:, 1]
                    u_island, v_island = u.copy(), v.copy()
                    turn = next((a[1] for a in src[2:] if isinstance(a, tuple) and a[0] == 'turn'), 0)
                    if name.endswith('_r'):
                        turn = -turn
                    if key == 'cyl' and 'wrap' in src[2:]:   # the panel once round the limb
                        u = (u + turn) % 1.0
                    elif key == 'cyl':                       # front of the panel, folded round
                        u = 0.5 + 0.5 * np.sin((u - 0.5 + turn) * 2 * np.pi)
                    if mirror:
                        u = 1 - u
                    img = flat[n]
                    sx = ((crop[0] + u.clip(0, 1) * (crop[2] - crop[0])) * (img.shape[1] - 1)).astype(int)
                    sy = ((crop[1] + v.clip(0, 1) * (crop[3] - crop[1])) * (img.shape[0] - 1)).astype(int)
                    col = img[sy, sx]
                    for a in src[2:]:                        # ('band', u0, u1, tone): a painted stripe
                        if isinstance(a, tuple) and a[0] == 'band':
                            col[(u_island >= a[1]) & (u_island <= a[2])] = tones[a[3]]
                        if isinstance(a, tuple) and a[0] == 'vband':  # a ring round a limb (v along it)
                            col[(v_island >= a[1]) & (v_island <= a[2])] = tones[a[3]]
                    page[ys, xs] = col
                filled[ys, xs] = True
    # pad every island with its own edge colour (no bleeding across seams)
    _, lab = cv2.distanceTransformWithLabels((~filled).astype(np.uint8), cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    src_px = np.zeros((lab.max() + 1, 3), np.uint8)
    src_px[lab[filled]] = page[filled]
    page = src_px[lab]
    small = cv2.resize(page, (PAGE, PAGE), interpolation=cv2.INTER_NEAREST)
    # one 15-colour palette for the page (the PS1 CLUT)
    px = small.reshape(-1, 3).astype(np.float32)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.2)
    k = getattr(m, 'PAGE_COLOURS', COLOURS)       # an outfit with many materials may take two CLUTs' worth
    _, _, centres = cv2.kmeans(px, k, None, crit, 4, cv2.KMEANS_PP_CENTERS)
    pal = Image.new('P', (1, 1))
    pal.putpalette(centres.astype(np.uint8).ravel().tolist() + [0, 0, 0] * (256 - k))
    out = Image.fromarray(small).quantize(palette=pal, dither=Image.Dither.NONE)
    # the generator never touches the page the model uses (it may be painted by hand in Blender):
    # it writes <name>_pagina_256_gerada.png and creates <name>_pagina_256.png only if missing
    path = m.SRC / f'{m.NAME}_pagina_256_gerada.png'
    out.save(path)
    out.convert('RGB').resize((PAGE * 4, PAGE * 4), Image.NEAREST).save(m.SRC / f'{m.NAME}_pagina_256_gerada_x4.png')
    page = m.SRC / f'{m.NAME}_pagina_256.png'
    if page.exists():
        print('wrote', path, '-', page.name, 'kept (it may be painted by hand; copy over it on purpose)')
    else:
        out.save(page)
        print('wrote', path, 'and', page)
    return path


def merge(module_name, islands):
    """Copy islands ['part:key', ...] from the generated page into the page the model uses
    (painted by hand): only those islands' texels change, snapped to the page's own colours."""
    m = importlib.import_module(module_name)
    parts = json.loads((m.SRC / f'{m.NAME}_pecas.json').read_text())
    gen = np.array(Image.open(m.SRC / f'{m.NAME}_pagina_256_gerada.png').convert('RGB'))
    path = m.SRC / f'{m.NAME}_pagina_256.png'
    page = np.array(Image.open(path).convert('RGB'))
    mask = np.zeros(page.shape[:2], np.uint8)
    for spec in islands:
        name, key = spec.split(':')
        p = parts[name]
        if key.startswith('f') and key[1:2].isdigit():      # head:f56,f57 = single faces
            faces = [int(x[1:]) for x in key.split(',')]
        else:
            keys = [k for k in p['islands'] if key == '*' or k.split('.')[0] == key]
            faces = [f for k in keys for f in p['islands'][k]]
        for fi in faces:
            uv = np.array(p['uv'][fi])
            pts = np.stack([uv[:, 0] * PAGE, (1 - uv[:, 1]) * PAGE], 1)
            cv2.fillPoly(mask, [np.round(pts).astype(np.int32)], 1)
    mask = cv2.dilate(mask, np.ones((3, 3), np.uint8)).astype(bool)
    colours = np.unique(page.reshape(-1, 3), axis=0).astype(np.float32)
    src = gen[mask].astype(np.float32)
    page[mask] = colours[((src[:, None, :] - colours) ** 2).sum(-1).argmin(1)].astype(np.uint8)
    Image.fromarray(page).save(path)
    print('merged', islands, int(mask.sum()), 'texels into', path.name)


def symmetrize(module_name, islands, keep='+x'):
    """Mirror islands of a symmetric part (top:front, shorts:*) on the page the model uses: the
    half on the kept side ('+x' her left, '-x' her right) is copied over the other, about the
    page column where x = 0 falls (fitted from the island's vertices)."""
    m = importlib.import_module(module_name)
    parts = json.loads((m.SRC / f'{m.NAME}_pecas.json').read_text())
    path = m.SRC / f'{m.NAME}_pagina_256.png'
    page = np.array(Image.open(path).convert('RGB'))
    out = page.copy()
    for spec in islands:
        if '>' in spec:                                     # shorts_leg_l>shorts_leg_r: mirror part, face by face
            a_name, b_name = spec.split('>')
            A, B = parts[a_name], parts[b_name]
            for fi, f in enumerate(B['f']):
                fa = A['f'][fi]                             # the mirror reverses the winding
                ua = np.array(A['uv'][fi])[[fa.index(v) for v in f]]
                ub = np.array(B['uv'][fi])
                for t in range(1, len(f) - 1):
                    tri = [0, t, t + 1]
                    pb = np.stack([ub[tri, 0] * PAGE, (1 - ub[tri, 1]) * PAGE], 1)
                    r = raster(pb, (PAGE, PAGE))
                    if r is None or not len(r[0]):
                        continue
                    xs_, ys_, bary = r
                    q = bary @ ua[tri]
                    out[ys_, xs_] = page[((1 - q[:, 1]) * PAGE).astype(int).clip(0, PAGE - 1),
                                         (q[:, 0] * PAGE).astype(int).clip(0, PAGE - 1)]
            continue
        name, key = spec.split(':')
        p = parts[name]
        P = np.array(p['v'])
        keys = [k for k in p['islands'] if key == '*' or k.split('.')[0] == key]
        for k in keys:
            faces = p['islands'][k]
            xs = np.concatenate([P[p['f'][fi]][:, 0] for fi in faces])
            us = np.concatenate([np.array(p['uv'][fi])[:, 0] * PAGE for fi in faces])
            if np.ptp(xs) < 1e-6:
                continue
            a, c = np.polyfit(xs, us, 1)                      # page column = a x + c
            mask = np.zeros(page.shape[:2], np.uint8)
            for fi in faces:
                uv = np.array(p['uv'][fi])
                cv2.fillPoly(mask, [np.round(np.stack([uv[:, 0] * PAGE, (1 - uv[:, 1]) * PAGE], 1)).astype(np.int32)], 1)
            mask = cv2.dilate(mask, np.ones((3, 3), np.uint8)).astype(bool)
            ys, xs_ = np.nonzero(mask)
            side = np.sign(a) * (1 if keep == '+x' else -1)  # kept columns lie on this side of c
            drop = (xs_ + 0.5 - c) * side < 0
            src = np.floor(2 * c - (xs_[drop] + 0.5)).astype(int).clip(0, PAGE - 1)
            ok = mask[ys[drop], src]
            out[ys[drop][ok], xs_[drop][ok]] = page[ys[drop][ok], src[ok]]
    Image.fromarray(out).save(path)
    print('mirrored', islands, 'keeping', keep, 'into', path.name)


if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1] == 'merge':          # legends_paint.py merge <module> part:key ...
        merge(sys.argv[2], sys.argv[3:])
    elif len(sys.argv) > 2 and sys.argv[1] == 'sym':          # legends_paint.py sym <module> [-x] part:key ...
        keep = '-x' if '-x' in sys.argv[3:] else '+x'
        symmetrize(sys.argv[2], [a for a in sys.argv[3:] if ':' in a or '>' in a], keep)
    else:
        paint(sys.argv[1] if len(sys.argv) > 1 else 'x12_modelo')
