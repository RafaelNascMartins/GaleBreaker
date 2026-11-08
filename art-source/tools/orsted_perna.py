"""Orsted's legs (fighter id `volt`), by hand on the Legends references.

Mega Man / X12 legs: straight prisms, here baggy cargo trousers (thigh and shin, 8 sides, the
pockets and straps painted), a riveted scrap plate on each knee, the boot shaft and a big boot
block with a mustard toe cap and a thick sole (painted). Left leg listed, the right mirrors it.
Measured on his crops (MPP 1.86/840): hip (0.10, 0.87), knee (0.16, 0.58), ankle (0.185, 0.15);
trousers up to +-0.13 deep (profile), the boot from y +0.14 (heel) to -0.20 (toe).
"""
import numpy as np

import legends_kit as lk

Z = np.array([0.0, 0.0, 1.0])

# (centre x, centre y, z, half width, half depth) per section; sides; bone; tone
LEG = {
    'thigh_l': ([(0.100, 0.015, 0.880, 0.100, 0.130), (0.150, 0.015, 0.700, 0.115, 0.140),
                 (0.160, 0.020, 0.560, 0.100, 0.120)], 8, 'thigh_l', 'trousers'),
    'shin_l': ([(0.160, 0.030, 0.600, 0.100, 0.115), (0.166, 0.040, 0.440, 0.112, 0.118),
                (0.172, 0.045, 0.255, 0.082, 0.088)], 8, 'shin_l', 'trousers'),
    'boot_shaft_l': ([(0.180, 0.035, 0.280, 0.080, 0.082), (0.186, 0.030, 0.110, 0.082, 0.086)], 8, 'shin_l', 'boot'),
}
KNEE_PLATE = ((0.165, -0.098, 0.565), (0.066, 0.068), (-0.128, -0.080))    # front crop x .10-.23, z .50-.63
# boot block: sections along the foot (y forward is -): (centre x, y, z bottom, z top, half width)
BOOT = [(0.205, 0.135, 0.0, 0.165, 0.085),     # heel
        (0.208, -0.030, 0.0, 0.145, 0.108),    # instep
        (0.210, -0.150, 0.0, 0.105, 0.106),    # toe cap
        (0.210, -0.205, 0.0, 0.060, 0.088)]    # chamfered toe


def parts():
    out = {}
    for name, (secs, n, bone, tone) in LEG.items():
        P, F = lk.loft([lk.ring((cx, cy, z), lk.X, lk.FRONT, hx, hy, n) for cx, cy, z, hx, hy in secs])
        out[name] = lk.part(P, F, bone, tone)
    (cx, cy, cz), (hw, hh), (yf, yb) = KNEE_PLATE
    P, F = lk.loft([lk.ring((cx, y, cz), lk.X, Z, hw, hh, 6, flat_front=False) for y in (yf, yb)])
    out['knee_plate_l'] = lk.part(P, F, 'shin_l', 'plate')
    rings = []
    for cx, y, z0, z1, hw in BOOT:      # 6-sided section across the foot: flat sole, sloped top
        zc, hz = (z0 + z1) / 2, (z1 - z0) / 2
        rings.append([(cx - hw, y, z0), (cx + hw, y, z0), (cx + hw, y, zc + hz * 0.4),
                      (cx + hw * 0.6, y, z1), (cx - hw * 0.6, y, z1), (cx - hw, y, zc + hz * 0.4)])
    P, F = lk.loft(rings)
    out['boot_l'] = lk.part(P, F, 'foot_l', 'boot')
    return out
