"""Orsted's energy hand cannon (fighter id `volt`), by hand on its 5-view sheet
(concept-art/characters/orsted/orsted-canhao-mao-5-vistas-psx-v1.png: a 55 cm scrap pistol).

Rigid pieces on the `cannon` bone (the game's muzzle socket), held in his right hand: from the
back, the octagonal rear block, a dark ring, the cyan glass chamber, a dark ring, the long
octagonal mustard barrel and the dark muzzle ring (the cyan glow painted on its face); the
copper carry handle over the chamber (a bar on two posts), the grip leaning back ~25 deg under the
rear and the trigger guard under the chamber (painted). The cables are painted.
Built in the gun's own frame (f along the barrel, z over the grip), then placed as a real pistol
grip in his right hand: barrel along the hand on the thumb side, grip through the fist.
Side view measures (845 px = 0.55 m): barrel 0.10 m across, muzzle 0.116, chamber 0.114, rear block
0.07 high; handle 0.14 long and 0.05 over the barrel; grip 0.10 long, 0.055 wide.
"""
import numpy as np

import legends_kit as lk

# along the barrel (f, metres from the grip top), octagon half size (side, up), centre height
SECTIONS = {
    'gun_rear': ((-0.100, -0.005), (0.036, 0.036), 0.012),
    'gun_ring_back': ((-0.005, 0.022), (0.060, 0.060), 0.0),
    'gun_chamber': ((0.022, 0.125), (0.056, 0.056), 0.0),
    'gun_ring_front': ((0.125, 0.152), (0.060, 0.060), 0.0),
    'gun_barrel': ((0.152, 0.375), (0.050, 0.050), 0.0),
    'gun_muzzle': ((0.375, 0.440), (0.058, 0.058), 0.0),
}
# boxes: centre (f, s, z), half size (f, s, z), lean about s (deg, + leans the bottom back)
BOXES = {
    'gun_handle_bar': ((0.075, 0.0, 0.098), (0.070, 0.014, 0.012), 0),
    'gun_handle_post_back': ((0.012, 0.0, 0.075), (0.012, 0.012, 0.022), 0),
    'gun_handle_post_front': ((0.138, 0.0, 0.075), (0.012, 0.012, 0.022), 0),
    'gun_grip': ((-0.070, 0.0, -0.095), (0.026, 0.024, 0.065), 25),
    'gun_guard': ((0.040, 0.0, -0.068), (0.040, 0.008, 0.012), 0),
}
# A pistol grip, not a gun stuck across the hand: the barrel runs along the hand and forearm, over
# the fist on the thumb side, and the grip goes through the fist toward the little finger. With
# the arm hanging (A-pose: hand down, palm to the thigh, thumb forward) the cannon points at the
# floor; arm out, it points ahead with the wrist straight; forearm up, it stands up.
FIST_R = np.array([-0.389, 0.030, 0.967])               # middle of his right fist (A-pose)
HAND_AXIS_R = np.array([-0.2419, 0.0, -0.9703])         # wrist -> knuckles, right hand (tilted 14 deg)
THUMB_SIDE = np.array([0.0, -1.0, 0.0])                 # the thumb side of the right fist (forward)
GRIP_LOCAL = np.array([-0.070, 0.0, -0.095])            # the grip's centre in the gun's frame
BONE = 'cannon'


def to_world(P):
    """Gun frame (f along the barrel, s, z over the grip) -> body: f along the hand, z to the thumb
    side, the grip's centre in the fist."""
    P = np.asarray(P, float) - GRIP_LOCAL
    S = np.cross(THUMB_SIDE, HAND_AXIS_R)
    return FIST_R + np.outer(P[:, 0], HAND_AXIS_R) + np.outer(P[:, 1], S) + np.outer(P[:, 2], THUMB_SIDE)


def octagon_prism(f0, f1, hs, hz, zc):
    F_AXIS = np.array([1.0, 0, 0])
    rings = [lk.ring((f, 0.0, zc), np.array([0, 1.0, 0]), np.array([0, 0, 1.0]), hs, hz, 8) for f in (f0, f1)]
    return lk.loft(rings)


def box(c, h, lean):
    (cf, cs, cz), (hf, hs, hz) = c, h
    corners = np.array([[sf * hf, ss * hs, sz * hz] for sz in (1, -1) for sf, ss in ((1, 1), (1, -1), (-1, -1), (-1, 1))])
    t = np.radians(lean)                       # lean the box: its bottom goes back (-f)
    R = np.array([[np.cos(t), 0, np.sin(t)], [0, 1, 0], [-np.sin(t), 0, np.cos(t)]])
    corners = corners @ R.T + [cf, cs, cz]
    return lk.loft([corners[:4], corners[4:]])


def parts():
    out = {}
    for name, ((f0, f1), (hs, hz), zc) in SECTIONS.items():
        P, F = octagon_prism(f0, f1, hs, hz, zc)
        P = to_world(P)
        out[name] = lk.part(P, lk.orient(P, F), BONE, 'gun')
    for name, (c, h, lean) in BOXES.items():
        P, F = box(c, h, lean)
        P = to_world(P)
        out[name] = lk.part(P, lk.orient(P, F), BONE, 'gun')
    return out


# the gun sits on his right side only: legends_build leaves it out of the symmetry check
ASYMMETRIC = {}
for _n, _p in parts().items():
    ASYMMETRIC[_n] = [tuple(v) for v in np.round(_p['v'], 4)]
