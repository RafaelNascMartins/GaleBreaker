"""Pages for Dale's outfits (256, 15 colours), never touching the hand-painted base page.

- preto: the base page (dale_pagina_256.png) with the jeans, belt, boots and hat recoloured black
  (luminance kept, so the painted folds stay); skin, beard and the gold buckle untouched.
- coronel / physique: the outfit bodies (legends_dale_outfits) - kept parts copy the base page
  at their unchanged UVs; clothing comes from the outfit's panels (limbs wrapped, no seam) and the
  outfit turnaround projected for the torso and the coat. Physique repaints all the skin bronze
  and paints the head without the beard (the face comes from dale-sem-barba).

python dale_outfit_texture.py [preto|coronel|physique|faces]
"""
import json
import sys

import cv2
import numpy as np
from PIL import Image

import dale_outfit_panels as panels_mod
import dale_texture as dt
import legends_texture as lt

SRC = dt.SRC
OUT = lt.ROOT / 'godot/assets/characters/ignis/textures'
BASE_PAGE = SRC / 'dale_pagina_256.png'


def part_mask(tris, parts, size):
    m = np.zeros((size, size), bool)
    for t in tris:
        if t['part'] in parts:
            uv = np.array(t['uv']) * [size, -size] + [0, size]
            r = lt.raster(uv, (size, size))
            if r is not None:
                m[r[1], r[0]] = True
    return cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)


def preto():
    """Black jeans, belt, boots and hat on the hand-painted page."""
    base = np.array(Image.open(BASE_PAGE).convert('RGB'))
    tris = json.loads((SRC / 'dale_uv_tris.json').read_text())
    cloth = cv2.dilate(part_mask(tris, {'pelvis', 'thigh_l', 'thigh_r', 'shin_l', 'shin_r', 'belt', 'foot_l', 'foot_r', 'hat'}, 256).astype(np.uint8),
                       np.ones((3, 3), np.uint8)).astype(bool)
    # The jeans' blue is used by nothing else on the page: catch the padding around the islands too.
    d = base.astype(int)
    cloth |= (d[..., 2] > d[..., 0] + 25)
    lum = base.astype(np.float32).mean(2) / 255.0
    # Keep the jeans' and leather's light/dark bands, mapped to charcoal tones.
    lo, hi = np.percentile(lum[cloth], 5), np.percentile(lum[cloth], 95)
    t = np.clip((lum - lo) / max(hi - lo, 1e-3), 0, 1)
    black = (20 + 58 * t)[..., None] * np.array([1.0, 1.0, 1.06])
    out = base.copy()
    out[cloth] = np.clip(black[cloth], 0, 255).astype(np.uint8)
    Image.fromarray(out).save(SRC / 'dale_pagina_256_preto.png')
    return out


class Painter:
    def __init__(self, outfit):
        self.outfit = outfit
        self.tris = json.loads((SRC / f'dale_{outfit}_uv_tris.json').read_text())
        self.raw = {v: lt.load_view_path(SRC / f'dale_{outfit}_{v}.png') for v in ('frente', 'costas', 'perfil')}
        self.zb = lt.zbuffers(self.tris, self.raw)
        self.panels = panels_mod.load(outfit)
        self.base = cv2.resize(np.array(Image.open(BASE_PAGE).convert('RGB')), (lt.WORK, lt.WORK), interpolation=cv2.INTER_NEAREST)
        self.pmap = dt.PanelMap(self.tris)
        self.invalid = {n: lt.masks(self.raw[n]) for n in self.raw}

    def wrap(self, part, p, margin=.14):
        u, v = self.pmap.wrap(part, p)
        return .5 + (u - .5) * (1 - 2 * margin) / .72, v

    def project(self, t, pts, n, sides=True):
        score = {'front': -n[1], 'back': n[1], 'left': n[0], 'right': -n[0]}
        if not sides:
            score['left'] = score['right'] = -9
        colour = np.zeros((len(pts), 3), np.float32)
        done = np.zeros(len(pts), bool)
        for v in sorted(score, key=score.get, reverse=True):
            if score[v] < -0.5:
                break
            img_name, hor, dep = lt.VIEWS[v]
            img = self.images[img_name]
            px, py = lt.to_px(img, hor(pts), pts[:, 2])
            ix, iy = np.clip(px.astype(int), 0, img.shape[1] - 1), np.clip(py.astype(int), 0, img.shape[0] - 1)
            ok = ~self.invalid[img_name][iy, ix] & ~done
            if sides:
                ok &= dep(pts) <= self.zb[v][iy, ix] + 0.03
            colour[ok] = img[iy[ok], ix[ok]]
            done |= ok
            if done.all():
                break
        return colour, done

    def palette(self, keep, use_raw, skip_panels):
        """15 colours from what this outfit really shows: its panels (minus skip_panels), its
        turnaround if it is projected (the Physique's concept still has the old beard), and the
        base page only where parts are kept - so no jeans blue or beard brown sneaks in."""
        px = [v.reshape(-1, 3) for k, v in self.panels.items() if k not in skip_panels]
        if use_raw:
            px += [cv2.pyrMeanShiftFiltering(cv2.cvtColor(im, cv2.COLOR_RGB2BGR), 4, 12)[..., ::-1][~lt.masks(im)] for im in self.raw.values()]
        if keep:
            m = part_mask(self.tris, keep, lt.WORK)
            px.append(np.repeat(self.base[m], 3, axis=0))
        px = np.concatenate(px).astype(np.float32)
        crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.2)
        _, _, centres = cv2.kmeans(px, lt.COLOURS, None, crit, 4, cv2.KMEANS_PP_CENTERS)
        flat = {n: cv2.pyrMeanShiftFiltering(cv2.cvtColor(im, cv2.COLOR_RGB2BGR), 4, 12)[..., ::-1].copy() for n, im in self.raw.items()}
        return flat, centres

    def run(self, rule, keep, use_raw=True, skip_panels=()):
        flat, centres = self.palette(keep, use_raw, skip_panels)
        self.images = {k: lt.snap(flat[k], centres) for k in flat}
        pan = {k: lt.snap(v, centres) for k, v in self.panels.items()}
        W = lt.WORK
        page = np.zeros((W, W, 3), np.float32)
        filled = np.zeros((W, W), bool)
        kept = np.zeros((W, W), bool)
        for t in self.tris:
            co, n = np.array(t['co']), np.array(t['n'])
            uv = np.array(t['uv']) * [W, -W] + [0, W]
            r = lt.raster(uv, (W, W))
            if r is None:
                continue
            xs, ys, bary = r
            if t['part'] in keep:
                page[ys, xs] = self.base[ys, xs]
                kept[ys, xs] = True
                filled[ys, xs] = True
                continue
            pts = bary @ co
            hit = rule(self, t, pts, n)
            if hit is None:
                continue
            if hit[0] == 'project':
                colour, done = self.project(t, pts, n, hit[1])
                page[ys[done], xs[done]] = colour[done]
                filled[ys[done], xs[done]] = True
                continue
            if hit[0] == 'flat':
                page[ys, xs] = hit[1]
                filled[ys, xs] = True
                continue
            if hit[0] == 'colours':
                page[ys, xs] = hit[1]
                filled[ys, xs] = True
                continue
            name, u, v = hit
            img = pan[name]
            u = np.broadcast_to(np.clip(u, 0, 1), (len(xs),))
            v = np.broadcast_to(np.clip(v, 0, 1), (len(xs),))
            page[ys, xs] = img[(v * (img.shape[0] - 1)).astype(int), (u * (img.shape[1] - 1)).astype(int)]
            filled[ys, xs] = True
        page8 = page.clip(0, 255).astype(np.uint8)
        _, labels = cv2.distanceTransformWithLabels((~filled).astype(np.uint8), cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
        src = np.zeros((labels.max() + 1, 3), np.uint8)
        src[labels[filled]] = page8[filled]
        exact = src[labels].copy()
        page8 = lt.snap(src[labels], centres)
        page8[kept] = exact[kept]
        Image.fromarray(page8).save(SRC / f'dale_pagina_1024_{self.outfit}.png')
        lt.quantise(page8, centres).convert('RGB').save(SRC / f'dale_pagina_256_{self.outfit}.png')
        return page8


def base_of(part):
    return part.rsplit('_', 1)[0] if part[-2:] in ('_l', '_r') else part


def leg_uv(x, y, z, top, bottom):
    cx = 0.11 + (1.0 - np.clip(z, .2, 1.0)) * 0.15
    return .5 + (np.abs(x) - cx) / .3, (top - z) / (top - bottom)


def coronel_rule(P, t, p, n):
    part, b = t['part'], base_of(t['part'])
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    c = p.mean(0)
    side = abs(n[0]) > abs(n[1])
    if b in ('chest', 'coat'):
        if side and b == 'coat':
            return 'coat_side', (y + .22) / .5, (1.17 - z) / .4
        if abs(n[2]) > .6:                  # caps under/over the torso show through the coat opening
            return 'jacket_back', .3 + 0 * x, .3 + 0 * z
        if n[1] > .2:                       # the back: plain linen with the centre vent
            top = 1.72 if b == 'chest' else 1.17
            return 'jacket_back', (.25 - x) / .5, (1.72 - z) / (1.72 - .77)
        return ('project', False)
    if b == 'upper_arm':
        return ('sleeve_upper',) + P.wrap(part, p)
    if b == 'forearm':
        return ('sleeve_lower',) + P.wrap(part, p)
    if b in ('pelvis', 'thigh') or (b == 'shin' and c[2] > .50):
        u, v = leg_uv(x, y, z, 1.12, .50)
        if side:
            return 'pants_side', (y + .15) / .38, v
        return ('pants_front' if n[1] < 0 else 'pants_back'), (u if n[1] < 0 else 1 - u), v
    if b == 'shin':
        u, _ = P.wrap(part, p)
        return 'boot_shaft', u * .5 + (0 if n[1] < 0 else .5), (.50 - z) / .32
    if b == 'foot':
        if n[2] < -.5:
            return 'sole', (np.abs(x) - .105) / .295, (y + .245) / .465
        if side:
            return 'boot', .5 + .5 * (y + .245) / .465, (.25 - z) / .25
        return 'boot', .5 * (np.abs(x) - .105) / .295, (.25 - z) / .25
    if b == 'hat':
        if np.hypot(x, y - .045).max() < .14 and z.min() > 1.96:
            ang = np.arctan2(x, -(y - .045))
            v = (2.145 - z) / .17
            if c[2] < 2.01:
                return 'hat_band', (ang / np.pi) % 1.0, .5 + 0 * v
            return 'straw_crown', 0.5 + 0.5 * np.sin(ang), v * .4
        r = np.hypot(x, y - .045) / .3
        ang = np.arctan2(x, -(y - .045))
        half = 0 if n[2] > 0 else .5
        return 'straw_brim', half + .25 + .25 * r * np.sin(ang), .5 + .5 * r * np.cos(ang)
    return ('project', True)


TAG = {'x': (-.215, -.085), 'z': (.965, 1.07)}      # the "58" card pinned on the right hip


def physique_rule(P, t, p, n):
    part, b = t['part'], base_of(t['part'])
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    c = p.mean(0)
    side = abs(n[0]) > abs(n[1])
    if b == 'chest':
        if abs(n[0]) > max(abs(n[1]), .55):
            return 'torso_side', (y + .2) / .47 if n[0] < 0 else (.27 - y) / .47, (1.72 - z) / .54
        front = -n[1]
        return ('chest_front' if front > 0 else 'chest_back'), (x * np.sign(front) + .25) / .5, (1.72 - z) / .54
    if b in ('upper_arm', 'forearm'):
        return (b,) + P.wrap(part, p)
    if b == 'hand':
        u, v = P.wrap(part, p)
        return ('fist', u, v) if -n[1] > .3 else ('hands', u * .5, v)
    if b == 'pelvis' and -n[1] > .3 and TAG['x'][0] < c[0] < TAG['x'][1] and TAG['z'][0] < c[2] < TAG['z'][1]:
        return 'number', (x - TAG['x'][0]) / (TAG['x'][1] - TAG['x'][0]), (TAG['z'][1] - z) / (TAG['z'][1] - TAG['z'][0])
    if b in ('pelvis', 'thigh'):
        u, v = leg_uv(x, y, z, 1.12, .62)
        if side and b == 'thigh':
            return 'shorts_side', (y + .15) / .34, v
        return ('shorts_front' if n[1] < 0 else 'shorts_back'), (u if n[1] < 0 else 1 - u), v
    if b == 'belt':
        ang = np.arctan2(x, -(y - .02))
        return 'waistband', 0.5 + 0.5 * np.sin(ang), (1.195 - z) / .08 * .5
    if b == 'shin':
        u, v = P.wrap(part, p)
        return ('shin_front' if n[1] < 0 else 'shin_back'), u, v
    if b == 'foot':
        if n[2] < -.5:
            return 'sole', (np.abs(x) - .12) / .27, (y + .24) / .41
        return 'foot_top', (np.abs(x) - .12) / .27, (y + .24) / .41
    if b == 'mohawk':
        return 'mohawk', .25 + .2 * x / .04, (2.12 - z) / .15 * .5 + .25 * (y + .11) / .27
    if b == 'head':
        if t['face']:
            return ('flat', P.skin)
        # Clean-shaven with a skin fade: skin up to the ears (z 1.93), then the shaved sides and
        # nape blend from skin into short dark hair by the crown; the mohawk sits on top.
        k = np.clip((z - 2.00) / .06, 0, 1)[:, None]
        k = np.round(k * 3) / 3                                  # three hard bands, PS1 style
        return ('colours', P.skin * (1 - .75 * k) + P.hair * (.75 * k))
    return ('project', True)


# Bronze skin in three facet tones (lit / mid / shade), read off the concept's chest and arms.
# The face atlas's own three skin tones (dale_physique_rosto_atlas), so face and body match.
SKIN_TONES = np.array([[215, 112, 48], [185, 93, 38], [154, 75, 29]], np.float32)
SKIN_PARTS = {'chest', 'upper_arm_l', 'upper_arm_r', 'forearm_l', 'forearm_r', 'hand_l', 'hand_r',
              'shin_l', 'shin_r', 'foot_l', 'foot_r', 'ear_l', 'ear_r', 'neck'}


def physique_skin_tones(tris):
    """The panels' dark muscle shading lands on brown in a 15-colour page and reads as dirt: every
    skin texel becomes one of three orange tones by its brightness, so the facets stay and the
    brown is left to the mohawk."""
    path = SRC / 'dale_pagina_256_physique.png'
    page = np.array(Image.open(path).convert('RGB'))
    skin = part_mask(tris, SKIN_PARTS, 256)
    keep_out = part_mask(tris, {'mohawk', 'pelvis', 'thigh_l', 'thigh_r', 'belt'}, 256)
    skin &= ~keep_out
    d = page.astype(np.float32)
    # Smooth the brightness first: the panels' shading, reduced to 256, breaks into a mosaic of
    # little dark specks that read as dirt; whole facets read as muscle.
    lum = cv2.medianBlur(d.mean(2).astype(np.uint8), 5).astype(np.float32)
    m = skin                                         # skin parts hold nothing but skin
    lo, hi = np.percentile(lum[m], 3), np.percentile(lum[m], 22)
    tone = np.where(lum >= hi, 0, np.where(lum >= lo, 1, 2))
    # Limbs keep the panels' muscle lines (biceps, forearm, calf) in the mid / shade tones, read
    # off a wider blur and opened so only whole muscle shapes stay, no specks.
    limbs = part_mask(tris, SKIN_PARTS - {'chest'}, 256) & ~part_mask(tris, {'chest'}, 256)
    llum = cv2.medianBlur(d.mean(2).astype(np.uint8), 7).astype(np.float32)
    l1, l2 = np.percentile(llum[limbs], 12), np.percentile(llum[limbs], 32)
    ltone = np.where(llum >= l2, 0, np.where(llum >= l1, 1, 2)).astype(np.uint8)
    for k in (1, 2):                                  # drop shade islands smaller than a muscle
        blob = cv2.morphologyEx((ltone >= k).astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)).astype(bool)
        ltone[(ltone >= k) & ~blob] = k - 1
    tone[limbs] = ltone[limbs]
    page[m] = SKIN_TONES[tone[m]].astype(np.uint8)
    # Head skin (painted flat by the rule) in the same lit tone as the face atlas.
    head = part_mask(tris, {'head'}, 256)
    hd = page.astype(int)
    orange = head & (hd[..., 0] > 170) & (hd[..., 0] - hd[..., 2] > 100)
    page[orange] = SKIN_TONES[0].astype(np.uint8)
    # Back of the chest: the concept's lat / trapezius V reads in the mid tone.
    back = np.zeros_like(m)
    for t in tris:
        if t['part'] == 'chest' and t['n'][1] > .5:
            uv = np.array(t['uv']) * [256, -256] + [0, 256]
            r = lt.raster(uv, (256, 256))
            if r is not None:
                back[r[1], r[0]] = True
    crease = back & (lum < np.percentile(lum[m], 45))
    page[crease] = SKIN_TONES[1].astype(np.uint8)
    # Shorts: two clean blacks (the panels' fold noise breaks up into specks at 256).
    shorts = part_mask(tris, {'pelvis', 'thigh_l', 'thigh_r'}, 256) & (d.max(2) < 90)
    slum = cv2.medianBlur(d.mean(2).astype(np.uint8), 5).astype(np.float32)
    page[shorts] = np.where((slum[shorts] > np.percentile(slum[shorts], 60))[:, None], [52, 49, 50], [32, 30, 31]).astype(np.uint8)
    number_card(page, tris)
    Image.fromarray(page).save(path)


# "58" as pixel art (3x5 digits): the card has ~16 px on the page, too few to sample the
# panel's lettering, so the digits are drawn straight onto its texels.
CARD_X, CARD_Z = (-.216, -.084), (.90, 1.12)       # the whole right-hip front facet
DIGITS = {'5': ['###', '#..', '###', '..#', '###'], '8': ['###', '#.#', '###', '#.#', '###']}


def number_card(page, tris):
    # The card facet has 16 texels across (x) and 8 up (z): digits 3x5 doubled in width.
    card = np.ones((8, 16), bool)                     # True = white card, False = ink
    for i, ch in enumerate('58'):
        for r, row in enumerate(DIGITS[ch]):
            for c, px in enumerate(row):
                if px == '#':
                    x = 1 + 8 * i + 2 * c
                    card[1 + r, x:x + 2] = False
    x0, x1 = TAG['x']; z0, z1 = TAG['z']
    for t in tris:
        co = np.array(t['co']); c = co.mean(0)
        if t['part'] != 'pelvis' or -t['n'][1] <= .3 or not (x0 < c[0] < x1 and z0 < c[2] < z1):
            continue
        uv = np.array(t['uv']) * [256, -256] + [0, 256]
        r = lt.raster(uv, (256, 256))
        if r is None:
            continue
        px, py = r[0] + .5, r[1] + .5
        a, b, cc = uv
        den = (b[1] - cc[1]) * (a[0] - cc[0]) + (cc[0] - b[0]) * (a[1] - cc[1])
        w0 = ((b[1] - cc[1]) * (px - cc[0]) + (cc[0] - b[0]) * (py - cc[1])) / den
        w1 = ((cc[1] - a[1]) * (px - cc[0]) + (a[0] - cc[0]) * (py - cc[1])) / den
        w2 = 1 - w0 - w1
        p3 = w0[:, None] * co[0] + w1[:, None] * co[1] + w2[:, None] * co[2]
        u = np.clip(((p3[:, 0] - CARD_X[0]) / (CARD_X[1] - CARD_X[0]) * 16).astype(int), 0, 15)
        v = np.clip(((CARD_Z[1] - p3[:, 2]) / (CARD_Z[1] - CARD_Z[0]) * 8).astype(int), 0, 7)
        page[r[1], r[0]] = np.where(card[v, u][:, None], [236, 232, 224], [24, 22, 24]).astype(np.uint8)


def physique_head_fix(page, tris, skin, size):
    """No beard: on the head below the cheekbones, dark brown becomes skin."""
    head = part_mask([t for t in tris if t['part'] == 'head' and np.mean([c[2] for c in t['co']]) < 1.95], {'head'}, size)
    d = page.astype(int)
    brown = (d[..., 0] < 150) & (d[..., 0] > d[..., 2]) & (d.sum(2) < 330)
    page[head & brown] = skin
    return page


def main(which):
    if which == 'preto':
        preto()
        return
    if which == 'faces':
        dt.face_atlas(lt.ROOT / 'concept-art/characters/dale/dale-sem-barba-expressoes-24-psx-v1.png',
                      SRC / 'dale_physique_rosto_atlas.png')
        return
    P = Painter(which)
    if which == 'coronel':
        page = P.run(coronel_rule, keep={'head', 'ear_l', 'ear_r', 'neck', 'hand_l', 'hand_r'})
    else:
        fx, fy = lt.to_px(P.raw['frente'], 0.05, 1.38)         # the chest's lit skin (207, 116, 61)
        P.skin = P.raw['frente'][int(fy), int(fx)].astype(np.float32)
        hx, hy = lt.to_px(P.raw['costas'], 0.0, 2.06)              # the mohawk's brown, back view
        P.hair = P.raw['costas'][int(hy), int(hx)].astype(np.float32)
        page = P.run(physique_rule, keep=set(), use_raw=False, skip_panels={'head_side'})
        physique_skin_tones(P.tris)



if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'preto')
