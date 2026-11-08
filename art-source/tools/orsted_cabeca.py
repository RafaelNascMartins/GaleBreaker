"""Orsted's head (fighter id `volt`), by hand on the Legends references.

Built on X12's approved head (x12_cabeca: Mega Man topology, 7-vertex centre line, a 3-face eye
band, the nose tip out, mouth and chin going back, the ear a small plate), brought to Orsted's
measurements on his crops (orsted_frente / perfil / costas, MPP 1.86/840: his height with the hair
spikes; front is -y, his left is +x):
    chin z 1.555 y -0.05, nose tip z 1.625 y -0.074, brows z 1.695, face half width 0.075 at the
    eyes, ears x +-0.095 at z 1.62-1.665, skull under the spikes at about z 1.78.
Her asymmetric fringe is replaced by a short symmetric hair edge on the forehead, and his spiky
hair is added as blades: each spike is a tip over one face of the hair shell (a face per edge of
the base round the tip: 3 or 4, no pole), placed on the drawn tips. Blond on top, dark brown underneath: the
painting splits them.
"""
import numpy as np

import legends_kit as lk
import x12_cabeca as x

SCALE = 0.85                     # his face against hers (eye band half width 0.085 -> 0.072)
# the Legends head is big against the body (user 2026-11-07: "muito pequena"): the whole head
# grows 25 % from under the chin, about 20 % of his height with the spikes (X12 19 %)
GROW, GROW_PIVOT = 1.25, np.array([0.0, 0.0, 1.530])
# Mega Man's hair is long thick blades: the spike tips reach further out from the skull
BLADE, BLADE_CENTRE = 1.00, np.array([0.0, 0.040, 1.680])
SHADE_BELOW = -0.45              # skin faces facing well down (jaw underside, under the chin) are shade; the chin front stays light
CHIN_Z, X12_CHIN_Z = 1.555, 1.472
CROWN_FROM, CROWN_SQUASH = 1.700, 0.85   # the skull top a little lower (0.6 read flat on top: user 2026-11-07)
BACK = 0.040                     # his head sits further back on the neck (profile: nose tip y -0.074, chin -0.05)
SPIKE_BACK = 0.030


def place(p):
    px, py, pz = p
    z = CHIN_Z + (pz - X12_CHIN_Z) * SCALE
    if z > CROWN_FROM:
        z = CROWN_FROM + (z - CROWN_FROM) * CROWN_SQUASH
    return (px * SCALE, py * SCALE + BACK, round(z, 4))


V = {k: place(p) for k, p in x.V.items()}
# Mega Man's way: the hair shell's own outline vertices are pulled out to the drawn spike tips,
# so every spike has a wide base (the faces round it), not a needle on a dome. Measured on the
# crops at the drawing's scale (the head grows afterwards); front is -y, his left +x.
HAIR_TIPS = {
    # a spike shows only between notches: each ring alternates out (tip) and in (notch), and the
    # upper ring is turned against the lower one, so the spikes stack in two layers as drawn
    'T0': (0.0, 0.000, 1.815),       # crown (the two tall top spikes stand on it)
    'A0': (0.0, -0.105, 1.790),      # notch
    'A1': (0.115, -0.125, 1.800),    # upper front-corner spike, forward and out
    'A2': (0.095, 0.020, 1.795),     # notch
    'A3': (0.135, 0.165, 1.790),     # upper back-corner spike
    'A4': (0.0, 0.110, 1.795),       # notch
    'B0': (0.0, -0.195, 1.735),      # the forward point over the brow (profile y -.20 at 1.73)
    'B1': (0.075, -0.120, 1.715),    # notch
    'B2': (0.172, 0.020, 1.715),     # the big side spikes (x +-.17, z 1.71)
    'B3': (0.100, 0.130, 1.705),     # notch
    'B4': (0.0, 0.210, 1.720),       # back point (profile y +.20 at 1.71)
    'BK': (0.120, 0.150, 1.625),     # dark brown spikes low at the back
    'NE': (0.140, 0.060, 1.640),     # dark brown side spikes over the ears
}
for _k, _p in HAIR_TIPS.items():
    V[_k] = (_p[0], _p[1] + BACK, _p[2])

# the forehead hair edge: a short symmetric fringe (the concept's bangs are spikes, added below)
V['FR'] = place((0.040, -0.150, 1.690))
F_LEFT = list(x.F_LEFT) + [
    ('B0', 'B1', 'FR'), ('B1', 'N2', 'FR'), ('FR', 'N2', 'E1'), ('FR', 'E1', 'FH'), ('B0', 'FR', 'FH'),
]

# spikes: tip (absolute, measured on the crops) -> the shell face it grows from (names, her
# x12 vertex names; "'" = his right side). Asymmetric on purpose, like the drawing.
SPIKES = {
    # extra points on top of the shell, asymmetric like the drawing
    'K1': ((-0.060, -0.030, 1.860), ('T0', "A1'", "A2'")),     # the tallest, his right
    'K2': ((0.030, 0.010, 1.850), ('A1', 'B1', 'B2', 'A2')),   # second top spike
    # the lock falling over his left eye (front crop: from z 1.79 down to 1.67 at x +.02)
    'F2': ((0.030, -0.160, 1.660), ('B1', 'N2', 'FR')),
    # nape: dark brown points hanging down (back view z 1.56-1.60)
    'N1': ((-0.075, 0.150, 1.565), ("BL'", "BK'", "NP1'")),
    'N2': ((0.070, 0.150, 1.560), ('BL', 'BK', 'NP1')),
}


def parts():
    P, F, names = lk.named(V, F_LEFT)
    idx = {n: i for i, n in enumerate(names)}
    P = list(map(tuple, P))
    F = [list(f) for f in F]
    tone = ['hair' if 2 * sum(names[i].rstrip("'") in HAIR for i in f) > len(f) else 'skin' for f in F]
    for tip_name, (tip, base) in SPIKES.items():
        tip = BLADE_CENTRE + (np.array((tip[0], tip[1] + SPIKE_BACK, tip[2])) - BLADE_CENTRE) * BLADE
        tip = tuple(tip)
        b = [idx[n] for n in base]
        # the shell face holding these three corners (any order of its corners)
        hit = next(fi for fi, f in enumerate(F) if set(f) == set(b))
        ring = F.pop(hit)
        tone.pop(hit)
        t = len(P)
        P.append(tip)
        names.append(tip_name)
        for k in range(len(ring)):                       # one face per edge of the base, round the tip
            F.append([ring[k], ring[(k + 1) % len(ring)], t])
            tone.append('hair')
    P = np.array(P, float)
    P = GROW_PIVOT + (P - GROW_PIVOT) * GROW
    F = lk.orient(P, F)
    # hair in flat blocks like Mega Man's: blond on top (lighter where the blade faces up), dark
    # brown underneath at the sides and back (concept: below z 1.68 before the head grows)
    dark_below = GROW_PIVOT[2] + (1.680 - GROW_PIVOT[2]) * GROW
    for fi, f in enumerate(F):
        if tone[fi] != 'hair':
            continue
        q = P[f]
        n = np.cross(q[1] - q[0], q[2] - q[0])
        n /= np.linalg.norm(n) + 1e-9
        c = q.mean(0)
        if c[2] < dark_below and c[1] > -0.06:
            tone[fi] = 'hair_dark'
        elif n[2] > 0.55:
            tone[fi] = 'hair_hi'
    # jaw painted apart like Mega Man's: skin faces under the jaw and the chin take the shade tone,
    # the jaw's sides (facing out and down behind the cheek) too
    for fi, f in enumerate(F):
        if tone[fi] != 'skin':
            continue
        q = P[f]
        n = np.cross(q[1] - q[0], q[2] - q[0])
        n /= np.linalg.norm(n) + 1e-9
        if n[2] < SHADE_BELOW or (abs(n[0]) > 0.6 and n[2] < 0.05 and q[:, 2].mean() < GROW_PIVOT[2] + 0.06):
            tone[fi] = 'shade'
    return {'head': lk.part(P, F, 'head', ftone=tone)}


HAIR = (x.HAIR - set(x.V_FRINGE)) | {'FR'} | set(SPIKES)
ASYMMETRIC = {'head': [tuple(np.round(GROW_PIVOT + (BLADE_CENTRE + (np.array((t[0], t[1] + SPIKE_BACK, t[2])) - BLADE_CENTRE) * BLADE
                                                    - GROW_PIVOT) * GROW, 4)) for t, _ in SPIKES.values()]}
