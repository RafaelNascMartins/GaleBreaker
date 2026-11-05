"""Dale (fighter id 'ignis') limited-animation sheets for legends_anim.place().

Heavy brawler: wide planted stance, slow committed wind-ups, big holds on impact (timings from
anim_timing.TIMING['ignis'], contact keys land on those frames). Grappler (Zangief-like): hunched,
wide and low, arms open to grab; strikes are clubbing arm blows driven by the whole body.
Moves (GDD "Soco de Roça"): J1 forearm club, J2 short lariat, J3 two-fist hammer down.

Run in Blender: import legends_dale_anim as d; d.author(rig) (or d.author(rig, ['idle'])).
"""
import math

import legends_anim as la
from legends_anim import FIST

# Ankles on the ground: rest ankle height 0.13 (legends_dale.JOINTS). Grappler's wide, low base.
L0, R0 = (.25, -.12, .13), (-.27, .34, .13)
GROUND = .13
# Hip to ankle is ~.89 at rest and the leg .86: sink well below it, knees bent wide.
BASE_SINK = .19
# Grappler's guard (Zangief-like): hunched forward, both arms open wide and low in front of the
# belly, elbows out, ready to grab; the lead (left) arm a little further out.
HANDS = {'l': (.42, -.46, 1.00), 'r': (-.38, -.32, .95)}
ELBOW = {'l': (1, .4, -.1), 'r': (-1, .4, -.1)}
TURN = {'hips': (6, 0, 0), 'spine': (8, 0, 0), 'chest': (12, 0, -6), 'head': (-22, 0, 4)}
la.PROFILES['ignis'] = {'L0': L0, 'R0': R0, 'GROUND': GROUND, 'BASE_SINK': BASE_SINK, 'HANDS': HANDS,
                        'ELBOW': ELBOW, 'TURN': TURN}


def ankle(base, forward=0.0, up=0.0):
    return (base[0], base[1] - forward, base[2] + up)


def hand(side, dx=0.0, fwd=0.0, up=0.0):
    b = HANDS[side]
    return (b[0] + dx, b[1] - fwd, b[2] + up)


def idle_sheet(n=52, keys=13):
    """Heavy breathing on bent knees: shoulders and fists rise on the in-breath, the hips sink a
    little on the out-breath, the chest swells; feet planted. Slower and deeper than Babuin."""
    out = []
    for i in range(keys + 1):
        t = i / keys
        breath = .5 - .5 * math.cos(2 * math.pi * t)          # 0 out, 1 in
        sway = math.sin(2 * math.pi * t)
        out.append((round(n * t), {
            'hips': (.015 * sway, .03 * (1 - breath)),
            'turn': {'chest': (12 - 4 * breath, 0, -6 + 2 * sway), 'head': (-22 + 4 * breath, 0, 4 - 2 * sway)},
            'shrug': {'l': (4 + 9 * breath, 3), 'r': (4 + 9 * breath, 3)},
            'feet': {'l': L0, 'r': R0},
            # the open arms drift out and in with the breath, like circling an opponent
            'hands': {'l': hand('l', dx=.03 * breath, up=.04 * breath), 'r': hand('r', dx=-.03 * breath, up=.04 * breath)},
        }))
    return out


def walk_sheet(direction=1, n=34, keys=9, stride=.62):
    """Heavy stomping walk: each foot lifts low and plants flat, the hips drop on every plant and
    the shoulders roll with the steps; the guard stays up."""
    out = []
    uL, uR = -L0[1], -R0[1]
    for i in range(keys + 1):
        t = i / keys
        tt = t if direction > 0 else 1 - t
        r_sw = la.ease(min(tt / .5, 1.0))
        l_sw = la.ease(max((tt - .5) / .5, 0.0))
        root = stride * tt
        ur = uR + stride * r_sw - root
        ul = uL + stride * l_sw - root
        lift_r = .09 * math.sin(math.pi * min(tt / .5, 1.0)) if tt < .5 else 0.0
        lift_l = .09 * math.sin(math.pi * max((tt - .5) / .5, 0.0)) if tt > .5 else 0.0
        sway = math.sin(2 * math.pi * tt)
        plant = abs(math.cos(2 * math.pi * tt))               # 1 when a foot is down
        out.append((round(n * t), {
            'hips': (.02 * direction, .015 + .04 * plant),
            'turn': {'hips': (6, 3 * sway, 10 * sway), 'spine': (8, 0, 0), 'chest': (12 + 4 * direction, -3 * sway, -6 - 12 * sway),
                     'head': (-22 - 4 * direction, 0, 4 - 5 * sway)},
            'shrug': {'l': (6, 8 * sway), 'r': (6, -8 * sway)},
            'feet': {'l': (L0[0], -ul, GROUND + lift_l), 'r': (R0[0], -ur, GROUND + lift_r)},
        }))
    return out


def hold(n, pose, settle=None):
    keys = [(0, pose)]
    if settle:
        keys.append((n // 2, settle))
    keys.append((n, settle or pose))
    return keys


GUARD_HIGH = {'hips': (-.03, .06), 'turn': {'chest': (10, 0, -4), 'head': (-14, 0, 2)},
              'shrug': {'l': (16, 12), 'r': (16, 12)},
              'hands': {'l': (.10, -.40, 1.72), 'r': (-.09, -.36, 1.70)},
              'elbow': {'l': (.3, -1, -.6), 'r': (-.3, -1, -.6)}, 'aim': {'l': (0, 0, 1), 'r': (0, 0, 1)}}
CROUCH = {'hips': (.04, .32), 'turn': {'hips': (12, 0, 0), 'chest': (14, 0, -4), 'head': (-20, 0, 4)},
          'shrug': {'l': (8, 8), 'r': (8, 8)},
          'feet': {'l': ankle(L0, .04), 'r': ankle(R0, -.04)},
          'hands': {'l': (.16, -.50, 1.12), 'r': (-.10, -.40, 1.06)}}
GUARD_LOW = {**CROUCH, 'shrug': {'l': (14, 14), 'r': (14, 14)},
             'hands': {'l': (.10, -.46, 1.20), 'r': (-.08, -.40, 1.16)},
             'elbow': {'l': (.3, -1, -.6), 'r': (-.3, -1, -.6)}}

# ---- Soco de Roça (anim_timing ignis light: wind 8, contact 11, hold 14, follow 17, end 30;
# J3 wind 13, contact 17, hold 21, follow 25, end 40) ----
LIGHT = {
    # J1: forearm club. The right arm swings up and back over the shoulder, then the whole
    # body drops behind it and the forearm clubs down across the front; held on impact.
    'light_1': [
        (0, {}),
        (5, {'hips': (-.05, -.01), 'turn': {'hips': (4, 0, -12), 'spine': (2, 0, 0), 'chest': (-2, 0, -24), 'head': (-10, 0, 16)},
             'shrug': {'r': (24, -12)}, 'feet': {'l': ankle(L0, .02, .05)},
             'hands': {'r': (-.34, .06, 1.84)}, 'elbow': {'r': (-.6, .4, 1)}, 'aim': {'r': (0, .3, 1)}}),
        (11, {'hips': (.15, .14), 'turn': {'hips': (12, 0, 18), 'spine': (10, 0, 8), 'chest': (26, 0, 20), 'head': (-30, 0, -14)},
              'feet': {'l': ankle(L0, .16)}, 'shrug': {'r': (6, 18)},
              'hands': {'r': (-.02, -.86, 1.18)}, 'elbow': {'r': (-1, -.2, .5)}, 'aim': {'r': (1, -.3, -.3)},
              'scale': {'forearm_r': (1.2, 1.15, 1.2), 'hand_r': (1.25, 1.25, 1.25)}}),
        (14, {'hips': (.14, .14), 'turn': {'hips': (11, 0, 16), 'spine': (9, 0, 7), 'chest': (24, 0, 18), 'head': (-28, 0, -12)},
              'feet': {'l': ankle(L0, .16)}, 'shrug': {'r': (5, 15)},
              'hands': {'r': (-.02, -.84, 1.16)}, 'elbow': {'r': (-1, -.2, .5)}, 'aim': {'r': (1, -.3, -.3)}}),
        (17, {'hips': (.10, .10), 'turn': {'chest': (18, 0, 10), 'head': (-24, 0, -6)},
              'feet': {'l': ankle(L0, .10)}, 'hands': {'r': (-.12, -.66, 1.14)}}),
        (24, {'hips': (.04, .04), 'feet': {'l': ankle(L0, .03)}}),
        (30, {}),
    ],
    # J2: short lariat. From the end of J1 the left arm swings out wide and back, then the body
    # turns over and the straight arm sweeps across at neck height, the right arm left open.
    'light_2': [
        (0, {'from': ('light_1', 17)}),
        (5, {'hips': (.05, .07), 'turn': {'hips': (6, 0, 20), 'chest': (8, 0, 32), 'head': (-18, 0, -20)},
             'shrug': {'l': (14, -18)}, 'hands': {'l': (.66, .10, 1.44)}, 'elbow': {'l': (.2, .5, -1)}}),
        (11, {'hips': (.15, .12), 'turn': {'hips': (10, 0, -22), 'spine': (8, 0, -10), 'chest': (18, 0, -32), 'head': (-24, 0, 18)},
              'shrug': {'l': (8, 16), 'r': (0, -8)},
              'hands': {'l': (-.10, -1.02, 1.52), 'r': (-.42, -.18, 1.12)}, 'elbow': {'l': (.2, 0, -1)}, 'aim': {'l': (-1, -.6, 0)},
              'scale': {'upper_arm_l': (1.15, 1.1, 1.15), 'hand_l': (1.25, 1.25, 1.25)}}),
        (14, {'hips': (.14, .12), 'turn': {'hips': (9, 0, -20), 'chest': (16, 0, -29), 'head': (-22, 0, 16)},
              'shrug': {'l': (6, 13)},
              'hands': {'l': (-.08, -1.00, 1.51), 'r': (-.42, -.18, 1.12)}, 'elbow': {'l': (.2, 0, -1)}, 'aim': {'l': (-1, -.6, 0)}}),
        (17, {'hips': (.08, .08), 'turn': {'chest': (14, 0, -14)}, 'hands': {'l': (.12, -.80, 1.40)}}),
        (24, {'hips': (.03, .03)}),
        (30, {}),
    ],
    # J3: two-fist hammer. Joins the fists and raises them high over the hat, rising on the toes
    # of the stance, then drives everything down into a deep squat, fists smashing low in front.
    'light_3': [
        (0, {'from': ('light_2', 17)}),
        (10, {'hips': (-.04, -.02), 'turn': {'spine': (-6, 0, 0), 'chest': (-14, 0, 0), 'head': (8, 0, 0)},
              'shrug': {'l': (24, -6), 'r': (24, -6)},
              'hands': {'l': (.05, -.12, 2.12), 'r': (-.05, -.12, 2.10)}, 'aim': {'l': (0, .3, 1), 'r': (0, .3, 1)},
              'elbow': {'l': (1, .2, .2), 'r': (-1, .2, .2)}}),
        (13, {'hips': (-.06, -.04), 'turn': {'spine': (-8, 0, 0), 'chest': (-18, 0, 0), 'head': (10, 0, 0)},
              'shrug': {'l': (28, -10), 'r': (28, -10)},
              'hands': {'l': (.05, -.02, 2.18), 'r': (-.05, -.02, 2.16)}, 'aim': {'l': (0, .6, .8), 'r': (0, .6, .8)},
              'elbow': {'l': (1, .3, .3), 'r': (-1, .3, .3)}}),
        (17, {'hips': (.16, .36), 'turn': {'hips': (14, 0, 0), 'spine': (14, 0, 0), 'chest': (26, 0, 0), 'head': (-24, 0, 0)},
              'feet': {'l': ankle(L0, .14)}, 'shrug': {'l': (2, 16), 'r': (2, 16)},
              'hands': {'l': (.05, -.88, .78), 'r': (-.05, -.88, .76)}, 'aim': {'l': (0, -.3, -1), 'r': (0, -.3, -1)},
              'scale': {'hand_l': (1.3, 1.3, 1.3), 'hand_r': (1.3, 1.3, 1.3)}}),
        (21, {'hips': (.15, .38), 'turn': {'hips': (14, 0, 0), 'spine': (12, 0, 0), 'chest': (24, 0, 0), 'head': (-22, 0, 0)},
              'feet': {'l': ankle(L0, .14)}, 'shrug': {'l': (2, 14), 'r': (2, 14)},
              'hands': {'l': (.05, -.86, .74), 'r': (-.05, -.86, .72)}, 'aim': {'l': (0, -.3, -1), 'r': (0, -.3, -1)}}),
        (25, {'hips': (.12, .30), 'turn': {'hips': (10, 0, 0), 'chest': (18, 0, 0), 'head': (-16, 0, 0)},
              'feet': {'l': ankle(L0, .12)},
              'hands': {'l': (.08, -.70, .90), 'r': (-.06, -.66, .88)}}),
        (33, {'hips': (.05, .12), 'turn': {'chest': (6, 0, 0)}, 'feet': {'l': ankle(L0, .04)}}),
        (40, {}),
    ],
}

SHEETS = {
    'idle': idle_sheet(),
    'walk_forward': walk_sheet(1),
    'walk_back': walk_sheet(-1),
    'crouch': hold(14, CROUCH),
    'guard_high': hold(14, GUARD_HIGH),
    'guard_low': hold(14, GUARD_LOW),
    **LIGHT,
}
la.SHEETS['ignis'] = SHEETS


def author(rig, clips=None, force=False):
    """Author Dale's sheets on dale_Rig (all, or the named clips, in order)."""
    return [la.author(rig, c, 'ignis', force).name for c in (clips or SHEETS)]
