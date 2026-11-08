"""Orsted, mad scientist outfit (fighter id `volt`): the pieces, on the base's joints and scale.

Concept: concept-art/characters/orsted/orsted-cientista-maluco-turnaround-psx-v1.png (17 texture
panels in orsted-cientista-maluco-texturas-17-paineis-psx-v1.png). Base pieces repainted: the head
(his spiky hair reads as the static-blown one), the shirt trunk = the lab coat's top open over the
turtleneck and the chest battery (painted), the neck, the belt, the sleeves (rolled white coat), the
arms (forearm = long black rubber glove), the fists, the grey trousers, the rubber boots, the back
tank = the tesla coil backpack with its straps, the energy hand cannon. New pieces:
    - the long lab coat's skirt from the belt to the knees (its hem on the cloth bones);
    - the turtleneck's rolled collar;
    - the brass welding goggles pushed up over the fringe (strap and two cyan lenses);
    - the brass ball on top of the coil and its cyan spark;
and the hair blown up by static: the base head's hair-only vertices pushed out (sides and back
x1.3, up x1.25 above the crown's middle, the fringe barely), the face untouched.
"""
import numpy as np

import legends_kit as lk
import orsted_arma
import orsted_braco
import orsted_cabeca
import orsted_perna
import orsted_pistoleiro
import orsted_tronco

TRONCO = ('chest', 'belly', 'pelvis', 'neck', 'belt', 'cell', 'cell_cap_top', 'cell_cap_bottom', 'cell_strap0', 'cell_strap1')
BRACO = ('sleeve_l', 'sleeve_cuff_l', 'upper_arm_l', 'forearm_l', 'bracer_l', 'hand_l')
PERNA = ('thigh_l', 'shin_l', 'boot_shaft_l', 'boot_l')

# lab coat skirt: from under the belt to the knees, flaring, open in front (two flaps, as the
# gunslinger's duster: orsted_pistoleiro.flap)
SKIRT = [
    (1.060, [(.060, -.128), (.150, -.118), (.182, .0), (.150, .118), (.004, .126)]),
    (0.800, [(.080, -.142), (.176, -.132), (.240, .0), (.176, .140), (.004, .150)]),
    (0.500, [(.100, -.156), (.200, -.146), (.272, .0), (.200, .156), (.004, .166)]),
]
COLLAR = [(1.545, .062, .064), (1.480, .074, .076)]
# goggles over the fringe (head joint column y -0.07; the fringe's front at z 1.80 ~ y -0.20)
GOGGLE_STRAP = ((0.0, -0.065), [(1.820, .150, .150), (1.790, .150, .150)])
LENS_L = ((0.058, -0.228, 1.805), 0.034)      # his left lens; the right one is its mirror
COIL_BALL = ((0.0, 0.195), [(1.540, .010, .010), (1.522, .024, .024), (1.500, .012, .012)])
COIL_SPARK = ((0.0, 0.195, 1.585), 0.030)          # a flat 5-point flash over the ball (panel 15)
FRIZZ_C = np.array([0.0, 0.04, 1.70])


def frizz(v):
    """Static-blown hair: a hair-only vertex pushed out from the crown's middle."""
    d = np.asarray(v, float) - FRIZZ_C
    d[0] *= 1.3
    d[1] *= 1.3 if d[1] > 0 else 1.1
    if d[2] > 0:
        d[2] *= 1.25
    return FRIZZ_C + d


def frizzy_head(head):
    tones = head['ftone']
    hair = {i for f, t in zip(head['f'], tones) if t.startswith('hair') for i in f}
    skin = {i for f, t in zip(head['f'], tones) if not t.startswith('hair') for i in f}
    V = [list(frizz(v)) if i in hair - skin else v for i, v in enumerate(head['v'])]
    return {**head, 'v': V}, {tuple(np.round(head['v'][i], 4)) for i in hair - skin}


def parts():
    out = {k: v for k, v in orsted_cabeca.parts().items()}
    out['head'], _ = frizzy_head(out['head'])
    t, b, p = orsted_tronco.parts(), orsted_braco.parts(), orsted_perna.parts()
    out.update({k: t[k] for k in TRONCO})
    out.update({k: b[k] for k in BRACO})
    out.update({k: p[k] for k in PERNA})
    out.update(orsted_arma.parts())
    P, F = orsted_pistoleiro.flap(SKIRT)
    out['coat_skirt_l'] = lk.part(P, F, 'hips', 'coat')
    P, F = lk.prism(COLLAR, 8)
    out['collar'] = lk.part(P, F, 'neck', 'rubber')
    (cx, cy), levels = GOGGLE_STRAP
    P, F = lk.prism(levels, 8, centre=(cx, cy))
    out['goggle_strap'] = lk.part(P, F, 'head', 'leather')
    (x, y, z), r = LENS_L
    P, F = lk.loft([lk.ring((x, y + dy, z), lk.X, np.array([0, 0, 1.0]), r, r, 8, flat_front=False)
                    for dy in (.012, -.014)])
    out['lens_l'] = lk.part(P, lk.orient(P, F), 'head', 'brass')
    (cx, cy), levels = COIL_BALL
    P, F = lk.prism(levels, 6, centre=(cx, cy))
    out['coil_ball'] = lk.part(P, F, 'chest', 'brass')
    (sx, sy, sz), r = COIL_SPARK
    P, F = lk.loft([lk.ring((sx, sy + dy, sz), lk.X, np.array([0, 0, 1.0]), r, r, 5, flat_front=False) for dy in (-.003, .003)])
    out['coil_spark'] = lk.part(P, F, 'chest', 'glass')
    return out


# the head's declared asymmetric vertices, moved like the hair they belong to
_moved = frizzy_head(orsted_cabeca.parts()['head'])[1]
ASYMMETRIC = {k: [tuple(np.round(frizz(v), 4)) if tuple(np.round(v, 4)) in _moved else v for v in vs]
              for k, vs in orsted_cabeca.ASYMMETRIC.items()}
ASYMMETRIC.update(orsted_arma.ASYMMETRIC)
