"""X12's skirt, legs and boots, modelled by hand on the Legends references
(docs/estudos/legends-modelagem.md).

Mega Man / Tifa legs: straight prisms (thigh, shin), a band at the ankle and a big block for
the foot. The skirt is one flared 8-sided piece like the chest (its overlapping plates are
painted). Left leg listed, right is the mirror. Sizes from the drawn outlines (front and
profile crops, per height).
"""
import legends_kit as lk

# skirt: z and left-half (x, y) of front centre, front corner, side, back corner, back centre
SKIRT = [
    (1.140, [(0, -0.140), (0.100, -0.120), (0.130, 0.0), (0.100, 0.115), (0, 0.130)]),   # waist, under the chest
    (0.990, [(0, -0.190), (0.180, -0.165), (0.240, -0.010), (0.180, 0.140), (0, 0.155)]),
    (0.790, [(0, -0.240), (0.220, -0.210), (0.285, -0.020), (0.220, 0.165), (0, 0.185)]),  # hem
]
SKIRT_Z = {(2, 0): 0.745, (2, 4): 0.760}   # front and back plates come down to a point (V)

# leg parts: (centre x, centre y, z) per section, half width x, half depth y; n sides; vertical
LEG = {
    # thigh leans out ~10 deg (A stance): hip centre x 0.115, knee x 0.160 (lines up with the shin)
    'thigh_l': ([(0.115, 0.0, 0.860, 0.080, 0.125), (0.160, 0.0, 0.600, 0.080, 0.125)], 6, 'thigh_l'),
    'shin_l': ([(0.160, -0.010, 0.640, 0.085, 0.120),        # knee, inside the thigh
                (0.175, -0.005, 0.500, 0.112, 0.135),        # widest calf / shin plate
                (0.205, 0.000, 0.290, 0.092, 0.115)], 6, 'shin_l'),
    'ankle_cuff_l': ([(0.225, 0.000, 0.312, 0.112, 0.132), (0.225, 0.000, 0.215, 0.112, 0.132)], 8, 'shin_l'),
}
# boot: sections along the foot (y forward is -), (centre x, y, z bottom, z top, half width)
BOOT = [(0.240, 0.140, 0.0, 0.215, 0.120),     # heel
        (0.240, -0.060, 0.0, 0.215, 0.165),    # instep, widest
        (0.240, -0.230, 0.0, 0.140, 0.160),    # toe box
        (0.240, -0.310, 0.0, 0.070, 0.120)]    # chamfered toe


def parts():
    P, F, _ = lk.loft_sym(SKIRT, SKIRT_Z)
    out = {'skirt': lk.part(P, F, 'hips')}
    for name, (secs, n, bone) in LEG.items():
        P, F = lk.loft([lk.ring((cx, cy, z), lk.X, lk.FRONT, hx, hy, n) for cx, cy, z, hx, hy in secs])
        out[name] = lk.part(P, F, bone, 'metal' if 'cuff' in name else 'stone')
    rings = []
    for cx, y, z0, z1, hw in BOOT:      # 6-sided section across the foot: flat sole, sloped top
        zc, hz = (z0 + z1) / 2, (z1 - z0) / 2
        rings.append([(cx - hw, y, z0), (cx + hw, y, z0), (cx + hw, y, zc + hz * 0.4),
                      (cx + hw * 0.6, y, z1), (cx - hw * 0.6, y, z1), (cx - hw, y, zc + hz * 0.4)])
    P, F = lk.loft(rings)
    out['boot_l'] = lk.part(P, F, 'foot_l')
    return out
