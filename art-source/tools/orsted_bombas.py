"""Orsted's thrown bombs (fighter id `volt`), by hand on their 3-view sheets: the low-J bomb thrown
at the enemy's feet.

- Hi-tech bomb (default outfit; concept-art/characters/orsted/orsted-bomba-azul-3-vistas-psx-v1.png):
  a chunky faceted slate bomb about 15 cm tall, egg-shaped (fuller at the bottom), the big blue gem
  standing out of its front, three small blue orbs on copper brackets round the gem's edge, a
  riveted copper collar under a loop handle, a lug on its upper shoulder and a small blue gem in
  copper clamps on its back.
- Dynamite (gunslinger outfit; orsted-dinamite-3-vistas-psx-v1.png): a red 8-sided stick about 18 cm
  long with a grey cap, a curved three-segment fuse and the star-shaped spark.
Props, not body parts: legends_rig builds each as its own object on the left hand bone (PROPS in
the character module), shown only while a clip throws it. Held in his left fist (A-pose).
"""
import numpy as np

import legends_kit as lk

Z = np.array([0.0, 0.0, 1.0])
Y = np.array([0.0, 1.0, 0.0])
FIST_L = np.array([0.389, 0.030, 0.967])     # middle of his left fist (A-pose)
BONE = 'hand_l'

# ---- hi-tech bomb, centred beside the fist (palm side) ----
BOMB_C = FIST_L + np.array([-0.075, 0.0, -0.010])
BOMB_RINGS = [(-0.070, 0.040), (-0.050, 0.064), (-0.010, 0.072), (0.030, 0.062), (0.052, 0.044), (0.062, 0.030)]
BOMB_DEPTH = 0.85                                     # a little flatter front to back
GEM = ((-0.008, -0.004), [(-0.054, 0.042), (-0.068, 0.042), (-0.080, 0.028)])   # (x, z) offset, (y, radius) rings
ORBS = [(0.050, -0.046, 0.030), (0.058, -0.040, -0.002), (0.048, -0.046, -0.036)]
COLLAR = [(0.052, 0.047), (0.064, 0.047)]
HANDLE = [((-0.022, 0.0, 0.080), (0.007, 0.010, 0.018)), ((0.022, 0.0, 0.080), (0.007, 0.010, 0.018)),
          ((0.0, 0.0, 0.100), (0.029, 0.010, 0.007))]
LUG = ((-0.052, 0.0, 0.050), (0.016, 0.022, 0.018))
BACK_GEM = ((0.0, 0.060, -0.004), (0.022, 0.008, 0.009))

# ---- dynamite, upright in the fist ----
STICK_C = FIST_L + np.array([-0.030, 0.0, 0.0])
STICK = [(-0.090, 0.020), (-0.084, 0.024), (0.060, 0.024)]
CAP = [(0.060, 0.026), (0.078, 0.026), (0.084, 0.020)]
FUSE = [(0.0, 0.0, 0.084), (0.002, 0.0, 0.104), (0.010, 0.0, 0.122), (0.026, 0.0, 0.134)]
SPARK_C = (0.032, 0.0, 0.140)


def _ring_y(c, rx, rz, n):
    return lk.ring(c, lk.X, Z, rx, rz, n)


def _box(c, h):
    (cx, cy, cz), (hx, hy, hz) = c, h
    P, F = lk.prism([(cz + hz, hx, hy), (cz - hz, hx, hy)], 4, centre=(cx, cy))
    return P, F


def parts():
    out = {}
    # bomb body: 8-sided rings up the egg
    rings = [lk.ring(BOMB_C + [0, 0, dz], lk.X, lk.FRONT, r, r * BOMB_DEPTH, 8) for dz, r in BOMB_RINGS]
    P, F = lk.loft(rings)
    out['bomb_body'] = lk.part(P, F, BONE, 'slate')
    (gx, gz), gem = GEM
    P, F = lk.loft([_ring_y(BOMB_C + [gx, y, gz], r, r, 8) for y, r in gem])
    out['bomb_gem'] = lk.part(P, F, BONE, 'glass')
    for k, o in enumerate(ORBS):
        c = BOMB_C + np.array(o)
        P, F = lk.loft([lk.ring(c + [0, 0, dz], lk.X, lk.FRONT, r, r, 6) for dz, r in ((.011, .006), (0, .012), (-.011, .006))])
        out[f'bomb_orb{k}'] = lk.part(P, F, BONE, 'glass')
    P, F = lk.prism([(z, r, r * BOMB_DEPTH) for z, r in COLLAR[::-1]], 8, centre=(BOMB_C[0], BOMB_C[1]))
    P[:, 2] += BOMB_C[2]
    out['bomb_collar'] = lk.part(P, F, BONE, 'copper')
    for k, (c, h) in enumerate(HANDLE):
        P, F = _box(BOMB_C + np.array(c), h)
        out[f'bomb_handle{k}'] = lk.part(P, F, BONE, 'slate')
    P, F = _box(BOMB_C + np.array(LUG[0]), LUG[1])
    out['bomb_lug'] = lk.part(P, F, BONE, 'slate')
    P, F = _box(BOMB_C + np.array(BACK_GEM[0]), BACK_GEM[1])
    out['bomb_back_gem'] = lk.part(P, F, BONE, 'glass')
    # dynamite
    P, F = lk.prism([(z, r, r) for z, r in STICK[::-1]], 8, centre=(STICK_C[0], STICK_C[1]))
    P[:, 2] += STICK_C[2]
    out['dynamite_stick'] = lk.part(P, F, BONE, 'dynamite')
    P, F = lk.prism([(z, r, r) for z, r in CAP[::-1]], 8, centre=(STICK_C[0], STICK_C[1]))
    P[:, 2] += STICK_C[2]
    out['dynamite_cap'] = lk.part(P, F, BONE, 'cap')
    P, F = lk.loft([lk.ring(STICK_C + np.array(c), lk.X, lk.FRONT, .005, .005, 4) for c in FUSE])
    out['dynamite_fuse'] = lk.part(P, F, BONE, 'fuse')
    c = STICK_C + np.array(SPARK_C)
    P, F = lk.loft([lk.ring(c + [0, y, 0], lk.X, Z, .016, .016, 5, flat_front=False) for y in (-.003, .003)])
    out['dynamite_spark'] = lk.part(P, F, BONE, 'spark')
    return out


# the props sit in his left hand only: legends_build leaves them out of the symmetry check
ASYMMETRIC = {n: [tuple(v) for v in np.round(p['v'], 4)] for n, p in parts().items()}
