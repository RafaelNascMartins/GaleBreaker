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

# ---- Specials. Same logic as the light chain: one short wind-up key, a hard cut to the contact
# pose, held through the hit. Timings (anim_timing ignis): heavy contact 21 / follow 30 / end 48,
# elemental contact 19 / follow 28 / end 44, ultimate contact 28 / follow 40 / end 58. ----
OVERHEAD = {'l': (.06, -.10, 2.20), 'r': (-.06, -.10, 2.18)}
SPECIALS = {
    # K1 Botada: a short hop of the rear foot in, the lead knee chambers high, then the boot drives
    # flat into the gut, sole first, body leaning back behind it; the arms stay open.
    'heavy': [
        (0, {}),
        (4, {'hips': (-.04, .02), 'turn': {'hips': (-4, 0, 0), 'chest': (-6, 0, 4), 'head': (-16, 0, -2)},
             'feet': {'l': (.20, -.30, .60), 'r': ankle(R0, .04)}, 'knee': {'l': (.2, -1, .5)}, 'foot_turn': {'l': -25},
             'hands': {'l': (.42, -.30, 1.10), 'r': (-.40, -.14, 1.06)}}),
        (9, {'hips': (-.06, -.04), 'turn': {'hips': (-14, 0, 0), 'spine': (-6, 0, 0), 'chest': (-10, 0, 4), 'head': (-12, 0, 0)},
             'feet': {'l': (.18, -.88, .66), 'r': ankle(R0, .06)}, 'knee': {'l': (.2, -1, .4)}, 'sole': {'l': ((0, -1, 0), (0, 0, 1))},
             'hands': {'l': (.46, -.18, 1.14), 'r': (-.44, -.02, 1.10)},
             'scale': {'foot_l': (1.35, 1.35, 1.35), 'shin_l': (1.1, 1.05, 1.1)}}),
        (12, {'hips': (-.06, -.04), 'turn': {'hips': (-14, 0, 0), 'spine': (-6, 0, 0), 'chest': (-10, 0, 4), 'head': (-12, 0, 0)},
              'feet': {'l': (.18, -.86, .66), 'r': ankle(R0, .06)}, 'knee': {'l': (.2, -1, .4)}, 'sole': {'l': ((0, -1, 0), (0, 0, 1))},
              'hands': {'l': (.46, -.18, 1.14), 'r': (-.44, -.02, 1.10)}}),
        (15, {'hips': (.0, .02), 'feet': {'l': (.20, -.50, .40), 'r': ankle(R0, .06)}, 'knee': {'l': (.2, -1, .5)}}),
        (21, {'hips': (.02, .04), 'feet': {'l': ankle(L0, .04), 'r': ankle(R0, .04)}}),
        (26, {}),
    ],
    # Marreta Caipira: locks the feet wide, joins the fists high over the hat leaning back, then
    # drops into a deep squat and hammers the ground in front; the shoulders stay hunched.
    'heavy_2': [
        (0, {}),
        (6, {'hips': (-.08, -.06), 'turn': {'hips': (-4, 0, 0), 'spine': (-10, 0, 0), 'chest': (-20, 0, 0), 'head': (6, 0, 0)},
             'shrug': {'l': (30, -10), 'r': (30, -10)},
             'feet': {'l': ankle(L0, .04), 'r': ankle(R0, -.02)},
             'hands': OVERHEAD, 'aim': {'l': (0, .5, .8), 'r': (0, .5, .8)},
             'elbow': {'l': (1, .3, .3), 'r': (-1, .3, .3)}}),
        (21, {'hips': (.14, 0.29), 'turn': {'hips': (18, 0, 0), 'spine': (18, 0, 0), 'chest': (30, 0, 0), 'head': (-28, 0, 0)},
              'shrug': {'l': (0, 20), 'r': (0, 20)},
              'feet': {'l': ankle(L0, .04), 'r': ankle(R0, -.02)},
              'hands': {'l': (.06, -.92, .36), 'r': (-.06, -.92, .34)}, 'aim': {'l': (0, -.2, -1), 'r': (0, -.2, -1)},
              'scale': {'hand_l': (1.35, 1.35, 1.35), 'hand_r': (1.35, 1.35, 1.35), 'forearm_l': (1.15, 1.1, 1.15), 'forearm_r': (1.15, 1.1, 1.15)}}),
        (26, {'hips': (.14, 0.29), 'turn': {'hips': (18, 0, 0), 'spine': (18, 0, 0), 'chest': (30, 0, 0), 'head': (-28, 0, 0)},
              'shrug': {'l': (0, 18), 'r': (0, 18)},
              'feet': {'l': ankle(L0, .04), 'r': ankle(R0, -.02)},
              'hands': {'l': (.06, -.92, .34), 'r': (-.06, -.92, .32)}, 'aim': {'l': (0, -.2, -1), 'r': (0, -.2, -1)}}),
        (30, {'hips': (.12, 0.25), 'turn': {'hips': (14, 0, 0), 'spine': (14, 0, 0), 'chest': (24, 0, 0), 'head': (-22, 0, 0)},
              'feet': {'l': ankle(L0, .04), 'r': ankle(R0, -.02)},
              'hands': {'l': (.10, -.84, .46), 'r': (-.08, -.82, .44)}}),
        (40, {'hips': (.06, 0.18), 'turn': {'chest': (14, 0, -4)}, 'feet': {'l': ankle(L0, .02)}}),
        (48, {}),
    ],
    # Pisada da Fornalha: the lead knee comes up high, fists pulled in, then the boot stamps down
    # flat with the whole weight dropping onto it, arms flung out wide for the blast.
    'elemental': [
        (0, {}),
        (3, {'hips': (-.05, .06), 'turn': {'chest': (4, 0, 4), 'head': (-18, 0, -2)},
             'shrug': {'l': (10, 0), 'r': (10, 0)}, 'feet': {'l': ankle(L0, -.02)},
             'hands': {'l': (.34, -.40, 1.04), 'r': (-.30, -.24, 1.00)}}),
        (8, {'hips': (-.06, .0), 'turn': {'hips': (-4, 0, 0), 'chest': (-4, 0, 6), 'head': (-14, 0, -4)},
             'shrug': {'l': (14, 4), 'r': (14, 4)},
             'feet': {'l': (.20, -.30, .58)}, 'knee': {'l': (.2, -1, .5)}, 'foot_turn': {'l': -15},
             'hands': {'l': (.30, -.40, 1.24), 'r': (-.26, -.28, 1.20)}}),
        (12, {'hips': (-.08, -.06), 'turn': {'hips': (-8, 0, 0), 'spine': (-6, 0, 0), 'chest': (-12, 0, 6), 'head': (-10, 0, -4)},
              'shrug': {'l': (22, 2), 'r': (22, 2)},
              'feet': {'l': (.18, -.40, .92)}, 'knee': {'l': (.2, -1, .7)}, 'foot_turn': {'l': -25},
              'hands': {'l': (.30, -.30, 1.50), 'r': (-.26, -.18, 1.46)}, 'scale': {'foot_l': (1.2, 1.2, 1.2)}}),
        (16, {'hips': (-.09, -.08), 'turn': {'hips': (-10, 0, 0), 'spine': (-8, 0, 0), 'chest': (-14, 0, 6), 'head': (-8, 0, -4)},
              'shrug': {'l': (26, 0), 'r': (26, 0)},
              'feet': {'l': (.18, -.42, .98)}, 'knee': {'l': (.2, -1, .8)}, 'foot_turn': {'l': -25},
              'hands': {'l': (.32, -.28, 1.58), 'r': (-.28, -.16, 1.54)}, 'scale': {'foot_l': (1.3, 1.3, 1.3)}}),
        (19, {'hips': (.10, 0.25), 'turn': {'hips': (16, 0, 0), 'spine': (10, 0, 0), 'chest': (20, 0, 0), 'head': (-24, 0, 0)},
              'shrug': {'l': (2, -6), 'r': (2, -6)},
              'feet': {'l': ankle(L0, .16)},
              'hands': {'l': (.66, -.30, 1.04), 'r': (-.62, -.10, 1.00)}, 'elbow': {'l': (.2, .4, -1), 'r': (-.2, .4, -1)},
              'scale': {'foot_l': (1.3, 1.3, 1.3), 'shin_l': (1.1, 1, 1.1)}}),
        (24, {'hips': (.10, 0.25), 'turn': {'hips': (16, 0, 0), 'spine': (10, 0, 0), 'chest': (20, 0, 0), 'head': (-24, 0, 0)},
              'shrug': {'l': (2, -6), 'r': (2, -6)},
              'feet': {'l': ankle(L0, .16)},
              'hands': {'l': (.66, -.30, 1.02), 'r': (-.62, -.10, .98)}, 'elbow': {'l': (.2, .4, -1), 'r': (-.2, .4, -1)}}),
        (28, {'hips': (.08, 0.21), 'turn': {'hips': (12, 0, 0), 'chest': (16, 0, 0), 'head': (-22, 0, 0)},
              'feet': {'l': ankle(L0, .14)}, 'hands': {'l': (.56, -.36, 1.04), 'r': (-.52, -.18, 1.00)}}),
        (37, {'hips': (.04, 0.12), 'feet': {'l': ankle(L0, .05)}}),
        (44, {}),
    ],
    # Fúria do Meio-Dia: tips the hat with the right hand and crouches low behind the left
    # shoulder, then explodes forward in a shoulder charge, body nearly horizontal, both fists
    # tucked; the lead foot lands far ahead on contact.
    'ultimate': [
        (0, {}),
        (6, {'hips': (-.02, 0.10), 'turn': {'chest': (4, 0, -8), 'head': (-30, 0, 6)},
             'hands': {'l': hand('l'), 'r': (-.10, -.20, 1.86)}, 'aim': {'r': (0, -.2, 1)},
             'elbow': {'r': (-1, -.3, .3)}}),
        (16, {'hips': (-.08, 0.22), 'turn': {'hips': (14, 0, -16), 'spine': (12, 0, -10), 'chest': (20, 0, -26), 'head': (-30, 0, 20)},
              'shrug': {'l': (22, 16), 'r': (10, 4)},
              'feet': {'l': ankle(L0, -.04), 'r': ankle(R0, -.06)},
              'hands': {'l': (.22, -.44, 1.08), 'r': (-.12, -.30, 1.00)}}),
        (28, {'hips': (.36, 0.21), 'turn': {'hips': (24, 0, -22), 'spine': (20, 0, -14), 'chest': (34, 0, -34), 'head': (-38, 0, 26)},
              'shrug': {'l': (24, 22), 'r': (8, 6)},
              'feet': {'l': ankle(L0, .44), 'r': ankle(R0, .04, .06)},
              'hands': {'l': (.20, -.58, .84), 'r': (-.10, -.38, .80)}, 'elbow': {'l': (1, -.6, .2)},
              'scale': {'upper_arm_l': (1.3, 1.1, 1.3), 'chest': (1.08, 1.0, 1.08)}}),
        (34, {'hips': (.38, 0.22), 'turn': {'hips': (24, 0, -22), 'spine': (20, 0, -14), 'chest': (34, 0, -34), 'head': (-38, 0, 26)},
              'shrug': {'l': (24, 22), 'r': (8, 6)},
              'feet': {'l': ankle(L0, .44), 'r': ankle(R0, .10)},
              'hands': {'l': (.20, -.60, .84), 'r': (-.10, -.40, .80)}, 'elbow': {'l': (1, -.6, .2)}}),
        (40, {'hips': (.30, 0.17), 'turn': {'hips': (14, 0, -12), 'chest': (22, 0, -18), 'head': (-30, 0, 12)},
              'feet': {'l': ankle(L0, .40), 'r': ankle(R0, .20)}}),
        (50, {'hips': (.12, 0.12), 'feet': {'l': ankle(L0, .10), 'r': ankle(R0, .06)}}),
        (58, {}),
    ],
}


# ---- Reactions (anim_timing ignis states: hit 22, knockdown 32, ko 44). A heavy man: he barely
# rocks back from a hit, and when he goes down he slams flat and bounces once. Floor poses are
# Babuin's (legends_anim) scaled to Dale's bigger frame. ----
def big(pose, k=1.1):
    out = dict(pose)
    for key in ('feet', 'hands'):
        if key in pose:
            out[key] = {sd: (v[0] * k, v[1] * k, v[2] * k) for sd, v in pose[key].items()}
    return out


D_LYING, D_SPLAT, D_FLUNG, D_FALLING = (big(p) for p in (la.LYING, la.SPLAT, la.FLUNG, la.FALLING))
D_BOUNCE = {**D_LYING, 'hips': (-.12, .70), 'turn': {'hips': (-76, 0, 0), 'chest': (-10, 0, 0), 'head': (20, 0, 8)}}

REACTIONS = {
    # Hit: the chest snaps back and the head whips, the open arms fly up; the feet stay planted.
    'hit': [
        (0, {'hips': (-.08, .02), 'turn': {'hips': (-4, 0, 0), 'spine': (-6, 0, 6), 'chest': (-14, 0, 12), 'head': (16, 0, -12)},
             'shrug': {'l': (16, -12), 'r': (16, -12)},
             'hands': {'l': (.50, -.18, 1.40), 'r': (-.46, .02, 1.30)}}),
        (5, {'hips': (-.10, .06), 'turn': {'spine': (-4, 0, 4), 'chest': (-10, 0, 10), 'head': (12, 0, -8)},
             'shrug': {'l': (12, -8), 'r': (12, -8)},
             'hands': {'l': (.48, -.24, 1.28), 'r': (-.44, -.04, 1.20)}}),
        (12, {'hips': (-.05, .04), 'turn': {'chest': (4, 0, 2), 'head': (-14, 0, 0)}}),
        (22, {}),
    ],
    'knockdown': [
        (0, {'hips': (-.08, .0), 'turn': {'spine': (-8, 0, 4), 'chest': (-20, 0, 10), 'head': (16, 0, -10)},
             'shrug': {'l': (14, -12), 'r': (14, -12)},
             'hands': {'l': (.46, -.16, 1.62), 'r': (-.42, .06, 1.50)}}),
        (5, D_FLUNG),
        (12, D_FALLING),
        (18, D_LYING),
        (21, D_BOUNCE),
        (25, D_LYING),
        (32, D_LYING),
    ],
    'ko': [
        (0, {'hips': (-.10, .0), 'turn': {'spine': (-10, 0, 6), 'chest': (-24, 0, 14), 'head': (20, 0, -14)},
             'shrug': {'l': (16, -14), 'r': (16, -14)},
             'hands': {'l': (.48, -.14, 1.64), 'r': (-.44, .08, 1.52)}}),
        (6, {**D_FLUNG, 'hips': (-.26, -.10), 'turn': {'hips': (-34, 0, 0), 'chest': (-26, 0, 14), 'head': (22, 0, -16)}}),
        (14, D_FALLING),
        (21, D_LYING),
        (25, D_BOUNCE),
        (30, D_LYING),
        (38, D_SPLAT),
        (44, D_SPLAT),
    ],
    # Get up: rolls up onto one knee with a hand on it, pushes up heavily, shakes out into guard.
    'get_up': [
        (0, D_LYING),
        (6, {'free': True, 'hips': (-.12, .78), 'turn': {'hips': (-40, 0, 0), 'chest': (14, 0, 0), 'head': (-10, 0, 0)},
             'feet': {'l': (.18, -.50, .14), 'r': (-.18, -.32, .14)}, 'knee': {'l': la.UP, 'r': la.UP},
             'hands': {'l': (.34, .12, .16), 'r': (-.22, -.32, .62)}}),
        (12, {'hips': (.0, .30), 'turn': {'hips': (16, 0, 0), 'chest': (20, 0, 0), 'head': (-20, 0, 0)},
              'feet': {'r': ankle(R0, .10)},
              'hands': {'l': (.24, -.44, .80), 'r': (-.20, -.30, .78)}}),
        (18, {'hips': (.0, .08), 'shrug': {'l': (20, 0), 'r': (20, 0)}}),
        (24, {}),
    ],
}


# ---- Movement and defence (anim_timing ignis states: dash 14, parry 18). The game holds the
# jump on a fixed time (~frame 5 of jump_start while rising, of jump_air while falling). ----
D_TUCK = {'turn': {'hips': (6, 0, 0), 'chest': (16, 0, -4), 'head': (-22, 0, 4)}, 'shrug': {'l': (10, 6), 'r': (10, 6)},
          'feet': {'l': ankle(L0, .10, .40), 'r': ankle(R0, -.02, .30)}, 'knee': {'l': (.3, -1, .3), 'r': (-.3, -1, .3)},
          'hands': {'l': (.48, -.40, 1.30), 'r': (-.44, -.26, 1.24)}}
MOVES = {
    # Dash: a heavy lunge - drops the shoulder and charges two stomping steps, arms spread to grab.
    'dash': [
        (0, {'hips': (.04, .08), 'turn': {'hips': (10, 0, 0), 'chest': (20, 0, -6), 'head': (-28, 0, 4)},
             'feet': {'l': ankle(L0, .08, .05)}}),
        (4, {'hips': (.18, .14), 'turn': {'hips': (14, 0, 0), 'spine': (8, 0, 0), 'chest': (26, 0, -10), 'head': (-32, 0, 6)},
             'shrug': {'l': (6, 14), 'r': (6, 14)},
             'feet': {'l': ankle(L0, .34), 'r': ankle(R0, .02, .06)},
             'hands': {'l': (.52, -.62, 1.02), 'r': (-.48, -.48, .98)}}),
        (9, {'hips': (.14, .12), 'turn': {'hips': (10, 0, 0), 'chest': (20, 0, -6), 'head': (-28, 0, 4)},
             'feet': {'l': ankle(L0, .18), 'r': ankle(R0, -.14, .08)},
             'hands': {'l': (.48, -.54, 1.02), 'r': (-.44, -.40, .98)}}),
        (14, {'hips': (.03, .04)}),
    ],
    # Jump: a big squat to load, a stiff spring up with the arms thrown high, then knees tucked.
    'jump_start': [
        (0, {'hips': (.0, .24), 'turn': {'hips': (10, 0, 0), 'chest': (20, 0, -4), 'head': (-24, 0, 4)},
             'shrug': {'l': (4, 10), 'r': (4, 10)},
             'hands': {'l': (.46, -.40, .86), 'r': (-.42, -.26, .82)}}),
        (3, {'hips': (.02, -.08), 'turn': {'chest': (-6, 0, -4), 'head': (-6, 0, 4)}, 'shrug': {'l': (20, 0), 'r': (20, 0)},
             'feet': {'l': ankle(L0, .04, .10), 'r': ankle(R0, -.04, .06)},
             'hands': {'l': (.40, -.36, 1.80), 'r': (-.36, -.24, 1.74)}}),
        (8, D_TUCK),
    ],
    'jump_air': [
        (0, D_TUCK),
        (8, {**D_TUCK, 'turn': {'hips': (8, 0, 0), 'chest': (20, 0, -6), 'head': (-24, 0, 6)},
             'feet': {'l': ankle(L0, .14, .44), 'r': ankle(R0, .0, .34)}}),
        (16, D_TUCK),
    ],
    # Landing: hits the ground hard on both feet, absorbs deep with the arms out, rises slowly.
    'jump_land': [
        (0, {'hips': (.04, .30), 'turn': {'hips': (12, 0, 0), 'chest': (22, 0, -4), 'head': (-28, 0, 4)},
             'shrug': {'l': (0, 12), 'r': (0, 12)},
             'hands': {'l': (.58, -.34, .82), 'r': (-.54, -.16, .78)}}),
        (5, {'hips': (.02, .14), 'turn': {'chest': (16, 0, -4)}}),
        (12, {}),
    ],
    # Parry: both open arms sweep the attack aside and down, the body turning with them, then a
    # shove back out to the guard.
    'parry': [
        (0, {}),
        (2, {'hips': (-.02, .04), 'turn': {'chest': (8, 0, 14), 'head': (-20, 0, -8)}, 'shrug': {'l': (14, -6), 'r': (8, 4)},
             'hands': {'l': (.46, -.58, 1.46), 'r': (-.10, -.56, 1.40)}}),
        (5, {'hips': (.04, .10), 'turn': {'hips': (6, 0, -10), 'chest': (18, 0, -22), 'head': (-24, 0, 12)}, 'shrug': {'l': (6, 16), 'r': (6, 10)},
             'hands': {'l': (-.08, -.86, .86), 'r': (-.50, -.66, .80)},
             'scale': {'forearm_l': (1.1, 1.2, 1.1)}}),
        (10, {'hips': (.03, .09), 'turn': {'hips': (6, 0, -8), 'chest': (16, 0, -18), 'head': (-24, 0, 10)},
              'hands': {'l': (-.06, -.84, .88), 'r': (-.48, -.64, .82)}}),
        (14, {'hips': (.06, .06), 'hands': {'l': (.50, -.66, 1.12), 'r': (-.44, -.50, 1.08)}}),
        (18, {}),
    ],
}

# ---- Crouch / air / sweep attacks (anim_timing ignis: down_punch contact 9 / end 28, air_punch
# contact 8 / end 26, sweep contact 10 / end 30) and the presentation clips. ----
OTHER = {
    # Down punch: from the crouch the right fist cocks up by the ear, then the forearm clubs
    # down low in front at shin height, the shoulders dropping over it.
    'down_punch': [
        (0, CROUCH),
        (6, {**CROUCH, 'hips': (.0, .36), 'turn': {'hips': (12, 0, -8), 'chest': (8, 0, -18), 'head': (-16, 0, 12)},
             'shrug': {'r': (20, -10)}, 'hands': {'l': (.20, -.50, 1.06), 'r': (-.30, .0, 1.40)},
             'elbow': {'r': (-.6, .4, 1)}, 'aim': {'r': (0, .3, 1)}}),
        (9, {**CROUCH, 'hips': (.12, .40), 'turn': {'hips': (16, 0, 12), 'spine': (10, 0, 6), 'chest': (26, 0, 18), 'head': (-28, 0, -10)},
             'shrug': {'r': (4, 18)}, 'feet': {'l': ankle(L0, .12), 'r': ankle(R0, -.04)},
             'hands': {'l': (.22, -.46, 1.00), 'r': (-.04, -.84, .62)}, 'elbow': {'r': (-1, -.2, .5)}, 'aim': {'r': (1, -.3, -.6)},
             'scale': {'forearm_r': (1.2, 1.15, 1.2), 'hand_r': (1.3, 1.3, 1.3)}}),
        (13, {**CROUCH, 'hips': (.12, .40), 'turn': {'hips': (15, 0, 11), 'spine': (9, 0, 5), 'chest': (24, 0, 16), 'head': (-26, 0, -9)},
              'shrug': {'r': (4, 16)}, 'feet': {'l': ankle(L0, .12), 'r': ankle(R0, -.04)},
              'hands': {'l': (.22, -.46, 1.00), 'r': (-.04, -.82, .60)}, 'elbow': {'r': (-1, -.2, .5)}, 'aim': {'r': (1, -.3, -.6)}}),
        (16, {**CROUCH, 'hips': (.08, .36), 'feet': {'l': ankle(L0, .08)}, 'hands': {'l': (.20, -.48, 1.06), 'r': (-.10, -.66, .80)}}),
        (22, CROUCH),
        (28, CROUCH),
    ],
    # Air punch: knees tucked, the fists join over the hat and hammer down-forward together.
    'air_punch': [
        (0, D_TUCK),
        (5, {**D_TUCK, 'turn': {'hips': (0, 0, 0), 'spine': (-6, 0, 0), 'chest': (-14, 0, 0), 'head': (4, 0, 0)},
             'shrug': {'l': (24, -6), 'r': (24, -6)},
             'hands': {'l': (.06, -.14, 2.10), 'r': (-.06, -.14, 2.08)}, 'aim': {'l': (0, .4, .9), 'r': (0, .4, .9)},
             'elbow': {'l': (1, .2, .2), 'r': (-1, .2, .2)}}),
        (8, {**D_TUCK, 'turn': {'hips': (12, 0, 0), 'spine': (12, 0, 0), 'chest': (28, 0, 0), 'head': (-26, 0, 0)},
             'shrug': {'l': (2, 18), 'r': (2, 18)},
             'hands': {'l': (.06, -.86, .92), 'r': (-.06, -.86, .90)}, 'aim': {'l': (0, -.5, -1), 'r': (0, -.5, -1)},
             'scale': {'hand_l': (1.3, 1.3, 1.3), 'hand_r': (1.3, 1.3, 1.3)}}),
        (12, {**D_TUCK, 'turn': {'hips': (11, 0, 0), 'spine': (11, 0, 0), 'chest': (26, 0, 0), 'head': (-24, 0, 0)},
              'shrug': {'l': (2, 16), 'r': (2, 16)},
              'hands': {'l': (.06, -.84, .94), 'r': (-.06, -.84, .92)}, 'aim': {'l': (0, -.5, -1), 'r': (0, -.5, -1)}}),
        (15, {**D_TUCK, 'hands': {'l': (.20, -.66, 1.06), 'r': (-.18, -.60, 1.04)}}),
        (26, D_TUCK),
    ],
    # Sweep: drops low on the rear leg and shoves the lead boot out along the floor, flat and
    # heavy, the body leaning back over the planted knee, arms out for balance.
    'sweep': [
        (0, {}),
        (7, {'hips': (-.06, .40), 'turn': {'hips': (8, 0, 0), 'chest': (14, 0, -4), 'head': (-18, 0, 4)},
             'feet': {'l': (.24, -.26, .30), 'r': ankle(R0, .02)}, 'knee': {'l': (.3, -1, .4)},
             'hands': {'l': (.40, -.30, .86), 'r': (-.40, -.10, .84)}}),
        (10, {'hips': (-.10, .52), 'turn': {'hips': (-6, 0, -10), 'spine': (-4, 0, 0), 'chest': (2, 0, -10), 'head': (-14, 0, 10)},
              'shrug': {'l': (12, 4), 'r': (12, 4)},
              'feet': {'l': (.30, -1.02, .14), 'r': ankle(R0, .04)}, 'knee': {'l': (.3, -.4, 1)}, 'sole': {'l': ((0, -1, 0), (.3, 0, 1))},
              'hands': {'l': (.58, -.20, .90), 'r': (-.56, .10, .86)},
              'scale': {'foot_l': (1.35, 1.35, 1.35), 'shin_l': (1.1, 1.05, 1.1)}}),
        (14, {'hips': (-.10, .52), 'turn': {'hips': (-6, 0, -9), 'spine': (-4, 0, 0), 'chest': (2, 0, -9), 'head': (-14, 0, 9)},
              'shrug': {'l': (10, 4), 'r': (10, 4)},
              'feet': {'l': (.30, -1.00, .14), 'r': ankle(R0, .04)}, 'knee': {'l': (.3, -.4, 1)}, 'sole': {'l': ((0, -1, 0), (.3, 0, 1))},
              'hands': {'l': (.58, -.20, .90), 'r': (-.56, .10, .86)}}),
        (17, {'hips': (-.04, .42), 'feet': {'l': (.26, -.56, .20), 'r': ankle(R0, .04)}, 'knee': {'l': (.3, -1, .5)},
              'hands': {'l': (.46, -.30, .90), 'r': (-.44, -.10, .88)}}),
        (24, {'hips': (.0, .26), 'feet': {'l': ankle(L0, .04)}}),
        (30, {}),
    ],
    # Breaker: hunches in with the forearms crossed over the chest, then throws them wide with a
    # roar, chest up, the shockwave pushing the opponent off.
    'breaker': [
        (0, {}),
        (3, {'hips': (.0, .24), 'turn': {'chest': (18, 0, 0), 'head': (-18, 0, 0)}, 'shrug': {'l': (10, 16), 'r': (10, 16)},
             'hands': {'l': (-.14, -.40, 1.50), 'r': (.14, -.38, 1.56)}, 'elbow': {'l': (1, -.6, -.3), 'r': (-1, -.6, -.3)}}),
        (6, {'hips': (-.04, -.02), 'turn': {'spine': (-6, 0, 0), 'chest': (-16, 0, 0), 'head': (14, 0, 0)},
             'shrug': {'l': (20, -16), 'r': (20, -16)},
             'feet': {'l': ankle(L0, .08), 'r': ankle(R0, -.04)},
             'hands': {'l': (.86, .02, 1.66), 'r': (-.86, .06, 1.66)}, 'aim': {'l': (1, 0, .3), 'r': (-1, 0, .3)},
             'scale': {'hand_l': (1.35, 1.35, 1.35), 'hand_r': (1.35, 1.35, 1.35), 'chest': (1.08, 1.0, 1.08)}}),
        (11, {'hips': (-.04, .0), 'turn': {'spine': (-5, 0, 0), 'chest': (-13, 0, 0), 'head': (11, 0, 0)},
              'shrug': {'l': (16, -12), 'r': (16, -12)},
              'feet': {'l': ankle(L0, .08), 'r': ankle(R0, -.04)},
              'hands': {'l': (.82, .02, 1.62), 'r': (-.82, .06, 1.62)}, 'aim': {'l': (1, 0, .3), 'r': (-1, 0, .3)}}),
        (16, {}),
    ],
    # Arcade select: stands tall, feet wide, arms folded over the chest, chin up, slow breathing.
    'select': [
        (f, {'hips': (.0, .06 + .02 * (1 - math.cos(math.pi * f / 24))),
             'feet': {'l': (.30, -.04, GROUND), 'r': (-.30, .08, GROUND)},
             'turn': {'hips': (0, 0, 0), 'spine': (0, 0, 0), 'chest': (-6 + 2 * (1 - math.cos(math.pi * f / 24)), 0, 0), 'head': (-10, 0, 0)},
             'shrug': {'l': (8 + 4 * (1 - math.cos(math.pi * f / 24)), 6), 'r': (8 + 4 * (1 - math.cos(math.pi * f / 24)), 6)},
             'hands': {'l': (-.22, -.30, 1.42), 'r': (.22, -.32, 1.48)},
             'elbow': {'l': (1, -1.2, -.3), 'r': (-1, -1.2, -.2)}})
        for f in range(0, 49, 6)
    ],
    # Victory: plants the feet, slams both fists up into a double-biceps flex, chest puffed and
    # head back laughing; holds it, then rolls the shoulders and flexes again.
    'victory': [
        (0, {}),
        (8, {'hips': (.0, .14), 'turn': {'chest': (16, 0, 0), 'head': (-20, 0, 0)}, 'shrug': {'l': (6, 10), 'r': (6, 10)},
             'feet': {'l': (.32, -.04, GROUND), 'r': (-.32, .10, GROUND)},
             'hands': {'l': (.40, -.30, .96), 'r': (-.40, -.30, .96)}}),
        (12, {'hips': (.0, .04), 'turn': {'spine': (-4, 0, 0), 'chest': (-12, 0, 0), 'head': (16, 0, 0)},
              'shrug': {'l': (22, 0), 'r': (22, 0)},
              'feet': {'l': (.32, -.04, GROUND), 'r': (-.32, .10, GROUND)},
              'hands': {'l': (.56, -.06, 1.94), 'r': (-.56, -.06, 1.94)}, 'aim': {'l': (-.3, 0, 1), 'r': (.3, 0, 1)},
              'elbow': {'l': (1, .1, -.4), 'r': (-1, .1, -.4)},
              'scale': {'upper_arm_l': (1.2, 1.0, 1.2), 'upper_arm_r': (1.2, 1.0, 1.2), 'chest': (1.06, 1.0, 1.06)}}),
        (28, {'hips': (.0, .04), 'turn': {'spine': (-4, 0, 0), 'chest': (-12, 0, 4), 'head': (16, 0, -4)},
              'shrug': {'l': (20, 0), 'r': (20, 0)},
              'feet': {'l': (.32, -.04, GROUND), 'r': (-.32, .10, GROUND)},
              'hands': {'l': (.56, -.06, 1.92), 'r': (-.56, -.06, 1.92)}, 'aim': {'l': (-.3, 0, 1), 'r': (.3, 0, 1)},
              'elbow': {'l': (1, .1, -.4), 'r': (-1, .1, -.4)},
              'scale': {'upper_arm_l': (1.2, 1.0, 1.2), 'upper_arm_r': (1.2, 1.0, 1.2), 'chest': (1.06, 1.0, 1.06)}}),
        (34, {'hips': (.0, .08), 'turn': {'chest': (4, 0, -6), 'head': (-6, 0, 6)}, 'shrug': {'l': (12, 6), 'r': (12, 6)},
              'feet': {'l': (.32, -.04, GROUND), 'r': (-.32, .10, GROUND)},
              'hands': {'l': (.62, -.10, 1.60), 'r': (-.62, -.10, 1.60)}, 'elbow': {'l': (1, .1, -.6), 'r': (-1, .1, -.6)}}),
        (40, {'hips': (.0, .04), 'turn': {'spine': (-4, 0, 0), 'chest': (-14, 0, 0), 'head': (18, 0, 0)},
              'shrug': {'l': (24, 0), 'r': (24, 0)},
              'feet': {'l': (.32, -.04, GROUND), 'r': (-.32, .10, GROUND)},
              'hands': {'l': (.56, -.06, 1.96), 'r': (-.56, -.06, 1.96)}, 'aim': {'l': (-.3, 0, 1), 'r': (.3, 0, 1)},
              'elbow': {'l': (1, .1, -.4), 'r': (-1, .1, -.4)},
              'scale': {'upper_arm_l': (1.25, 1.0, 1.25), 'upper_arm_r': (1.25, 1.0, 1.25), 'chest': (1.08, 1.0, 1.08)}}),
        (56, {'hips': (.0, .04), 'turn': {'spine': (-4, 0, 0), 'chest': (-14, 0, 0), 'head': (18, 0, 0)},
              'shrug': {'l': (24, 0), 'r': (24, 0)},
              'feet': {'l': (.32, -.04, GROUND), 'r': (-.32, .10, GROUND)},
              'hands': {'l': (.56, -.06, 1.96), 'r': (-.56, -.06, 1.96)}, 'aim': {'l': (-.3, 0, 1), 'r': (.3, 0, 1)},
              'elbow': {'l': (1, .1, -.4), 'r': (-1, .1, -.4)},
              'scale': {'upper_arm_l': (1.25, 1.0, 1.25), 'upper_arm_r': (1.25, 1.0, 1.25), 'chest': (1.08, 1.0, 1.08)}}),
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
    **SPECIALS,
    **REACTIONS,
    **MOVES,
    **OTHER,
}
la.SHEETS['ignis'] = SHEETS


def ensure_clip(rig, clip):
    """A clip the old Ignis rig never had (heavy_2): an empty action on its own NLA track, so
    legends_anim.author can replace it and the export picks it up."""
    import bpy
    if clip in bpy.data.actions:
        return
    act = bpy.data.actions.new(clip)
    act.use_fake_user = True
    track = rig.animation_data.nla_tracks.new()
    track.name = clip
    strip = track.strips.new(clip, 0, act)
    track.mute = True


def author(rig, clips=None, force=False):
    """Author Dale's sheets on dale_Rig (all, or the named clips, in order)."""
    for c in (clips or SHEETS):
        ensure_clip(rig, c)
    return [la.author(rig, c, 'ignis', force).name for c in (clips or SHEETS)]
