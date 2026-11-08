"""Orsted's trunk (fighter id `volt`), by hand on the Legends references: the shirt (chest and
belly), the trouser top (pelvis), the neck, the belt with two front pouches, the chest plate with
the energy core, the energy cell on his back, the torn mustard cloth hanging in front and the red
rag at the back.

Like Mega Man's and X12's torso: 8-sided sections (front centre, front corner, side, back corner,
back centre per half), caps as strips. Measured on his crops (orsted_frente / perfil, MPP 1.86/840;
front is -y, his left is +x): shoulders +-0.20 at z 1.45, chest +-0.165 at 1.33, waist +-0.135 at
1.20, belt z 1.04-1.11, the baggy trouser top +-0.18 at 0.95 and the crotch at 0.80; the chest
from y -0.115 to +0.105; the plate z 1.27-1.45 out to y -0.13; the cell centred at y +0.19,
z 1.17-1.45.
"""
import numpy as np

import legends_kit as lk

Z = np.array([0.0, 0.0, 1.0])

CHEST = [
    (1.505, [(0, -.060), (.050, -.055), (.075, .0), (.050, .060), (0, .070)]),      # collar round the neck
    (1.455, [(0, -.095), (.130, -.080), (.200, .0), (.130, .085), (0, .100)]),      # shoulder line
    (1.330, [(0, -.115), (.120, -.100), (.165, .0), (.120, .092), (0, .105)]),      # chest, widest
    (1.200, [(0, -.100), (.100, -.090), (.137, .0), (.100, .085), (0, .095)]),      # lower chest
]
BELLY = [
    (1.215, [(0, -.096), (.098, -.086), (.132, .0), (.098, .080), (0, .090)]),
    (1.095, [(0, -.096), (.104, -.086), (.140, .0), (.104, .080), (0, .090)]),
]
PELVIS = [
    (1.120, [(0, -.100), (.110, -.090), (.150, .0), (.110, .086), (0, .095)]),
    (0.950, [(0, -.118), (.140, -.108), (.195, .0), (.140, .105), (0, .115)]),     # baggy trouser top (front crop +-.23 with the pockets)
    (0.850, [(0, -.110), (.140, -.110), (.205, .0), (.140, .112), (0, .110)]),     # crotch line: wide enough to hold the thigh tops
]
NECK = [(1.470, .045, .048), (1.590, .045, .048)]
BELT = ((0.0, -.004), [(1.112, .158, .110), (1.040, .162, .114)])
POUCH_L = ((.150, -.085), (1.110, 1.010), (.040, .030))                        # front pouch (front crop x .10-.20)
PLATE = ((0.0, -.118, 1.360), (.120, .090), (-.142, -.112))                     # centre, half width/height, front/back y
# energy tank on the back, in 3D (concept z 1.17-1.50, y +.14..+.25, x +-.065): a glass body,
# bigger dark metal caps top and bottom and two leather straps round it
CELL_C = (0.0, .195)
CELL = [(1.440, .052, .050), (1.205, .052, .050)]
CELL_CAPS = ([(1.495, .045, .044), (1.480, .064, .060), (1.440, .064, .060)],
             [(1.205, .064, .060), (1.165, .064, .060), (1.150, .045, .044)])
CELL_STRAPS = [(1.395, 1.370), (1.275, 1.250)]
# the chest core: a round housing standing out of the plate (concept: the ring glows cyan)
CORE = ((0.0, 1.380), [(-.140, .052), (-.160, .052), (-.172, .036)])
TABARD = ((0.0, -.112), (1.060, 0.700), (.050, .010))                          # torn mustard cloth, front
RAG = ((0.0, .108), (1.060, 0.760), (.045, .008))                              # red rag, back


def box(centre, z, half, n=4):
    (cx, cy), (z1, z0), (hx, hy) = centre, z, half
    return lk.prism([(z1, hx, hy), (z0, hx, hy)], n, centre=(cx, cy))


def plate():
    """A hexagonal plate standing on the chest: two hexagon rings (front and back face) in the
    x/z plane, joined; caps as strips."""
    (cx, cy, cz), (hw, hh), (yf, yb) = PLATE
    rings = [lk.ring((cx, y, cz), lk.X, Z, hw, hh, 6, flat_front=False) for y in (yf, yb)]
    return lk.loft(rings)


def parts():
    out = {}
    P, F, _ = lk.loft_sym(CHEST)
    out['chest'] = lk.part(P, F, 'chest', 'shirt')
    P, F, _ = lk.loft_sym(BELLY)
    out['belly'] = lk.part(P, F, 'spine', 'shirt')
    P, F, _ = lk.loft_sym(PELVIS)
    out['pelvis'] = lk.part(P, F, 'hips', 'trousers')
    P, F = lk.prism(NECK)
    out['neck'] = lk.part(P, F, 'neck', 'skin')
    (cx, cy), levels = BELT
    P, F = lk.prism(levels, 8, centre=(cx, cy))
    out['belt'] = lk.part(P, F, 'hips', 'leather')
    P, F = box(*POUCH_L)
    out['pouch_l'] = lk.part(P, F, 'hips', 'leather')
    P, F = plate()
    out['chest_plate'] = lk.part(P, F, 'chest', 'plate')
    P, F = lk.prism(CELL, 8, centre=CELL_C)
    out['cell'] = lk.part(P, F, 'chest', 'glass')
    for name, levels in zip(('cell_cap_top', 'cell_cap_bottom'), CELL_CAPS):
        P, F = lk.prism(levels, 8, centre=CELL_C)
        out[name] = lk.part(P, F, 'chest', 'metal')
    for k, (z1, z0) in enumerate(CELL_STRAPS):
        P, F = lk.prism([(z1, .058, .056), (z0, .058, .056)], 8, centre=CELL_C)
        out[f'cell_strap{k}'] = lk.part(P, F, 'chest', 'leather')
    (cx, cz), rings = CORE
    P, F = lk.loft([lk.ring((cx, y, cz), lk.X, Z, r, r, 8) for y, r in rings])
    out['core'] = lk.part(P, F, 'chest', 'glass')
    P, F = box(*TABARD)
    out['tabard'] = lk.part(P, F, 'hips', 'cloth')
    P, F = box(*RAG)
    out['rag'] = lk.part(P, F, 'hips', 'rag')
    return out
