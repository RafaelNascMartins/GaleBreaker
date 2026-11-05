"""Babuin's Peixão outfit (fish mascot costume, the face showing through the fish mouth).

Concept: concept-art/characters/babuin/babuin-peixao-turnaround-v1.png, traced to
art-source/characters/kaze/legends/peixao/peixao_*_facetas.png (concept_facets.py --edge 3.2
--sr 6 --dark 50 --min-area 150), and the panel sheet babuin-peixao-texturas-referencia-v1.png.
The costume is drawn with a bigger head and a lower shoulder line than the Jade turnaround, so
the shapes come from the drawing but every piece sits on the Jade joints (same skeleton, clips
and hitboxes): a hood shell around the Jade head with an open lipped mouth, googly eyes on top,
a dorsal fin and side fins, a round-bellied suit, sleeves with fins and glove cuffs, legs with
boot cuffs and a little tail. The Jade head (face decal), ears, neck, fists and feet are kept:
fists and feet become the gloves and booties on the Peixão page.

Run in Blender: import legends_peixao as lp; lp.build(); lp.assemble()
"""
import bpy
from mathutils import Vector

import legends_model as lm
import legends_executivo as lx
from legends_babuin import JOINTS

TEAL = ('teal', (0.13, 0.52, 0.47))
FIN = ('fin', (0.45, 0.82, 0.72))
LIP = ('lip', (0.93, 0.47, 0.45))
EYE = ('eye', (0.97, 0.94, 0.85))
PUPIL = ('pupil', (0.05, 0.12, 0.12))
CREAM = ('cream', (0.94, 0.87, 0.70))
KEPT = ['head', 'neck', 'ear_l', 'ear_r', 'hand_l', 'hand_r', 'foot_l', 'foot_r']
CARRIED_BY = {'upper_arm': 'upper_arm', 'forearm': 'forearm', 'cuff': 'forearm', 'arm_fin': 'upper_arm'}

# Hood along the front-back axis: rings (x, y, z, half width, half height), back to front.
# Encloses the Jade head (x +-.152, y -.197...156, z 1.555...1.895) and ears (x .178).
HOOD = [(0, .225, 1.74, .10, .10), (0, .15, 1.75, .195, .205), (0, .02, 1.745, .222, .23),
        (0, -.12, 1.72, .205, .215), (0, -.19, 1.70, .182, .21)]
# 12-sided round section for the mouth and the front of the hood (an octagon read as a stop sign).
import math as _m
ROUND12 = [(_m.cos(_m.pi / 2 + i * _m.pi / 6), _m.sin(_m.pi / 2 + i * _m.pi / 6)) for i in range(12)]
# The mouth: a thick oval lip, taller than wide like the drawing, around the face (decal x +-.118,
# z 1.565...1.80), rolled outwards at the front and running back into a throat around the face,
# so the opening reads deep.
LIP_RINGS = [(0, -.185, 1.69, .178, .205), (0, -.235, 1.69, .19, .218), (0, -.262, 1.69, .158, .19),
             (0, -.25, 1.69, .128, .158), (0, -.205, 1.69, .124, .152), (0, -.17, 1.69, .132, .16)]
# Suit body (z, x0, x1, y0, y1): chest under the hood, a round belly that sticks out in front.
SUIT_TOP = [(1.57, -.10, .10, -.09, .10), (1.50, -.19, .19, -.15, .15),
            (1.38, -.205, .205, -.20, .16), (1.27, -.215, .215, -.24, .165)]
SUIT_LOW = [(1.30, -.205, .205, -.23, .16), (1.15, -.23, .23, -.27, .165),
            (1.0, -.22, .22, -.26, .165), (0.90, -.175, .175, -.17, .145), (0.84, -.10, .10, -.08, .08)]


def _j(name, s):
    v = Vector(JOINTS[name])
    return Vector((v.x if s == 'l' else -v.x, v.y, v.z))


def _along(p0, p1, t, off=Vector()):
    return tuple(p0.lerp(p1, t) + off)


def fin(bm, base, tip_a, tip_b, thick, mirror=False):
    """A flat fan fin: a quad from two base points to two tips, `thick` apart along its normal."""
    a, b = Vector(base[0]), Vector(base[1])
    c, d = Vector(tip_a), Vector(tip_b)
    if mirror:
        a, b, c, d = [Vector((-p.x, p.y, p.z)) for p in (a, b, c, d)]
    n = (b - a).cross(c - a).normalized() * thick / 2
    front = [bm.verts.new(p + n) for p in (a, b, d, c)]
    back = [bm.verts.new(p - n) for p in (a, b, d, c)]
    bm.faces.new(front)
    bm.faces.new(list(reversed(back)))
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((front[j], front[i], back[i], back[j]))


def parts():
    out = [
        ('hood', 'head', TEAL, lambda bm: lm.tilted(bm, HOOD, (0, -1, 0), ROUND12, True, False)),
        ('lip', 'head', LIP, lambda bm: lm.tilted(bm, LIP_RINGS, (0, -1, 0), ROUND12, False, False)),
        ('dorsal', 'head', FIN, lambda bm: fin(bm, ((0, .10, 1.96), (0, -.06, 1.975)), (0, .02, 2.10), (0, -.04, 2.07), .02)),
        ('suit_top', 'chest', TEAL, lambda bm: lm.stack(bm, SUIT_TOP, lm.OCT)),
        ('suit_low', 'hips', TEAL, lambda bm: lm.stack(bm, SUIT_LOW, lm.OCT)),
        ('tail', 'hips', FIN, lambda bm: fin(bm, ((0, .15, 1.0), (0, .15, .93)), (0, .29, 1.06), (0, .29, .88), .025)),
    ]
    for s, k in (('l', 1), ('r', -1)):
        S, E, W = _j('shoulder', s), _j('elbow', s), _j('wrist', s)
        H, K, A = _j('hip', s), _j('knee', s), _j('ankle', s)
        out += [
            ('eye_' + s, 'head', EYE, lambda bm, k=k: lm.ball(bm, (k * .11, -.12, 1.93), .065, 8)),
            ('pupil_' + s, 'head', PUPIL, lambda bm, k=k: lm.ball(bm, (k * .11, -.185, 1.935), .025, 6)),
            ('side_fin_' + s, 'head', FIN, lambda bm, m=(s == 'r'): fin(
                bm, ((.205, .03, 1.76), (.205, .03, 1.62)), (.34, .07, 1.80), (.33, .07, 1.57), .02, m)),
            ('upper_arm_' + s, 'upper_arm_' + s, TEAL, lambda bm, S=S, E=E: lm.tilted(
                bm, [(*_along(S, E, -.12), .09, .09), (*_along(S, E, .1), .105, .10),
                     (*_along(S, E, 1.06), .095, .092)], E - S, lm.OCT)),
            ('arm_fin_' + s, 'upper_arm_' + s, FIN, lambda bm, S=S, E=E, k=k: fin(
                bm, (_along(S, E, .3, Vector((k * .09, .03, 0))), _along(S, E, .75, Vector((k * .085, .03, 0)))),
                _along(S, E, .2, Vector((k * .21, .06, -.02))), _along(S, E, .85, Vector((k * .19, .06, -.06))), .02)),
            ('forearm_' + s, 'forearm_' + s, TEAL, lambda bm, E=E, W=W: lm.tilted(
                bm, [(*_along(E, W, -.10), .085, .083), (*_along(E, W, .08), .095, .092),
                     (*_along(E, W, .80), .098, .095)], W - E, lm.OCT)),
            ('cuff_' + s, 'forearm_' + s, TEAL, lambda bm, E=E, W=W: lm.tilted(
                bm, [(*_along(E, W, .76), .112, .108), (*_along(E, W, 1.0), .108, .104)], W - E, lm.OCT)),
            ('thigh_' + s, 'thigh_' + s, TEAL, lambda bm, H=H, K=K: lm.tilted(
                bm, [(*_along(H, K, -.12), .105, .12), (*_along(H, K, .4), .11, .118),
                     (*_along(H, K, 1.05), .098, .108)], K - H, lm.OCT)),
            ('shin_' + s, 'shin_' + s, TEAL, lambda bm, K=K, A=A: lm.tilted(
                bm, [(*_along(K, A, -.08), .10, .11), (*_along(K, A, .08), .108, .115),
                     (*_along(K, A, .55), .09, .098), (*_along(K, A, .72), .10, .108)], A - K, lm.OCT)),
            ('boot_cuff_' + s, 'shin_' + s, TEAL, lambda bm, K=K, A=A: lm.tilted(
                bm, [(*_along(K, A, .70), .118, .125), (*_along(K, A, .98), .115, .12)], A - K, lm.OCT)),
        ]
    return out


def build(collection_name='Babuin_Peixao'):
    col = bpy.data.collections.get(collection_name)
    if not col:
        col = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(col)
    total, report = 0, []
    for name, bone, colour, builder in parts():
        n = lm.part('PX_' + name, builder, colour, col)
        bpy.data.objects['PX_' + name]['bone'] = bone
        total += n
        report.append(f'{name}:{n}')
    print('TRIS', total, ' '.join(report))
    return total


def assemble(name='kaze_Peixe_Body'):
    return lx.assemble(name, 'Babuin_Peixao', 'PX_', KEPT, CARRIED_BY)
