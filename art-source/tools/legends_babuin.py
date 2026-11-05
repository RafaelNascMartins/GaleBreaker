"""Babuin (Kaze) rebuilt as Mega Man Legends style rigid parts.

Measured from concept-art/characters/babuin/babuin-turnaround-psx-1997-v3.png at
1.9 m tall: head 1.545-1.90, belt 1.17-1.245, robe hem 0.90, pant cuff 0.40.
Run in Blender: exec(open(path).read()) or import legends_babuin; legends_babuin.build().
"""
import json
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

import legends_model as lm
from legends_model import BOX, FACE, FACE6, HEX, OCT, SOLE, loft

JADE = ('jade', (0.16, 0.38, 0.27))
SAGE = ('sage', (0.74, 0.80, 0.60))
SKIN = ('skin', (0.93, 0.62, 0.38))
UP = Vector((0, 0, 1))

# Arm read facet by facet from babuin_*_facetas.png (front, profile, back), in centimetres for
# the left arm. Rings: deltoid cap (c), deltoid (d), under the deltoid (e), elbow (l); the
# outer biceps (o), inner biceps (i) and front/back crease (b) vertices only exist where the
# drawing has a corner. f/b = front/back, i/o = towards/away from the torso.
UPPER_ARM_V = {
    'c1': (15.0, 0.6, 150.1), 'c2': (21.2, 0.6, 149.7), 'c3': (21.4, 8.0, 149.4), 'c4': (15.6, 8.0, 150.1),
    'd_fi': (13.8, 0.5, 141.4), 'd_f': (20.4, -4.1, 140.0), 'd_fo': (25.9, -1.0, 143.9),
    'd_bo': (26.1, 10.0, 144.1), 'd_b': (21.4, 13.4, 140.0), 'd_bi': (13.8, 9.0, 142.6),
    'e_fi': (14.8, 1.0, 134.4), 'e_f': (21.0, -1.2, 136.6), 'e_fo': (26.7, 1.5, 138.2),
    'e_bo': (27.0, 10.5, 138.3), 'e_b': (21.8, 12.4, 136.4), 'e_bi': (15.2, 8.5, 134.0),
    'o_f': (31.0, 2.5, 131.1), 'o_b': (31.3, 11.5, 130.9), 'i_f': (18.7, 2.5, 130.1), 'i_b': (18.3, 9.0, 130.1),
    'b_f': (23.0, 1.0, 127.2), 'b_b': (24.0, 14.5, 127.0),
    'l_fi': (22.2, 2.0, 122.0), 'l_f': (28.8, -1.6, 120.0), 'l_fo': (37.0, 3.5, 126.6),
    'l_bo': (37.3, 12.5, 125.8), 'l_b': (29.6, 16.0, 120.2), 'l_bi': (22.2, 10.0, 121.8),
}
UPPER_ARM_F = [
    ('c1', 'c2', 'c3', 'c4'),
    ('c1', 'd_fi', 'd_f', 'd_fo', 'c2'), ('c2', 'd_fo', 'd_bo', 'c3'),       # deltoid front and outer
    ('c3', 'd_bo', 'd_b', 'd_bi', 'c4'), ('c4', 'd_bi', 'd_fi', 'c1'),       # deltoid back and inner
    ('d_fi', 'e_fi', 'e_f', 'd_f'), ('d_f', 'e_f', 'e_fo', 'd_fo'), ('d_fo', 'e_fo', 'e_bo', 'd_bo'),
    ('d_bo', 'e_bo', 'e_b', 'd_b'), ('d_b', 'e_b', 'e_bi', 'd_bi'), ('d_bi', 'e_bi', 'e_fi', 'd_fi'),
    ('e_fi', 'i_f', 'b_f', 'e_f'), ('e_f', 'b_f', 'l_f', 'l_fo', 'o_f', 'e_fo'), ('i_f', 'l_fi', 'l_f', 'b_f'),
    ('e_fo', 'o_f', 'o_b', 'e_bo'), ('o_f', 'l_fo', 'l_bo', 'o_b'),
    ('e_bi', 'e_b', 'b_b', 'i_b'), ('e_b', 'e_bo', 'o_b', 'l_bo', 'l_b', 'b_b'), ('i_b', 'b_b', 'l_b', 'l_bi'),
    ('e_fi', 'e_bi', 'i_b', 'i_f'), ('i_f', 'i_b', 'l_bi', 'l_fi'),
    ('l_fi', 'l_f', 'l_fo', 'l_bo', 'l_b', 'l_bi'),                           # elbow cap, under the forearm
]
ELBOW = ['l_fi', 'l_f', 'l_fo', 'l_bo', 'l_b', 'l_bi']


def _onto_plane(verts, free, plane):
    """Move vertex `free` onto the plane through the `plane` vertices (Newell normal), so the
    big biceps facet stays one flat face instead of folding into a groove at the crease."""
    pts = [Vector(verts[k]) for k in plane]
    n = Vector()
    for a, b in zip(pts, pts[1:] + pts[:1]):
        n += Vector(((a.y - b.y) * (a.z + b.z), (a.z - b.z) * (a.x + b.x), (a.x - b.x) * (a.y + b.y)))
    n.normalize()
    c = sum(pts, Vector()) / len(pts)
    v = Vector(verts[free])
    verts[free] = tuple(v - n * (v - c).dot(n))


_onto_plane(UPPER_ARM_V, 'b_f', ['e_f', 'l_f', 'l_fo', 'o_f', 'e_fo'])
_onto_plane(UPPER_ARM_V, 'b_b', ['e_b', 'e_bo', 'o_b', 'l_bo', 'l_b'])


def forearm():
    """The elbow ring shrunk 20% and tucked 1 cm into the upper arm (any more and it pokes through
    the biceps crease), and the same ring moved down the
    bracelet's axis and shrunk to sit 4 cm inside the bracelet. A ring and its scaled copy
    make flat trapezoid sides: one drawn facet each, no fold."""
    ring = [Vector(UPPER_ARM_V[k]) for k in ELBOW]
    c = sum(ring, Vector()) / 6
    top = [c + (v - c) * .8 + Vector((0, 0, 1.0)) for v in ring]
    end = (Vector(BRACELET_TOP) + Vector(BRACELET_DIR).normalized() * .04) * 100
    bottom = [end + (v - c) * .62 for v in ring]
    verts = {**{f't{i}': tuple(v) for i, v in enumerate(top)}, **{f'w{i}': tuple(v) for i, v in enumerate(bottom)}}
    faces = [(f't{i}', f'w{i}', f'w{(i + 1) % 6}', f't{(i + 1) % 6}') for i in range(6)]
    return verts, faces + [tuple(f't{i}' for i in range(6)), tuple(f'w{i}' for i in reversed(range(6)))]


# Bracelet: three stacked bands along the forearm, each narrowing at its foot so a groove shows.
BRACELET_DIR = (0.065, 0.005, -0.165)
BRACELET_TOP, BRACELET_LEN = (0.344, 0.078, 1.140), 0.177


def bracelet(bm, mirror=False):
    d = Vector(BRACELET_DIR).normalized()
    top = Vector(BRACELET_TOP)
    if mirror:
        d.x, top.x = -d.x, -top.x
    band = BRACELET_LEN / 3
    for i, (a, b) in enumerate([(.092, .101), (.095, .102), (.096, .102)]):
        c0, c1 = top + d * (band * i), top + d * (band * (i + 1) + .004)
        # Only the outer ends need caps; the inner ones sit inside the neighbouring band.
        lm.tilted(bm, [(*c0, a, b), (*c1, a - .009, b - .009)], d, HEX, i == 0, i == 2)


# Legs read from the facet polygons. Pants: one front facet (#77 front / #57 back) from the
# robe to the knee, one from the knee to the wide hem, then the cuff band. Rings are
# (z, x0, x1, y0, y1) in metres for the left leg; the knee is a capped hinge like the
# Mega Man reference instead of an extra hidden ring.
THIGH = [(0.615, .039, .232, -.122, .128, -.6), (0.88, .045, .190, -.085, .090),
         (1.0, .035, .165, -.085, .085)]  # under the robe, into the pelvis
SHIN = [(0.403, .087, .208, -.058, .089), (0.505, .084, .209, -.059, .089), (0.52, .058, .234, -.092, .128),
        (0.615, .042, .228, -.119, .124, -.6)]  # knee crease: 66 cm inside, 57 cm outside
CALF = [(0.15, .100, .205, -.045, .070), (0.44, .095, .197, -.045, .072)]
# Foot, centimetres: heel 12 cm wide, toes flare out to 31 cm; the toe grooves are painted.
FOOT_V = {
    'h_bi': (9.5, 10.8, 0.0), 'h_bo': (21.6, 10.8, 0.0), 'h_ti': (10.0, 10.5, 8.5), 'h_to': (21.0, 10.5, 8.5),
    's_oi': (6.5, -23.7, 0.0), 's_oo': (31.0, -23.7, 0.0), 's_bo': (31.0, -6.0, 0.0), 's_bi': (6.8, -6.0, 0.0),
    'i_i': (11.0, -13.0, 12.8), 'i_o': (25.0, -12.0, 12.0),     # instep line (front z 12.4-14, profile -13, 11.1)
    'o_i': (7.0, -22.0, 7.8), 'o_o': (31.0, -22.0, 7.8),        # top edge of the toes
    't1': (10.5, -4.5, 17.0), 't2': (20.0, -4.5, 17.0), 't3': (20.0, 7.0, 17.0), 't4': (10.5, 7.0, 17.0),
}
FOOT_F = [
    ('h_bi', 'h_bo', 's_bo', 's_oo', 's_oi', 's_bi'),                                   # sole
    ('h_bi', 'h_ti', 'h_to', 'h_bo'), ('h_ti', 't4', 't3', 'h_to'),                     # heel, back of the ankle
    ('h_bo', 'h_to', 't3', 't2', 'i_o', 'o_o', 's_oo', 's_bo'),                         # outer side
    ('h_bi', 's_bi', 's_oi', 'o_i', 'i_i', 't1', 't4', 'h_ti'),                         # inner side
    ('t1', 'i_i', 'i_o', 't2'), ('i_i', 'o_i', 'o_o', 'i_o'), ('o_i', 's_oi', 's_oo', 'o_o'),  # ankle, top, toes
    ('t1', 't2', 't3', 't4'),                                                           # hidden in the calf
]


# Fist, centimetres: wrist (hidden in the bracelet), the knuckle line where the back of the
# hand meets the fingers (front 91-96, profile 88-89), the finger row and the flat bottom.
# The thumb and finger grooves are painted, as on the drawing's faces.
HAND_RINGS = [
    [(34.0, -0.5, 98.5), (47.0, 0.5, 101.0), (47.0, 13.5, 101.0), (34.0, 12.5, 98.5)],
    [(30.3, -2.5, 92.6), (50.9, -1.0, 96.0), (50.9, 16.0, 96.0), (30.3, 15.5, 92.6)],
    [(31.7, -1.4, 87.0), (49.6, -0.8, 87.5), (49.6, 16.0, 87.5), (31.7, 15.5, 87.0)],
    [(36.8, -0.6, 80.8), (45.9, -0.6, 81.2), (45.9, 14.8, 81.2), (36.8, 14.5, 80.8)],
]
HAND_V = {f'{r}{c}': v for r, ring in enumerate(HAND_RINGS) for c, v in enumerate(ring)}
HAND_F = [(f'{r}{c}', f'{r + 1}{c}', f'{r + 1}{(c + 1) % 4}', f'{r}{(c + 1) % 4}') for r in range(3) for c in range(4)] +          [('00', '03', '02', '01'), ('30', '31', '32', '33')]


# Torso, belt and head from the facet corners (metres). Robe: waist, chest (widest in
# profile at 1.39), the shoulder line where the straps meet the deltoid caps, and the collar.
CHEST = [(1.26, -.119, .119, -.13, .13), (1.35, -.15, .15, -.152, .132),
         (1.51, -.154, .154, -.07, .115), (1.555, -.072, .072, -.02, .086)]
BELT = [(1.175, -.125, .125, -.155, .165), (1.262, -.12, .12, -.135, .135)]
# Head, centimetres, from the facet corners of all three views. Each ring lists the right half
# (front, side-front, side-back, back) and is mirrored. The back corners sit lower than the
# sides, as the drawing's back facets do; the side-front corners follow the temple line
# that separates the lit face from the shaded side in profile: the crown facet ends at 176, the nape facet at 161.
HEAD_RINGS = [
    [(5.5, -8.4, 189.5), (7.0, -3.0, 189.5), (7.0, 3.0, 189.5), (5.5, 5.8, 189.5)],          # flat crown
    [(12.0, -16.3, 181.6), (14.6, -7.0, 182.0), (14.4, 5.0, 181.6), (8.0, 13.8, 176.0)],      # forehead
    [(13.0, -18.1, 172.5), (15.2, -6.0, 172.0), (15.2, 7.0, 172.0), (8.2, 15.5, 166.0)],      # brow, widest; the
    # front facet spans the eyes' outer corners (13 cm), so the expression never wraps a corner
    # The jaw runs straight from the brow ring to the chin (front 15 -> 10 -> 6 cm); the chin
    # facet underneath is the bottom cap.
    [(4.5, -16.5, 155.5), (10.0, -6.0, 157.5), (8.5, 2.0, 158.0), (5.0, 7.0, 158.5)],
]

def head_mesh():
    verts, loops = {}, []
    for r, ring in enumerate(HEAD_RINGS):
        f, sf, sb, b = ring
        pts = [(-f[0],) + f[1:], f, sf, sb, b, (-b[0],) + b[1:], (-sb[0],) + sb[1:], (-sf[0],) + sf[1:]]
        loops.append([f'{r}_{i}' for i in range(8)])
        verts.update(zip(loops[-1], pts))
    faces = [(r0[i], r1[i], r1[(i + 1) % 8], r0[(i + 1) % 8]) for r0, r1 in zip(loops, loops[1:]) for i in range(8)]
    return verts, faces + [tuple(reversed(loops[0])), tuple(loops[-1])]


# Skirt, centimetres: under the belt down to a hem that dips at the front and back centre
# (83-84) and rises at the hips (93-97), as the drawing's flap facets show.
SKIRT_TOP = [(0, -15.5), (8.5, -15.0), (12.0, 0), (8.5, 15.5), (0, 16.0), (-8.5, 15.5), (-12.0, 0), (-8.5, -15.0)]
SKIRT_HEM = [(0, -20.0, 83.5), (13.4, -17.5, 88.5), (21.6, 0, 95.0), (13.0, 18.0, 88.5), (0, 19.0, 84.0),
             (-13.0, 18.0, 88.5), (-21.6, 0, 95.0), (-13.4, -17.5, 88.5)]
SKIRT_V = {**{f't{i}': (x, y, 119.5) for i, (x, y) in enumerate(SKIRT_TOP)}, **{f'h{i}': v for i, v in enumerate(SKIRT_HEM)}}
SKIRT_F = [(f't{i}', f'h{i}', f'h{(i + 1) % 8}', f't{(i + 1) % 8}') for i in range(8)] +           [tuple(f't{i}' for i in reversed(range(8))), tuple(f'h{i}' for i in range(8))]


SLICES = Path(__file__).resolve().parents[2] / 'art-source/characters/kaze/legends/babuin_slices.json'


def parts():
    """(part name, bone, colour, builder) for every rigid piece.

    Shapes come from concept_slices.py: horizontal rings measured on the turnaround every
    centimetre and kept where the outline turns. Each piece is closed and tucks into its
    parent with an extra hidden ring, so a bent joint never shows a hollow.
    """
    d = {k: [tuple(r) for r in v] for k, v in json.loads(SLICES.read_text()).items()}
    tuck = lm.ring_scaled
    head, chest, belt, skirt = d['head'], d['chest'], d['belt'], d['skirt']
    # The robe straps slope from the collar (x 7.2, z 155) to the deltoid cap (x 15.4, z 151),
    # where the drawing joins torso and shoulder: end the chest on that line, not flat.
    chest = [r for r in chest if r[0] < 1.515] + [(1.553, -0.075, 0.075, -0.05, 0.09)]
    ear = d['ear']
    ear_rings = [(ear[0][0], .11, max(x for _, x in ear) - .005, .03, .078),
                 (ear[-1][0], .11, max(x for _, x in ear), .028, .08)]
    arm, fore, wrap, fist = d['upper_arm'], d['forearm'], d['wrap'], d['fist']
    thigh, shin, calf, foot = d['thigh'], d['shin'], d['calf'], d['foot']
    def tucked(rings, end, dz, k):
        """Move the end ring (0 first, -1 last) dz into the neighbouring part, shrunk by k."""
        rings = list(rings)
        rings[end] = tuck(rings[end], rings[end][0] + dz, k)
        return rings

    side = {
        'thigh': THIGH,
        'shin': SHIN,
        'calf': CALF,
    }
    out = [
        ('head', 'head', SKIN, lambda bm: lm.poly(bm, *head_mesh())),
        ('neck', 'neck', SKIN, lambda bm: loft(bm, (0, 0.02, 1.47), (0, 0.02, 1.585), [(0, .052, .052), (1, .05, .05)], HEX, False, False)),  # both ends sit inside head and chest
        ('chest', 'chest', JADE, lambda bm: lm.stack(bm, CHEST, FACE6)),
        ('belt', 'hips', JADE, lambda bm: lm.stack(bm, BELT, FACE6)),
        # Pants seat under the robe: the thighs tuck into it, so no gap shows when the robe swings.
        ('pelvis', 'hips', JADE, lambda bm: lm.stack(bm, [(0.92, -.17, .17, -.11, .11), (1.19, -.12, .12, -.13, .14)], FACE6)),
        ('orbs', 'hips', SAGE, lambda bm: [lm.ball(bm, (x, -0.155, 1.207), .036) for x in (-0.06, 0.06)]),
        ('skirt', 'hips', JADE, lambda bm: lm.poly(bm, SKIRT_V, SKIRT_F)),
        ('sash', 'sash', SAGE, lambda bm: loft(bm, (0.07, -0.155, 1.18), (0.10, -0.19, 0.92), [(0, .045, .008), (1, .05, .008)], BOX)),
    ]
    bones = {'ear': 'head', 'wrap': 'forearm', 'calf': 'shin'}
    colours = {'wrap': JADE, 'thigh': JADE, 'shin': JADE}
    # The drawn pants show one facet per segment from the front and from the side: a square
    # section, not a hexagon.
    shapes = {'ear': BOX, 'thigh': BOX, 'shin': BOX, 'calf': BOX}
    for s, mirror in (('l', False), ('r', True)):
        fv, ff = forearm()
        out += [
            ('upper_arm_' + s, 'upper_arm_' + s, SKIN, lambda bm, m=mirror: lm.poly(bm, UPPER_ARM_V, UPPER_ARM_F, m)),
            ('forearm_' + s, 'forearm_' + s, SKIN, lambda bm, m=mirror, v=fv, f=ff: lm.poly(bm, v, f, m)),
            ('wrap_' + s, 'forearm_' + s, JADE, lambda bm, m=mirror: bracelet(bm, m)),
            ('foot_' + s, 'foot_' + s, SKIN, lambda bm, m=mirror: lm.poly(bm, FOOT_V, FOOT_F, m)),
            ('hand_' + s, 'hand_' + s, SKIN, lambda bm, m=mirror: lm.poly(bm, HAND_V, HAND_F, m)),
            # Ear: a faceted disc standing off the side of the head, like the drawing's C shape.
            ('ear_' + s, 'head', SKIN, lambda bm, k=-1 if mirror else 1: lm.tilted(
                bm, [(k * .125, .045, 1.665, .056, .042), (k * .178, .045, 1.665, .045, .032)], (k, 0, 0), HEX)),
        ]
        for name, rings in side.items():
            rings = [lm.mirror_ring(r) for r in rings] if mirror else rings
            bone = bones.get(name, name) + ('_' + s if name != 'ear' else '')
            out.append((name + '_' + s, bone, colours.get(name, SKIN),
                        lambda bm, rings=rings, shape=shapes.get(name, HEX): lm.stack(bm, rings, shape)))
    return out


def build(collection_name='Babuin_Legends'):
    col = bpy.data.collections.get(collection_name)
    if not col:
        col = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(col)
    total = 0
    report = []
    for name, bone, colour, builder in parts():
        n = lm.part('BL_' + name, builder, colour, col)
        bpy.data.objects['BL_' + name]['bone'] = bone
        total += n
        report.append(f'{name}:{n}')
    print('TRIS', total, ' '.join(report))
    return total


# Joints for model_rig.fit_skeleton, in metres (left side; the right mirrors). Read off the
# parts: the deltoid centre, the elbow ring, the bracelet foot, the fist, the hip under the
# robe, the knee crease, the ankle inside the calf and the toe tip.
JOINTS = {
    'pelvis': (0, 0, 1.0), 'abdomen': (0, 0, 1.17), 'chest_top': (0, 0.01, 1.45), 'neck_base': (0, 0.02, 1.53),
    'neck_head': (0, 0.02, 1.575), 'head_top': (0, 0, 1.895),
    'shoulder': (0.19, 0.05, 1.455), 'elbow': (0.296, 0.074, 1.227), 'wrist': (0.409, 0.083, 0.975),
    'hand_tip': (0.414, 0.07, 0.81), 'hip': (0.10, 0.0, 0.98), 'knee': (0.135, 0.0, 0.615),
    'ankle': (0.15, 0.01, 0.13), 'toe': (0.19, -0.22, 0.03),
}


def joints():
    j = {}
    for k, v in JOINTS.items():
        if k in ('pelvis', 'abdomen', 'chest_top', 'neck_base', 'neck_head', 'head_top'):
            j[k] = Vector(v)
        else:
            j[k + '_l'] = Vector(v)
            j[k + '_r'] = Vector((-v[0], v[1], v[2]))
    return j


def assemble(name='kaze_Body', collection_name='Babuin_Legends'):
    """Join copies of the parts into one mesh. Every vertex follows exactly one bone (rigid
    parts, no blended weights), and the mesh gets one UV map packed for a single page."""
    import math
    col = bpy.data.collections[collection_name]
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    copies = []
    names = []
    for o in [o for o in col.objects if o.name.startswith('BL_')]:
        c = o.copy()
        c.data = o.data.copy()
        col.objects.link(c)
        # Remember the source part on every face, for the texture painter.
        names.append(o.name[3:])
        attr = c.data.attributes.new('part', 'INT', 'FACE')
        attr.data.foreach_set('value', [len(names) - 1] * len(c.data.polygons))
        g = c.vertex_groups.new(name=o['bone'])
        g.add(list(range(len(c.data.vertices))), 1.0, 'REPLACE')
        c.data.uv_layers.new(name='UVMap')
        copies.append(c)
    bpy.ops.object.mode_set(mode='OBJECT') if bpy.context.object and bpy.context.object.mode != 'OBJECT' else None
    bpy.ops.object.select_all(action='DESELECT')
    for c in copies:
        c.select_set(True)
    bpy.context.view_layer.objects.active = copies[0]
    bpy.ops.object.join()
    body = bpy.context.view_layer.objects.active
    body.name = body.data.name = name
    body['parts'] = names
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(50), island_margin=0.012, area_weight=0.0, scale_to_bounds=False)
    bpy.ops.uv.pack_islands(margin=0.008, rotate=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    face_uv(body)
    for o in col.objects:
        if o.name.startswith('BL_'):
            o.hide_set(True)
    return body


# Expression decal: the front of the head inside this square (metres) shows one cell of the
# expression sheet through a second UV map, as in Mega Man Legends; the page keeps plain skin
# there. The square runs from the chin to just above the brows, like the sheet's cells.
FACE_BOX = {'x': (-0.118, 0.118), 'z': (1.565, 1.801), 'min_front': 0.05}  # raised 3 cell px


def in_face(points, n):
    """A head polygon takes the decal when it faces forward at all and overlaps the square: the angled cheek facets carry the outer corners of the eyes. Its UVs may run past
    the square; the decal clamps to the cell border, which is transparent skin."""
    x0, x1 = FACE_BOX['x']
    z0, z1 = FACE_BOX['z']
    xs, zs = [p[0] for p in points], [p[2] for p in points]
    overlaps = min(xs) < x1 and max(xs) > x0 and min(zs) < z1 and max(zs) > z0
    return -n[1] > FACE_BOX['min_front'] and overlaps


def face_uv(body):
    """FaceUV: the face square for front-facing head faces, (-1, -1) everywhere else (the
    toon shader only draws the expression where UV2.x >= 0)."""
    me = body.data
    layer = me.uv_layers.get('FaceUV') or me.uv_layers.new(name='FaceUV')
    head = list(body['parts']).index('head')
    part = me.attributes['part'].data
    (x0, x1), (z0, z1) = FACE_BOX['x'], FACE_BOX['z']
    for poly in me.polygons:
        pts = [me.vertices[v].co for v in poly.vertices]
        on = part[poly.index].value == head and in_face(pts, poly.normal)
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            layer.data[li].uv = ((co.x - x0) / (x1 - x0), (co.z - z0) / (z1 - z0)) if on else (-1.0, -1.0)
    me.uv_layers.active = me.uv_layers['UVMap']


def dump_triangles(body, path):
    """UV, position and normal of every triangle, for legends_texture.py to paint the page
    by projecting the turnaround onto the model."""
    me = body.data
    me.calc_loop_triangles()
    uv = me.uv_layers.active.data
    part = me.attributes['part'].data
    names = list(body['parts'])
    tris = []
    for t in me.loop_triangles:
        poly = me.polygons[t.polygon_index]
        name = names[part[t.polygon_index].value]
        tris.append({'part': name, 'uv': [list(uv[l].uv) for l in t.loops],
                     'co': [list(me.vertices[v].co) for v in t.vertices],
                     'n': list(t.normal), 'face': name == 'head' and in_face([me.vertices[v].co for v in poly.vertices], poly.normal)})
    Path(path).write_text(json.dumps(tris))
    return len(tris)


def skirt_weights(body):
    """The robe skirt hangs from the hips at the waist; its front, back and side hem corners
    follow the robe_front / robe_back / robe_side cloth bones, so a kick lifts the flap instead
    of passing through it. Still one bone per vertex."""
    me = body.data
    skirt = list(body['parts']).index('skirt')
    part = me.attributes['part'].data
    verts = {v for p in me.polygons if part[p.index].value == skirt for v in p.vertices}
    groups = {n: body.vertex_groups.get(n) or body.vertex_groups.new(name=n)
              for n in ('hips', 'robe_front', 'robe_back', 'robe_side_l', 'robe_side_r')}
    for i in verts:
        co = me.vertices[i].co
        target = 'hips'
        if co.z < 1.10:
            if abs(co.y) > 0.05:
                target = 'robe_front' if co.y < 0 else 'robe_back'
            else:   # the hem corners at the hips swing with the side panels
                target = 'robe_side_l' if co.x > 0 else 'robe_side_r'
        for g in groups.values():
            g.remove([i])
        groups[target].add([i], 1.0, 'REPLACE')
    return len(verts)



# Bones of the shared humanoid builder that Babuin does not use: Volt's cannon, Ignis's hat,
# finger bones (fists are rigid; an open hand is a swapped piece) and the old model's loose
# bracelet tails and the sash tail (the concept's back has none). The game skips a missing
# socket bone (fighter_view._update_sockets).
UNUSED_BONES = ['cannon', 'hat', 'wrap_tail_l', 'wrap_tail_r', 'sash_tail'] + \
    [f'finger_{d}_{s}' for d in ('index', 'middle', 'ring', 'pinky', 'thumb') for s in 'lr']


def prune_rig(arm):
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')
    for name in UNUSED_BONES:
        eb = arm.data.edit_bones.get(name)
        if eb:
            arm.data.edit_bones.remove(eb)
    bpy.ops.object.mode_set(mode='OBJECT')
    return len(arm.data.bones)


# Open hand (babuin-mao-aberta-v1.png, traced in legends/mao/): swapped in for the fist on
# palm strikes, like Mega Man's arm pieces. Hand-local centimetres at the reference scale
# (0.45 mm/px): h along the hand from the wrist, u across the back of the hand (+u away from
# the thumb), d through it (-d = palm). Rings: wrist (hidden in the bracelet), heel facets,
# widest palm, finger base, fingertip chamfer, tip. OPEN_HAND_SCALE fits it to the fist.
OPEN_HAND_RINGS = [   # (h, extent towards the thumb, extent away from it, palm depth, back depth)
    (0.3, 4.5, 6.7, 2.85, 2.85), (4.7, 4.6, 6.7, 2.9, 2.8), (7.2, 7.3, 8.5, 3.5, 3.3),
    (10.8, 7.4, 11.0, 3.9, 3.9), (18.9, 7.4, 11.0, 3.9, 3.9), (21.6, 7.4, 10.0, 3.1, 3.9),
    (24.0, 7.4, 9.2, 2.0, 3.0), (33.9, 7.4, 9.2, 2.0, 2.6), (36.2, 5.3, 7.1, 1.9, 2.6),
]
# Thumb block on the palm side: the back view's outline runs to -10.9 there, the hand's own
# edge is at -7.4 (it overlaps 0.4 cm into the palm block).
OPEN_THUMB = [(13.9, -10.9, -7.0, -3.9, 0.2), (21.6, -10.9, -7.0, -3.6, -0.2), (24.0, -9.3, -7.0, -3.0, -0.6)]
OPEN_HAND_SCALE = 0.85


def open_hand_local():
    """Vertices (h, u, d) and faces of the open hand: one lofted block with a square section
    and a separate thumb block on the palm side."""
    verts, faces, loops = {}, [], []
    for r, (h, ul, ur, dp, db) in enumerate(OPEN_HAND_RINGS):
        names = [f'h{r}_{c}' for c in range(4)]
        for n, uv in zip(names, [(-ul, -dp), (ur, -dp), (ur, db), (-ul, db)]):
            verts[n] = (h, *uv)
        loops.append(names)
    for a, b in zip(loops, loops[1:]):
        faces += [(a[i], b[i], b[(i + 1) % 4], a[(i + 1) % 4]) for i in range(4)]
    faces += [tuple(reversed(loops[0])), tuple(loops[-1])]
    tl = []
    for r, (h, u0, u1, d0, d1) in enumerate(OPEN_THUMB):
        names = [f't{r}_{c}' for c in range(4)]
        for n, uv in zip(names, [(u0, d0), (u1, d0), (u1, d1), (u0, d1)]):
            verts[n] = (h, *uv)
        tl.append(names)
    for a, b in zip(tl, tl[1:]):
        faces += [(a[i], b[i], b[(i + 1) % 4], a[(i + 1) % 4]) for i in range(4)]
    faces += [tuple(reversed(tl[0])), tuple(tl[-1])]
    return verts, faces


def open_hand_world(side, wrist, axis, out):
    """Hand-local (h, u, d) -> A-pose world: h runs down the hand axis from 4 cm inside the
    bracelet, the back of the hand faces +y, the thumb points away from the body."""
    sx = 1 if side == 'l' else -1
    axis = Vector(axis).normalized()
    across = Vector((-sx, 0, 0))                  # +u: away from the thumb, towards the body
    across = (across - axis * across.dot(axis)).normalized()
    depth = axis.cross(across)
    if depth.y < 0:
        depth = -depth                            # +d: back of the hand (+y)
    base = Vector(wrist) - axis * 0.04
    k = OPEN_HAND_SCALE / 100
    verts, faces = open_hand_local()
    return {n: tuple(base + axis * (h * k) + across * (u * k) + depth * (d * k)) for n, (h, u, d) in verts.items()}, faces


def add_open_hands(arm, body, apose):
    """Build both open hands as separate objects (shown instead of the fist on palm strikes),
    carried from the A-pose to the rest pose by each fist's rigid motion, parented to the
    hand bone with the origin at the wrist. Each face borrows the UVs of the fist face pointing the same way, fitted to
    that face's UV box, so the hand reads as the same painted skin without touching the page."""
    import bmesh
    from mathutils import Matrix

    def frame_of(me, idx):
        a, b, c = (me.vertices[i].co for i in idx)
        x = (b - a).normalized()
        z = x.cross(c - a).normalized()
        m = Matrix((x, z.cross(x), z)).transposed().to_4x4()
        m.translation = a
        return m

    meta = json.loads((Path(__file__).resolve().parents[2] / 'art-source/characters/kaze/legends/babuin_mao_pagina.json').read_text())
    made = []
    for s, sx in (('l', 1), ('r', -1)):
        name = f'kaze_HandOpen_{s}'
        old = bpy.data.objects.get(name)
        if old:
            save_hand_pose(old)
            bpy.data.objects.remove(old, do_unlink=True)
        g = body.vertex_groups['hand_' + s].index
        idx = [v.index for v in body.data.vertices if any(x.group == g for x in v.groups)]
        tri = [idx[0], idx[len(idx) // 3], idx[2 * len(idx) // 3]]
        T = frame_of(body.data, tri) @ frame_of(apose.data, tri).inverted()
        w = Vector((sx * JOINTS['wrist'][0], JOINTS['wrist'][1], JOINTS['wrist'][2]))
        f = Vector((sx * JOINTS['hand_tip'][0], JOINTS['hand_tip'][1], JOINTS['hand_tip'][2]))
        verts, faces = open_hand_world(s, w, f - w, None)
        me = bpy.data.meshes.new(name)
        bm = bmesh.new()
        bv = {k: bm.verts.new(T @ Vector(v)) for k, v in verts.items()}
        for fc in faces:
            bm.faces.new([bv[k] for k in fc])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bmesh.ops.planar_faces(bm, faces=bm.faces, iterations=200, factor=0.5)
        # UVs: the hand's own page (legends_texture.hand_page) holds the three reference views
        # side by side; each face takes the view it faces, at the reference's own coordinates.
        uvl = bm.loops.layers.uv.new('UVMap')
        fuv = bm.loops.layers.uv.new('FaceUV')
        local, _ = open_hand_local()
        name_of = {bv[k]: k for k in bv}
        sx_, sy_ = meta['size']
        for face in bm.faces:
            pts = [Vector(local[name_of[v]]) for v in face.verts]   # (h, u, d)
            n = Vector()
            for a_, b_ in zip(pts, pts[1:] + pts[:1]):
                n += a_.cross(b_)
            if abs(n.z) >= max(abs(n.y), abs(n.x)):
                view, horiz = ('costas', 1) if n.z > 0 else ('palma', -1)
                hx = [p.y * horiz for p in pts]
            else:
                view, hx = 'perfil', [p.z for p in pts]
            v = meta['views'][view]
            for loop, p, x in zip(face.loops, pts, hx):
                px = v['x'] + (v['crop_w'] / 2 + x / meta['cm_per_px']) * meta['scale']
                py = (meta['crop_h'] - 12 - p.x / meta['cm_per_px']) * meta['scale']
                loop[uvl].uv = (px / sx_, 1 - py / sy_)
                loop[fuv].uv = (-1.0, -1.0)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
        # Rigid piece on the hand bone with its origin at the wrist, so it turns about the
        # wrist (pose the hand bone, or rotate the object itself) and rides the forearm.
        rest = arm.matrix_world @ arm.data.bones['hand_' + s].matrix_local
        me.transform(rest.inverted())
        ob = bpy.data.objects.new(name, me)
        body.users_collection[0].objects.link(ob)
        ob.parent, ob.parent_type, ob.parent_bone = arm, 'BONE', 'hand_' + s
        ob.matrix_world = rest
        poses = json.loads(HAND_POSE.read_text()) if HAND_POSE.exists() else {}
        if name in poses:
            # The hand as placed by hand in Blender, relative to its bone.
            from mathutils import Matrix
            ob.matrix_basis = Matrix(poses[name])
        me.materials.append(hand_material())
        made.append((name, len(me.polygons)))
    return made


HAND_POSE = Path(__file__).resolve().parents[2] / 'art-source/characters/kaze/legends/babuin_mao_pose.json'


def save_hand_pose(ob):
    """Keep an open hand's placement (adjusted by hand in Blender) for the next rebuild."""
    poses = json.loads(HAND_POSE.read_text()) if HAND_POSE.exists() else {}
    poses[ob.name] = [list(row) for row in ob.matrix_basis]
    HAND_POSE.write_text(json.dumps(poses, indent=1))


def hand_material():
    """Flat (emission) preview material with the open hand's page, nearest filtering."""
    path = Path(__file__).resolve().parents[2] / 'art-source/characters/kaze/legends/babuin_mao_pagina.png'
    img = bpy.data.images.load(str(path), check_existing=True)
    img.reload()
    m = bpy.data.materials.get('babuin_mao') or bpy.data.materials.new('babuin_mao')
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    t = nt.nodes.new('ShaderNodeTexImage')
    t.image, t.interpolation = img, 'Closest'
    e = nt.nodes.new('ShaderNodeEmission')
    o = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(t.outputs[0], e.inputs[0])
    nt.links.new(e.outputs[0], o.inputs[0])
    return m


# ---------------------------------------------------------------------------------------------
# Godot export. The live scene keeps its preview materials (face mix, emission) and the fist
# masks; the export works on copies: fists split into kaze_Fist_l/r so Godot can swap them with
# kaze_HandOpen_l/r per clip, and plain Principled materials so glTF embeds the right page.
GODOT_GLB = Path(__file__).resolve().parents[2] / 'godot/assets/characters/kaze/kaze.glb'
# Exported outfit body -> scene object (legends_executivo.assemble). In Godot the outfit's
# palette entry names the exported body ("body") and its page.
OUTFIT_BODIES = {'kaze_ExecBody': 'kaze_Exec_Body', 'kaze_PeixeBody': 'kaze_Peixe_Body'}


def _export_material(name, image):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out, bsdf = nt.nodes.new('ShaderNodeOutputMaterial'), nt.nodes.new('ShaderNodeBsdfPrincipled')
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image, tex.interpolation = image, 'Closest'
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    nt.links.new(bsdf.outputs[0], out.inputs['Surface'])
    return m


def export_godot(path=GODOT_GLB):
    """Export rig, body (fists split off), fists and open hands with every NLA clip at 60 fps."""
    bpy.context.scene.render.fps = 60
    body, rig = bpy.data.objects['kaze_Body'], bpy.data.objects['kaze_Rig']
    page = _export_material('kaze_page', bpy.data.images['babuin_pagina_256.png'])
    hand_img = next(n.image for n in bpy.data.materials['babuin_mao'].node_tree.nodes if n.type == 'TEX_IMAGE')
    hand = _export_material('kaze_hand', hand_img)
    parts = list(body['parts'])
    made = []

    def copy(name, keep, source=None):
        src = source or body
        ob = src.copy()
        ob.data = src.data.copy()
        ob.name = ob.data.name = name
        for m in [m for m in ob.modifiers if m.type == 'MASK']:
            ob.modifiers.remove(m)
        bpy.context.scene.collection.objects.link(ob)
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        layer = bm.faces.layers.int['part']
        names = list(src['parts'])
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if not keep(names[f[layer]])], context='FACES')
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
        bm.to_mesh(ob.data)
        bm.free()
        ob.data.materials.clear()
        ob.data.materials.append(page)
        made.append(ob)
        return ob

    copy('kaze_BodyExport', lambda p: p not in ('hand_l', 'hand_r'))
    copy('kaze_Fist_l', lambda p: p == 'hand_l')
    copy('kaze_Fist_r', lambda p: p == 'hand_r')
    # Outfits with their own pieces: their body without the fists (the fists are shared).
    for outfit, source in OUTFIT_BODIES.items():
        if source in bpy.data.objects:
            copy(outfit, lambda p: p not in ('hand_l', 'hand_r'), bpy.data.objects[source])
    opens = [bpy.data.objects['kaze_HandOpen_' + s] for s in 'lr']
    for o in opens:     # hidden objects are skipped by the selection export
        o.hide_set(False)
    for o in opens:
        save_hand_pose(o)
    saved = [o.material_slots[0].material for o in opens]
    for o in opens:
        o.material_slots[0].material = hand
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in [rig] + made + opens:
        o.select_set(True)
    try:
        bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', use_selection=True, export_yup=True,
                                  export_apply=False, export_animations=True, export_animation_mode='NLA_TRACKS',
                                  export_skins=True, export_materials='EXPORT')
    finally:
        for o, m in zip(opens, saved):
            o.material_slots[0].material = m
        for ob in made:
            me = ob.data
            bpy.data.objects.remove(ob)
            bpy.data.meshes.remove(me)
