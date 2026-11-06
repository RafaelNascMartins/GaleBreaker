"""Dale (ex-Ignis) as Mega Man Legends style rigid parts, base outfit (shirtless, jeans, hat).

Measured from concept-art/characters/dale/dale-turnaround-psx-v1.png, crops in
art-source/characters/ignis/legends/dale_{frente,perfil,costas}.png traced by concept_facets.py
at 2.05 m to the top of the skull (MPP = 2.05 / 933 px; the hat reaches 2.15 m). Heavy brawler
build, taller than Babuin (1.90). Overlay pixel (X, Y) -> x = (X/2 - 330) * MPP,
z = (1002 - Y/2) * MPP; profile X gives y (front is -y).
Run in Blender: import legends_dale; legends_dale.build(); legends_dale.assemble().
"""
import json
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

import legends_model as lm
from legends_model import BOX, FACE6, HEX, OCT, loft

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'art-source/characters/ignis/legends'
MPP = 2.05 / 933
COLLECTION = 'Dale_Legends'

SKIN = ('d_skin', (0.93, 0.42, 0.33))
PALE = ('d_pale', (0.98, 0.84, 0.70))
DENIM = ('d_denim', (0.25, 0.33, 0.50))
LEATHER = ('d_leather', (0.42, 0.25, 0.14))
BOOT = ('d_boot', (0.62, 0.36, 0.20))
HAT = ('d_hat', (0.52, 0.31, 0.17))
GOLD = ('d_gold', (0.90, 0.66, 0.18))

# Joints (left side, metres), read off the front and profile facets: deltoid centre, the
# elbow crease (front Y 800), the wrist under the fist (Y 1030), the hip under the belt, the
# knee patch centre (Y 1360), the ankle inside the boot shaft.
JOINTS = {
    'pelvis': (0, 0.02, 1.0), 'abdomen': (0, 0.02, 1.19), 'chest_top': (0, 0.04, 1.62),
    'neck_base': (0, 0.03, 1.70), 'neck_head': (0, 0.02, 1.76), 'head_top': (0, 0.04, 2.05),
    'shoulder': (0.30, 0.08, 1.60), 'elbow': (0.45, 0.10, 1.29), 'wrist': (0.53, 0.03, 1.0),
    'hand_tip': (0.54, -0.01, 0.82), 'hip': (0.13, 0.01, 0.98), 'knee': (0.18, 0.04, 0.70),
    'ankle': (0.24, 0.06, 0.13), 'toe': (0.25, -0.24, 0.03),
}


def J(name):
    return Vector(JOINTS[name])


# Torso rings (z, x0, x1, y0, y1): waist above the belt, belly, chest (widest, pecs at the
# front), upper chest under the traps, and the trap line meeting the neck.
CHEST = [(1.18, -.212, .212, -.150, .185), (1.27, -.215, .215, -.152, .19),
         (1.43, -.245, .245, -.20, .27), (1.58, -.235, .235, -.12, .25),
         (1.70, -.15, .15, -.03, .17)]
BELT = [(1.115, -.218, .218, -.158, .192), (1.195, -.218, .218, -.158, .192)]
HIPS = [(0.90, -.20, .20, -.13, .16), (1.12, -.215, .215, -.15, .185)]
BUCKLE = [(1.125, -.07, .07, -.178, -.15), (1.19, -.07, .07, -.178, -.15)]

# Head, centimetres: (front, side-front, side-back, back) of the right half, mirrored.
# Beard bottom (chin) 172, jaw 177, brow 189, forehead 197, crown 205.
HEAD_RINGS = [
    [(6.0, -5.0, 205.0), (9.0, 0.0, 205.0), (9.0, 10.0, 205.0), (6.0, 15.0, 204.0)],
    [(10.5, -10.5, 197.0), (12.5, -3.0, 197.5), (12.5, 12.0, 197.0), (8.0, 19.5, 194.0)],
    [(11.5, -12.0, 189.0), (12.8, -3.0, 189.0), (12.8, 12.5, 189.0), (8.5, 20.0, 186.0)],
    [(10.5, -13.0, 178.0), (12.0, -3.5, 178.5), (11.0, 9.0, 180.0), (6.0, 14.0, 180.0)],
    [(5.0, -13.0, 171.5), (8.5, -6.0, 172.0), (7.5, 3.0, 175.0), (4.0, 8.0, 176.0)],
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


def hat(bm):
    """Crown (8 sides, pinched top) on a brim that curls up at the sides, plus the band."""
    cy = 0.045
    crown = [(1.975, .135, .125), (2.08, .13, .12), (2.145, .095, .085)]
    lm.stack(bm, [(z, -a, a, cy - b, cy + b) for z, a, b in crown], HEX)
    # Brim: inner ring hidden inside the crown, outer ring raised at the sides (front Y 175).
    n = 8
    inner, outer, under = [], [], []
    for i in range(n):
        t = 2 * math.pi * i / n
        sx, sy = math.sin(t), -math.cos(t)
        side = abs(sx)
        inner.append(bm.verts.new((.12 * sx, cy + .11 * sy, 1.985)))
        outer.append(bm.verts.new((.29 * sx, cy + .27 * sy, 1.94 + .10 * side ** 2)))
        under.append(bm.verts.new((.29 * sx, cy + .27 * sy, 1.92 + .10 * side ** 2)))
    lower = [bm.verts.new((.12 * math.sin(2 * math.pi * i / n), cy - .11 * math.cos(2 * math.pi * i / n), 1.965)) for i in range(n)]
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((inner[i], inner[j], outer[j], outer[i]))
        bm.faces.new((outer[i], outer[j], under[j], under[i]))
        bm.faces.new((under[i], under[j], lower[j], lower[i]))
        bm.faces.new((lower[i], lower[j], inner[j], inner[i]))


def badge(bm):
    lm.tilted(bm, [(0, -0.087, 2.0, .028, .028), (0, -0.097, 2.0, .024, .024)], (0, -1, 0), OCT)


def arm_part(bm, a, b, rings, mirror, shape=OCT):
    a, b = Vector(a), Vector(b)
    if mirror:
        a.x, b.x = -a.x, -b.x
    loft(bm, a, b, rings, shape)


def boot(bm, mirror):
    """Sole slab, toe block sloping up to the instep and the shaft, in metres (left boot)."""
    k = -1 if mirror else 1
    x0, x1 = .105, .40
    v = {
        'sb0': (x0, .22, 0), 'sb1': (x1, .22, 0), 'sf1': (x1, -.245, 0), 'sf0': (x0, -.245, 0),
        'st0': (x0, .22, .055), 'st1': (x1, .22, .055), 'tf1': (x1, -.245, .055), 'tf0': (x0, -.245, .055),
        'toe0': (x0 + .02, -.215, .13), 'toe1': (x1 - .02, -.215, .13),
        'ins0': (x0 + .015, -.06, .21), 'ins1': (x1 - .03, -.06, .21),
        'sh0': (x0 + .015, .20, .24), 'sh1': (x1 - .03, .20, .24),
    }
    v = {n: (k * p[0] * 100, p[1] * 100, p[2] * 100) for n, p in v.items()}
    faces = [('sb0', 'sf0', 'sf1', 'sb1'), ('st0', 'st1', 'tf1', 'tf0'),
             ('sb0', 'sb1', 'st1', 'st0'), ('sf0', 'tf0', 'tf1', 'sf1'),
             ('sb1', 'sf1', 'tf1', 'st1'), ('sb0', 'st0', 'tf0', 'sf0'),
             ('tf0', 'tf1', 'toe1', 'toe0'), ('toe0', 'toe1', 'ins1', 'ins0'),
             ('ins0', 'ins1', 'sh1', 'sh0'), ('st0', 'st1', 'sh1', 'sh0'),
             ('tf1', 'st1', 'sh1', 'ins1', 'toe1'), ('tf0', 'toe0', 'ins0', 'sh0', 'st0')]
    vs = {n: bm.verts.new(Vector(p) / 100) for n, p in v.items()}
    for f in faces:
        try:
            bm.faces.new([vs[n] for n in f])
        except ValueError:
            pass


def parts():
    """(name, bone, colour, builder). Arms are lofted between the joints with rings
    (t, half_side, half_depth, shift_side, shift_depth) read across the drawn facets."""
    out = [
        ('head', 'head', SKIN, lambda bm: lm.poly(bm, *head_mesh())),
        ('hat', 'head', HAT, hat),
        ('badge', 'head', GOLD, badge),
        ('neck', 'neck', SKIN, lambda bm: loft(bm, (0, .03, 1.62), (0, .03, 1.80), [(0, .085, .085), (1, .075, .075)], HEX, False, False)),
        ('chest', 'chest', PALE, lambda bm: lm.stack(bm, CHEST, FACE6)),
        ('belt', 'hips', LEATHER, lambda bm: lm.stack(bm, BELT, OCT)),
        ('buckle', 'hips', GOLD, lambda bm: lm.stack(bm, BUCKLE, HEX)),
        ('pelvis', 'hips', DENIM, lambda bm: lm.stack(bm, HIPS, OCT)),
    ]
    for s, m in (('l', False), ('r', True)):
        k = -1 if m else 1
        sh, el, wr, tip = J('shoulder'), J('elbow'), J('wrist'), J('hand_tip')
        out += [
            # Deltoid cap above the shoulder to the elbow: deltoid (front Y 560 widest), biceps.
            ('upper_arm_' + s, 'upper_arm_' + s, SKIN, lambda bm, m=m, sh=sh, el=el: arm_part(
                bm, sh + Vector((-.03, -.01, .075)), el + Vector((0, 0, -.02)),
                [(0, .095, .105), (.2, .128, .145), (.8, .11, .125), (1, .085, .10)], m, HEX)),
            ('forearm_' + s, 'forearm_' + s, SKIN, lambda bm, m=m, el=el, wr=wr: arm_part(
                bm, el + Vector((0, 0, .03)), wr,
                [(0, .088, .098), (.3, .108, .122), (1, .078, .088)], m, HEX)),
            ('hand_' + s, 'hand_' + s, SKIN, lambda bm, m=m, wr=wr, tip=tip: arm_part(
                bm, wr + Vector((0, 0, .03)), tip,
                [(0, .09, .1), (.25, .125, .13), (.85, .12, .125), (1, .095, .10)], m, BOX)),
            ('thigh_' + s, 'thigh_' + s, DENIM, lambda bm, k=k: lm.stack(bm, [
                (0.70, *sorted((k * .055, k * .315)), -.10, .18), (0.99, *sorted((k * .0, k * .295)), -.125, .16)], HEX)),
            ('shin_' + s, 'shin_' + s, DENIM, lambda bm, k=k: lm.stack(bm, [
                (0.20, *sorted((k * .085, k * .37)), -.09, .21), (0.40, *sorted((k * .07, k * .34)), -.093, .19),
                (0.71, *sorted((k * .055, k * .315)), -.10, .18)], HEX)),
            ('foot_' + s, 'foot_' + s, BOOT, lambda bm, m=m: boot(bm, m)),
            ('ear_' + s, 'head', SKIN, lambda bm, k=k: lm.tilted(
                bm, [(k * .118, .045, 1.86, .042, .032), (k * .148, .05, 1.86, .036, .026)], (k, 0, 0), HEX)),
        ]
    return out


# Parts adjusted by hand in Blender (2026-11-04: crotch filled under the pelvis, thighs, shins
# and boots reshaped), saved as world-space triangles; they replace the measured builders.
EDITED = SRC / 'dale_pecas_editadas.json'


def _edited(data):
    def build_part(bm):
        vs = [bm.verts.new(v) for v in data['v']]
        for f in data['f']:
            bm.faces.new([vs[i] for i in f])
    return build_part


def build(collection_name=COLLECTION):
    col = bpy.data.collections.get(collection_name)
    if not col:
        col = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(col)
    total, report = 0, []
    edited = json.loads(EDITED.read_text()) if EDITED.exists() else {}
    for name, bone, colour, builder in parts():
        if name in edited:
            builder = _edited(edited[name])
        n = lm.part('DL_' + name, builder, colour, col)
        bpy.data.objects['DL_' + name]['bone'] = bone
        total += n
        report.append(f'{name}:{n}')
    print('TRIS', total, ' '.join(report))
    return total


def joints():
    j = {}
    for k, v in JOINTS.items():
        if k in ('pelvis', 'abdomen', 'chest_top', 'neck_base', 'neck_head', 'head_top'):
            j[k] = Vector(v)
        else:
            j[k + '_l'] = Vector(v)
            j[k + '_r'] = Vector((-v[0], v[1], v[2]))
    return j


# Expression decal square: brows (z 1.905) to the beard's chin (1.715), centred on the face.
FACE_BOX = {'x': (-0.12, 0.12), 'z': (1.70, 1.94), 'min_front': 0.05}


def in_face(points, n):
    x0, x1 = FACE_BOX['x']
    z0, z1 = FACE_BOX['z']
    xs, zs = [p[0] for p in points], [p[2] for p in points]
    overlaps = min(xs) < x1 and max(xs) > x0 and min(zs) < z1 and max(zs) > z0
    return -n[1] > FACE_BOX['min_front'] and overlaps


def assemble(name='dale_Body', collection_name=COLLECTION):
    """Join the parts into one mesh, one bone per vertex, one packed UV map plus FaceUV."""
    col = bpy.data.collections[collection_name]
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    copies, names = [], []
    for o in [o for o in col.objects if o.name.startswith('DL_')]:
        c = o.copy()
        c.data = o.data.copy()
        col.objects.link(c)
        names.append(o.name[3:])
        attr = c.data.attributes.new('part', 'INT', 'FACE')
        attr.data.foreach_set('value', [len(names) - 1] * len(c.data.polygons))
        g = c.vertex_groups.new(name=o['bone'])
        g.add(list(range(len(c.data.vertices))), 1.0, 'REPLACE')
        c.data.uv_layers.new(name='UVMap')
        copies.append(c)
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
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
        if o.name.startswith('DL_'):
            o.hide_set(True)
    return body


def face_uv(body):
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


def dump_triangles(body, path=SRC / 'dale_uv_tris.json'):
    me = body.data
    me.calc_loop_triangles()
    uv = me.uv_layers['UVMap'].data
    part = me.attributes['part'].data
    names = list(body['parts'])
    tris = []
    for t in me.loop_triangles:
        poly = me.polygons[t.polygon_index]
        name = names[part[t.polygon_index].value]
        tris.append({'part': name, 'uv': [list(uv[l].uv) for l in t.loops],
                     'co': [list(me.vertices[v].co) for v in t.vertices], 'n': list(t.normal),
                     'face': name == 'head' and in_face([me.vertices[v].co for v in poly.vertices], poly.normal)})
    Path(path).write_text(json.dumps(tris))
    return len(tris)


GODOT_GLB = ROOT / 'godot/assets/characters/ignis/ignis.glb'


def export_godot(path=GODOT_GLB):
    """Rig + body (on a plain material with the hand-painted page) with every NLA clip at 60 fps.
    The live scene keeps its preview material; the export works on a copy."""
    import contextlib
    import io
    rig, body = bpy.data.objects['dale_Rig'], bpy.data.objects['dale_Body']
    ad = rig.animation_data
    ad.action = None
    for t in ad.nla_tracks:
        t.mute = False
    for pb in rig.pose.bones:
        pb.location, pb.rotation_quaternion, pb.scale = (0, 0, 0), (1, 0, 0, 0), (1, 1, 1)
    bpy.context.scene.render.fps = 60
    exp = body.copy()
    exp.data = body.data.copy()
    exp.name = exp.data.name = 'ignis_BodyExport'
    bpy.context.scene.collection.objects.link(exp)
    m = bpy.data.materials.get('dale_export') or bpy.data.materials.new('dale_export')
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out, bsdf, tex = (nt.nodes.new(t) for t in ('ShaderNodeOutputMaterial', 'ShaderNodeBsdfPrincipled', 'ShaderNodeTexImage'))
    tex.image, tex.interpolation = bpy.data.images['dale_pagina_256.png'], 'Closest'
    nt.links.new(tex.outputs[0], bsdf.inputs['Base Color'])
    nt.links.new(bsdf.outputs[0], out.inputs[0])
    exp.data.materials.clear()
    exp.data.materials.append(m)
    # Outfits with their own pieces (legends_dale_outfits): exported as ignis_<Outfit>Body; the
    # game shows the one the palette names ("body") and hides the default ignis_BodyExport.
    extra = []
    for outfit in ('Coronel', 'Physique'):
        src = bpy.data.objects.get(f'dale_{outfit}_Body')
        if src is None:
            continue
        o = src.copy()
        o.data = src.data.copy()
        o.name = o.data.name = f'ignis_{outfit}Body'
        o.location = (0, 0, 0)
        o.hide_set(False)
        bpy.context.scene.collection.objects.link(o)
        o.data.materials.clear()
        o.data.materials.append(m)
        extra.append(o)
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    rig.select_set(True)
    exp.select_set(True)
    for o in extra:
        o.select_set(True)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', use_selection=True, export_yup=True,
                                      export_apply=False, export_animations=True, export_animation_mode='NLA_TRACKS',
                                      export_skins=True, export_materials='EXPORT')
    finally:
        for o in [exp] + extra:
            me = o.data
            bpy.data.objects.remove(o)
            bpy.data.meshes.remove(me)
        # Back to editing: with every NLA track playing at once the pose can't be moved by hand.
        import legends_anim
        legends_anim.edit(rig, 'idle')
