"""X12 (fighter id 'tophia') limited-animation sheets for legends_anim.place().

A boxer (Balrog in SF2 is the reference): high guard with the fists in front of the chin, chin
tucked, lead (left) foot forward, always on the balls of the feet. Her rig is the new Legends
body (legends_rig.py), so poses start from its rest pose ('START': 'rest'), not from the old
clips. Joints (x12_modelo.JOINTS): ankle z .26, hip .86, knee .62, shoulder 1.37.

Run in Blender: import legends_x12_anim as x; x.author(rig, ['idle', 'select'])
"""
import math

import legends_anim as la

GROUND = .26                                 # ankle height with the sole flat on the floor
L0, R0 = (.15, -.14, GROUND), (-.15, .22, GROUND)       # boxing stance: left foot leads
BASE_SINK = .05                              # knees a little bent
# Guard: fists in front of the chin (wrists a fist below), elbows down in front of the ribs.
HANDS = {'l': (.10, -.32, 1.30), 'r': (-.07, -.24, 1.26)}
ELBOW = {'l': (.25, -.2, -1), 'r': (-.25, -.2, -1)}
AIM_UP = (0, -.35, 1)                        # fist knuckles up and a little forward
# Side-on to the opponent (left shoulder forward), chin down, eyes on the opponent.
TURN = {'hips': (2, 0, -16), 'spine': (4, 0, -6), 'chest': (8, 0, -10), 'head': (-6, 0, 22)}
la.PROFILES['tophia'] = {'L0': L0, 'R0': R0, 'GROUND': GROUND, 'BASE_SINK': BASE_SINK, 'HANDS': HANDS,
                         'ELBOW': ELBOW, 'TURN': TURN, 'START': 'rest'}
# ankle -> toe tip of her boot at rest (x12_perna BOOT), for standing on tiptoe
TOE = (0.0, -.30, -.23)


def tiptoe(base, lift):
    """Ankle target and foot pitch (degrees) for a heel raised `lift` metres with the toe tip
    staying where it was (on the balls of the feet)."""
    y, z = TOE[1], TOE[2]
    want = z - lift
    lo, hi = 0.0, 80.0
    for _ in range(40):
        mid = (lo + hi) / 2
        t = math.radians(mid)
        if y * math.sin(t) + z * math.cos(t) > want:
            lo = mid
        else:
            hi = mid
    t = math.radians(lo)
    dy = (y * math.cos(t) - z * math.sin(t)) - y            # the ankle moves so the toe stays put
    return (base[0], base[1] - dy, base[2] + lift), lo


def hand(side, dx=0.0, fwd=0.0, up=0.0):
    b = HANDS[side]
    return (b[0] + dx, b[1] - fwd, b[2] + up)


def idle_sheet(n=40):
    """Boxer's bounce: two hops per cycle on the balls of the feet. Land (heels just down,
    knees bent), push up onto the toes, a moment in the air with the toes pointed, land on the
    toes; the fists bob a beat behind the body and the shoulders roll."""
    out = []
    hop = n // 2
    for h in range(2):
        f0 = h * hop
        side = 1 if h == 0 else -1               # the shoulders roll the other way on each hop
        lands = {s: tiptoe(b, .03) for s, b in (('l', L0), ('r', R0))}
        toes = {s: tiptoe(b, .09) for s, b in (('l', L0), ('r', R0))}
        air = {s: tiptoe((b[0], b[1], b[2] + .07), .09) for s, b in (('l', L0), ('r', R0))}
        aim = {'l': AIM_UP, 'r': AIM_UP}
        keys = [
            (0, {'hips': (0, .08), 'feet': {s: lands[s][0] for s in 'lr'}, 'foot_turn': {s: lands[s][1] for s in 'lr'},
                 'shrug': {'l': (2, 4 * side), 'r': (2, -4 * side)},
                 'hands': {'l': hand('l', up=-.03), 'r': hand('r', up=-.03)}, 'aim': aim}),
            (5, {'hips': (0, -.03), 'feet': {s: toes[s][0] for s in 'lr'}, 'foot_turn': {s: toes[s][1] for s in 'lr'},
                 'shrug': {'l': (8, 2 * side), 'r': (8, -2 * side)},
                 'hands': {'l': hand('l', up=-.01), 'r': hand('r', up=-.01)}, 'aim': aim}),
            (10, {'free': True, 'hips': (0, BASE_SINK - .10), 'turn': TURN,
                  'feet': {s: air[s][0] for s in 'lr'}, 'foot_turn': {s: air[s][1] + 6 for s in 'lr'},
                  'shrug': {'l': (10, 0), 'r': (10, 0)},
                  'hands': {'l': hand('l', up=.02), 'r': hand('r', up=.02)}, 'aim': aim, 'elbow': ELBOW}),
            (15, {'hips': (0, .0), 'feet': {s: toes[s][0] for s in 'lr'}, 'foot_turn': {s: toes[s][1] for s in 'lr'},
                  'shrug': {'l': (6, -2 * side), 'r': (6, 2 * side)},
                  'hands': {'l': hand('l', up=.01), 'r': hand('r', up=.01)}, 'aim': aim}),
        ]
        out += [(f0 + f, k) for f, k in keys]
    out.append((n, out[0][1]))
    return out


# Select (presentation, no fight): feet together, arms behind her back, rocking forward onto her
# toes and back onto her heels, face to the camera (the select screen shows her front).
FEET_TOGETHER = {'l': (.11, -.02, GROUND), 'r': (-.11, .02, GROUND)}
BEHIND = {'l': (.13, .24, 1.04), 'r': (-.13, .24, 1.04)}           # wrists behind the lower back
BEHIND_ELBOW = {'l': (1, .7, -.3), 'r': (-1, .7, -.3)}
FRONT_TURN = {'hips': (0, 0, 0), 'spine': (0, 0, 0), 'chest': (0, 0, 0), 'head': (0, 0, 0)}


def select_sheet(n=40, keys=10):     # the menu loops it over the victory length (40)
    out = []
    for i in range(keys + 1):
        t = i / keys
        rock = math.sin(2 * math.pi * t)          # + forward onto the toes, - back onto the heels
        fwd = max(rock, 0.0)
        feet, pitch = {}, {}
        for s, b in FEET_TOGETHER.items():
            if fwd > 0.05:
                feet[s], pitch[s] = tiptoe(b, .07 * fwd)
            else:
                feet[s], pitch[s] = b, 12 * rock    # back on the heels: toes lift a little
        out.append((round(n * t), {
            'hips': (.05 * rock, -.03 * fwd),
            'turn': {**FRONT_TURN, 'spine': (3 * rock, 0, 0), 'chest': (6 * rock, 0, 2 * rock),
                     'head': (-6 * rock, 6 * math.sin(math.pi * t), 0)},
            'shrug': {'l': (6 - 4 * rock, -10), 'r': (6 - 4 * rock, -10)},
            'feet': feet, 'foot_turn': pitch,
            'hands': BEHIND, 'elbow': BEHIND_ELBOW,
        }))
    return out


def ankle(base, forward=0.0, up=0.0):
    return (base[0], base[1] - forward, base[2] + up)


def held(pose, settle=.01):
    out = {k: v for k, v in pose.items() if k != 'scale'}
    if 'hips' in out:
        out['hips'] = (out['hips'][0], out['hips'][1] + settle)
    return out


# ---- J1 jab and J2 cross, after the references (SLYNYRD Pixelblog 53; the SF4/SF5 punch
# comparison, 80.lv): power from the hips, the trunk leaning far into the punch with the head
# dropped behind the lead shoulder (you barely see it), never upright with the face to camera.
# Jab: NO wind-up (it would telegraph); the key pose is already in the first (smear) frame, the
# hit frame held a little longer, the arm one notch further on the follow, a snap back past the
# guard. Cross: a short load (both fists up, elbows out like chicken wings) and pull, then the
# hips turn the whole body into profile, the rear knee forward and down, the rear heel high, the
# free elbow jutting behind the trunk. Hand targets are world space (gfist follows the hips). ----
def gfist(side, fwd, up=0.0):
    return hand(side, fwd=fwd, up=up)


_jab_heel, _jab_pitch = tiptoe(ankle(R0, .12), .12)
JAB = {'hips': (.30, .14), 'turn': {'hips': (10, 0, -30), 'spine': (12, 0, -12), 'chest': (26, 0, -36), 'head': (6, 0, 14)},
       'feet': {'l': ankle(L0, .36), 'r': _jab_heel}, 'foot_turn': {'r': _jab_pitch}, 'knee': {'r': (0, -1, -.4)},
       'shrug': {'l': (6, 30), 'r': (8, -6)},
       'hands': {'l': (.04, -1.04, 1.22), 'r': gfist('r', .40, -.08)}, 'elbow': {'l': (1, 0, -.3), 'r': ELBOW['r']},
       'aim': {'l': (0, -1, 0), 'r': AIM_UP}, 'robe': {'robe_front': (22, 0, 0), 'robe_back': (16, 0, 0)},
       'scale': {'forearm_l': (1, 1.12, 1), 'hand_l': (1.4, 1.4, 1.4)}}
_cross_heel, _cross_pitch = tiptoe(ankle(R0, -.02), .20)         # rear foot stays back, heel high
CROSS = {'hips': (.36, .09), 'turn': {'hips': (12, 0, 40), 'spine': (14, 0, 20), 'chest': (30, 0, 56), 'head': (8, 0, -26)},
         'feet': {'l': ankle(L0, .46), 'r': _cross_heel}, 'foot_turn': {'r': _cross_pitch}, 'pivot': {'r': 60},
         'knee': {'r': (0, -1, -.2), 'l': (0, -1, 0)},
         'shrug': {'r': (6, 34), 'l': (10, -18)},
         'hands': {'r': (-.02, -1.16, 1.20), 'l': (.24, -.02 - .40, 1.14)}, 'elbow': {'r': (-1, 0, -.3), 'l': (1, 1, -.2)},
         'aim': {'r': (0, -1, 0), 'l': AIM_UP}, 'robe': {'robe_front': (26, 0, 0), 'robe_back': (18, 0, 0)},
         'scale': {'forearm_r': (1, 1.12, 1), 'hand_r': (1.45, 1.45, 1.45)}}
# J3 body hook (the game's third punch hits low): an arc, not a straight line. A short dip and
# lean to her right loads the left side, the elbow swings out wide (smear), the fist comes round
# level into the liver with the elbow out at the same height, the trunk turned hard through, the
# head down behind the right fist.
HOOK = {'hips': (.30, .22), 'turn': {'hips': (10, -4, -44), 'spine': (14, -6, -20), 'chest': (26, -10, -54), 'head': (10, 8, 20)},
        'feet': {'l': ankle(L0, .34), 'r': ankle(R0, .02, .06)}, 'knee': {'l': (.4, -1, 0)},
        'shrug': {'l': (8, 26), 'r': (6, -10)},
        'hands': {'l': (-.06, -.74, 1.00), 'r': gfist('r', .34, -.10)}, 'elbow': {'l': (1, .2, .2), 'r': ELBOW['r']},
        'aim': {'l': (-1, -.2, 0), 'r': AIM_UP}, 'robe': {'robe_front': (18, 0, 0), 'robe_back': (10, 0, 0)},
        'scale': {'hand_l': (1.45, 1.45, 1.45), 'forearm_l': (1.1, 1.1, 1.1)}}
LIGHT = {
    # J1 jab (anim_timing tophia light_1: contact 3, hold 8, follow 10, recover 16, end 22)
    'light_1': [
        (0, {}),
        (2, {**JAB, 'hips': (.20, .12), 'feet': {'l': ankle(L0, .26, .04), 'r': ankle(R0, .06)}, 'foot_turn': {},
             'hands': {'l': (.06, -.86, 1.24), 'r': gfist('r', .30, -.06)},
             'scale': {'forearm_l': (1, 1.45, 1), 'hand_l': (1.2, 1.2, 1.2)}}),            # smear
        (3, JAB),
        (8, held(JAB)),
        (10, {**held(JAB, .02), 'hands': {'l': (.03, -1.10, 1.21), 'r': gfist('r', .40, -.08)},
              'turn': {'hips': (10, 0, -34), 'spine': (12, 0, -14), 'chest': (28, 0, -40), 'head': (6, 0, 14)},
              'robe': {'robe_front': (-10, 0, 0), 'robe_back': (-6, 0, 0)}}),          # follow-through
        (16, {'hips': (.10, .08), 'turn': {'chest': (12, 0, -14), 'head': (-2, 0, 18)},
              'feet': {'l': ankle(L0, .10)}, 'hands': {'l': gfist('l', .16), 'r': gfist('r', .10)},
              'aim': {'l': AIM_UP, 'r': AIM_UP}, 'robe': {'robe_front': (6, 0, 0)}}),       # recover
        (19, {'hips': (-.04, .07), 'hands': {'l': gfist('l', -.04), 'r': gfist('r', -.04)},
              'aim': {'l': AIM_UP, 'r': AIM_UP}, 'robe': {'robe_front': (-4, 0, 0)}}),       # snap back
        (22, {}),
    ],
    # J2 cross (anim_timing tophia light_2: wind 5, contact 8, hold 12, follow 14, end 26)
    'light_2': [
        (0, {'from': ('light_1', 10)}),
        # load: both fists up, elbows out like chicken wings, weight settling
        (3, {'hips': (.16, .14), 'turn': {'hips': (8, 0, -24), 'chest': (16, 0, -30), 'head': (4, 0, 22)},
             'feet': {'l': ankle(L0, .22)}, 'shrug': {'l': (16, 0), 'r': (16, 0)},
             'hands': {'l': gfist('l', .18, .10), 'r': gfist('r', .14, .10)}, 'elbow': {'l': (1, -.2, 0), 'r': (-1, -.2, 0)},
             'aim': {'l': AIM_UP, 'r': AIM_UP}}),
        # pull: the right forearm drawn back, trunk wound to the left
        (5, {'hips': (.14, .16), 'turn': {'hips': (8, 0, -30), 'chest': (18, 0, -40), 'head': (4, 0, 26)},
             'feet': {'l': ankle(L0, .22)}, 'shrug': {'l': (12, 4), 'r': (10, -16)},
             'hands': {'l': gfist('l', .18, .06), 'r': (-.16, .02, 1.22)}, 'elbow': {'l': (1, -.2, -.2), 'r': (-1, .6, -.2)},
             'aim': {'l': AIM_UP, 'r': (0, -1, .2)}}),
        # smear: hips whip round into profile, the arm nearly out, forearm stretched
        (7, {**CROSS, 'hips': (.30, .09), 'turn': {'hips': (12, 0, 26), 'spine': (12, 0, 14), 'chest': (26, 0, 40), 'head': (8, 0, -16)},
             'hands': {'r': (-.04, -.94, 1.21), 'l': (.24, -.36, 1.14)},
             'scale': {'forearm_r': (1, 1.45, 1), 'hand_r': (1.2, 1.2, 1.2)}}),
        (8, CROSS),
        (12, held(CROSS)),
        (14, {**held(CROSS, .02), 'hands': {'r': (-.04, -1.22, 1.19), 'l': (.24, -.42, 1.14)},
              'turn': {'hips': (12, 0, 44), 'spine': (14, 0, 22), 'chest': (32, 0, 60), 'head': (8, 0, -28)},
              'robe': {'robe_front': (-12, 0, 0), 'robe_back': (-8, 0, 0)}}),
        (20, {'hips': (.14, .08), 'turn': {'chest': (12, 0, 10), 'head': (-2, 0, 10)},
              'feet': {'l': ankle(L0, .14)}, 'hands': {'l': gfist('l', .14), 'r': gfist('r', .14)},
              'aim': {'l': AIM_UP, 'r': AIM_UP}, 'robe': {'robe_front': (6, 0, 0)}}),
        (23, {'hips': (-.04, .07), 'hands': {'l': gfist('l', -.04), 'r': gfist('r', -.04)},
              'aim': {'l': AIM_UP, 'r': AIM_UP}, 'robe': {'robe_front': (-4, 0, 0)}}),
        (26, {}),
    ],
    # J3 body hook (anim_timing tophia light_3: wind 4, contact 7, hold 11, follow 13, end 24)
    'light_3': [
        (0, {'from': ('light_2', 14)}),
        (4, {'hips': (.16, .24), 'turn': {'hips': (8, 6, 16), 'spine': (10, 8, 8), 'chest': (18, 12, 24), 'head': (8, -6, 26)},
             'feet': {'l': ankle(L0, .20)}, 'shrug': {'l': (4, -18)},
             'hands': {'l': (.42, -.14, 1.04), 'r': gfist('r', .18, -.06)}, 'elbow': {'l': (1, .5, .1)},
             'aim': {'l': (0, -.5, .5), 'r': AIM_UP}}),
        (6, {**HOOK, 'hips': (.24, .22), 'turn': {'hips': (10, -2, -20), 'spine': (12, -4, -8), 'chest': (22, -6, -24), 'head': (10, 6, 24)},
             'hands': {'l': (.36, -.62, 1.02), 'r': gfist('r', .26, -.10)}, 'elbow': {'l': (1, .3, .2)},
             'aim': {'l': (-.6, -.8, 0), 'r': AIM_UP},
             'scale': {'forearm_l': (1.1, 1.4, 1.1), 'hand_l': (1.2, 1.2, 1.2)}}),
        (7, HOOK),
        (11, held(HOOK)),
        (13, {**held(HOOK, .02), 'hands': {'l': (-.18, -.66, 1.00), 'r': gfist('r', .34, -.10)},
              'turn': {'hips': (10, -4, -50), 'spine': (14, -6, -22), 'chest': (28, -10, -60), 'head': (10, 8, 22)},
              'robe': {'robe_front': (-12, 0, 0), 'robe_back': (-8, 0, 0)}}),
        (19, {'hips': (.12, .10), 'turn': {'chest': (12, 0, -14), 'head': (-2, 0, 18)},
              'feet': {'l': ankle(L0, .12)}, 'hands': {'l': gfist('l', .12), 'r': gfist('r', .10)},
              'aim': {'l': AIM_UP, 'r': AIM_UP}, 'robe': {'robe_front': (6, 0, 0)}}),
        (21, {'hips': (-.04, .07), 'hands': {'l': gfist('l', -.04), 'r': gfist('r', -.04)},
              'aim': {'l': AIM_UP, 'r': AIM_UP}}),
        (24, {}),
    ],
}

def walk_sheet(direction=1, n=24, keys=8, stride=.42):
    """Boxer's shuffle (never crossing the feet): walking in, the lead foot steps first and the
    rear one follows; walking back, the rear foot steps back first. Feet are written in the
    ground's frame and moved back by the body's travel, so a planted foot holds its spot. Light
    on the balls of the feet, a little bob on each step, the guard up."""
    out = []
    uL, uR = -L0[1], -R0[1]
    for i in range(keys + 1):
        t = i / keys
        first = la.ease(min(t / .5, 1.0))
        second = la.ease(max((t - .5) / .5, 0.0))
        root = stride * t * direction
        lead_sw, rear_sw = (first, second) if direction > 0 else (second, first)
        ul = uL + stride * lead_sw * direction - root
        ur = uR + stride * rear_sw * direction - root
        lift_l = .05 * math.sin(math.pi * lead_sw) if 0 < lead_sw < 1 else 0.0
        lift_r = .05 * math.sin(math.pi * rear_sw) if 0 < rear_sw < 1 else 0.0
        bob = abs(math.sin(2 * math.pi * t))
        fl, pl = tiptoe((L0[0], -ul, GROUND + lift_l), .03)
        fr, pr = tiptoe((R0[0], -ur, GROUND + lift_r), .05)
        out.append((round(n * t), {
            'hips': (.02 * direction, .03 - .025 * bob),
            'turn': {'chest': (8 + 3 * direction, 0, -10), 'head': (-6 - 3 * direction, 0, 22)},
            'shrug': {'l': (4 + 4 * bob, 0), 'r': (4 + 4 * bob, 0)},
            'feet': {'l': fl, 'r': fr}, 'foot_turn': {'l': pl, 'r': pr},
            'aim': {'l': AIM_UP, 'r': AIM_UP},
        }))
    return out


def hold(n, pose, settle=None):
    keys = [(0, pose)]
    if settle:
        keys.append((n // 2, settle))
    keys.append((n, settle or pose))
    return keys


# Peekaboo guard: both gloves up in front of the face, forearms together covering the chin and
# chest, elbows in, chin tucked behind the gloves.
GUARD_HIGH = {'hips': (-.03, .07), 'turn': {'chest': (12, 0, -6), 'head': (-2, 0, 14)},
              'shrug': {'l': (14, 10), 'r': (14, 10)},
              'hands': {'l': (.07, -.30, 1.48), 'r': (-.05, -.26, 1.46)},
              'elbow': {'l': (.2, -.4, -1), 'r': (-.2, -.4, -1)}, 'aim': {'l': (0, 0, 1), 'r': (0, 0, 1)}}
CROUCH = {'hips': (.04, .42), 'turn': {'hips': (14, 0, -10), 'chest': (20, 0, -8), 'head': (-14, 0, 18)},
          'shrug': {'l': (8, 6), 'r': (8, 6)},
          'feet': {'l': ankle(L0, .04), 'r': ankle(R0, -.04)},
          'hands': {'l': (.10, -.42, .96), 'r': (-.07, -.34, .92)}, 'aim': {'l': AIM_UP, 'r': AIM_UP}}
GUARD_LOW = {**CROUCH, 'shrug': {'l': (14, 12), 'r': (14, 12)},
             'hands': {'l': (.07, -.32, 1.02), 'r': (-.05, -.28, 1.00)},
             'elbow': {'l': (.2, -.3, -1), 'r': (-.2, -.3, -1)}, 'aim': {'l': (0, 0, 1), 'r': (0, 0, 1)}}
# Parry as a slip: the head and trunk duck off the line to her right and down (knees bend, the
# weight on the rear leg), gloves still up; held, then back up into the guard.
SLIP = {'hips': (-.06, .14), 'turn': {'hips': (4, -6, 6), 'spine': (8, -10, 4), 'chest': (14, -16, 6), 'head': (-6, -10, 16)},
        'feet': {'l': ankle(L0, .02), 'r': ankle(R0, -.02)}, 'shrug': {'l': (12, 6), 'r': (8, 0)},
        'hands': {'l': (.02, -.32, 1.28), 'r': (-.14, -.20, 1.22)}, 'aim': {'l': (0, 0, 1), 'r': (0, 0, 1)}}

MOVEMENT = {
    'walk_forward': walk_sheet(1),
    'walk_back': walk_sheet(-1),
    'crouch': hold(10, CROUCH),
    'guard_high': hold(10, GUARD_HIGH, held(GUARD_HIGH)),
    'guard_low': hold(10, GUARD_LOW, held(GUARD_LOW)),
    'parry': [(0, {}), (3, SLIP), (10, held(SLIP)), (16, {})],
}


# ---- Heavy: dash overhand (the game's heavy is an overhead). A real wind-up (heavy blow): she
# sinks back onto the rear leg, the right fist cocked high behind the head, then lunges far in,
# the fist coming over the top and down onto the head, the whole body behind it. ----
_oh_heel, _oh_pitch = tiptoe(ankle(R0, .10), .22)
OVERHAND = {'hips': (.56, .18), 'turn': {'hips': (14, 0, 40), 'spine': (16, 0, 22), 'chest': (36, 0, 54), 'head': (12, 0, -22)},
            'feet': {'l': ankle(L0, .66), 'r': _oh_heel}, 'foot_turn': {'r': _oh_pitch}, 'pivot': {'r': 55},
            'knee': {'r': (0, -1, -.3)}, 'shrug': {'r': (10, 34), 'l': (6, -16)},
            'hands': {'r': (-.02, -1.18, 1.28), 'l': (.26, -.50, 1.06)}, 'elbow': {'r': (-1, .3, .6), 'l': (1, 1, -.2)},
            'aim': {'r': (0, -.6, -.8), 'l': AIM_UP}, 'robe': {'robe_front': (28, 0, 0), 'robe_back': (20, 0, 0)},
            'scale': {'hand_r': (1.5, 1.5, 1.5), 'forearm_r': (1.1, 1.15, 1.1)}}
# ---- down_punch: rising uppercut out of the crouch, launching (the move launches). ----
UPPER = {'hips': (.18, -.08), 'turn': {'hips': (-4, 0, 34), 'spine': (-4, 0, 18), 'chest': (-10, 0, 44), 'head': (-8, 0, -10)},
         'feet': {'l': tiptoe(ankle(L0, .16), .10)[0], 'r': tiptoe(ankle(R0, .04), .12)[0]},
         'foot_turn': {'l': tiptoe(ankle(L0, .16), .10)[1], 'r': tiptoe(ankle(R0, .04), .12)[1]},
         'shrug': {'r': (24, 20), 'l': (6, -10)},
         'hands': {'r': (-.02, -.48, 1.86), 'l': gfist('l', .18, .02)}, 'elbow': {'r': (-1, -.2, -.3), 'l': ELBOW['l']},
         'aim': {'r': (0, -.2, 1), 'l': AIM_UP}, 'robe': {'robe_front': (-16, 0, 0), 'robe_back': (-10, 0, 0)},
         'scale': {'hand_r': (1.45, 1.45, 1.45), 'forearm_r': (1, 1.15, 1)}}
CROUCH_START = {'hips': (.04, .42), 'turn': {'hips': (14, 0, -10), 'chest': (20, 0, -8), 'head': (-4, 0, 18)},
                'feet': {'l': ankle(L0, .04), 'r': ankle(R0, -.04)},
                'hands': {'l': (.10, -.42, .96), 'r': (-.07, -.34, .92)}, 'aim': {'l': AIM_UP, 'r': AIM_UP}}
# ---- sweep (crouching heavy, low): dash low punch, the body nearly flat over the lead leg,
# the right fist driving at the shins. ----
LOWPUNCH = {'hips': (.50, .52), 'turn': {'hips': (24, 0, 36), 'spine': (20, 0, 18), 'chest': (34, 0, 48), 'head': (14, 0, -16)},
            'feet': {'l': ankle(L0, .66), 'r': ankle(R0, .02)}, 'knee': {'r': (0, -1, -1)},
            'shrug': {'r': (6, 32), 'l': (8, -14)},
            'hands': {'r': (-.02, -1.24, .52), 'l': (.24, -.62, .92)}, 'elbow': {'r': (-1, .2, -.3), 'l': (1, 1, -.2)},
            'aim': {'r': (0, -1, -.15), 'l': AIM_UP}, 'robe': {'robe_front': (20, 0, 0), 'robe_back': (30, 0, 0)},
            'scale': {'hand_r': (1.45, 1.45, 1.45), 'forearm_r': (1, 1.15, 1)}}
# ---- air_punch (overhead): in the air, knees tucked, both fists hammered down in front. ----
AIR_TUCK = {'free': True, 'hips': (.0, -.30), 'turn': {'hips': (10, 0, -10), 'chest': (16, 0, -10), 'head': (-2, 0, 14)},
            'feet': {'l': (.15, -.24, .90), 'r': (-.15, .16, .84)}, 'knee': {'l': (0, -1, .2), 'r': (0, -1, .2)},
            'hands': {'l': (.10, -.34, 1.58), 'r': (-.07, -.28, 1.54)}, 'aim': {'l': AIM_UP, 'r': AIM_UP}, 'elbow': ELBOW}
HAMMER = {**AIR_TUCK, 'turn': {'hips': (24, 0, 0), 'spine': (14, 0, 0), 'chest': (30, 0, 0), 'head': (12, 0, 0)},
          'feet': {'l': (.15, -.10, .84), 'r': (-.15, .32, .92)},
          'hands': {'l': (.06, -.78, 1.10), 'r': (-.06, -.78, 1.08)}, 'aim': {'l': (0, -.4, -.9), 'r': (0, -.4, -.9)},
          'elbow': {'l': (1, .2, .2), 'r': (-1, .2, .2)}, 'shrug': {'l': (6, 24), 'r': (6, 24)},
          'robe': {'robe_front': (-20, 0, 0), 'robe_back': (24, 0, 0)},
          'scale': {'hand_l': (1.4, 1.4, 1.4), 'hand_r': (1.4, 1.4, 1.4)}}

SPECIAL = {
    # heavy (anim_timing tophia heavy: wind 8, contact 12, hold 17, follow 20, recover 28, end 34)
    'heavy': [
        (0, {}),
        (4, {'hips': (-.10, .16), 'turn': {'hips': (6, 0, -30), 'chest': (10, 0, -44), 'head': (6, 0, 34)},
             'feet': {'l': ankle(L0, -.02, .03)}, 'shrug': {'r': (24, -20)},
             'hands': {'r': (-.24, .14, 1.56), 'l': gfist('l', -.06)}, 'elbow': {'r': (-1, .5, .3)},
             'aim': {'r': (0, .2, 1), 'l': AIM_UP}, 'robe': {'robe_front': (-8, 0, 0)}}),
        (8, {'hips': (-.14, .18), 'turn': {'hips': (6, 0, -36), 'chest': (8, 0, -52), 'head': (6, 0, 38)},
             'feet': {'l': ankle(L0, -.02, .03)}, 'shrug': {'r': (28, -22)},
             'hands': {'r': (-.28, .20, 1.62), 'l': gfist('l', -.08)}, 'elbow': {'r': (-1, .5, .4)},
             'aim': {'r': (0, .3, 1), 'l': AIM_UP}, 'robe': {'robe_front': (-10, 0, 0)}}),
        (11, {**OVERHAND, 'hips': (.42, .12), 'hands': {'r': (-.06, -.86, 1.70), 'l': (.26, -.40, 1.10)},
              'aim': {'r': (0, -.6, .6), 'l': AIM_UP}, 'feet': {'l': ankle(L0, .54, .06), 'r': _oh_heel},
              'scale': {'forearm_r': (1.1, 1.45, 1.1), 'hand_r': (1.25, 1.25, 1.25)}}),
        (12, OVERHAND),
        (17, held(OVERHAND, .02)),
        (20, {**held(OVERHAND, .04), 'hands': {'r': (-.02, -1.10, 1.02), 'l': (.26, -.52, 1.06)},
              'turn': {'hips': (16, 0, 44), 'spine': (18, 0, 24), 'chest': (40, 0, 58), 'head': (14, 0, -24)},
              'robe': {'robe_front': (-14, 0, 0), 'robe_back': (-10, 0, 0)}}),
        (28, {'hips': (.22, .10), 'turn': {'chest': (12, 0, 10), 'head': (-2, 0, 12)},
              'feet': {'l': ankle(L0, .24)}, 'hands': {'l': gfist('l', .22), 'r': gfist('r', .22)},
              'aim': {'l': AIM_UP, 'r': AIM_UP}, 'robe': {'robe_front': (8, 0, 0)}}),
        (31, {'hips': (-.04, .07), 'hands': {'l': gfist('l', -.04), 'r': gfist('r', -.04)}, 'aim': {'l': AIM_UP, 'r': AIM_UP}}),
        (34, {}),
    ],
    # down_punch (wind 3, contact 6, hold 10, follow 12, recover 18, end 24)
    'down_punch': [
        (0, CROUCH_START),
        (3, {**CROUCH_START, 'hips': (.02, .48), 'turn': {'hips': (16, 0, -20), 'chest': (24, 0, -28), 'head': (6, 0, 26)},
             'shrug': {'r': (2, -14)}, 'hands': {'r': (-.14, -.20, .78), 'l': (.10, -.42, .98)},
             'aim': {'r': (0, -.3, 1), 'l': AIM_UP}}),
        (5, {**UPPER, 'hips': (.12, .14), 'hands': {'r': (-.04, -.58, 1.30), 'l': gfist('l', .12)},
             'turn': {'hips': (6, 0, 20), 'spine': (4, 0, 10), 'chest': (6, 0, 26), 'head': (2, 0, -4)},
             'scale': {'forearm_r': (1, 1.45, 1), 'hand_r': (1.2, 1.2, 1.2)}}),
        (6, UPPER),
        (10, held(UPPER)),
        (12, {**held(UPPER, .0), 'hands': {'r': (-.02, -.40, 1.96), 'l': gfist('l', .18, .04)},
              'robe': {'robe_front': (10, 0, 0), 'robe_back': (6, 0, 0)}}),
        (18, {'hips': (.08, .10), 'hands': {'l': gfist('l', .08), 'r': gfist('r', .08)}, 'aim': {'l': AIM_UP, 'r': AIM_UP}}),
        (24, {}),
    ],
    # sweep (wind 5, contact 8, hold 12, follow 15, recover 22, end 28)
    'sweep': [
        (0, CROUCH_START),
        (5, {**CROUCH_START, 'hips': (-.06, .50), 'turn': {'hips': (18, 0, -24), 'chest': (24, 0, -34), 'head': (8, 0, 28)},
             'shrug': {'r': (4, -16)}, 'hands': {'r': (-.20, .06, .90), 'l': (.10, -.40, .96)}, 'aim': {'r': (0, -1, 0), 'l': AIM_UP}}),
        (7, {**LOWPUNCH, 'hips': (.36, .50), 'hands': {'r': (-.04, -1.00, .58), 'l': (.24, -.52, .94)},
             'scale': {'forearm_r': (1, 1.45, 1), 'hand_r': (1.2, 1.2, 1.2)}}),
        (8, LOWPUNCH),
        (12, held(LOWPUNCH)),
        (15, {**held(LOWPUNCH, .01), 'hands': {'r': (-.02, -1.30, .50), 'l': (.24, -.66, .92)},
              'robe': {'robe_front': (-8, 0, 0), 'robe_back': (10, 0, 0)}}),
        (22, {**CROUCH_START, 'hips': (.20, .40)}),
        (28, {}),
    ],
    # air_punch (wind 3, contact 5, hold 9, follow 11, recover 17, end 24)
    'air_punch': [
        (0, AIR_TUCK),
        (3, {**AIR_TUCK, 'turn': {'hips': (-4, 0, 0), 'chest': (-10, 0, 0), 'head': (-10, 0, 0)},
             'hands': {'l': (.08, -.10, 1.84), 'r': (-.08, -.08, 1.82)}, 'aim': {'l': (0, .3, 1), 'r': (0, .3, 1)},
             'elbow': {'l': (1, .2, .3), 'r': (-1, .2, .3)}, 'shrug': {'l': (24, -10), 'r': (24, -10)}}),
        (4, {**HAMMER, 'hands': {'l': (.06, -.62, 1.46), 'r': (-.06, -.62, 1.44)}, 'aim': {'l': (0, -.8, .3), 'r': (0, -.8, .3)},
             'scale': {'forearm_l': (1, 1.4, 1), 'forearm_r': (1, 1.4, 1)}}),
        (5, HAMMER),
        (9, held(HAMMER, 0)),
        (11, {**HAMMER, 'hands': {'l': (.06, -.70, .96), 'r': (-.06, -.70, .94)}, 'scale': {}}),
        (17, AIR_TUCK),
        (24, AIR_TUCK),
    ],
    # dash (state, 10 frames): a low burst forward, lead shoulder first, guard up, rear foot trailing
    'dash': [
        (0, {'hips': (.10, .16), 'turn': {'hips': (10, 0, -20), 'chest': (22, 0, -16), 'head': (6, 0, 20)},
             'feet': {'l': ankle(L0, .16, .06), 'r': tiptoe(ankle(R0, .02), .10)[0]}, 'foot_turn': {'r': tiptoe(ankle(R0, .02), .10)[1]},
             'hands': {'l': gfist('l', .12), 'r': gfist('r', .10)}, 'aim': {'l': AIM_UP, 'r': AIM_UP},
             'robe': {'robe_front': (20, 0, 0), 'robe_back': (26, 0, 0)}}),
        (5, {'hips': (.18, .14), 'turn': {'hips': (10, 0, -20), 'chest': (24, 0, -16), 'head': (8, 0, 20)},
             'feet': {'l': ankle(L0, .30), 'r': tiptoe(ankle(R0, .10), .08)[0]}, 'foot_turn': {'r': tiptoe(ankle(R0, .10), .08)[1]},
             'hands': {'l': gfist('l', .20), 'r': gfist('r', .18)}, 'aim': {'l': AIM_UP, 'r': AIM_UP},
             'robe': {'robe_front': (14, 0, 0), 'robe_back': (18, 0, 0)}}),
        (10, {'hips': (.06, .10), 'feet': {'l': ankle(L0, .08)}, 'robe': {'robe_front': (-6, 0, 0)}}),
    ],
}


# ---- Ranged: the stone jab (elemental), the barrage (ultimate), the falling-stone spike
# (rock_spike, half circle forward + elemental) and the combo breaker. ----
STONE_JAB = {**JAB, 'hips': (.30, .12), 'hands': {'l': (.04, -1.10, 1.30), 'r': gfist('r', .36, -.04)},
             'shrug': {'l': (10, 34), 'r': (8, -6)},
             'scale': {'hand_l': (1.6, 1.6, 1.6), 'forearm_l': (1.1, 1.15, 1.1)}}
BIG_CROSS = {**CROSS, 'hips': (.44, .14), 'hands': {'r': (-.02, -1.22, 1.32), 'l': (.26, -.46, 1.12)},
             'scale': {'hand_r': (1.8, 1.8, 1.8), 'forearm_r': (1.15, 1.2, 1.15)}}
SCOOP = {'hips': (.30, .50), 'turn': {'hips': (24, 0, 20), 'spine': (20, 0, 12), 'chest': (30, 0, 26), 'head': (10, 0, 4)},
         'feet': {'l': ankle(L0, .30), 'r': ankle(R0, .02)}, 'shrug': {'r': (2, 24)},
         'hands': {'r': (-.08, -.70, .34), 'l': (.20, -.30, .66)}, 'elbow': {'r': (-1, 0, -.2), 'l': (1, .4, -.4)},
         'aim': {'r': (0, -.4, -1), 'l': AIM_UP}, 'robe': {'robe_back': (24, 0, 0)}}
TOSS = {**UPPER, 'hips': (.24, -.06), 'hands': {'r': (-.02, -.70, 1.90), 'l': gfist('l', .24, .02)},
        'aim': {'r': (0, -.6, .8), 'l': AIM_UP}, 'scale': {'hand_r': (1.4, 1.4, 1.4)}}
BURST = {'hips': (-.06, .02), 'turn': {'hips': (-6, 0, 0), 'spine': (-8, 0, 0), 'chest': (-16, 0, 0), 'head': (-14, 0, 0)},
         'feet': {'l': ankle(L0, .04), 'r': ankle(R0, -.04)}, 'shrug': {'l': (20, -14), 'r': (20, -14)},
         'hands': {'l': (.62, -.10, 1.50), 'r': (-.62, -.06, 1.48)}, 'elbow': {'l': (.4, .2, -1), 'r': (-.4, .2, -1)},
         'aim': {'l': (1, 0, .2), 'r': (-1, 0, .2)}, 'robe': {'robe_front': (-20, 0, 0), 'robe_back': (-20, 0, 0)},
         'scale': {'hand_l': (1.3, 1.3, 1.3), 'hand_r': (1.3, 1.3, 1.3)}}

RANGED_CLIPS = {
    # elemental: stone jab (wind 3, contact 6, hold 10, follow 12, recover 18, end 22). A short
    # cock (it throws a stone), then the jab snaps out and the stone leaves the glove.
    'elemental': [
        (0, {}),
        (3, {'hips': (-.08, .12), 'turn': {'hips': (4, 0, -4), 'chest': (10, 0, 10), 'head': (6, 0, 16)},
             'shrug': {'l': (14, -14)}, 'hands': {'l': (.20, .02, 1.40), 'r': gfist('r', -.06)},
             'elbow': {'l': (1, .5, 0)}, 'aim': {'l': (0, -1, .3), 'r': AIM_UP}, 'robe': {'robe_front': (-8, 0, 0)}}),
        (5, {**STONE_JAB, 'hips': (.20, .10), 'hands': {'l': (.06, -.88, 1.32), 'r': gfist('r', .26, -.04)},
             'scale': {'forearm_l': (1, 1.5, 1), 'hand_l': (1.3, 1.3, 1.3)}}),
        (6, STONE_JAB),
        (10, held(STONE_JAB)),
        (12, {**held(STONE_JAB, .02), 'hands': {'l': (.02, -1.14, 1.28), 'r': gfist('r', .36, -.04)},
              'robe': {'robe_front': (-10, 0, 0)}}),
        (18, {'hips': (.10, .08), 'hands': {'l': gfist('l', .12), 'r': gfist('r', .10)}, 'aim': {'l': AIM_UP, 'r': AIM_UP}}),
        (22, {}),
    ],
    # ultimate: barrage (wind 26, contact 30, hold 36, follow 40, recover 50, end 58). Four fast
    # alternating punches walking in, a big wind-up, and a huge straight that hurls the giant stone.
    'ultimate': [
        (0, {}),
        (4, {'hips': (-.04, .20), 'turn': {'chest': (18, 0, 0), 'head': (10, 0, 0)},
             'shrug': {'l': (16, 8), 'r': (16, 8)},
             'hands': {'l': (.06, -.30, 1.20), 'r': (-.06, -.30, 1.20)}, 'aim': {'l': (0, 0, 1), 'r': (0, 0, 1)}}),
        (8, {**JAB, 'hips': (.16, .12), 'hands': {'l': (.04, -.92, 1.26), 'r': gfist('r', .16, -.06)}}),
        (11, {**CROSS, 'hips': (.24, .12), 'hands': {'r': (-.02, -1.00, 1.24), 'l': gfist('l', .24, .02)}}),
        (14, {**JAB, 'hips': (.32, .12), 'hands': {'l': (.04, -1.08, 1.26), 'r': gfist('r', .32, -.06)}}),
        (17, {**CROSS, 'hips': (.40, .12), 'hands': {'r': (-.02, -1.16, 1.24), 'l': gfist('l', .40, .02)}}),
        (21, {'hips': (.20, .20), 'turn': {'hips': (8, 0, -36), 'chest': (10, 0, -50), 'head': (6, 0, 36)},
              'feet': {'l': ankle(L0, .26)}, 'shrug': {'r': (26, -22)},
              'hands': {'r': (-.30, .22, 1.62), 'l': gfist('l', .16)}, 'elbow': {'r': (-1, .5, .4)},
              'aim': {'r': (0, .3, 1), 'l': AIM_UP}, 'robe': {'robe_front': (-10, 0, 0)}}),
        (26, {'hips': (.16, .22), 'turn': {'hips': (8, 0, -40), 'chest': (8, 0, -56), 'head': (6, 0, 40)},
              'feet': {'l': ankle(L0, .26)}, 'shrug': {'r': (30, -24)},
              'hands': {'r': (-.34, .26, 1.66), 'l': gfist('l', .12)}, 'elbow': {'r': (-1, .5, .4)},
              'aim': {'r': (0, .3, 1), 'l': AIM_UP}, 'robe': {'robe_front': (-12, 0, 0)}}),
        (29, {**BIG_CROSS, 'hips': (.36, .12), 'hands': {'r': (-.04, -1.00, 1.32), 'l': (.26, -.40, 1.12)},
              'scale': {'forearm_r': (1.1, 1.5, 1.1), 'hand_r': (1.4, 1.4, 1.4)}}),
        (30, BIG_CROSS),
        (36, held(BIG_CROSS, .02)),
        (40, {**held(BIG_CROSS, .03), 'hands': {'r': (-.04, -1.28, 1.30), 'l': (.26, -.50, 1.12)},
              'robe': {'robe_front': (-14, 0, 0), 'robe_back': (-10, 0, 0)}}),
        (50, {'hips': (.16, .10), 'hands': {'l': gfist('l', .16), 'r': gfist('r', .16)}, 'aim': {'l': AIM_UP, 'r': AIM_UP}}),
        (58, {}),
    ],
    # rock_spike: scoop a stone off the floor and toss it up in an arc (wind 6, contact 10,
    # hold 13, follow 16, recover 24, end 30)
    'rock_spike': [
        (0, {}),
        (4, SCOOP),
        (6, {**SCOOP, 'hips': (.28, .52), 'hands': {'r': (-.06, -.66, .30), 'l': (.20, -.28, .64)}}),
        (9, {**TOSS, 'hips': (.20, .12), 'hands': {'r': (-.04, -.66, 1.30), 'l': gfist('l', .20)},
             'scale': {'forearm_r': (1, 1.45, 1), 'hand_r': (1.2, 1.2, 1.2)}}),
        (10, TOSS),
        (13, held(TOSS, 0)),
        (16, {**TOSS, 'hands': {'r': (-.02, -.56, 1.98), 'l': gfist('l', .24, .02)}, 'scale': {},
              'robe': {'robe_front': (10, 0, 0)}}),
        (24, {'hips': (.10, .10), 'hands': {'l': gfist('l', .10), 'r': gfist('r', .10)}, 'aim': {'l': AIM_UP, 'r': AIM_UP}}),
        (30, {}),
    ],
    # breaker: covering up, then bursting out with the arms flung wide (16 frames)
    'breaker': [
        (0, {'hips': (-.02, .30), 'turn': {'hips': (10, 0, -10), 'chest': (20, 0, -8), 'head': (6, 0, 16)},
             'hands': {'l': (.07, -.30, 1.10), 'r': (-.05, -.26, 1.08)}, 'aim': {'l': (0, 0, 1), 'r': (0, 0, 1)},
             'elbow': {'l': (.2, -.3, -1), 'r': (-.2, -.3, -1)}}),
        (3, BURST),
        (9, held(BURST, 0)),
        (13, {'hips': (-.04, .10), 'hands': {'l': gfist('l', -.04), 'r': gfist('r', -.04)}, 'aim': {'l': AIM_UP, 'r': AIM_UP}}),
        (16, {}),
    ],
}


# ---- Jump, reactions and victory. The game holds the jump on a fixed time (~frame 1 of
# jump_start while rising, of jump_air while falling): those are single held poses. ----
UP = (0, 0, 1)
X_LYING = {'free': True, 'hips': (-.10, .76), 'turn': {'hips': (-86, 0, 0), 'chest': (-4, 0, 0), 'head': (8, 0, 14)},
           'feet': {'l': (.18, -.78, .20), 'r': (-.18, -.70, .24)}, 'knee': {'l': UP, 'r': UP},
           'hands': {'l': (.50, .30, .16), 'r': (-.50, .36, .16)}, 'aim': {'l': (1, 0, 0), 'r': (-1, 0, 0)}}
X_SPLAT = {**X_LYING, 'turn': {'hips': (-90, 0, 0), 'chest': (-2, 0, 0), 'head': (4, 0, 26)},
           'feet': {'l': (.28, -.80, .18), 'r': (-.26, -.74, .18)},
           'hands': {'l': (.62, .30, .12), 'r': (-.62, .42, .12)}}
X_BOUNCE = {**X_LYING, 'hips': (-.10, .66), 'turn': {'hips': (-80, 0, 0), 'chest': (-12, 0, 0), 'head': (16, 0, 10)},
            'feet': {'l': (.18, -.80, .34), 'r': (-.18, -.70, .40)}}
X_FLUNG = {'free': True, 'hips': (-.24, -.04), 'turn': {'hips': (-24, 0, 0), 'chest': (-24, 0, 10), 'head': (-20, 0, -12)},
           'shrug': {'l': (16, -14), 'r': (16, -14)},
           'feet': {'l': (.18, -.30, .44), 'r': (-.16, -.12, .52)}, 'knee': {'l': (0, -1, 0), 'r': (0, -1, 0)},
           'hands': {'l': (.44, -.10, 1.66), 'r': (-.44, .10, 1.60)}, 'robe': {'robe_front': (-30, 0, 0), 'robe_back': (20, 0, 0)}}
X_FALLING = {'free': True, 'hips': (-.30, .42), 'turn': {'hips': (-58, 0, 0), 'chest': (-12, 0, 6), 'head': (14, 0, -6)},
             'feet': {'l': (.18, -.62, .60), 'r': (-.18, -.48, .70)}, 'knee': {'l': UP, 'r': UP},
             'hands': {'l': (.50, .10, .98), 'r': (-.50, .18, .92)}}
HIT_SNAP = {'hips': (-.10, .06), 'turn': {'hips': (-4, 0, 6), 'spine': (-8, 0, 6), 'chest': (-18, 0, 12), 'head': (-26, 6, -16)},
            'feet': {'l': ankle(L0, -.04, .04)}, 'shrug': {'l': (16, -10), 'r': (16, -10)},
            'hands': {'l': (.22, -.10, 1.50), 'r': (-.20, .02, 1.44)}, 'elbow': {'l': (1, .3, -.3), 'r': (-1, .3, -.3)},
            'aim': {'l': (0, .2, 1), 'r': (0, .2, 1)}, 'robe': {'robe_front': (-14, 0, 0)}}
JUMP_RISE = {'free': True, 'hips': (0, -.08), 'turn': {'hips': (2, 0, -10), 'chest': (6, 0, -10), 'head': (-2, 0, 18)},
             'feet': {'l': (.15, -.10, .30), 'r': (-.15, .16, .20)}, 'foot_turn': {'l': 30, 'r': 40},
             'hands': {'l': (.10, -.34, 1.40), 'r': (-.07, -.26, 1.36)}, 'aim': {'l': AIM_UP, 'r': AIM_UP}, 'elbow': ELBOW,
             'robe': {'robe_front': (14, 0, 0), 'robe_back': (14, 0, 0)}}
JUMP_FALL = {'free': True, 'hips': (0, -.24), 'turn': {'hips': (8, 0, -10), 'chest': (14, 0, -10), 'head': (-2, 0, 18)},
             'feet': {'l': (.15, -.22, .78), 'r': (-.15, .12, .72)}, 'knee': {'l': (0, -1, .2), 'r': (0, -1, .2)},
             'hands': {'l': (.10, -.34, 1.56), 'r': (-.07, -.28, 1.52)}, 'aim': {'l': AIM_UP, 'r': AIM_UP}, 'elbow': ELBOW,
             'robe': {'robe_front': (-16, 0, 0), 'robe_back': (-10, 0, 0)}}
CHAMP = {'hips': (0, .0), 'turn': {'hips': (0, 0, 0), 'spine': (-6, 0, 0), 'chest': (-12, 0, 0), 'head': (-14, 0, 0)},
         'feet': {'l': ankle(L0, .02), 'r': ankle(R0, -.02)},
         'shrug': {'l': (30, -6), 'r': (30, -6)},
         'hands': {'l': (.22, -.10, 2.02), 'r': (-.22, -.06, 2.00)}, 'elbow': {'l': (1, 0, .2), 'r': (-1, 0, .2)},
         'aim': {'l': (0, 0, 1), 'r': (0, 0, 1)}, 'scale': {'hand_l': (1.2, 1.2, 1.2), 'hand_r': (1.2, 1.2, 1.2)}}

REACTIONS = {
    'jump_start': [(0, JUMP_RISE), (8, JUMP_RISE)],
    'jump_air': [(0, JUMP_FALL), (16, JUMP_FALL)],
    # landing: knees soak it (squash), back up into the bounce
    'jump_land': [(0, {'hips': (0, .22), 'turn': {'hips': (10, 0, -10), 'chest': (16, 0, -10), 'head': (2, 0, 18)},
                       'hands': {'l': hand('l', up=-.12), 'r': hand('r', up=-.12)}, 'aim': {'l': AIM_UP, 'r': AIM_UP},
                       'robe': {'robe_front': (10, 0, 0), 'robe_back': (10, 0, 0)}}),
                  (4, {'hips': (0, .12), 'robe': {'robe_front': (-6, 0, 0)}}),
                  (10, None)],
    # hit (16): the head snaps back, the guard flies up, a step back, then she shakes it off
    'hit': [(0, HIT_SNAP), (6, held(HIT_SNAP, .02)),
            (10, {'hips': (-.06, .08), 'turn': {'chest': (-4, 0, 4), 'head': (-8, 0, 8)},
                  'hands': {'l': hand('l', up=.06), 'r': hand('r', up=.06)}, 'aim': {'l': AIM_UP, 'r': AIM_UP}}),
            (16, None)],
    'knockdown': [(0, HIT_SNAP), (5, X_FLUNG), (12, X_FALLING), (18, X_LYING), (21, X_BOUNCE), (24, X_LYING)],
    'ko': [(0, {**HIT_SNAP, 'turn': {'spine': (-10, 0, 6), 'chest': (-24, 0, 14), 'head': (-30, 0, -14)}}),
           (6, {**X_FLUNG, 'hips': (-.28, -.10), 'turn': {'hips': (-34, 0, 0), 'chest': (-26, 0, 14), 'head': (-22, 0, -16)}}),
           (14, X_FALLING), (20, X_LYING), (23, X_BOUNCE), (26, X_LYING), (30, X_SPLAT)],
    # get up: kip to one knee, push up, bounce back into the guard
    'get_up': [(0, X_LYING),
               (6, {'free': True, 'hips': (-.12, .62), 'turn': {'hips': (-40, 0, 0), 'chest': (14, 0, 0), 'head': (-4, 0, 0)},
                    'feet': {'l': (.18, -.50, .26), 'r': (-.18, -.32, .26)}, 'knee': {'l': UP, 'r': UP},
                    'hands': {'l': (.36, .12, .30), 'r': (-.24, -.34, .74)}}),
               (12, {'hips': (.0, .34), 'turn': {'hips': (16, 0, 0), 'chest': (20, 0, 0), 'head': (-6, 0, 10)},
                     'feet': {'r': ankle(R0, .10)}, 'hands': {'l': (.24, -.44, .92), 'r': (-.20, -.30, .90)}}),
               (18, {'hips': (.0, .10), 'shrug': {'l': (16, 0), 'r': (16, 0)}}),
               (24, None)],
    # victory (40): two quick punches at the air, then both fists raised high, bouncing on her toes
    'victory': [(0, {}),
                (4, {**JAB, 'hips': (.10, .10), 'feet': {'l': ankle(L0, .12)}, 'foot_turn': {},
                     'hands': {'l': (.04, -.80, 1.40), 'r': gfist('r', .10)}, 'scale': {}}),
                (9, {**CROSS, 'hips': (.12, .10), 'feet': {'l': ankle(L0, .12), 'r': CROSS['feet']['r']},
                     'hands': {'r': (-.02, -.84, 1.42), 'l': gfist('l', .12)}, 'scale': {}}),
                (15, CHAMP),
                (20, {**CHAMP, 'feet': {s: tiptoe(b, .08)[0] for s, b in (('l', ankle(L0, .02)), ('r', ankle(R0, -.02)))},
                      'foot_turn': {s: tiptoe(b, .08)[1] for s, b in (('l', ankle(L0, .02)), ('r', ankle(R0, -.02)))},
                      'hips': (0, -.06)}),
                (25, CHAMP),
                (30, {**CHAMP, 'feet': {s: tiptoe(b, .08)[0] for s, b in (('l', ankle(L0, .02)), ('r', ankle(R0, -.02)))},
                      'foot_turn': {s: tiptoe(b, .08)[1] for s, b in (('l', ankle(L0, .02)), ('r', ankle(R0, -.02)))},
                      'hips': (0, -.06)}),
                (40, CHAMP)],
}

SHEETS = {
    'idle': idle_sheet(),
    **MOVEMENT,
    **LIGHT,
    **SPECIAL,
    **RANGED_CLIPS,
    **REACTIONS,
    'select': select_sheet(),
}
# Attack clips end on the idle's first key (landing on her toes, knees bent) instead of the
# flat guard, so the bounce picks up from where the attack recovers (no pop into the idle).
IDLE0 = SHEETS['idle'][0][1]
for _clip, _keys in SHEETS.items():
    SHEETS[_clip] = [(f, IDLE0 if k is None else k) for f, k in _keys]
for _clip in ('light_1', 'light_2', 'light_3', 'heavy', 'down_punch', 'sweep', 'elemental', 'ultimate',
              'rock_spike', 'breaker'):
    _keys = SHEETS[_clip]
    if _keys[-1][1] == {}:
        _keys[-1] = (_keys[-1][0], IDLE0)
la.SHEETS['tophia'] = SHEETS


def author(rig, clips=None, force=False):
    """Author X12's sheets on x12_Rig (all, or the named clips, in order)."""
    import bpy
    for c in (clips or SHEETS):
        if c not in bpy.data.actions:
            act = bpy.data.actions.new(c)
            act.use_fake_user = True
            track = rig.animation_data.nla_tracks.new()
            track.name = c
            track.strips.new(c, 0, act)
    out = [la.author(rig, c, 'tophia', force).name for c in (clips or SHEETS)]
    la.sync_strips(rig)
    return out
