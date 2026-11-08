"""Orsted (fighter id 'volt') limited-animation sheets for legends_anim.place().

A calm, tactical zoner (user's sketches, 2026-11-07): at rest he stands easy, the energy hand cannon
held up behind his shoulder (the forearm up, the barrel up and back), the free fist in front of
his hips, eyes on the opponent. The light chain (J1-J3) are point-blank shots that hit like melee
(J1 low from the hip with the hips snapping round, J2 the arm thrown out in a long lunge, J3 a full
360 deg spin into a deep lunge), the heavy (K) is his real projectile (a long aim with both hands
and a kick that throws him back), down+J throws the bomb underhand at the enemy's feet, the
crouching heavy (sweep) shoots low from a knee.

The cannon is held as a real pistol (orsted_arma): the barrel runs along the hand and forearm, so a
pose sets the forearm along the line of fire (wrist straight, never bent across the barrel) and
'point': {'cannon': direction} trims the barrel exactly onto it (legends_anim.point_bone).
Turns (world degrees about the vertical, + brings the right shoulder forward) stop at profile
(~90 deg summed over hips, spine and chest) and the head turns back as much: he looks at the
opponent down the barrel. Attack poses follow the attack-poses skill: an anticipation the other
way, a long step with the hips travelling, the trunk leaning into the shot, the rear heel up,
contact held, a kick that overshoots and a recovery.
His rig is the Legends body (legends_rig.py): poses start from its rest ('START': 'rest').
Joints (orsted_modelo.JOINTS): ankle z .15, hip .87, knee .58, shoulder 1.42 (x .225), upper arm
.21, forearm .175.

Run in Blender: import legends_orsted_anim as o; o.author(rig, ['idle', 'select'])
"""
import math

import legends_anim as la

GROUND = .15                                  # ankle height with the sole flat on the floor
L0, R0 = (.13, -.10, GROUND), (-.15, .12, GROUND)   # easy stance, left foot a little forward
BASE_SINK = .03
# rest: the upper arm hanging, the forearm up and a little back, the cannon standing behind his
# shoulder (beside the head, not over the face); the free fist in front of the belt
HANDS = {'l': (.08, -.19, 1.00), 'r': (-.29, .09, 1.38)}
ELBOW = {'l': (1, -.2, -.8), 'r': (-1, .1, -1)}
UP_BACK = (0, .35, 1)                         # barrel directions
FWD = (0, -1, 0)
FWD_LOW = (0, -1, -.12)
KICK = (0, -.75, .65)
DOWN_FWD = (0, -.6, -.8)
REST_L = (0, -.2, -1)                         # the free fist hanging (knuckles down)
TURN = {'hips': (0, 0, -10), 'spine': (0, 0, -6), 'chest': (2, 0, -12), 'head': (-2, 0, 28)}
la.PROFILES['volt'] = {'L0': L0, 'R0': R0, 'GROUND': GROUND, 'BASE_SINK': BASE_SINK, 'HANDS': HANDS,
                       'ELBOW': ELBOW, 'TURN': TURN, 'START': 'rest'}
AIM = {'l': REST_L}
GUN = {'cannon': UP_BACK}


def ankle(base, forward=0.0, up=0.0):
    return (base[0], base[1] - forward, base[2] + up)


def held(pose, settle=.01):
    out = {k: v for k, v in pose.items() if k != 'scale'}
    if 'hips' in out:
        out['hips'] = (out['hips'][0], out['hips'][1] + settle)
    return out


def hold(n, pose, settle=None):
    keys = [(0, pose)]
    if settle:
        keys.append((n // 2, settle))
    keys.append((n, settle or pose))
    return keys


# ankle -> toe tip of his boot at rest (orsted_perna BOOT / JOINTS toe), for the rear foot on its toes
TOE = (0.0, -.225, -.12)


def tiptoe(base, lift):
    """Ankle target and foot pitch (degrees) for a heel raised `lift` metres with the toe tip
    staying where it was (X12's way)."""
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
    dy = (y * math.cos(t) - z * math.sin(t)) - y
    return (base[0], base[1] - dy, base[2] + lift), lo


def heel(base, forward, lift):
    """Rear foot pushed onto its toes (the heel up, the toe planted)."""
    return tiptoe(ankle(base, forward), lift)


def idle_sheet(n=64):
    """Calm: a slow breath, the shoulders rise and settle, the cannon bobs a little, a glance."""
    out = []
    for i in range(5):
        t = i / 4
        b = math.sin(2 * math.pi * t)
        out.append((round(n * t), {
            'hips': (0, .005 - .01 * b),
            'turn': {**TURN, 'chest': (2 - 1.5 * b, 0, -12), 'head': (-2 + b, 0, 28 + 3 * math.sin(math.pi * t))},
            'shrug': {'l': (2 + 3 * b, 0), 'r': (2 + 3 * b, 0)},
            'hands': {'l': HANDS['l'], 'r': (HANDS['r'][0], HANDS['r'][1], HANDS['r'][2] + .012 * b)},
            'aim': AIM, 'point': GUN,
        }))
    return out


# select: the cannon on his shoulder pointing back, the free fist on the hip, a breath, a look
SEL = {'feet': {'l': (.12, -.04, GROUND), 'r': (-.14, .06, GROUND)},
       'turn': {'hips': (0, 0, 0), 'spine': (0, 0, 0), 'chest': (-2, 0, 0), 'head': (-4, 0, 0)},
       'hands': {'r': (-.24, -.12, 1.52), 'l': (.24, .02, 1.02)}, 'elbow': {'r': (-1, -.4, -.3), 'l': (1, .6, -.2)},
       'aim': {'l': (-.3, 0, -1)}, 'point': {'cannon': (0, .85, .5)}}


def select_sheet(n=40):
    out = []
    for i in range(5):
        t = i / 4
        b = math.sin(2 * math.pi * t)
        out.append((round(n * t), {**SEL, 'hips': (0, -.01 * b), 'shrug': {'l': (3 + 3 * b, 0), 'r': (6 + 3 * b, -6)},
                                   'turn': {**SEL['turn'], 'head': (-4 + 2 * b, 3 * math.sin(math.pi * t), 0)}}))
    return out


def walk_sheet(direction=1, n=22, keys=8, stride=.48):
    """An easy walk, heel to toe, the cannon kept up; feet in the ground's frame."""
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
        lift_l = .06 * math.sin(math.pi * lead_sw) if 0 < lead_sw < 1 else 0.0
        lift_r = .06 * math.sin(math.pi * rear_sw) if 0 < rear_sw < 1 else 0.0
        bob = abs(math.sin(2 * math.pi * t))
        out.append((round(n * t), {
            'hips': (.01 * direction, .02 - .02 * bob),
            'turn': {**TURN, 'chest': (2 + 2 * direction, 0, -12)},
            'feet': {'l': (L0[0], -ul, GROUND + lift_l), 'r': (R0[0], -ur, GROUND + lift_r)},
            'aim': AIM, 'point': GUN,
        }))
    return out


# ---- J1: from the hip, point blank. Anticipation: the hips wind away (left shoulder in), the
# cannon drawn back to the hip; then a long step in, the hips snap round to profile, knees deep,
# the trunk leaning in, the forearm level at the hip and the shot into the belly. ----
_j1_heel, _j1_pitch = heel(R0, -.04, .05)
J1_WIND = {'hips': (-.06, .14), 'turn': {'hips': (4, 0, -24), 'spine': (6, 0, -10), 'chest': (10, 0, -22), 'head': (4, 0, 50)},
           'feet': {'l': ankle(L0, .02, .03)}, 'shrug': {'r': (6, -12)},
           'hands': {'r': (-.30, .14, 1.04), 'l': (.12, -.24, 1.10)}, 'elbow': {'r': (-1, .8, 0), 'l': (1, -.2, -.6)},
           'aim': {'l': (0, -.3, 1)}, 'point': {'cannon': FWD_LOW}}
J1 = {'hips': (.30, .20), 'turn': {'hips': (10, 0, 36), 'spine': (10, 0, 16), 'chest': (18, 0, 36), 'head': (8, 0, -82)},
      'feet': {'l': ankle(L0, .42), 'r': _j1_heel}, 'foot_turn': {'r': _j1_pitch}, 'knee': {'r': (0, -1, -.4)},
      'shrug': {'r': (4, 24), 'l': (10, -14)},
      'hands': {'r': (-.06, -.62, 1.02), 'l': (.24, -.06, 1.18)}, 'elbow': {'r': (-1, .6, -.3), 'l': (1, .5, -.4)},
      'aim': {'l': (0, -.4, 1)}, 'point': {'cannon': FWD_LOW},
      'robe': {'robe_front': (20, 0, 0), 'robe_back': (12, 0, 0)}, 'scale': {'hand_r': (1.15, 1.15, 1.15)}}
# ---- J2: the arm thrown straight out at shoulder height in a long lunge, the trunk leaning in
# hard, the head down behind the shoulder sighting along the barrel, the free arm flung back. ----
_j2_heel, _j2_pitch = heel(R0, -.06, .07)
J2_WIND = {'hips': (.06, .14), 'turn': {'hips': (4, 0, -20), 'spine': (6, 0, -10), 'chest': (8, 0, -24), 'head': (4, 0, 54)},
           'feet': {'l': ankle(L0, .18)}, 'shrug': {'r': (14, -16)},
           'hands': {'r': (-.30, .06, 1.48), 'l': (.14, -.26, 1.22)}, 'elbow': {'r': (-1, .2, -1)},
           'aim': {'l': (0, -.4, 1)}, 'point': {'cannon': UP_BACK}}
J2 = {'hips': (.42, .14), 'turn': {'hips': (10, 0, 40), 'spine': (12, 0, 18), 'chest': (24, 0, 30), 'head': (10, 0, -84)},
      'feet': {'l': ankle(L0, .56), 'r': _j2_heel}, 'foot_turn': {'r': _j2_pitch}, 'knee': {'r': (0, -1, -.2)}, 'pivot': {'r': 40},
      'shrug': {'r': (6, 32), 'l': (10, -22)},
      'hands': {'r': (-.02, -.98, 1.38), 'l': (.30, .14, 1.16)}, 'elbow': {'r': (-1, .2, -.3), 'l': (1, 1, -.2)},
      'aim': {'l': (0, .3, -1)}, 'point': {'cannon': FWD},
      'robe': {'robe_front': (24, 0, 0), 'robe_back': (16, 0, 0)}, 'scale': {'hand_r': (1.2, 1.2, 1.2), 'forearm_r': (1, 1.08, 1)}}
# ---- J3: a full turn on the lead foot, the cannon swung round at arm's length, ending in the
# deepest lunge of the chain, low, the arm out. ----
_j3_heel, _j3_pitch = heel(R0, -.04, .08)
J3 = {'hips': (.56, .26), 'turn': {'hips': (12, 0, 44), 'spine': (14, 0, 22), 'chest': (26, 0, 26), 'head': (12, 0, -88)},
      'feet': {'l': ankle(L0, .70), 'r': _j3_heel}, 'foot_turn': {'r': _j3_pitch}, 'knee': {'r': (0, -1, -.5)}, 'pivot': {'r': 50},
      'shrug': {'r': (6, 34), 'l': (10, -24)},
      'hands': {'r': (-.02, -1.12, 1.24), 'l': (.32, .18, 1.10)}, 'elbow': {'r': (-1, .2, -.3), 'l': (1, 1, -.2)},
      'aim': {'l': (0, .3, -1)}, 'point': {'cannon': FWD},
      'robe': {'robe_front': (30, 0, 0), 'robe_back': (20, 0, 0)}, 'scale': {'hand_r': (1.25, 1.25, 1.25), 'forearm_r': (1, 1.1, 1)}}


def kick(pose, up=.08, back=.05, hips=.05):
    """The shot's kick: the barrel thrown up past the line, the forearm with it, the hips rocked
    back a little; overshoots, then the recovery settles."""
    h = dict(pose['hands'])
    x, y, z = h['r']
    h['r'] = (x, y + back, z + up)
    f, d = pose['hips']
    return {**held(pose, .01), 'hips': (f - hips, d), 'hands': h, 'point': {'cannon': KICK}}


RECOVER = {'hips': (.08, .08), 'turn': {**TURN, 'chest': (8, 0, 0), 'head': (0, 0, 10)},
           'hands': {'r': (-.24, -.04, 1.30), 'l': HANDS['l']}, 'aim': AIM, 'point': {'cannon': (0, -.2, 1)}}

LIGHT = {
    # J1 (wind 4, contact 6, hold 10, follow 12, recover 18, end 24)
    'light_1': [
        (0, {}),
        (4, J1_WIND),
        (5, {**J1, 'hips': (.18, .18), 'turn': {'hips': (8, 0, 14), 'spine': (8, 0, 6), 'chest': (14, 0, 12), 'head': (6, 0, -30)},
             'hands': {'r': (-.16, -.36, 1.02), 'l': (.20, -.14, 1.16)}, 'scale': {'forearm_r': (1, 1.35, 1)}}),   # smear
        (6, J1),
        (10, held(J1)),
        (12, kick(J1, .07, .04, .04)),
        (18, RECOVER),
        (24, {}),
    ],
    # J2 (wind 4, contact 7, hold 11, follow 13, recover 19, end 26)
    'light_2': [
        (0, {'from': ('light_1', 12)}),
        (4, J2_WIND),
        (6, {**J2, 'hips': (.28, .14), 'turn': {'hips': (8, 0, 22), 'spine': (10, 0, 10), 'chest': (18, 0, 16), 'head': (8, 0, -50)},
             'hands': {'r': (-.10, -.70, 1.44), 'l': (.26, .02, 1.18)}, 'scale': {'forearm_r': (1, 1.4, 1)}}),     # smear
        (7, J2),
        (11, held(J2)),
        (13, kick(J2, .10, .06, .06)),
        (19, RECOVER),
        (26, {}),
    ],
    # J3: the spin into the lunge (wind 10, contact 14, hold 18, follow 21, recover 28, end 36)
    'light_3': [
        (0, {'from': ('light_2', 13)}),
        (3, {'hips': (.08, .22), 'turn': {'hips': (6, 0, -24), 'chest': (10, 0, -26), 'head': (6, 0, 40)},
             'feet': {'l': ankle(L0, .14)}, 'hands': {'r': (-.30, .02, 1.44), 'l': (.18, -.20, 1.14)},
             'aim': AIM, 'point': GUN}),
        (6, {'hips': (.18, .18), 'spin': -120, 'feet': {'l': ankle(L0, .20), 'r': ankle(R0, .06, .08)}, 'pivot': {'l': -120},
             'turn': {'chest': (6, 0, 0), 'head': (0, 0, -30)},
             'hands': {'r': (-.52, -.06, 1.34), 'l': (.40, .04, 1.18)}, 'elbow': {'r': (-1, .3, 0), 'l': (1, .3, 0)},
             'aim': {'l': (1, 0, -.3)}, 'point': {'cannon': (-1, -.2, 0)},
             'robe': {'robe_front': (-24, 0, 0), 'robe_back': (34, 0, 0)}}),
        (9, {'hips': (.30, .18), 'spin': -240, 'feet': {'l': ankle(L0, .28), 'r': ankle(R0, .16, .10)}, 'pivot': {'l': -240},
             'turn': {'chest': (6, 0, 0), 'head': (0, 0, 40)},
             'hands': {'r': (-.54, -.02, 1.32), 'l': (.40, .08, 1.16)}, 'elbow': {'r': (-1, .3, 0), 'l': (1, .3, 0)},
             'aim': {'l': (1, 0, -.3)}, 'point': {'cannon': (-1, -.2, 0)},
             'robe': {'robe_front': (34, 0, 0), 'robe_back': (-24, 0, 0)}}),
        (12, {**J3, 'hips': (.46, .24), 'spin': -320, 'pivot': {'l': -320},
              'hands': {'r': (-.22, -.86, 1.28), 'l': (.30, .10, 1.12)}, 'scale': {'forearm_r': (1, 1.4, 1)}}),       # smear
        (14, J3),
        (18, held(J3)),
        (21, kick(J3, .12, .07, .07)),
        (28, RECOVER),
        (36, {}),
    ],
}

# ---- K: the real projectile. He plants wide and charges, the cannon raised in both hands, then
# brings it level and fires; the kick throws the arms up and rocks him back onto the rear foot. ----
CHARGE = {'hips': (-.06, .16), 'turn': {'hips': (6, 0, 20), 'spine': (8, 0, 10), 'chest': (-6, 0, 30), 'head': (-10, 0, -50)},
          'feet': {'l': ankle(L0, .20), 'r': ankle(R0, -.08)},
          'shrug': {'r': (14, 18), 'l': (14, 18)},
          'hands': {'r': (-.14, -.20, 1.62), 'l': (-.06, -.14, 1.52)}, 'elbow': {'r': (-1, -.2, -.6), 'l': (1, -.4, -.8)},
          'aim': {'l': (-.6, -.2, .7)}, 'point': {'cannon': (0, -.25, 1)}}
AIM_TWO = {'hips': (.06, .18), 'turn': {'hips': (8, 0, 30), 'spine': (10, 0, 14), 'chest': (16, 0, 44), 'head': (8, 0, -84)},
           'feet': {'l': ankle(L0, .30), 'r': ankle(R0, -.08)}, 'knee': {'l': (0, -1, 0), 'r': (0, -1, -.2)},
           'shrug': {'r': (6, 28), 'l': (8, 24)},
           'hands': {'r': (-.04, -.80, 1.34), 'l': (.00, -.62, 1.28)}, 'elbow': {'r': (-1, 0, -.4), 'l': (1, -.2, -.6)},
           'aim': {'l': (-.6, -.2, .7)}, 'point': {'cannon': FWD}}
_fire_heel, _fire_pitch = heel(R0, -.16, .0)
FIRE = {**AIM_TWO, 'hips': (-.14, .14), 'turn': {'hips': (0, 0, 30), 'spine': (-6, 0, 14), 'chest': (-16, 0, 44), 'head': (-8, 0, -84)},
        'feet': {'l': ankle(L0, .26, .06), 'r': ankle(R0, -.16)},
        'hands': {'r': (-.04, -.62, 1.56), 'l': (.00, -.48, 1.48)}, 'point': {'cannon': KICK},
        'robe': {'robe_front': (-20, 0, 0), 'robe_back': (22, 0, 0)}, 'scale': {'hand_r': (1.2, 1.2, 1.2)}}
# ---- down + J: the bomb thrown underhand at the enemy's feet with the free hand, the cannon
# kept up. Anticipation: the weight back, the arm swung back low; then a step in and the throw. ----
TUCK_R, TUCK_ELBOW = (-.26, -.22, 1.12), (-1, .3, -1)   # the cannon hand tucked by the shoulder when he leans in
# leaning into the toss his shoulder goes ~.6 m forward (y -.60, z 1.00): the cannon hand stays just
# in front of it, the elbow down, the cannon up
TOSS_R = (-.36, -.62, 1.08)
TOSS_BACK = {'hips': (-.10, .24), 'turn': {'hips': (10, 0, -30), 'spine': (12, 0, -12), 'chest': (18, 0, -30), 'head': (-22, 0, 30)},
             'feet': {'l': ankle(L0, .02, .04), 'r': ankle(R0, -.06)},
             'hands': {'l': (.30, .30, .90), 'r': TUCK_R}, 'elbow': {'l': (1, .4, .2), 'r': TUCK_ELBOW},
             'aim': {'l': (0, .4, -1)}, 'point': GUN}
TOSS = {'hips': (.28, .26), 'turn': {'hips': (16, 0, 12), 'spine': (16, 0, 4), 'chest': (24, 0, 6), 'head': (-36, 0, -8)},
        'feet': {'l': ankle(L0, .44), 'r': heel(R0, -.02, .06)[0]}, 'foot_turn': {'r': heel(R0, -.02, .06)[1]},
        'knee': {'r': (0, -1, -.5)}, 'shrug': {'l': (2, 30)},
        'hands': {'l': (.08, -.80, .78), 'r': TOSS_R}, 'elbow': {'l': (1, 0, -.5), 'r': (-1, .2, -1)},
        'aim': {'l': (0, -1, .35)}, 'point': {'cannon': (0, .1, 1)}, 'robe': {'robe_front': (24, 0, 0)}}
# ---- crouching heavy (sweep): down on the rear knee, the arm out low, a shot at the shins. ----
# crouch idle (user's sketch): low, the cannon held in front of the belly pointing ahead and a
# little down, the elbow down beside the ribs, the free fist up in front of the chest; the hands
# sit low enough for the sunk shoulders (shoulder ~1.04 m) that the arms never fold shut
CROUCH = {'hips': (.02, .38), 'turn': {'hips': (14, 0, 16), 'spine': (10, 0, 6), 'chest': (16, 0, 16), 'head': (-26, 0, -34)},
          'feet': {'l': ankle(L0, .08), 'r': ankle(R0, -.06)}, 'knee': {'l': (0, -1, 0), 'r': (0, -1, -.4)},
          'hands': {'r': (-.20, -.34, .80), 'l': (.14, -.30, .90)}, 'elbow': {'r': (-1, .4, -.6), 'l': (1, .2, -.6)},
          'aim': {'l': (0, -.4, 1)}, 'point': {'cannon': (0, -1, -.3)}}
LOW_SHOT = {**CROUCH, 'hips': (.24, .40), 'turn': {'hips': (16, 0, 34), 'spine': (12, 0, 16), 'chest': (22, 0, 40), 'head': (-32, 0, -84)},
            'feet': {'l': ankle(L0, .40), 'r': ankle(R0, -.04)}, 'shrug': {'r': (2, 32)},
            'hands': {'r': (-.02, -.94, .90), 'l': (.26, .02, .96)}, 'elbow': {'r': (-1, 0, -.3), 'l': (1, 1, -.2)},
            'aim': {'l': (0, .3, -1)}, 'point': {'cannon': FWD_LOW}, 'scale': {'hand_r': (1.2, 1.2, 1.2)}}
# ---- air (overhead): in the air, the cannon pointed down at the opponent below. ----
AIR = {'free': True, 'hips': (.0, -.28), 'turn': {'hips': (8, 0, -10), 'chest': (12, 0, -12), 'head': (-4, 0, 26)},
       'feet': {'l': (.13, -.20, .70), 'r': (-.15, .14, .64)}, 'knee': {'l': (0, -1, .2), 'r': (0, -1, .2)},
       'hands': {'r': HANDS['r'], 'l': (.10, -.22, 1.10)}, 'aim': AIM, 'point': GUN}
AIR_SHOT = {**AIR, 'turn': {'hips': (18, 0, 26), 'chest': (26, 0, 34), 'head': (16, 0, -70)},
            'hands': {'r': (-.04, -.66, .98), 'l': (.26, .06, 1.16)}, 'elbow': {'r': (-1, .4, .2)},
            'aim': {'l': REST_L}, 'point': {'cannon': DOWN_FWD}, 'shrug': {'r': (4, 26)}}

SPECIAL = {
    # heavy, the projectile (wind 12, contact 16, hold 20, follow 24, recover 32, end 40)
    'heavy': [
        (0, {}),
        (5, CHARGE),
        (10, held(CHARGE, .02)),
        (12, AIM_TWO),
        (15, held(AIM_TWO, .02)),
        (16, FIRE),
        (20, held(FIRE)),
        (24, {**held(AIM_TWO, .03), 'hips': (-.08, .14)}),
        (32, RECOVER),
        (40, {}),
    ],
    'down_punch': [   # wind 8, contact 14, hold 22, follow 24, recover 34, end 44; from the crouch
        (0, CROUCH),
        (8, TOSS_BACK),
        (12, {**TOSS, 'hips': (.16, .26), 'hands': {'l': (.20, -.30, .78), 'r': (-.36, -.52, 1.10)}, 'aim': {'l': (0, -.6, -.6)}}),
        (14, TOSS),
        (22, held(TOSS)),
        (24, {**held(TOSS, .02), 'hands': {'l': (.06, -.86, .94), 'r': TOSS_R}, 'aim': {'l': (0, -1, .7)}}),
        (34, RECOVER),
        (44, {}),
    ],
    # sweep, the crouching shot (wind 6, contact 10, hold 18, follow 20, recover 30, end 40)
    'sweep': [
        (0, CROUCH),
        (6, {**CROUCH, 'turn': {'hips': (14, 0, -10), 'chest': (16, 0, -14), 'head': (-8, 0, 30)}}),
        (9, {**LOW_SHOT, 'hips': (.14, .40), 'hands': {'r': (-.10, -.70, .92), 'l': (.22, -.10, .94)},
             'scale': {'forearm_r': (1, 1.35, 1)}}),
        (10, LOW_SHOT),
        (18, held(LOW_SHOT)),
        (20, kick(LOW_SHOT, .07, .04, .04)),
        (30, CROUCH),
        (40, {}),
    ],
    # air_punch, shot from the air (wind 3, contact 5, hold 9, follow 11, recover 17, end 24)
    'air_punch': [
        (0, AIR),
        (3, {**AIR, 'hands': {'r': (-.24, .02, 1.46), 'l': (.12, -.20, 1.10)}}),
        (5, AIR_SHOT),
        (9, held(AIR_SHOT, 0)),
        (11, {**AIR_SHOT, 'point': {'cannon': (0, -.9, -.4)}, 'hands': {'r': (-.04, -.60, 1.04), 'l': (.26, .06, 1.16)}}),
        (17, AIR),
        (24, AIR),
    ],
    # dash (12): a quick low step in, the cannon kept up
    'dash': [
        (0, {'hips': (.10, .12), 'turn': {**TURN, 'chest': (16, 0, -12)}, 'feet': {'l': ankle(L0, .16, .06), 'r': ankle(R0, .02)},
             'aim': AIM, 'point': GUN, 'robe': {'robe_front': (16, 0, 0), 'robe_back': (22, 0, 0)}}),
        (6, {'hips': (.20, .10), 'turn': {**TURN, 'chest': (18, 0, -12)}, 'feet': {'l': ankle(L0, .30), 'r': ankle(R0, .12, .06)},
             'aim': AIM, 'point': GUN, 'robe': {'robe_front': (10, 0, 0), 'robe_back': (14, 0, 0)}}),
        (12, {'hips': (.06, .06), 'feet': {'l': ankle(L0, .08)}, 'aim': AIM, 'point': GUN}),
    ],
}

# ---- elemental (Curto-Circuito): he slaps the chest core, crouches as it charges and throws his
# arms out in a ring of electricity. Ultimate (Sobrecarga Total): the cell overcharges, he drops to a
# knee, braces the cannon in both hands and fires a huge beam that pushes him back. ----
SLAP = {'hips': (.0, .16), 'turn': {'hips': (4, 0, 0), 'chest': (16, 0, 0), 'head': (14, 0, 0)},
        'hands': {'l': (.04, -.22, 1.32), 'r': HANDS['r']}, 'elbow': {'l': (1, -.4, -.4)}, 'aim': {'l': (-1, 0, .2)}, 'point': GUN}
PULSE = {'hips': (-.06, .08), 'turn': {'hips': (-4, 0, 0), 'spine': (-8, 0, 0), 'chest': (-18, 0, 0), 'head': (-12, 0, 0)},
         'feet': {'l': ankle(L0, .06), 'r': ankle(R0, -.06)}, 'shrug': {'l': (22, -14), 'r': (22, -14)},
         'hands': {'l': (.66, -.08, 1.42), 'r': (-.66, -.06, 1.42)}, 'elbow': {'l': (.4, .2, -1), 'r': (-.4, .2, -1)},
         'aim': {'l': (1, 0, .3)}, 'point': {'cannon': (-1, 0, .2)},
         'robe': {'robe_front': (-22, 0, 0), 'robe_back': (-22, 0, 0)}, 'scale': {'hand_l': (1.2, 1.2, 1.2)}}
KNEEL = {'hips': (.08, .42), 'turn': {'hips': (10, 0, 30), 'spine': (8, 0, 14), 'chest': (12, 0, 44), 'head': (6, 0, -84)},
         'feet': {'l': ankle(L0, .30), 'r': ankle(R0, -.10)}, 'knee': {'l': (0, -1, 0), 'r': (0, -1, -1)},
         'hands': {'r': (-.04, -.72, 1.04), 'l': (.00, -.56, .98)}, 'elbow': {'r': (-1, 0, -.4), 'l': (1, -.2, -.6)},
         'aim': {'l': (-.6, -.2, .7)}, 'point': {'cannon': FWD}}
BEAM = {**KNEEL, 'hips': (-.10, .40), 'turn': {'hips': (6, 0, 30), 'spine': (-2, 0, 14), 'chest': (-8, 0, 44), 'head': (-4, 0, -84)},
        'hands': {'r': (-.04, -.62, 1.14), 'l': (.00, -.48, 1.08)}, 'point': {'cannon': (0, -.97, .25)},
        'robe': {'robe_front': (-24, 0, 0), 'robe_back': (24, 0, 0)}, 'scale': {'hand_r': (1.25, 1.25, 1.25)}}
COVER = {'hips': (-.02, .26), 'turn': {'hips': (10, 0, 0), 'chest': (20, 0, 0), 'head': (6, 0, 0)},
         'hands': {'l': (.07, -.30, 1.16), 'r': (-.20, -.20, 1.40)}, 'elbow': {'l': (.2, -.3, -1), 'r': (-.6, -.3, -1)},
         'aim': {'l': (0, 0, 1)}, 'point': {'cannon': (0, -.2, 1)}}

RANGED_CLIPS = {
    # elemental (wind 8, contact 12, hold 18, follow 22, recover 30, end 36)
    'elemental': [
        (0, {}),
        (5, SLAP),
        (8, {**SLAP, 'hips': (.0, .24), 'turn': {'hips': (8, 0, 0), 'chest': (24, 0, 0), 'head': (18, 0, 0)},
             'shrug': {'l': (-4, 10), 'r': (-4, 10)}}),
        (11, {**PULSE, 'hands': {'l': (.46, -.14, 1.36), 'r': (-.46, -.12, 1.36)}, 'scale': {}}),
        (12, PULSE),
        (18, held(PULSE, 0)),
        (22, {**held(PULSE, .02), 'shrug': {'l': (14, -10), 'r': (14, -10)}}),
        (30, RECOVER),
        (36, {}),
    ],
    # ultimate (wind 26, contact 32, hold 40, follow 46, recover 56, end 66)
    'ultimate': [
        (0, {}),
        (6, SLAP),
        (12, {**SLAP, 'hips': (.0, .26), 'turn': {'hips': (8, 0, 0), 'chest': (26, 0, 0), 'head': (20, 0, 0)}}),
        (18, KNEEL),
        (26, held(KNEEL, .02)),
        (31, {**KNEEL, 'hips': (.06, .43)}),
        (32, BEAM),
        (40, held(BEAM, 0)),
        (46, {**held(BEAM, .01), 'hips': (-.16, .38)}),
        (56, RECOVER),
        (66, {}),
    ],
    # breaker (16): covering up, then the electric burst
    'breaker': [(0, COVER), (3, PULSE), (9, held(PULSE, 0)), (13, RECOVER), (16, {})],
}

GUARD_HIGH = {'hips': (-.03, .06), 'turn': {'chest': (10, 0, 0), 'head': (2, 0, -6)}, 'shrug': {'l': (12, 10), 'r': (12, 10)},
              'hands': {'l': (.06, -.28, 1.44), 'r': (-.14, -.22, 1.46)},
              'elbow': {'l': (.2, -.4, -1), 'r': (-.4, -.4, -1)}, 'aim': {'l': (0, 0, 1)}, 'point': {'cannon': (0, -.1, 1)}}
GUARD_LOW = {**CROUCH, 'hands': {'l': (.08, -.32, .98), 'r': (-.14, -.30, .92)},
             'elbow': {'l': (.6, -.3, -1), 'r': (-.8, -.2, -1)}, 'aim': {'l': (0, 0, 1)}, 'point': {'cannon': (0, -.6, 1)}}
SIDESTEP = {'hips': (-.08, .12), 'turn': {'hips': (4, -6, -14), 'spine': (8, -8, -6), 'chest': (12, -14, -10), 'head': (-6, -8, 30)},
            'feet': {'l': ankle(L0, .0), 'r': ankle(R0, -.06)}, 'aim': AIM, 'point': GUN}

MOVEMENT = {
    'walk_forward': walk_sheet(1),
    'walk_back': walk_sheet(-1),
    'crouch': hold(10, CROUCH),
    'guard_high': hold(10, GUARD_HIGH, held(GUARD_HIGH)),
    'guard_low': hold(10, GUARD_LOW, held(GUARD_LOW)),
    'parry': [(0, {}), (3, SIDESTEP), (12, held(SIDESTEP)), (18, {})],
}

# ---- jump, reactions and victory ----
UP = (0, 0, 1)
X_LYING = {'free': True, 'hips': (-.10, .70), 'turn': {'hips': (-86, 0, 0), 'chest': (-4, 0, 0), 'head': (8, 0, 14)},
           'feet': {'l': (.18, -.72, .12), 'r': (-.18, -.64, .16)}, 'knee': {'l': UP, 'r': UP},
           'hands': {'l': (.50, .30, .16), 'r': (-.50, .36, .16)}, 'aim': {'l': (1, 0, 0)}, 'point': {'cannon': (-1, 0, 0)}}
X_SPLAT = {**X_LYING, 'turn': {'hips': (-90, 0, 0), 'chest': (-2, 0, 0), 'head': (4, 0, 26)},
           'feet': {'l': (.28, -.74, .10), 'r': (-.26, -.68, .10)}, 'hands': {'l': (.62, .30, .12), 'r': (-.62, .42, .12)}}
X_BOUNCE = {**X_LYING, 'hips': (-.10, .60), 'turn': {'hips': (-80, 0, 0), 'chest': (-12, 0, 0), 'head': (16, 0, 10)},
            'feet': {'l': (.18, -.74, .26), 'r': (-.18, -.64, .32)}}
X_FLUNG = {'free': True, 'hips': (-.24, -.04), 'turn': {'hips': (-24, 0, 0), 'chest': (-24, 0, 10), 'head': (-20, 0, -12)},
           'shrug': {'l': (16, -14), 'r': (16, -14)},
           'feet': {'l': (.18, -.30, .34), 'r': (-.16, -.12, .42)}, 'knee': {'l': (0, -1, 0), 'r': (0, -1, 0)},
           'hands': {'l': (.44, -.10, 1.66), 'r': (-.44, .10, 1.60)}, 'point': {'cannon': (-.4, .3, 1)},
           'robe': {'robe_front': (-30, 0, 0), 'robe_back': (20, 0, 0)}}
X_FALLING = {'free': True, 'hips': (-.30, .40), 'turn': {'hips': (-58, 0, 0), 'chest': (-12, 0, 6), 'head': (14, 0, -6)},
             'feet': {'l': (.18, -.62, .50), 'r': (-.18, -.48, .60)}, 'knee': {'l': UP, 'r': UP},
             'hands': {'l': (.50, .10, .98), 'r': (-.50, .18, .92)}, 'point': {'cannon': (-1, .2, .2)}}
HIT_SNAP = {'hips': (-.10, .06), 'turn': {'hips': (-4, 0, -6), 'spine': (-8, 0, -4), 'chest': (-18, 0, -10), 'head': (-26, 6, 24)},
            'feet': {'l': ankle(L0, -.04, .04)}, 'shrug': {'l': (16, -10), 'r': (16, -10)},
            'hands': {'l': (.24, -.06, 1.28), 'r': (-.30, .14, 1.42)}, 'elbow': {'l': (1, .3, -.3), 'r': (-1, .3, -.6)},
            'aim': {'l': (.4, 0, -1)}, 'point': {'cannon': (-.2, .6, .8)}, 'robe': {'robe_front': (-14, 0, 0)}}
JUMP_RISE = {'free': True, 'hips': (0, -.08), 'turn': {'hips': (2, 0, -10), 'chest': (6, 0, -12), 'head': (-2, 0, 28)},
             'feet': {'l': (.13, -.08, .20), 'r': (-.15, .14, .12)}, 'foot_turn': {'l': 30, 'r': 40},
             'hands': HANDS, 'aim': AIM, 'point': GUN, 'robe': {'robe_front': (14, 0, 0), 'robe_back': (14, 0, 0)}}
JUMP_FALL = {'free': True, 'hips': (0, -.24), 'turn': {'hips': (8, 0, -10), 'chest': (14, 0, -12), 'head': (-2, 0, 28)},
             'feet': {'l': (.13, -.20, .66), 'r': (-.15, .10, .60)}, 'knee': {'l': (0, -1, .2), 'r': (0, -1, .2)},
             'hands': {'l': (.14, -.18, 1.12), 'r': (-.29, .09, 1.46)}, 'aim': AIM, 'point': GUN,
             'robe': {'robe_front': (-16, 0, 0), 'robe_back': (-10, 0, 0)}}
# victory: a twirl of the cannon out to his side, then he blows the smoke off the barrel by his face
TWIRL = {'hips': (0, .02), 'turn': {'hips': (0, 0, 10), 'chest': (0, 0, 14), 'head': (-4, 0, -6)},
         'hands': {'r': (-.52, -.16, 1.24), 'l': (.24, .02, 1.02)}, 'elbow': {'r': (-1, .2, -.6), 'l': (1, .6, -.2)},
         'aim': {'l': (-.3, 0, -1)}, 'point': {'cannon': (-1, -.3, .2)}}
BLOW = {'hips': (0, .0), 'turn': {'hips': (0, 0, 14), 'chest': (-4, 0, 20), 'head': (6, 0, -14)},
        'hands': {'r': (-.16, -.30, 1.48), 'l': (.24, .02, 1.02)}, 'elbow': {'r': (-1, .2, -1), 'l': (1, .6, -.2)},
        'aim': {'l': (-.3, 0, -1)}, 'point': {'cannon': (.15, -.35, 1)}}

def stretch(keys, n):
    """The same keys spread over n frames."""
    end = keys[-1][0]
    return [(round(f * n / end), k) for f, k in keys]


REACTIONS = {
    'jump_start': [(0, JUMP_RISE), (8, JUMP_RISE)],
    'jump_air': [(0, JUMP_FALL), (16, JUMP_FALL)],
    'jump_land': [(0, {'hips': (0, .18), 'turn': {**TURN, 'chest': (14, 0, -12)}, 'aim': AIM, 'point': GUN,
                       'robe': {'robe_front': (10, 0, 0), 'robe_back': (10, 0, 0)}}),
                  (4, {'hips': (0, .08), 'aim': AIM, 'point': GUN, 'robe': {'robe_front': (-6, 0, 0)}}),
                  (10, {})],
    'hit': [(0, HIT_SNAP), (8, held(HIT_SNAP, .02)),
            (13, {'hips': (-.06, .06), 'turn': {'chest': (-4, 0, -8), 'head': (-8, 0, 20)}, 'aim': AIM, 'point': GUN}),
            (20, {})],
    'knockdown': stretch([(0, HIT_SNAP), (5, X_FLUNG), (12, X_FALLING), (18, X_LYING), (21, X_BOUNCE), (24, X_LYING)], 30),
    'ko': stretch([(0, {**HIT_SNAP, 'turn': {'spine': (-10, 0, 6), 'chest': (-24, 0, 14), 'head': (-30, 0, -14)}}),
           (6, {**X_FLUNG, 'hips': (-.28, -.10), 'turn': {'hips': (-34, 0, 0), 'chest': (-26, 0, 14), 'head': (-22, 0, -16)}}),
           (14, X_FALLING), (20, X_LYING), (23, X_BOUNCE), (26, X_LYING), (30, X_SPLAT)], 40),
    'get_up': [(0, X_LYING),
               (6, {'free': True, 'hips': (-.12, .58), 'turn': {'hips': (-40, 0, 0), 'chest': (14, 0, 0), 'head': (-4, 0, 0)},
                    'feet': {'l': (.18, -.46, .16), 'r': (-.18, -.30, .16)}, 'knee': {'l': UP, 'r': UP},
                    'hands': {'l': (.36, .12, .26), 'r': (-.30, -.30, .70)}, 'point': {'cannon': (0, -.3, -1)}}),
               (12, {'hips': (.0, .30), 'turn': {'hips': (16, 0, 0), 'chest': (20, 0, 0), 'head': (-6, 0, -10)},
                     'feet': {'r': ankle(R0, .10)}, 'hands': {'l': (.24, -.40, .90), 'r': (-.26, -.20, 1.06)},
                     'point': {'cannon': (0, -.2, 1)}}),
               (18, {'hips': (.0, .08), 'aim': AIM, 'point': GUN}),
               (24, {})],
    'victory': stretch([(0, {}), (6, TWIRL), (10, {**TWIRL, 'point': {'cannon': (-.3, .3, -1)}}),
                (14, {**TWIRL, 'point': {'cannon': (-.6, -.8, 0)}}), (20, BLOW), (32, held(BLOW, .005)), (40, BLOW)], 48),
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
# the empty keys (start and end of a clip) are the idle's first key: no pop into or out of the idle
IDLE0 = SHEETS['idle'][0][1]
for _clip, _keys in SHEETS.items():
    for _i, (_f, _k) in enumerate(_keys):
        if _k == {}:
            _keys[_i] = (_f, IDLE0)
la.SHEETS['volt'] = SHEETS


def author(rig, clips=None, force=False):
    """Author Orsted's sheets on orsted_Rig (all, or the named clips, in order)."""
    import bpy
    for c in (clips or SHEETS):
        if c not in bpy.data.actions:
            act = bpy.data.actions.new(c)
            act.use_fake_user = True
            track = rig.animation_data.nla_tracks.new()
            track.name = c
            track.strips.new(c, 0, act)
    out = [la.author(rig, c, 'volt', force).name for c in (clips or SHEETS)]
    la.sync_strips(rig)
    return out
