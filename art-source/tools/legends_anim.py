"""Limited (stepped) animation for the Legends fighters, in the spirit of Arc System Works' 3D
anime fighters: every key is a drawn pose held for its own number of frames, with no
interpolation. Anticipation and impact are held, a one-key smear stretches the striking limb,
the impact overshoots, and the legs work (hips sink, knees bend, the front foot steps).

A pose is written in character space on top of the guard (frame 0 of the generated J1):
  'hips':  (forward, down) metres the hips travel (feet stay planted unless 'feet' moves them)
  'turn':  {bone: (lean, side, twist)} degrees in character space, applied hips -> head;
           lean > 0 bends forward, twist > 0 turns the left shoulder back (the right one forward)
  'feet':  {side: (x, y, z)} ankle targets; omitted feet stay where they are in the guard
  'hands': {side: (x, y, z)} wrist targets
  'elbow': {side: (x, y, z)} the way the elbow points (default out and down)
  'aim':   {side: (x, y, z)} direction the hand points (fist: forward; palm: up, heel forward)
  'scale': {bone: (x, y, z)} bone scale (y runs along the bone), for smears and impacts
  'shrug': {side: (up, forward)} degrees the shoulder (collarbone) lifts and rolls forward
  'foot_turn': {side: degrees} pitch of the foot (negative lifts the toes)
  'sole':  {side: ((sole faces), (toes point))} striking foot orientation (see orient_foot)
  'pivot': {side: degrees} a planted foot turning on the ground under a kick
  'point': {bone: (x, y, z)} a held prop's bone (the gun) points that way; its hand turns, the prop's
           top stays up
  'robe':  {bone: (lean, side, twist)} apron panel swing (lean > 0 swings it back)
  'spin':  degrees the whole body turns about the vertical through the hips (negative turns
           over the right shoulder); feet and hand targets stay in world space
  'knee':  {side: (x, y, z)} the way the knee points (default forward): sideways for a
           roundhouse, down for a back kick, so the leg never folds the wrong way
  'free':  True for poses off the stance (lying, sweeping on the floor): no base sink, hips
           go where 'hips' says and the feet are not held to the ground
Planted feet (on GROUND) are always reached: if the leg is too short the hips drop.
  'from':  (clip, frame) this key copies another clip's pose (chains start where the last ended)
Positions are metres with the rig at the origin: +X is the character's left, -Y forward, +Z up.
The Babuin faces -Y with the left foot and left hand in front.

Only clips listed in SHEETS are re-authored; every other clip (including clips edited by hand
in Blender) is left untouched. The generated clip is kept as <clip>_generated.
contact / follow / end stay on anim_timing's frames, so the combat frame data is unchanged.

Run in Blender: import legends_anim; legends_anim.author_all(rig)
"""
import math

import bpy
from mathutils import Euler, Matrix, Quaternion, Vector

FIST, PALM = (0, -1, 0), (0, -0.25, 1)

# Ankles on the ground (rest height .149, sole flat): left (front) and right (back) guard spots.
# The generated guard floated the feet 6-9 cm on tiptoe; every key now plants them flat.
# Every strike steps: the combat moves the fighter forward (combat.gd LIGHT_FEEL), so in the clip
# the stepping foot lands ahead on contact and both feet are back on the guard spots by the end,
# when the whole body has travelled. Advances: J1 .15 m, J2 .25 m, J3 .35 m.
L0, R0 = (.146, -.048, .149), (-.146, .233, .149)
GROUND = .149
# Every pose sits this much lower than the generated guard: knees bent, so the planted feet reach
# the ground (hip to ankle is 88 cm there, the leg only 83 cm).
BASE_SINK = .15


def ankle(base, forward=0.0, up=0.0):
    return (base[0], base[1] - forward, base[2] + up)


def ease(x):
    return x * x * (3 - 2 * x)


def walk_sheet(direction=1, n=26, keys=13, stride=.80):
    """Walk with the legs alternating: each half cycle one foot swings past the other (the right
    one first), so the stance swaps and swaps back; the hips turn with each step and the chest
    counters. Feet are written in the ground's frame and moved back by the body's travel, so a
    planted foot holds its spot (the game walks faster than the legs: the rest slides, as in
    most fighters). Walking back is the same cycle played in reverse."""
    out = []
    uL, uR = -L0[1], -R0[1]                     # forward coordinate of each guard spot
    for i in range(keys + 1):
        t = i / keys
        tt = t if direction > 0 else 1 - t
        r_sw = ease(min(tt / .5, 1.0))           # right foot swings in the first half
        l_sw = ease(max((tt - .5) / .5, 0.0))    # left foot in the second
        root = stride * tt
        ur = uR + stride * r_sw - root
        ul = uL + stride * l_sw - root
        lift_r = .14 * math.sin(math.pi * min(tt / .5, 1.0)) if tt < .5 else 0.0
        lift_l = .14 * math.sin(math.pi * max((tt - .5) / .5, 0.0)) if tt > .5 else 0.0
        sway = math.sin(2 * math.pi * tt)        # +: right leg forward half
        out.append((round(n * t), {
            'hips': (.02 * direction, .02 + .03 * abs(math.sin(2 * math.pi * tt))),
            'turn': {'hips': (0, 0, 14 * sway), 'chest': (4 * direction, 0, -10 * sway), 'head': (-4 * direction, 0, -4 * sway)},
            'shrug': {'l': (4, 6 * sway), 'r': (4, -6 * sway)},
            'feet': {'l': (L0[0], -ul, GROUND + lift_l), 'r': (R0[0], -ur, GROUND + lift_r)},
        }))
    return out


def hold(n, pose, settle=None):
    """A pose struck at once and held (guards, crouch): optional settle key at n // 2."""
    keys = [(0, pose)]
    if settle:
        keys.append((n // 2, settle))
    keys.append((n, pose if not settle else settle))
    return keys


CROUCH = {'hips': (.04, .34), 'turn': {'hips': (10, 0, 0), 'chest': (12, 0, -4), 'head': (-16, 0, 4)},
          'shrug': {'l': (6, 6), 'r': (6, 6)},
          'feet': {'l': ankle(L0, .04), 'r': ankle(R0, -.04)},
          'hands': {'l': (.16, -.46, 1.02), 'r': (-.04, -.30, .96)}}
GUARD_HIGH = {'hips': (-.02, .05), 'turn': {'chest': (8, 0, -6), 'head': (-10, 0, 4)},
              'shrug': {'l': (12, 10), 'r': (12, 10)},
              'hands': {'l': (.10, -.40, 1.58), 'r': (-.07, -.32, 1.52)}, 'aim': {'l': PALM, 'r': PALM}}
GUARD_LOW = {'hips': (.0, .36), 'turn': {'hips': (10, 0, 0), 'chest': (16, 0, -4), 'head': (-18, 0, 4)},
             'shrug': {'l': (12, 12), 'r': (12, 12)},
             'feet': {'l': ankle(L0, .04), 'r': ankle(R0, -.04)},
             'hands': {'l': (.10, -.42, 1.16), 'r': (-.07, -.34, 1.10)}, 'aim': {'l': PALM, 'r': PALM}}

BATCH1 = {
    'walk_forward': walk_sheet(1),
    'walk_back': walk_sheet(-1),
    # Dash: drops low and lunges, the lead foot reaching far, the rear foot dragging after.
    'dash': [
        (0, {'hips': (.06, .10), 'turn': {'chest': (14, 0, -6), 'head': (-14, 0, 4)}, 'shrug': {'l': (4, 8), 'r': (4, 8)},
             'feet': {'l': ankle(L0, .10, .06)}}),
        (3, {'hips': (.16, .14), 'turn': {'hips': (8, 0, 0), 'chest': (18, 0, -8), 'head': (-18, 0, 6)},
             'shrug': {'l': (2, 10), 'r': (2, 10)},
             'feet': {'l': ankle(L0, .30), 'r': ankle(R0, .0, .04)}}),
        (7, {'hips': (.12, .12), 'turn': {'chest': (14, 0, -6), 'head': (-14, 0, 4)},
             'feet': {'l': ankle(L0, .16), 'r': ankle(R0, -.12, .06)}}),
        (12, {'hips': (.02, .04)}),
    ],
    'crouch': hold(12, CROUCH),
    'guard_high': hold(12, GUARD_HIGH),
    'guard_low': hold(12, GUARD_LOW),
    # Parry: the lead palm sweeps a circle out and across, deflecting, then returns.
    'parry': [
        (0, {}),
        (2, {'hips': (-.02, .06), 'turn': {'chest': (-4, 0, 10)}, 'shrug': {'l': (10, -6)},
             'hands': {'l': (.32, -.42, 1.58), 'r': (-.06, -.28, 1.30)}, 'aim': {'l': PALM}}),
        (5, {'hips': (.04, .08), 'turn': {'chest': (8, 0, -14), 'head': (-8, 0, 8)}, 'shrug': {'l': (4, 14)},
             'hands': {'l': (-.06, -.62, 1.46), 'r': (-.06, -.30, 1.30)}, 'aim': {'l': (-1, -.4, .5)},
             'scale': {'forearm_l': (1, 1.2, 1)}}),
        (10, {'hips': (.03, .07), 'turn': {'chest': (6, 0, -10)}, 'shrug': {'l': (3, 10)},
              'hands': {'l': (.0, -.58, 1.44), 'r': (-.06, -.30, 1.30)}, 'aim': {'l': (-1, -.4, .5)}}),
        (14, {'hips': (.01, .04), 'hands': {'l': (.14, -.52, 1.40)}}),
        (18, {}),
    ],
    # Hit: thrown back from the chest, head snapping, arms flung, then pulled back to guard.
    'hit': [
        (0, {'hips': (-.10, .02), 'turn': {'hips': (-6, 0, 0), 'spine': (-8, 0, 6), 'chest': (-16, 0, 12), 'head': (14, 0, -10)},
             'shrug': {'l': (14, -12), 'r': (14, -12)},
             'feet': {'l': ankle(L0, -.06, .05)},
             'hands': {'l': (.32, -.18, 1.62), 'r': (-.30, .06, 1.48)}}),
        (4, {'hips': (-.12, .06), 'turn': {'spine': (-6, 0, 4), 'chest': (-12, 0, 10), 'head': (10, 0, -8)},
             'shrug': {'l': (10, -8), 'r': (10, -8)},
             'hands': {'l': (.30, -.22, 1.50), 'r': (-.28, .02, 1.40)}}),
        (10, {'hips': (-.06, .06), 'turn': {'chest': (-4, 0, 4)},
              'hands': {'l': (.20, -.38, 1.38), 'r': (-.12, -.20, 1.28)}}),
        (20, {}),
    ],
}


TUCK = {'turn': {'chest': (10, 0, -4), 'head': (-10, 0, 4)}, 'shrug': {'l': (8, 6), 'r': (8, 6)},
        'feet': {'l': ankle(L0, .10, .34), 'r': ankle(R0, -.02, .26)},
        'hands': {'l': (.14, -.46, 1.42), 'r': (-.06, -.30, 1.32)}}
SALUTE_HANDS = {'l': (.03, -.32, 1.40), 'r': (-.01, -.30, 1.37)}
FEET_TOGETHER = {'l': (.09, .0, GROUND), 'r': (-.09, .04, GROUND)}

BATCH2 = {
    # Jump: loads low on both legs, springs up stretched, then tucks the knees.
    'jump_start': [
        (0, {'hips': (.0, .22), 'turn': {'chest': (14, 0, -4), 'head': (-14, 0, 4)}, 'shrug': {'l': (2, 8), 'r': (2, 8)},
             'hands': {'l': (.16, -.40, 1.14), 'r': (-.08, -.24, 1.06)}}),
        (3, {'hips': (.02, -.06), 'turn': {'chest': (-4, 0, -4), 'head': (4, 0, 4)}, 'shrug': {'l': (14, 0), 'r': (14, 0)},
             'feet': {'l': ankle(L0, .04, .08), 'r': ankle(R0, -.04, .04)},
             'hands': {'l': (.18, -.40, 1.62), 'r': (-.10, -.26, 1.56)}}),
        (8, TUCK),
    ],
    'jump_air': [
        (0, TUCK),
        (8, {**TUCK, 'turn': {'chest': (14, 0, -6), 'head': (-14, 0, 6)},
             'feet': {'l': ankle(L0, .12, .38), 'r': ankle(R0, -.0, .30)}}),
        (16, TUCK),
    ],
    # Landing: absorbs deep on both legs, then rises back into the guard.
    'jump_land': [
        (0, {'hips': (.04, .30), 'turn': {'hips': (8, 0, 0), 'chest': (16, 0, -4), 'head': (-18, 0, 4)},
             'shrug': {'l': (2, 10), 'r': (2, 10)},
             'hands': {'l': (.20, -.40, 1.06), 'r': (-.12, -.22, .98)}}),
        (4, {'hips': (.02, .12), 'turn': {'chest': (6, 0, -4)}}),
        (10, {}),
    ],
    # Victory: the wing chun salute - feet together, right fist into the left palm before the
    # chest, a deep bow, then standing tall.
    'victory': [
        (0, {}),
        (6, {'hips': (.0, -.06), 'feet': FEET_TOGETHER, 'shrug': {'l': (6, 4), 'r': (6, 4)},
             'hands': SALUTE_HANDS, 'aim': {'l': (0, 0, 1), 'r': (0, -1, 0)}}),
        (14, {'hips': (-.04, -.02), 'feet': FEET_TOGETHER, 'turn': {'hips': (10, 0, 0), 'chest': (18, 0, 0), 'head': (12, 0, 0)},
              'shrug': {'l': (2, 10), 'r': (2, 10)},
              'hands': {'l': (.03, -.40, 1.22), 'r': (-.01, -.38, 1.19)}, 'aim': {'l': (0, -.3, 1), 'r': (0, -1, -.2)}}),
        (32, {'hips': (.0, -.08), 'feet': FEET_TOGETHER, 'turn': {'chest': (-4, 0, 0), 'head': (-6, 0, 0)},
              'shrug': {'l': (8, -4), 'r': (8, -4)},
              'hands': SALUTE_HANDS, 'aim': {'l': (0, 0, 1), 'r': (0, -1, 0)}}),
        (48, {'hips': (.0, -.08), 'feet': FEET_TOGETHER, 'turn': {'chest': (-4, 0, 0), 'head': (-6, 0, 0)},
              'shrug': {'l': (8, -4), 'r': (8, -4)},
              'hands': SALUTE_HANDS, 'aim': {'l': (0, 0, 1), 'r': (0, -1, 0)}}),
    ],
}


KICK_GUARD = {'l': (.14, -.46, 1.46), 'r': (-.06, -.30, 1.36)}
SHIN = ((0, .3, -.95), (-1, -.2, 0))          # roundhouse: instep/shin leading, toes pointed across
SOLE_FWD = ((0, -1, 0), (0, 0, 1))             # front kick: ball/sole forward, toes up
HEEL_BACK = ((0, -1, 0), (0, 0, -1))           # back kick: sole to the target, toes down
# After K1 the right foot lands in front (switch stance): the guard spots mirrored.
L_BACK, R_FRONT = (.146, .20, GROUND), (-.146, -.10, GROUND)

KCHAIN = {
    # K1: low roundhouse with the rear (right) leg - a short step in, the hips turn over, the
    # lead foot pivots out, the shin swings level into the thigh, the kicking-side arm swings
    # down for balance and the other hand covers the face; the leg lands in front.
    'heavy': [
        (0, {}),
        (3, {'hips': (.06, .04), 'turn': {'hips': (0, 0, 10), 'chest': (0, 0, -8)},
             'feet': {'l': (.20, -.14, GROUND), 'r': ankle(R0, -.02, .10)}, 'pivot': {'l': 25},
             'hands': {'l': (.14, -.30, 1.62), 'r': (-.10, -.30, 1.40)}}),
        (6, {'hips': (.03, .05), 'turn': {'hips': (0, 0, 30), 'chest': (-6, 0, 18), 'head': (4, 0, -16)},
             'robe': {'robe_side_r': (-25, 0, 0), 'robe_side_l': (24, 0, 0)},
             'feet': {'l': (.20, -.14, GROUND), 'r': (-.44, -.30, .58)}, 'knee': {'r': (-1, -.3, .6)},
             'sole': {'r': SHIN}, 'pivot': {'l': 55},
             'hands': {'l': (.06, -.24, 1.66), 'r': (-.34, .08, 1.10)}, 'scale': {'foot_r': (1.2, 1.2, 1.2)}}),
        (9, {'hips': (.14, .14), 'turn': {'hips': (-8, 0, 60), 'chest': (-16, 0, 30), 'head': (8, 0, -34)},
             'shrug': {'l': (10, 4), 'r': (-4, -12)},
             'robe': {'robe_side_r': (-45, 0, 0), 'robe_side_l': (-30, 0, 0), 'robe_front': (-20, 0, 0)},
             'feet': {'l': (.20, -.14, GROUND), 'r': (.22, -.90, .62)}, 'knee': {'r': (-.6, 0, 1)},
             'sole': {'r': SHIN}, 'pivot': {'l': 75},
             'hands': {'l': (.04, -.22, 1.68), 'r': (-.38, .20, 1.02)}, 'scale': {'foot_r': (1.15, 1.15, 1.15)}}),
        (12, {'hips': (.12, .13), 'turn': {'hips': (-6, 0, 55), 'chest': (-12, 0, 26), 'head': (6, 0, -30)},
              'robe': {'robe_side_r': (-35, 0, 0)},
              'feet': {'l': (.20, -.14, GROUND), 'r': (.24, -.84, .60)}, 'knee': {'r': (-.6, 0, 1)},
              'sole': {'r': SHIN}, 'pivot': {'l': 75},
              'hands': {'l': (.04, -.22, 1.68), 'r': (-.36, .18, 1.04)}}),
        (15, {'hips': (.10, .08), 'turn': {'hips': (0, 0, 20), 'chest': (0, 0, 10)},
              'feet': {'l': (.20, -.10, GROUND), 'r': (-.10, -.30, .24)}, 'knee': {'r': (-.6, -1, 0)}, 'pivot': {'l': 40},
              'hands': {'l': (.12, -.36, 1.56), 'r': (-.14, -.36, 1.40)}}),
        (21, {'hips': (.06, .06), 'feet': {'l': L_BACK, 'r': R_FRONT},
              'hands': {'l': (.12, -.36, 1.50), 'r': (-.10, -.48, 1.44)}}),
        (26, {}),
    ],
    # K2: switches the pivot to the right foot and fires a front kick (mae geri) with the left
    # leg: knee chambered high, then the leg snaps straight with the ball of the foot; lands in
    # front, back in the guard.
    'heavy_2': [
        (0, {'from': ('heavy', 15)}),
        (3, {'hips': (.02, .05), 'feet': {'l': L_BACK, 'r': R_FRONT}, 'pivot': {'r': 10},
             'hands': {'l': (.10, -.40, 1.48), 'r': (-.10, -.46, 1.46)}}),
        (6, {'hips': (.0, .02), 'turn': {'chest': (-6, 0, -6), 'head': (6, 0, 4)}, 'shrug': {'l': (8, -4), 'r': (8, -4)},
             'feet': {'l': (.12, -.30, .64), 'r': R_FRONT}, 'knee': {'l': (0, -1, .8)}, 'foot_turn': {'l': -25},
             'pivot': {'r': 20}, 'robe': {'robe_front': (-40, 0, 0)},
             'hands': {'l': (.12, -.36, 1.50), 'r': (-.08, -.40, 1.52)}}),
        (9, {'hips': (.06, .02), 'turn': {'chest': (-10, 0, -8)},
             'feet': {'l': (.10, -.66, .82), 'r': R_FRONT}, 'knee': {'l': (0, -1, .6)}, 'sole': {'l': SOLE_FWD},
             'pivot': {'r': 25}, 'robe': {'robe_front': (-50, 0, 0)},
             'hands': {'l': (.12, -.34, 1.50), 'r': (-.08, -.40, 1.52)}, 'scale': {'foot_l': (1.2, 1.2, 1.2)}}),
        (11, {'hips': (.14, .02), 'turn': {'hips': (-8, 0, -6), 'chest': (-16, 0, -10), 'head': (10, 0, 6)},
              'shrug': {'l': (4, 6), 'r': (4, -6)},
              'feet': {'l': (.08, -1.02, .98), 'r': R_FRONT}, 'knee': {'l': (0, -1, .4)}, 'sole': {'l': SOLE_FWD},
              'pivot': {'r': 30}, 'robe': {'robe_front': (-55, 0, 0), 'robe_side_l': (-25, 0, 0)},
              'hands': {'l': (.14, -.30, 1.48), 'r': (-.06, -.36, 1.50)}, 'scale': {'foot_l': (1.25, 1.25, 1.25)}}),
        (14, {'hips': (.13, .02), 'turn': {'hips': (-6, 0, -5), 'chest': (-13, 0, -8), 'head': (8, 0, 5)},
              'feet': {'l': (.08, -.98, .96), 'r': R_FRONT}, 'knee': {'l': (0, -1, .4)}, 'sole': {'l': SOLE_FWD},
              'pivot': {'r': 30}, 'robe': {'robe_front': (-45, 0, 0)},
              'hands': {'l': (.14, -.30, 1.48), 'r': (-.06, -.36, 1.50)}}),
        (18, {'hips': (.10, .02), 'turn': {'chest': (-6, 0, -4)},
              'feet': {'l': (.12, -.40, .60), 'r': R_FRONT}, 'knee': {'l': (0, -1, .8)}, 'foot_turn': {'l': -20},
              'pivot': {'r': 15}, 'hands': KICK_GUARD}),
        (25, {'hips': (.06, .05), 'feet': {'l': ankle(L0, .16), 'r': ankle(R0, .12)}}),
        (32, {}),
    ],
    # K3: spinning back kick - steps across and turns over the right shoulder, looks back over
    # it at the target, drives the right heel straight back into it with the back to the
    # opponent, then completes the turn and lands in the guard.
    'heavy_3': [
        (0, {'from': ('heavy_2', 18)}),
        (3, {'hips': (.04, .08), 'spin': -60, 'turn': {'head': (0, 0, -30)},
             'feet': {'l': (.06, -.18, GROUND), 'r': (-.20, .10, .12)}, 'pivot': {'l': -60},
             'hands': {'l': (.10, -.20, 1.48), 'r': (-.20, -.02, 1.46)}}),
        (6, {'hips': (.06, .06), 'spin': -140, 'turn': {'head': (0, 0, -60)},
             'feet': {'l': (.04, -.18, GROUND), 'r': (-.02, .0, .58)}, 'knee': {'r': (0, -.4, -1)},
             'pivot': {'l': -140}, 'robe': {'robe_back': (-20, 0, 0)},
             'hands': {'l': (.0, .06, 1.50), 'r': (-.14, .10, 1.52)}}),
        (10, {'hips': (.08, .04), 'spin': -180, 'turn': {'chest': (-14, 0, 0), 'head': (-6, 0, -70)},
              'feet': {'l': (.04, -.16, GROUND), 'r': (.0, -.52, .80)}, 'knee': {'r': (0, 0, -1)},
              'sole': {'r': HEEL_BACK}, 'pivot': {'l': -180}, 'robe': {'robe_back': (-30, 0, 0)},
              'hands': {'l': (-.04, .12, 1.44), 'r': (-.18, .08, 1.30)}, 'scale': {'foot_r': (1.2, 1.2, 1.2)}}),
        (13, {'hips': (.14, .06), 'spin': -180, 'turn': {'hips': (-12, 0, 0), 'chest': (-26, 0, 0), 'head': (-14, 0, -75)},
              'shrug': {'l': (6, 0), 'r': (6, 0)},
              'feet': {'l': (.04, -.12, GROUND), 'r': (.02, -1.06, .92)}, 'knee': {'r': (0, 0, -1)},
              'sole': {'r': HEEL_BACK}, 'pivot': {'l': -180},
              'robe': {'robe_back': (-40, 0, 0), 'robe_side_r': (-30, 0, 0)},
              'hands': {'l': (-.06, .14, 1.38), 'r': (-.22, .10, 1.22)}, 'scale': {'foot_r': (1.3, 1.3, 1.3)}}),
        (16, {'hips': (.13, .06), 'spin': -180, 'turn': {'hips': (-10, 0, 0), 'chest': (-22, 0, 0), 'head': (-12, 0, -72)},
              'feet': {'l': (.04, -.12, GROUND), 'r': (.02, -1.0, .90)}, 'knee': {'r': (0, 0, -1)},
              'sole': {'r': HEEL_BACK}, 'pivot': {'l': -180}, 'robe': {'robe_back': (-30, 0, 0)},
              'hands': {'l': (-.06, .14, 1.38), 'r': (-.22, .10, 1.22)}}),
        (20, {'hips': (.10, .06), 'spin': -250, 'turn': {'head': (0, 0, -40)},
              'feet': {'l': (.04, -.12, GROUND), 'r': (-.04, -.40, .46)}, 'knee': {'r': (0, -.3, -1)},
              'pivot': {'l': -250},
              'hands': {'l': (-.10, .0, 1.46), 'r': (-.16, -.20, 1.40)}}),
        (28, {'hips': (.06, .10), 'spin': -330, 'turn': {'head': (0, 0, -10)},
              'feet': {'l': ankle(L0, .10), 'r': ankle(R0, .02, .04)}, 'pivot': {'l': -20},
              'hands': KICK_GUARD}),
        (36, {}),
    ],
}


UP = (0, 0, 1)
# Lying on the back, head away from the opponent: hips on the floor, legs toward the opponent.
LYING = {'free': True, 'hips': (-.10, .90), 'turn': {'hips': (-86, 0, 0), 'chest': (-4, 0, 0), 'head': (8, 0, 10)},
         'feet': {'l': (.16, -.78, .10), 'r': (-.16, -.70, .14)}, 'knee': {'l': UP, 'r': UP},
         'hands': {'l': (.46, .30, .12), 'r': (-.46, .36, .12)}}
SPLAT = {**LYING, 'turn': {'hips': (-90, 0, 0), 'chest': (-2, 0, 0), 'head': (4, 0, 22)},
         'feet': {'l': (.24, -.80, .08), 'r': (-.22, -.74, .08)},
         'hands': {'l': (.58, .30, .08), 'r': (-.58, .42, .08)}}
FLUNG = {'free': True, 'hips': (-.22, -.04), 'turn': {'hips': (-24, 0, 0), 'chest': (-22, 0, 10), 'head': (18, 0, -12)},
         'shrug': {'l': (16, -14), 'r': (16, -14)},
         'feet': {'l': (.16, -.30, .34), 'r': (-.14, -.12, .42)}, 'knee': {'l': (0, -1, 0), 'r': (0, -1, 0)},
         'hands': {'l': (.40, -.10, 1.66), 'r': (-.40, .10, 1.60)}}
FALLING = {'free': True, 'hips': (-.30, .46), 'turn': {'hips': (-58, 0, 0), 'chest': (-12, 0, 6), 'head': (14, 0, -6)},
           'feet': {'l': (.16, -.62, .52), 'r': (-.16, -.48, .62)}, 'knee': {'l': UP, 'r': UP},
           'hands': {'l': (.46, .10, .96), 'r': (-.46, .18, .90)}}
LOW_FIST = ((0, -1, -.15))
LEAD_PALMS = {'l': PALM, 'r': PALM}

BATCH4 = {
    'knockdown': [
        (0, {'hips': (-.08, .0), 'turn': {'spine': (-8, 0, 4), 'chest': (-20, 0, 10), 'head': (16, 0, -10)},
             'shrug': {'l': (14, -12), 'r': (14, -12)},
             'hands': {'l': (.34, -.16, 1.62), 'r': (-.32, .06, 1.50)}}),
        (4, FLUNG),
        (10, FALLING),
        (16, LYING),
        (19, {**LYING, 'hips': (-.10, .80), 'turn': {'hips': (-80, 0, 0), 'chest': (-8, 0, 0), 'head': (16, 0, 8)}}),
        (23, LYING),
        (30, LYING),
    ],
    'ko': [
        (0, {'hips': (-.10, .0), 'turn': {'spine': (-10, 0, 6), 'chest': (-24, 0, 14), 'head': (20, 0, -14)},
             'shrug': {'l': (16, -14), 'r': (16, -14)},
             'hands': {'l': (.36, -.14, 1.64), 'r': (-.34, .08, 1.52)}}),
        (5, {**FLUNG, 'hips': (-.26, -.10), 'turn': {'hips': (-34, 0, 0), 'chest': (-26, 0, 14), 'head': (22, 0, -16)}}),
        (12, FALLING),
        (18, LYING),
        (22, {**LYING, 'hips': (-.10, .78), 'turn': {'hips': (-78, 0, 0), 'chest': (-8, 0, 0), 'head': (18, 0, 10)}}),
        (27, LYING),
        (34, SPLAT),
        (40, SPLAT),
    ],
    # Get up: sits up, plants a hand and the feet, rises through a crouch to the guard.
    'get_up': [
        (0, LYING),
        (5, {'free': True, 'hips': (-.12, .78), 'turn': {'hips': (-40, 0, 0), 'chest': (14, 0, 0), 'head': (-10, 0, 0)},
             'feet': {'l': (.16, -.46, .14), 'r': (-.16, -.30, .14)}, 'knee': {'l': UP, 'r': UP},
             'hands': {'l': (.30, .12, .16), 'r': (-.20, -.30, .60)}}),
        (10, {'hips': (.0, .40), 'turn': {'hips': (14, 0, 0), 'chest': (16, 0, 0), 'head': (-16, 0, 0)},
              'hands': {'l': (.20, -.40, .96), 'r': (-.10, -.26, .92)}}),
        (18, {}),
    ],
    # Down punch: low straight punch from the crouch with the lead fist.
    'down_punch': [
        (0, CROUCH),
        (3, {**CROUCH, 'hips': (-.02, .36), 'turn': {'hips': (10, 0, 0), 'chest': (10, 0, 10), 'head': (-14, 0, -6)},
             'hands': {'l': (.16, -.30, .98), 'r': (-.04, -.28, .98)}}),
        (5, {**CROUCH, 'hips': (.06, .36), 'hands': {'l': (.10, -.70, .96), 'r': (-.04, -.30, .98)},
             'aim': {'l': LOW_FIST}, 'scale': {'forearm_l': (1, 1.35, 1)}}),
        (6, {**CROUCH, 'hips': (.12, .38), 'turn': {'hips': (12, 0, 0), 'chest': (16, 0, -18), 'head': (-18, 0, 14)},
             'shrug': {'l': (2, 16), 'r': (4, -8)}, 'feet': {'l': ankle(L0, .12), 'r': ankle(R0, -.04)},
             'hands': {'l': (.04, -1.0, .94), 'r': (-.04, -.30, 1.02)}, 'aim': {'l': LOW_FIST},
             'scale': {'forearm_l': (1, 1.15, 1), 'hand_l': (1.2, 1.2, 1.2)}}),
        (10, {**CROUCH, 'hips': (.10, .38), 'feet': {'l': ankle(L0, .12), 'r': ankle(R0, -.04)},
              'hands': {'l': (.05, -.92, .94), 'r': (-.04, -.30, 1.02)}, 'aim': {'l': LOW_FIST}}),
        (12, {**CROUCH, 'hips': (.06, .36), 'feet': {'l': ankle(L0, .08)}}),
        (18, CROUCH),
        (24, CROUCH),
    ],
    # Air punch: knees tucked, a straight punch angled down at the opponent.
    'air_punch': [
        (0, TUCK),
        (3, {**TUCK, 'turn': {'chest': (4, 0, 12), 'head': (-6, 0, -8)},
             'hands': {'l': (.16, -.20, 1.46), 'r': (-.06, -.30, 1.32)}}),
        (5, {**TUCK, 'hands': {'l': (.10, -.62, 1.28), 'r': (-.06, -.30, 1.32)}, 'aim': {'l': (0, -1, -.45)},
             'scale': {'forearm_l': (1, 1.35, 1)}}),
        (6, {**TUCK, 'turn': {'chest': (18, 0, -18), 'head': (-16, 0, 14)}, 'shrug': {'l': (2, 16), 'r': (4, -8)},
             'hands': {'l': (.04, -.92, 1.12), 'r': (-.04, -.24, 1.36)}, 'aim': {'l': (0, -1, -.45)},
             'scale': {'forearm_l': (1, 1.15, 1), 'hand_l': (1.2, 1.2, 1.2)}}),
        (10, {**TUCK, 'turn': {'chest': (15, 0, -14)}, 'hands': {'l': (.05, -.86, 1.14), 'r': (-.04, -.24, 1.36)},
              'aim': {'l': (0, -1, -.45)}}),
        (14, TUCK),
        (24, TUCK),
    ],
    # Sweep: drops to the rear knee and swings the extended lead leg along the floor in an arc.
    'sweep': [
        (0, {}),
        (3, {'hips': (.0, .46), 'turn': {'hips': (14, 0, 0), 'chest': (16, 0, 0), 'head': (-16, 0, 0)},
             'feet': {'l': ankle(L0, .06), 'r': ankle(R0, -.04)},
             'hands': {'l': (.30, -.30, .62), 'r': (-.20, -.20, .70)}}),
        (5, {'free': True, 'hips': (.02, .58), 'spin': -40, 'turn': {'chest': (20, 0, 0), 'head': (-20, 0, 20)},
             'feet': {'l': (.52, -.40, .18), 'r': (-.14, .26, GROUND)}, 'knee': {'l': UP},
             'hands': {'l': (.20, -.30, .40), 'r': (-.30, -.10, .44)}}),
        (6, {'free': True, 'hips': (.04, .60), 'spin': -70, 'turn': {'chest': (22, 0, 0), 'head': (-22, 0, 30)},
             'feet': {'l': (.36, -.72, .18), 'r': (-.14, .26, GROUND)}, 'knee': {'l': UP}, 'pivot': {'r': -70},
             'robe': {'robe_side_l': (-40, 0, 0)},
             'hands': {'l': (.20, -.36, .38), 'r': (-.30, -.10, .44)}, 'scale': {'foot_l': (1.2, 1.2, 1.2)}}),
        (10, {'free': True, 'hips': (.04, .60), 'spin': -110, 'turn': {'chest': (22, 0, 0), 'head': (-20, 0, 50)},
              'feet': {'l': (.0, -.84, .18), 'r': (-.14, .26, GROUND)}, 'knee': {'l': UP}, 'pivot': {'r': -110},
              'hands': {'l': (.10, -.36, .38), 'r': (-.30, -.06, .44)}}),
        (12, {'free': True, 'hips': (.02, .58), 'spin': -150, 'turn': {'chest': (20, 0, 0), 'head': (-20, 0, 70)},
              'feet': {'l': (-.36, -.66, .18), 'r': (-.14, .26, GROUND)}, 'knee': {'l': UP}, 'pivot': {'r': -150},
              'hands': {'l': (.0, -.30, .40), 'r': (-.26, .0, .46)}}),
        (18, {'hips': (.0, .40), 'turn': {'hips': (12, 0, 0), 'chest': (14, 0, 0)},
              'hands': {'l': (.20, -.40, .96), 'r': (-.10, -.26, .92)}}),
        (24, {}),
    ],
    # Rajada de Vento: gathers the wind between both palms at the right hip, then drives both
    # palms forward with a step, releasing the gust.
    'elemental': [
        (0, {}),
        (5, {'hips': (-.03, .10), 'turn': {'chest': (-4, 0, 22), 'head': (4, 0, -18)}, 'shrug': {'l': (6, 6), 'r': (6, -10)},
             'hands': {'l': (-.04, -.20, 1.14), 'r': (-.18, -.06, 1.08)}, 'aim': {'l': (0, -.3, -1), 'r': (0, -.3, 1)}}),
        (11, {'hips': (-.05, .14), 'turn': {'chest': (-8, 0, 30), 'head': (6, 0, -24)}, 'shrug': {'l': (8, 8), 'r': (8, -14)},
              'hands': {'l': (-.06, -.16, 1.10), 'r': (-.20, -.02, 1.04)}, 'aim': {'l': (0, -.3, -1), 'r': (0, -.3, 1)}}),
        (13, {'hips': (.08, .12), 'turn': {'chest': (4, 0, 6)},
              'feet': {'l': ankle(L0, .10, .06)},
              'hands': {'l': (.10, -.60, 1.32), 'r': (-.10, -.60, 1.26)}, 'aim': LEAD_PALMS,
              'scale': {'forearm_l': (1, 1.35, 1), 'forearm_r': (1, 1.35, 1)}}),
        (14, {'hips': (.18, .12), 'turn': {'hips': (8, 0, 0), 'chest': (14, 0, -6), 'head': (-14, 0, 6)},
              'shrug': {'l': (4, 18), 'r': (4, 18)}, 'feet': {'l': ankle(L0, .20)},
              'hands': {'l': (.12, -1.04, 1.40), 'r': (-.12, -1.04, 1.30)}, 'aim': LEAD_PALMS,
              'scale': {'forearm_l': (1, 1.15, 1), 'forearm_r': (1, 1.15, 1), 'hand_l': (1.3, 1.3, 1.3), 'hand_r': (1.3, 1.3, 1.3)},
              'robe': {'robe_back': (30, 0, 0), 'robe_side_l': (20, 0, 0), 'robe_side_r': (20, 0, 0)}}),
        (18, {'hips': (.17, .12), 'turn': {'chest': (12, 0, -5)}, 'shrug': {'l': (4, 14), 'r': (4, 14)},
              'feet': {'l': ankle(L0, .20)},
              'hands': {'l': (.12, -.98, 1.40), 'r': (-.12, -.98, 1.30)}, 'aim': LEAD_PALMS}),
        (22, {'hips': (.12, .10), 'feet': {'l': ankle(L0, .12)},
              'hands': {'l': (.14, -.80, 1.38), 'r': (-.12, -.78, 1.30)}, 'aim': LEAD_PALMS}),
        (29, {'hips': (.04, .05), 'hands': {'l': (.14, -.56, 1.38), 'r': (-.08, -.40, 1.32)}}),
        (36, {}),
    ],
    # Tufão Celestial: sinks and sweeps the arms in a circle, rises with both palms overhead,
    # spins a full turn as the typhoon builds and fires a huge double palm forward.
    'ultimate': [
        (0, {}),
        (6, {'hips': (.0, .24), 'turn': {'chest': (16, 0, 0), 'head': (-14, 0, 0)}, 'shrug': {'l': (2, 10), 'r': (2, 10)},
             'hands': {'l': (.30, -.30, .80), 'r': (-.30, -.30, .80)}, 'aim': {'l': (0, 0, -1), 'r': (0, 0, -1)}}),
        (12, {'hips': (.0, -.06), 'turn': {'chest': (-12, 0, 0), 'head': (10, 0, 0)}, 'shrug': {'l': (20, -4), 'r': (20, -4)},
              'feet': {'l': ankle(L0, .0, .04), 'r': ankle(R0, .0, .04)},
              'hands': {'l': (.16, -.10, 2.10), 'r': (-.16, -.10, 2.10)}, 'aim': {'l': UP, 'r': UP},
              'robe': {'robe_front': (-20, 0, 0), 'robe_back': (20, 0, 0)}}),
        (18, {'hips': (-.04, .18), 'spin': -90, 'turn': {'chest': (-6, 0, 0), 'head': (0, 0, 50)},
              'hands': {'l': (.40, -.10, 1.50), 'r': (-.40, .10, 1.50)},
              'robe': {'robe_side_l': (-30, 0, 0), 'robe_side_r': (30, 0, 0)}}),
        (21, {'hips': (.02, .16), 'spin': -270, 'turn': {'chest': (4, 0, 0), 'head': (0, 0, -60)},
              'hands': {'l': (-.46, .10, 1.42), 'r': (.46, -.10, 1.42)},
              'scale': {'forearm_l': (1, 1.3, 1), 'forearm_r': (1, 1.3, 1)},
              'robe': {'robe_side_l': (30, 0, 0), 'robe_side_r': (-30, 0, 0), 'robe_back': (-30, 0, 0)}}),
        (24, {'hips': (.22, .14), 'turn': {'hips': (10, 0, 0), 'chest': (16, 0, 0), 'head': (-16, 0, 0)},
              'shrug': {'l': (6, 20), 'r': (6, 20)}, 'feet': {'l': ankle(L0, .26)},
              'hands': {'l': (.14, -1.10, 1.46), 'r': (-.14, -1.10, 1.30)}, 'aim': LEAD_PALMS,
              'scale': {'forearm_l': (1, 1.2, 1), 'forearm_r': (1, 1.2, 1), 'hand_l': (1.45, 1.45, 1.45), 'hand_r': (1.45, 1.45, 1.45)},
              'robe': {'robe_back': (45, 0, 0), 'robe_side_l': (30, 0, 0), 'robe_side_r': (30, 0, 0)}}),
        (30, {'hips': (.21, .14), 'turn': {'hips': (8, 0, 0), 'chest': (14, 0, 0), 'head': (-14, 0, 0)},
              'shrug': {'l': (6, 16), 'r': (6, 16)}, 'feet': {'l': ankle(L0, .26)},
              'hands': {'l': (.14, -1.04, 1.46), 'r': (-.14, -1.04, 1.30)}, 'aim': LEAD_PALMS,
              'scale': {'hand_l': (1.25, 1.25, 1.25), 'hand_r': (1.25, 1.25, 1.25)},
              'robe': {'robe_back': (35, 0, 0)}}),
        (35, {'hips': (.16, .12), 'feet': {'l': ankle(L0, .20)},
              'hands': {'l': (.14, -.84, 1.42), 'r': (-.12, -.82, 1.30)}, 'aim': LEAD_PALMS}),
        (44, {'hips': (.06, .06), 'feet': {'l': ankle(L0, .06)}, 'hands': {'l': (.14, -.56, 1.40), 'r': (-.08, -.40, 1.32)}}),
        (54, {}),
    ],
    # Breaker: closes up, arms crossed, then bursts open - arms flung wide, chest up.
    'breaker': [
        (0, {}),
        (3, {'hips': (.0, .16), 'turn': {'chest': (14, 0, 0), 'head': (-16, 0, 0)}, 'shrug': {'l': (8, 14), 'r': (8, 14)},
             'hands': {'l': (-.10, -.30, 1.40), 'r': (.10, -.28, 1.46)}}),
        (6, {'hips': (-.02, -.08), 'turn': {'chest': (-14, 0, 0), 'head': (12, 0, 0)}, 'shrug': {'l': (16, -16), 'r': (16, -16)},
             'feet': {'l': ankle(L0, .06), 'r': ankle(R0, -.04)},
             'hands': {'l': (.66, .0, 1.56), 'r': (-.66, .04, 1.56)}, 'aim': {'l': (1, 0, .3), 'r': (-1, 0, .3)},
             'scale': {'hand_l': (1.3, 1.3, 1.3), 'hand_r': (1.3, 1.3, 1.3)},
             'robe': {'robe_front': (-30, 0, 0), 'robe_back': (30, 0, 0), 'robe_side_l': (0, -25, 0), 'robe_side_r': (0, 25, 0)}}),
        (10, {'hips': (-.02, -.06), 'turn': {'chest': (-10, 0, 0), 'head': (8, 0, 0)}, 'shrug': {'l': (12, -12), 'r': (12, -12)},
              'feet': {'l': ankle(L0, .06), 'r': ankle(R0, -.04)},
              'hands': {'l': (.62, .0, 1.52), 'r': (-.62, .04, 1.52)}, 'aim': {'l': (1, 0, .3), 'r': (-1, 0, .3)}}),
        (16, {}),
    ],
    # Arcade select: arms folded across the chest, feet planted wide, chin up, breathing.
    'select': [
        (f, {'hips': (.0, .02 + .02 * (1 - math.cos(math.pi * f / 24))), 'feet': {'l': (.27, -.02, GROUND), 'r': (-.27, .08, GROUND)},
             'turn': {'chest': (-5 + 2 * (1 - math.cos(math.pi * f / 24)), 0, 0), 'head': (-8, 0, 0)},
             'shrug': {'l': (8 + 4 * (1 - math.cos(math.pi * f / 24)), 6), 'r': (8 + 4 * (1 - math.cos(math.pi * f / 24)), 6)},
             'hands': {'l': (-.17, -.17, 1.30), 'r': (.17, -.19, 1.36)},
             'elbow': {'l': (1, -1.2, -.3), 'r': (-1, -1.2, -.2)}})
        for f in range(0, 49, 6)
    ],
}


def idle_sheet(n=64, keys=16):
    """Bob on bent knees, rocking forward and back: the hips travel fore and aft once per
    cycle (dipping a little at each end), the chest leans with them and the head stays level;
    feet stay planted flat. Held keys every n / keys frames (limited animation)."""
    out = []
    for i in range(keys + 1):
        t = i / keys
        sn, c2 = math.sin(2 * math.pi * t), math.cos(4 * math.pi * t)
        out.append((round(n * t), {
            'hips': (.035 * sn, .012 - .012 * c2),
            'turn': {'chest': (4 * sn, 0, 0), 'head': (-4 * sn, 0, 0)},
            # shoulders breathe: up at the top of each dip, rolling forward with the lean
            'shrug': {'l': (6 + 6 * c2, 7 * sn), 'r': (6 + 6 * c2, 7 * sn)},
            'feet': {'l': L0, 'r': R0},
        }))
    return out


SHEETS = {
    'kaze': {
        'idle': idle_sheet(),
        **BATCH1,
        **BATCH2,
        **KCHAIN,
        **BATCH4,
        # J1: hesitates back with the lead hand out, then a shuffle step and a vertical-fist
        # punch down the centre line with the lead (left) hand; the right hand guards (wing chun).
        'light_1': [
            (0, {}),
            (2, {'hips': (-.05, .06), 'turn': {'chest': (-6, 0, 6)}, 'shrug': {'l': (6, -6), 'r': (6, -6)},
                 'feet': {'l': ankle(L0, -.02)},
                 'hands': {'l': (.16, -.50, 1.36), 'r': (-.06, -.28, 1.28)}}),
            (5, {'hips': (.06, .07), 'turn': {'chest': (6, 0, -10)},
                 'feet': {'l': ankle(L0, .08, .07)},
                 'hands': {'l': (.10, -.74, 1.40), 'r': (-.06, -.30, 1.28)}, 'aim': {'l': FIST},
                 'scale': {'forearm_l': (1, 1.4, 1)}}),
            (7, {'hips': (.13, .10), 'turn': {'hips': (8, 0, 0), 'spine': (6, 0, -8), 'chest': (14, 0, -20), 'head': (-16, 0, 14)},
                 'feet': {'l': ankle(L0, .16)},
                 'shrug': {'l': (4, 16), 'r': (2, -6)},
                 'hands': {'l': (.03, -1.08, 1.44), 'r': (-.04, -.32, 1.30)}, 'aim': {'l': FIST},
                 'scale': {'forearm_l': (1, 1.25, 1), 'hand_l': (1.2, 1.2, 1.2)}}),
            (10, {'hips': (.12, .10), 'turn': {'hips': (6, 0, 0), 'chest': (11, 0, -16), 'head': (-12, 0, 10)},
                  'feet': {'l': ankle(L0, .16)},
                  'shrug': {'l': (3, 12)},
                  'hands': {'l': (.04, -.98, 1.43), 'r': (-.04, -.32, 1.30)}, 'aim': {'l': FIST},
                  'scale': {'forearm_l': (1, 1.12, 1)}}),
            (12, {'hips': (.07, .08), 'turn': {'chest': (6, 0, -10)},
                  'feet': {'l': ankle(L0, .08), 'r': ankle(R0, -.07, .04)},
                  'hands': {'l': (.08, -.80, 1.41), 'r': (-.05, -.30, 1.29)}, 'aim': {'l': FIST}}),
            (16, {'hips': (.02, .05), 'turn': {'chest': (3, 0, -4)},
                  'feet': {'r': ankle(R0, -.02)},
                  'hands': {'l': (.14, -.62, 1.38)}}),
            (22, {}),
        ],
        # J2: from the J1 punch, the front knee rises for drive, the foot stamps far forward and
        # the rear hand comes over the top (overhand); the back foot drags up after it.
        'light_2': [
            (0, {'from': ('light_1', 12)}),
            (2, {'hips': (-.03, -.03), 'turn': {'chest': (-10, 0, -28), 'head': (6, 0, 16)},
                 'feet': {'l': ankle(L0, .04, .32)},
                 'shrug': {'r': (12, -14)},
                 'hands': {'l': (.14, -.55, 1.40), 'r': (-.28, -.02, 1.62)}, 'aim': {'r': (0, -.3, 1)}}),
            (5, {'hips': (.08, .03), 'turn': {'chest': (6, 0, 4)},
                 'feet': {'l': ankle(L0, .20, .12)},
                 'hands': {'l': (.14, -.40, 1.34), 'r': (-.16, -.58, 1.76)}, 'aim': {'r': FIST},
                 'scale': {'forearm_r': (1, 1.4, 1)}}),
            (7, {'hips': (.18, .12), 'turn': {'hips': (8, 0, 6), 'spine': (8, 0, 10), 'chest': (20, 0, 28), 'head': (-18, 0, -16)},
                 'feet': {'l': ankle(L0, .27)},
                 'shrug': {'r': (6, 18), 'l': (0, -8)},
                 'hands': {'l': (.12, -.26, 1.26), 'r': (-.02, -1.05, 1.34)}, 'aim': {'r': (0, -1, -.3)},
                 'scale': {'forearm_r': (1, 1.25, 1), 'hand_r': (1.2, 1.2, 1.2)}}),
            (10, {'hips': (.17, .12), 'turn': {'hips': (6, 0, 5), 'chest': (16, 0, 22), 'head': (-14, 0, -12)},
                  'feet': {'l': ankle(L0, .27)},
                  'shrug': {'r': (4, 14)},
                  'hands': {'l': (.12, -.27, 1.27), 'r': (-.03, -.96, 1.34)}, 'aim': {'r': (0, -1, -.3)},
                  'scale': {'forearm_r': (1, 1.12, 1)}}),
            (12, {'hips': (.10, .09), 'turn': {'chest': (10, 0, 12)},
                  'feet': {'l': ankle(L0, .14), 'r': ankle(R0, -.10, .05)},
                  'hands': {'l': (.13, -.32, 1.30), 'r': (-.06, -.78, 1.36)}}),
            (16, {'hips': (.03, .05), 'turn': {'chest': (4, 0, 4)},
                  'feet': {'r': ankle(R0, -.03)}}),
            (22, {}),
        ],
        # J3: sinks, then the rear foot steps through to the front with a standing palm from the
        # rear (right) hand, heel of the hand first, the whole body behind it. In the recovery
        # the right foot steps back, so the guard (left foot forward) is restored.
        'light_3': [
            (0, {'from': ('light_2', 12)}),
            (4, {'hips': (-.03, .12), 'turn': {'chest': (-6, 0, -18), 'head': (4, 0, 14)}, 'shrug': {'r': (8, -12)},
                 'hands': {'l': (.12, -.48, 1.36), 'r': (-.16, -.04, 1.10)}, 'aim': {'r': PALM}}),
            (7, {'hips': (.12, .11), 'turn': {'chest': (6, 0, 6)},
                 'feet': {'r': (-.10, -.06, .30)},
                 'hands': {'l': (.12, -.40, 1.34), 'r': (-.10, -.64, 1.28)}, 'aim': {'r': PALM},
                 'scale': {'forearm_r': (1, 1.45, 1)}}),
            (10, {'hips': (.24, .13), 'turn': {'hips': (8, 0, 10), 'spine': (6, 0, 10), 'chest': (16, 0, 28), 'head': (-14, 0, -18)},
                  'feet': {'r': (-.12, -.42, GROUND)},
                  'shrug': {'r': (4, 20), 'l': (0, -10)},
                  'hands': {'l': (.10, -.22, 1.24), 'r': (-.02, -1.10, 1.36)}, 'aim': {'r': PALM},
                  'scale': {'forearm_r': (1, 1.25, 1), 'hand_r': (1.3, 1.3, 1.3)}}),
            (13, {'hips': (.23, .13), 'turn': {'hips': (6, 0, 8), 'chest': (13, 0, 24), 'head': (-12, 0, -14)},
                  'feet': {'r': (-.12, -.42, GROUND)},
                  'shrug': {'r': (3, 16)},
                  'hands': {'l': (.10, -.22, 1.24), 'r': (-.02, -1.02, 1.36)}, 'aim': {'r': PALM},
                  'scale': {'forearm_r': (1, 1.12, 1)}}),
            (16, {'hips': (.14, .10), 'turn': {'chest': (9, 0, 16)},
                  'feet': {'r': (-.12, -.24, GROUND), 'l': ankle(L0, -.12, .03)},
                  'hands': {'l': (.10, -.26, 1.26), 'r': (-.05, -.84, 1.36)}, 'aim': {'r': PALM}}),
            (22, {'hips': (.04, .05), 'turn': {'chest': (3, 0, 4)},
                  'feet': {'r': ankle(R0, .10, .08)}}),
            (28, {}),
        ],
    },
}

def _contact(clip, frames, pose, fid='kaze'):
    """Replace the contact key (frames[0]) and its hold (frames[1]) of a sheet with one pose: the
    hold is the same pose settled a hair lower, without the scale pop."""
    held = {k: v for k, v in pose.items() if k != 'scale'}
    if 'hips' in held:
        held['hips'] = (held['hips'][0], held['hips'][1] + .01)
    keys = dict(SHEETS[fid][clip])
    keys[frames[0]], keys[frames[1]] = pose, held
    SHEETS[fid][clip] = sorted(keys.items())


# Whole-body contact poses for Babuin (attack-poses skill, docs/estudos): the lead foot steps
# far in, the rear leg straightens on the line of the torso, the shoulders turn side-on with the
# striking one forward, the free hand pulls back; kicks go high on a straight support leg, the
# torso leaning away as the counterweight, the arms open. Babuin whips: long straight lines.
_contact('light_1', (7, 10), {
    'hips': (.30, .12), 'turn': {'hips': (10, 0, -16), 'spine': (8, 0, -12), 'chest': (20, 0, -34), 'head': (-22, 0, 26)},
    'feet': {'l': ankle(L0, .36), 'r': ankle(R0, -.02, .05)}, 'shrug': {'l': (4, 22), 'r': (6, -10)},
    'hands': {'l': (.02, -1.30, 1.44), 'r': (-.12, .06, 1.30)}, 'aim': {'l': FIST},
    'scale': {'forearm_l': (1, 1.25, 1), 'hand_l': (1.25, 1.25, 1.25)}})
_contact('light_2', (7, 10), {
    'hips': (.36, .13), 'turn': {'hips': (10, 0, 16), 'spine': (10, 0, 14), 'chest': (24, 0, 38), 'head': (-24, 0, -28)},
    'feet': {'l': ankle(L0, .42), 'r': ankle(R0, .02, .06)}, 'shrug': {'r': (4, 22), 'l': (4, -12)},
    'hands': {'l': (.16, .10, 1.26), 'r': (-.02, -1.30, 1.36)}, 'aim': {'r': (0, -1, -.3)},
    'scale': {'forearm_r': (1, 1.25, 1), 'hand_r': (1.25, 1.25, 1.25)}})
_contact('light_3', (10, 13), {
    'hips': (.42, .16), 'turn': {'hips': (12, 0, 14), 'spine': (10, 0, 14), 'chest': (24, 0, 40), 'head': (-22, 0, -30)},
    'feet': {'r': (-.12, -.66, GROUND), 'l': ankle(L0, -.20, .06)}, 'shrug': {'r': (4, 24), 'l': (0, -12)},
    'hands': {'l': (.16, .12, 1.20), 'r': (-.02, -1.40, 1.38)}, 'aim': {'r': PALM},
    'scale': {'forearm_r': (1, 1.25, 1), 'hand_r': (1.35, 1.35, 1.35)}})
# K1 low roundhouse: still low (it takes the thigh), but the body leans far away, the arms swing.
_contact('heavy', (9, 12), {
    'hips': (.16, .12), 'turn': {'hips': (-14, 0, 70), 'spine': (-8, 0, 10), 'chest': (-22, 0, 30), 'head': (14, 0, -40)},
    'shrug': {'l': (14, 6), 'r': (-4, -14)},
    'robe': {'robe_side_r': (-50, 0, 0), 'robe_side_l': (-30, 0, 0), 'robe_front': (-24, 0, 0)},
    'feet': {'l': (.20, -.14, GROUND), 'r': (.26, -1.00, .70)}, 'knee': {'r': (-.6, 0, 1)},
    'sole': {'r': SHIN}, 'pivot': {'l': 85},
    'hands': {'l': (.30, -.20, 1.72), 'r': (-.52, .34, 1.10)}, 'scale': {'foot_r': (1.25, 1.25, 1.25)}})
# K2 front kick: the ball of the foot at chest height on a straight leg, torso far back.
_contact('heavy_2', (11, 14), {
    'hips': (.10, .0), 'turn': {'hips': (-18, 0, -6), 'spine': (-10, 0, 0), 'chest': (-20, 0, -10), 'head': (22, 0, 6)},
    'shrug': {'l': (14, -6), 'r': (14, -6)},
    'feet': {'l': (.08, -1.06, 1.34), 'r': R_FRONT}, 'knee': {'l': (0, -1, .2)}, 'sole': {'l': SOLE_FWD},
    'pivot': {'r': 35}, 'robe': {'robe_front': (-65, 0, 0), 'robe_side_l': (-30, 0, 0)},
    'hands': {'l': (.46, .04, 1.52), 'r': (-.42, .16, 1.46)}, 'scale': {'foot_l': (1.3, 1.3, 1.3)}})
# K3 spinning back kick: back to the opponent, the body tips nearly level into a T, heel high.
_contact('heavy_3', (13, 16), {
    'hips': (.12, .02), 'spin': -180, 'turn': {'hips': (-30, 0, 0), 'chest': (-30, 0, 0), 'head': (-24, 0, -75)},
    'shrug': {'l': (16, 0), 'r': (16, 0)},
    'feet': {'l': (.04, -.12, GROUND), 'r': (.02, -1.10, 1.30)}, 'knee': {'r': (0, 0, -1)},
    'sole': {'r': HEEL_BACK}, 'pivot': {'l': -180},
    'robe': {'robe_back': (-50, 0, 0), 'robe_side_r': (-40, 0, 0)},
    'hands': {'l': (.08, .40, 1.20), 'r': (-.30, .30, 1.30)}, 'scale': {'foot_r': (1.35, 1.35, 1.35)}})

SPINE_ORDER = ['hips', 'spine', 'chest', 'neck', 'head']

# Per-fighter stance used by place(): guard foot spots, ankle height on the ground, how far every
# pose sinks below the generated guard, and the guard hands (None: keep the generated guard's arms).
# Other fighters register theirs (legends_dale_anim.py adds 'ignis').
PROFILES = {'kaze': {'L0': L0, 'R0': R0, 'GROUND': GROUND, 'BASE_SINK': BASE_SINK, 'HANDS': None, 'ELBOW': None}}
GUARD_HANDS, GUARD_ELBOW, GUARD_TURN = None, None, None


def use(fid):
    """Point place() at a fighter's stance (module globals, so the sheets' helpers agree)."""
    global L0, R0, GROUND, BASE_SINK, GUARD_HANDS, GUARD_ELBOW, GUARD_TURN
    p = PROFILES[fid]
    L0, R0, GROUND, BASE_SINK = p['L0'], p['R0'], p['GROUND'], p['BASE_SINK']
    GUARD_HANDS, GUARD_ELBOW, GUARD_TURN = p['HANDS'], p['ELBOW'], p.get('TURN')


def fcurves(act):
    legacy = getattr(act, 'fcurves', None)
    if legacy is not None and len(legacy):
        return list(legacy)
    out = []
    for layer in getattr(act, 'layers', []):
        for strip in layer.strips:
            for bag in strip.channelbags:
                out.extend(bag.fcurves)
    return out


def sample(act, frame, bones):
    """{bone: (location, rotation_quaternion, scale)} of an action at a frame, from its curves."""
    curves = {(fc.data_path, fc.array_index): fc for fc in fcurves(act)}
    pose = {}
    for b in bones:
        def val(prop, i, default):
            fc = curves.get((f'pose.bones["{b}"].{prop}', i))
            return fc.evaluate(frame) if fc else default
        pose[b] = (Vector([val('location', i, 0.0) for i in range(3)]),
                   Quaternion([val('rotation_quaternion', i, 1.0 if i == 0 else 0.0) for i in range(4)]).normalized(),
                   Vector([val('scale', i, 1.0) for i in range(3)]))
    return pose


def generated(clip):
    return bpy.data.actions.get(clip + '_generated') or bpy.data.actions[clip]


def apply(rig, pose):
    for b in rig.pose.bones:
        b.location, b.rotation_quaternion, b.scale = pose[b.name]
    bpy.context.view_layer.update()


def orient_foot(foot, sole=None, pivot=0.0, pitch=0.0):
    """Foot orientation. Default: sole flat on the ground, toes forward (the rest orientation).
    pivot: degrees the foot turns on the ground about the vertical (a support foot pivoting
    under a kick); pitch: degrees about the side axis (negative lifts the toes).
    sole: ((x, y, z) the way the sole faces, (x, y, z) the way the toes point) for a striking
    foot, e.g. a push kick shows the sole forward with the toes up."""
    rest = foot.bone.matrix_local.to_3x3()
    if sole:
        def frame(n, t):
            n = Vector(n).normalized()
            t = (Vector(t) - n * Vector(t).dot(n)).normalized()
            return Matrix((t, n, t.cross(n))).transposed()
        rot = frame(*sole) @ frame((0, 0, -1), rest.col[1]).transposed()
    else:
        rot = Matrix.Rotation(math.radians(pivot), 3, 'Z') @ Matrix.Rotation(math.radians(pitch), 3, 'X')
    foot.matrix = Matrix.Translation(foot.head) @ (rot @ rest).to_4x4()


def point_bone(rig, bone, direction):
    """Turn a held prop's bone (a gun on the hand) so it points along direction, its rest 'up'
    (world +z at rest) kept as close to world up as it can: the parent (the hand) turns about its
    head, so the prop stays in the hand."""
    parent = bone.parent
    d = direction.normalized()
    cur = bone.matrix.to_3x3().col[1].normalized()
    turn = cur.rotation_difference(d).to_matrix().to_4x4()
    parent.matrix = Matrix.Translation(parent.head) @ turn @ Matrix.Translation(-parent.head) @ parent.matrix
    bpy.context.view_layer.update()
    up_local = bone.bone.matrix_local.to_3x3().inverted() @ Vector((0, 0, 1))
    up_now = (bone.matrix.to_3x3() @ up_local).normalized()
    want = Vector((0, 0, 1)) - d * d.z
    if want.length > 1e-3:
        want.normalize()
        a = up_now - d * up_now.dot(d)
        if a.length > 1e-3:
            a.normalize()
            ang = math.atan2(d.dot(a.cross(want)), a.dot(want))
            roll = Matrix.Rotation(ang, 4, d)
            parent.matrix = Matrix.Translation(parent.head) @ roll @ Matrix.Translation(-parent.head) @ parent.matrix
            bpy.context.view_layer.update()


def place(rig, key, start):
    """Pose the rig for one key: start pose, then hips, turns, legs, arms, hand aim and scale."""
    from character_polish import solve_limb
    pb = rig.pose.bones
    apply(rig, start)
    if 'from' in key:
        return
    if not key:
        key = {'feet': {'l': L0, 'r': R0}}
    spots = {'l': L0, 'r': R0}
    free = key.get('free', False)
    fwd, down = key.get('hips', (0, 0))
    down += 0.0 if free else BASE_SINK
    hips = pb['hips']
    hips.matrix = Matrix.Translation((0, -fwd, -down)) @ hips.matrix
    bpy.context.view_layer.update()
    spin = math.radians(key.get('spin', 0))
    if spin:
        # Whole-body turn about the vertical through the hips (spinning kicks).
        h = hips.head.copy()
        hips.matrix = Matrix.Translation(h) @ Matrix.Rotation(spin, 4, 'Z') @ Matrix.Translation(-h) @ hips.matrix
        bpy.context.view_layer.update()
    turns = {**(GUARD_TURN or {}), **key.get('turn', {})} if not free else key.get('turn', {})
    for name in SPINE_ORDER:
        if name in turns:
            lean, side, twist = turns[name]
            b = pb[name]
            r = Euler((math.radians(lean), math.radians(side), math.radians(twist)), 'XYZ').to_matrix().to_4x4()
            b.matrix = Matrix.Translation(b.head) @ r @ Matrix.Translation(-b.head) @ b.matrix
            bpy.context.view_layer.update()
    for s, (up, fwd) in key.get('shrug', {}).items():
        b = pb['shoulder_' + s]
        sx = 1 if s == 'l' else -1
        r = Euler((0, math.radians(-sx * up), math.radians(-sx * fwd)), 'XYZ').to_matrix().to_4x4()
        b.matrix = Matrix.Translation(b.head) @ r @ Matrix.Translation(-b.head) @ b.matrix
        bpy.context.view_layer.update()
    for name, (lean, side, twist) in key.get('robe', {}).items():
        b = pb[name]
        r = Euler((math.radians(lean), math.radians(side), math.radians(twist)), 'XYZ').to_matrix().to_4x4()
        b.matrix = Matrix.Translation(b.head) @ r @ Matrix.Translation(-b.head) @ b.matrix
        bpy.context.view_layer.update()
    targets = {s: Vector(key.get('feet', {}).get(s, spots[s])) for s in 'lr'}
    planted = [] if free else [s for s in 'lr' if targets[s].z <= GROUND + 1e-4]
    for _ in range(3):
        for s in 'lr':
            knee = Vector(key.get('knee', {}).get(s, (0, -1, 0)))
            if spin and s not in key.get('knee', {}):
                knee = Matrix.Rotation(spin, 3, 'Z') @ knee
            solve_limb(pb, 'thigh_' + s, 'shin_' + s, targets[s], knee)
        bpy.context.view_layer.update()
        # Planted feet sit exactly on the ground: a leg too short to reach drops the hips, a
        # leg folded through the floor (stretched stance) lifts them.
        errors = [pb['foot_' + s].head.z - GROUND for s in planted]
        off = max(errors, key=abs) if errors else 0.0
        if abs(off) < .003:
            break
        hips.matrix = Matrix.Translation((0, 0, -off)) @ hips.matrix
        bpy.context.view_layer.update()
    for s in 'lr':
        orient_foot(pb['foot_' + s], key.get('sole', {}).get(s), key.get('pivot', {}).get(s, 0),
                    key.get('foot_turn', {}).get(s, 0))
        bpy.context.view_layer.update()
    hands = dict(GUARD_HANDS or {})
    if 'free' not in key:
        hands.update(key.get('hands', {}))
    else:
        hands = dict(key.get('hands', {}))
    for s, target in hands.items():
        elbow = key.get('elbow', {}).get(s, (GUARD_ELBOW or {}).get(s, (1 if s == 'l' else -1, 0, -.6)))
        solve_limb(pb, 'upper_arm_' + s, 'forearm_' + s, Vector(target), Vector(elbow))
    for s, direction in key.get('aim', {}).items():
        hand = pb['hand_' + s]
        m = hand.matrix.copy()
        turn = m.to_3x3().col[1].normalized().rotation_difference(Vector(direction).normalized())
        hand.matrix = Matrix.Translation(hand.head) @ turn.to_matrix().to_4x4() @ Matrix.Translation(-hand.head) @ m
        bpy.context.view_layer.update()
    for name, direction in key.get('point', {}).items():
        point_bone(rig, pb[name], Vector(direction))
    for name, sc in key.get('scale', {}).items():
        pb[name].scale = sc
    bpy.context.view_layer.update()


def signature(act):
    """Fingerprint of an action's keys, to tell whether someone edited it after authoring."""
    vals = []
    for fc in sorted(fcurves(act), key=lambda c: (c.data_path, c.array_index)):
        vals.append(fc.data_path + str(fc.array_index))
        vals.extend(f'{k.co.x:.0f}:{k.co.y:.4f}' for k in fc.keyframe_points)
    return str(hash('|'.join(vals)) & 0xFFFFFFFF)


def edited_by_hand(clip):
    act = bpy.data.actions.get(clip)
    return act is not None and 'authored' in act and act['authored'] != signature(act)


def author(rig, clip, fid='kaze', force=False):
    """Re-author one clip from its sheet. A clip whose keys were changed by hand in Blender
    since it was authored is left alone (pass force=True to overwrite it anyway)."""
    if edited_by_hand(clip) and not force:
        print(f'{clip}: edited by hand in Blender - kept (author(..., force=True) overwrites)')
        return bpy.data.actions[clip]
    use(fid)
    sheet = SHEETS[fid][clip]
    bones = [b.name for b in rig.pose.bones]
    if PROFILES[fid].get('START') == 'rest':
        # a new body (its old clips were made for other proportions): poses start from the rest pose
        guard = {b: (Vector((0, 0, 0)), Quaternion((1, 0, 0, 0)), Vector((1, 1, 1))) for b in bones}
    else:
        guard = sample(generated('light_1'), 0, bones)
    old = bpy.data.actions[clip]
    if bpy.data.actions.get(clip + '_generated'):
        old.name = clip + '_old'
    else:
        old.name = clip + '_generated'
        old = None
    src = bpy.data.actions[clip + '_generated']
    ad = rig.animation_data
    keep = ad.action
    act = bpy.data.actions.new(clip)
    act.use_fake_user = True
    ad.action = act
    bpy.context.view_layer.update()
    prev = {}
    for frame, key in sheet:
        start = sample(bpy.data.actions[key['from'][0]], key['from'][1], bones) if 'from' in key else guard
        place(rig, key, start)
        for b in rig.pose.bones:
            if b.name in prev and prev[b.name].dot(b.rotation_quaternion) < 0:
                b.rotation_quaternion = -b.rotation_quaternion
            prev[b.name] = b.rotation_quaternion.copy()
            b.keyframe_insert('location', frame=frame)
            b.keyframe_insert('rotation_quaternion', frame=frame)
            b.keyframe_insert('scale', frame=frame)
    for fc in fcurves(act):
        for kp in fc.keyframe_points:
            kp.interpolation = 'CONSTANT'
    slot = act.slots[0] if hasattr(act, 'slots') and len(act.slots) else None
    for track in ad.nla_tracks:
        for strip in track.strips:
            if strip.action in (src, old):
                strip.action = act
                if slot is not None and hasattr(strip, 'action_slot'):
                    strip.action_slot = slot
                strip.frame_start, strip.frame_end = 0, sheet[-1][0]
    ad.action = keep if keep not in (src, old) else act
    if old is not None:
        bpy.data.actions.remove(old)
    for b in rig.pose.bones:
        b.location, b.rotation_quaternion, b.scale = (0, 0, 0), (1, 0, 0, 0), (1, 1, 1)
    act['authored'] = signature(act)
    return act


def sync_strips(rig):
    """Each NLA strip spans its whole action. A strip shorter or longer than its action (a clip
    created empty, or keys added past the end) is exported cut or frozen."""
    for track in rig.animation_data.nla_tracks:
        for strip in track.strips:
            start, end = strip.action.frame_range
            strip.action_frame_start, strip.action_frame_end = start, end
            strip.scale, strip.repeat = 1.0, 1.0
            strip.frame_start, strip.frame_end = start, end


def edit(rig, clip):
    """Set the scene up to edit one clip by hand: NLA tracks muted, the clip active, auto key
    on (every change is keyed, so moving to another frame keeps it)."""
    ad = rig.animation_data
    for t in ad.nla_tracks:
        t.mute = True
    ad.action = bpy.data.actions[clip]
    if hasattr(ad, 'action_slot') and len(ad.action.slots):
        ad.action_slot = ad.action.slots[0]
    scene = bpy.context.scene
    scene.tool_settings.use_keyframe_insert_auto = True
    scene.frame_start, scene.frame_end = 0, int(ad.action.frame_range[1])
    scene.frame_set(0)


def author_all(rig, fid='kaze'):
    """Author every sheet in order (later clips start from earlier ones)."""
    return [author(rig, clip, fid).name for clip in SHEETS[fid]]
