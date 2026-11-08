"""Orsted's arms (fighter id `volt`), by hand on the Legends references.

Mega Man's arm: a low-poly sphere at the shoulder (here the short shirt sleeve over it, with its
rolled cuff), a thin bare upper arm, the forearm, the leather bracer at the wrist and a big hand
(the fingerless glove and the fingers are painted on one block). On his right shoulder only, the
big riveted scrap plate. Left arm listed, the right is its mirror; the plate is one-sided.
Measured on his crops (MPP 1.86/840): shoulder (0.225, 1.42), elbow (0.30, 1.215), wrist
(0.37, 1.04), hand tip (0.43, 0.80) in the front view, the arm at y +0.03 in the profile.
"""
import numpy as np

import legends_kit as lk

UPPER_AXIS, UPPER_SIDE = lk.tilted(20)
FORE_AXIS, FORE_SIDE = lk.tilted(22)
HAND_AXIS, HAND_SIDE = lk.tilted(14)
PLATE_AXIS, PLATE_SIDE = lk.tilted(15)

# part: origin, axis, side, sections [(along, half side, half front)], sides, tone, bone
PARTS = {
    # short sleeve over the shoulder ball (front: x .14-.30 at z 1.40, sleeve end z 1.30)
    'sleeve_l': ((0.215, 0.030, 1.470), UPPER_AXIS, UPPER_SIDE, [
        (0.000, 0.050, 0.055), (0.040, 0.078, 0.082), (0.120, 0.078, 0.080), (0.170, 0.074, 0.076)], 6, 'shirt', 'upper_arm_l'),
    'sleeve_cuff_l': ((0.262, 0.030, 1.335), UPPER_AXIS, UPPER_SIDE, [(0.000, 0.082, 0.084), (0.050, 0.082, 0.084)], 8, 'shirt', 'upper_arm_l'),
    'upper_arm_l': ((0.270, 0.030, 1.320), UPPER_AXIS, UPPER_SIDE, [(0.000, 0.048, 0.052), (0.110, 0.046, 0.050)], 6, 'skin', 'upper_arm_l'),
    'forearm_l': ((0.300, 0.030, 1.215), FORE_AXIS, FORE_SIDE, [
        (0.000, 0.046, 0.050), (0.060, 0.054, 0.056), (0.170, 0.044, 0.046)], 6, 'skin', 'forearm_l'),
    'bracer_l': ((0.348, 0.030, 1.105), FORE_AXIS, FORE_SIDE, [(0.000, 0.060, 0.062), (0.080, 0.062, 0.064)], 8, 'leather', 'forearm_l'),
    # hand: a closed fist (user 2026-11-07), a short chunky block: the glove on its back, the
    # curled fingers painted on its end (the cannon's grip sits inside it)
    'hand_l': ((0.372, 0.030, 1.035), HAND_AXIS, HAND_SIDE, [
        (0.000, 0.048, 0.040), (0.025, 0.062, 0.054), (0.110, 0.062, 0.054), (0.140, 0.048, 0.042)], 4, 'glove', 'hand_l'),
}
# his right shoulder plate, armour not a ball (front crop: x -0.33..-0.19, z 1.38-1.53; profile
# y -0.09..+0.13): an 8-sided faceted cup, flat-topped, flaring to a lip at its lower edge,
# and the blue-grey fin standing on its back edge
PAULDRON_R = ((-0.250, 0.020, 1.555), [
    (0.000, 0.060, 0.070), (0.025, 0.118, 0.118), (0.120, 0.138, 0.130), (0.150, 0.150, 0.138), (0.168, 0.128, 0.120)])
FIN_R = ((-0.262, 0.075), (1.625, 1.520), (0.050, 0.016))


def parts():
    out = {}
    for name, (o, axis, side, secs, n, tone, bone) in PARTS.items():
        P, F = lk.loft(lk.along(o, axis, side, secs, n, flat_front=(n == 4)))
        out[name] = lk.part(P, F, bone, tone)
    o, secs = PAULDRON_R
    axis, side = PLATE_AXIS * [-1, 1, 1], PLATE_SIDE * [-1, 1, 1]
    P, F = lk.loft(lk.along(o, axis, side, secs, 8))
    out['pauldron_r'] = lk.part(P, F, 'upper_arm_r', 'plate')
    (cx, cy), (z1, z0), (hx, hy) = FIN_R
    P, F = lk.prism([(z1, hx * 0.6, hy), (z0, hx, hy)], 4, centre=(cx, cy))
    out['pauldron_fin_r'] = lk.part(P, F, 'upper_arm_r', 'rust')
    return out
