"""X12's arms, modelled by hand on the Legends references (docs/estudos/legends-modelagem.md).

Mega Man's arm: a low-poly sphere at the shoulder, a thin upper arm, a thicker forearm
cylinder and a big boxy hand; the arm narrows and grows again. X12 the same way: pauldron
(6-sided rounded rock), upper arm (6 sides, mostly inside the pauldron), forearm (6-sided
cylinder along the A-pose tilt), wrist cuff (8-sided metal band), fist (chamfered box).
Her left arm is listed, the right is its mirror. Measured on the concept crops: front (x, z),
profile (y), in metres (MPP 1.8/840).
"""
import legends_kit as lk

AXIS, SIDE = lk.tilted(25)         # forearm and cuff lean out from the vertical (front view)
PAUL_AXIS, PAUL_SIDE = lk.tilted(15)
FIST_AXIS, FIST_SIDE = lk.tilted(12)   # the fist hangs straighter than the forearm

# part: origin, axis, side, sections [(along, half side, half front)], sides, tone, bone
PARTS = {
    # pauldron: a rounded rock (6-sided sphere like Mega Man's shoulder), leaning out 15 deg
    # (front: the top edge runs from the collar down to the outer side; x 0.13-0.36,
    # profile y -0.10..0.17)
    'pauldron_l': ((0.235, 0.030, 1.450), PAUL_AXIS, PAUL_SIDE, [
        (0.000, 0.050, 0.060), (0.040, 0.100, 0.115), (0.110, 0.122, 0.136),
        (0.180, 0.100, 0.115), (0.225, 0.055, 0.065)], 6, 'stone', 'upper_arm_l'),
    # upper arm: thin, from inside the pauldron to the elbow (front cols 435-492, rows 262-320)
    'upper_arm_l': ((0.285, 0.015, 1.300), AXIS, SIDE, [
        (0.000, 0.050, 0.060), (0.150, 0.058, 0.068)], 6, 'stone', 'upper_arm_l'),
    # forearm: thick to the cuff, elbow (col 497, row 305) to the wrist (col 545, row 405)
    'forearm_l': ((0.355, 0.037, 1.185), AXIS, SIDE, [
        (0.000, 0.080, 0.095), (0.110, 0.095, 0.108), (0.235, 0.088, 0.100)], 6, 'stone', 'forearm_l'),
    # wrist cuff: dark studded band (front rows 388-430)
    'wrist_cuff_l': ((0.452, 0.037, 0.978), AXIS, SIDE, [
        (0.000, 0.100, 0.110), (0.050, 0.100, 0.110)], 8, 'metal', 'forearm_l'),
    # fist: big chamfered block, short (the fingers are painted); front cols 520-600
    'fist_l': ((0.470, 0.040, 0.925), FIST_AXIS, FIST_SIDE, [
        (0.000, 0.055, 0.095), (0.030, 0.080, 0.125), (0.135, 0.078, 0.120),
        (0.170, 0.055, 0.085)], 4, 'stone', 'hand_l'),
}


def parts():
    out = {}
    for name, (o, axis, side, secs, n, tone, bone) in PARTS.items():
        P, F = lk.loft(lk.along(o, axis, side, secs, n, flat_front=(n == 4)))
        out[name] = lk.part(P, F, bone, tone)
    return out
