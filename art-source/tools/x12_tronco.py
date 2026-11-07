"""X12's trunk, modelled by hand on the Legends references (docs/estudos/legends-modelagem.md):
chest, collar (with its studded band) and neck.

Like Mega Man's torso: a block of 8-sided sections (front centre, front corner, side, back
corner, back centre per half), no more rings than the silhouette needs, caps closed as strips
(no fan). Left half listed, mirrored; centre vertices at x = 0. Measured on the concept crops
(front: half widths per row; profile: front and back per row; back view: the back plate).
"""
import legends_kit as lk

# a section: z and the left half (x, y) of front centre, front corner, side, back corner, back centre
CHEST = [
    (1.395, [(0, -0.135), (0.095, -0.115), (0.125, 0.0), (0.095, 0.100), (0, 0.115)]),   # under the collar band
    (1.265, [(0, -0.205), (0.115, -0.165), (0.150, -0.010), (0.120, 0.120), (0, 0.140)]),  # pectorals, widest
    (1.185, [(0, -0.165), (0.085, -0.140), (0.105, -0.010), (0.085, 0.100), (0, 0.120)]),  # lower chest
    (1.130, [(0, -0.135), (0.075, -0.115), (0.095, 0.000), (0.075, 0.090), (0, 0.100)]),   # waist plate
]
CHEST_Z = {(2, 0): 1.170}          # the lower chest comes to a point at the centre (front view V)

COLLAR = [
    (1.462, [(0, -0.125), (0.095, -0.095), (0.127, 0.0), (0.095, 0.100), (0, 0.130)]),   # top rim
    (1.405, [(0, -0.117), (0.088, -0.088), (0.118, 0.0), (0.088, 0.093), (0, 0.121)]),   # bottom of the stone
    (1.405, [(0, -0.128), (0.096, -0.098), (0.128, 0.0), (0.096, 0.102), (0, 0.132)]),   # studded band, out
    (1.378, [(0, -0.128), (0.096, -0.098), (0.128, 0.0), (0.096, 0.102), (0, 0.132)]),
]
COLLAR_METAL = (1, 2)             # bands (between section k and k+1) painted metal

NECK = [(1.380, 0.040, 0.044), (1.500, 0.040, 0.044)]   # z, half width, half depth (6 sides)


def parts():
    P, F, _ = lk.loft_sym(CHEST, CHEST_Z)
    out = {'chest': lk.part(P, F, 'chest')}
    P, F, band = lk.loft_sym(COLLAR)
    out['collar'] = lk.part(P, F, 'chest', ftone=['metal' if b in COLLAR_METAL or b == len(COLLAR) else 'stone'
                                                for b in band])
    P, F = lk.prism(NECK)
    out['neck'] = lk.part(P, F, 'neck', 'skin')
    return out
