"""Babuin's Executivo outfit (charcoal suit, red tie, barefoot) in the Legends style.

Measured on concept-art/characters/babuin/babuin-executivo-turnaround-v1.png, cropped and traced
to art-source/characters/kaze/legends/executivo/executivo_{frente,perfil,costas}_facetas.png
(concept_facets.py --edge 3.2 --sr 6 --dark 38 --min-area 150). The concept is drawn at the
Jade turnaround's scale and its joints fall on the Jade joints (elbow x .30, wrist .40, knee
.13, ankle .155), so the new pieces follow the Jade bones (legends_babuin.JOINTS) and the same
skeleton, clips and hitboxes serve the outfit.

New pieces (A-pose, then carried to the rest pose by the same rigid motion as the Jade parts):
jacket in two (chest / hips, so it bends like the Jade torso), sleeves (upper arm / forearm)
ending in the white shirt cuff, trousers (thigh / shin) to the ankle with a front crease.
Head, ears, neck, fists and bare feet are copied from kaze_Body with their UVs, so the
hand-painted skin and face stay as they are.

Run in Blender: import legends_executivo as lx; lx.build(); lx.assemble()
"""
import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

import legends_model as lm
from legends_babuin import JOINTS

SUIT = ('suit', (0.20, 0.20, 0.22))
SHIRT = ('shirt', (0.93, 0.93, 0.93))
KEPT = ['head', 'neck', 'ear_l', 'ear_r', 'hand_l', 'hand_r', 'foot_l', 'foot_r']
# Every piece's rest-pose motion is measured on this Jade part (A-pose -> rest).
CARRIED_BY = {'upper_arm': 'upper_arm', 'forearm': 'forearm', 'cuff': 'forearm'}

# Trouser section: a crease vertex at the front, flat back (front -1 in the depth axis).
CREASE = [(0, -1), (.85, -.45), (1, .45), (.5, 1), (-.5, 1), (-1, .45), (-.85, -.45)]

# Jacket rings (z, x0, x1, y0, y1) read off the front and profile traces: shoulder line,
# chest, the waist the side panels pinch in to, and the hem that flares over the hips.
JACKET_TOP = [(1.525, -.085, .085, -.075, .085), (1.47, -.19, .19, -.105, .13),
              (1.37, -.20, .20, -.15, .165), (1.24, -.145, .145, -.155, .175)]
JACKET_LOW = [(1.27, -.135, .135, -.145, .165), (1.15, -.145, .145, -.156, .175),
              (1.05, -.175, .175, -.16, .175), (0.965, -.19, .19, -.165, .18)]


def _j(name, s):
    v = Vector(JOINTS[name])
    return Vector((v.x if s == 'l' else -v.x, v.y, v.z))


def _along(p0, p1, t, off=Vector()):
    return tuple(p0.lerp(p1, t) + off)


def sleeve_upper(s):
    S, E = _j('shoulder', s), _j('elbow', s)
    d = E - S
    # shoulder cap sits a little into the torso; the sleeve is a boxy tube to the elbow
    return [(*_along(S, E, -.12), .085, .08), (*_along(S, E, .05), .098, .092),
            (*_along(S, E, .55), .09, .086), (*_along(S, E, 1.06), .086, .083)], d


def sleeve_fore(s):
    E, W = _j('elbow', s), _j('wrist', s)
    d = W - E
    return [(*_along(E, W, -.10), .076, .073), (*_along(E, W, .06), .087, .084),
            (*_along(E, W, .55), .091, .087), (*_along(E, W, .88), .094, .089)], d


def cuff(s):
    E, W = _j('elbow', s), _j('wrist', s)
    d = W - E
    return [(*_along(E, W, .84), .076, .072), (*_along(E, W, 1.02), .074, .07)], d


def trouser_thigh(s):
    H, K = _j('hip', s), _j('knee', s)
    d = K - H
    y = Vector((0, .012, 0))
    return [(*_along(H, K, -.16, y), .10, .125), (*_along(H, K, .30, y), .098, .122),
            (*_along(H, K, 1.04, y), .086, .106)], d


def trouser_shin(s):
    K, A = _j('knee', s), _j('ankle', s)
    d = A - K
    # straight leg down to the hem just above the ankle bone, a touch wider at the hem
    return [(*_along(K, A, -.08, Vector((0, .012, 0))), .08, .1), (*_along(K, A, .45, Vector((0, .02, 0))), .082, .096),
            (*_along(K, A, .90, Vector((0, .03, 0))), .086, .095)], d


def parts():
    out = [
        ('jacket_top', 'chest', SUIT, lambda bm: lm.stack(bm, JACKET_TOP, lm.FACE6)),
        ('jacket_low', 'hips', SUIT, lambda bm: lm.stack(bm, JACKET_LOW, lm.FACE6)),
    ]
    for s in 'lr':
        for name, fn, bone, colour, shape in (
                ('upper_arm', sleeve_upper, 'upper_arm_' + s, SUIT, lm.BOX),
                ('forearm', sleeve_fore, 'forearm_' + s, SUIT, lm.BOX),
                ('cuff', cuff, 'forearm_' + s, SHIRT, lm.OCT),
                ('thigh', trouser_thigh, 'thigh_' + s, SUIT, CREASE),
                ('shin', trouser_shin, 'shin_' + s, SUIT, CREASE)):
            rings, d = fn(s)
            out.append((f'{name}_{s}', bone, colour,
                        lambda bm, r=rings, d=d, sh=shape: lm.tilted(bm, r, d, sh)))
    return out


def build(collection_name='Babuin_Executivo'):
    col = bpy.data.collections.get(collection_name)
    if not col:
        col = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(col)
    total, report = 0, []
    for name, bone, colour, builder in parts():
        n = lm.part('EX_' + name, builder, colour, col)
        bpy.data.objects['EX_' + name]['bone'] = bone
        total += n
        report.append(f'{name}:{n}')
    print('TRIS', total, ' '.join(report))
    return total


def rigid_motion(part):
    """Best-fit rotation + translation taking a Jade part from the A-pose copy to the rest pose."""
    body, apose = bpy.data.objects['kaze_Body'], bpy.data.objects['kaze_Body_Apose']
    idx = list(body['parts']).index(part)
    attr = body.data.attributes['part'].data
    verts = sorted({v for p in body.data.polygons if attr[p.index].value == idx for v in p.vertices})
    a = np.array([apose.data.vertices[i].co for i in verts])
    b = np.array([body.data.vertices[i].co for i in verts])
    ca, cb = a.mean(0), b.mean(0)
    u, _, vt = np.linalg.svd((a - ca).T @ (b - cb))
    r = vt.T @ u.T
    if np.linalg.det(r) < 0:
        vt[-1] *= -1
        r = vt.T @ u.T
    m = Matrix(r.tolist()).to_4x4()
    m.translation = Vector(cb) - Matrix(r.tolist()) @ Vector(ca)
    return m


def assemble(name='kaze_Exec_Body', collection_name='Babuin_Executivo', prefix='EX_', kept=None, carried=None):
    """One mesh for the outfit: the kept Jade parts copied from kaze_Body (same UVs, weights and
    face decal) plus the new pieces carried to the rest pose, each on its bone, with a 'part'
    attribute; parented to kaze_Rig with an armature modifier, like kaze_Body."""
    kept = KEPT if kept is None else kept
    carried = CARRIED_BY if carried is None else carried
    body, rig = bpy.data.objects['kaze_Body'], bpy.data.objects['kaze_Rig']
    col = bpy.data.collections[collection_name]
    old = bpy.data.objects.get(name)
    if old:
        me = old.data
        bpy.data.objects.remove(old, do_unlink=True)
        bpy.data.meshes.remove(me)
    jade_parts = list(body['parts'])
    names = list(kept)
    bm = bmesh.new()
    bm.from_mesh(body.data)
    # A-pose position of every vertex (the concept's pose), for projecting the turnaround.
    apose = bm.verts.layers.float_vector.new('apose')
    ap = bpy.data.objects['kaze_Body_Apose'].data.vertices
    for v in bm.verts:
        v[apose] = ap[v.index].co
    part = bm.faces.layers.int['part']
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if jade_parts[f[part]] not in kept], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    for f in bm.faces:
        f[part] = names.index(jade_parts[f[part]])
    deform = bm.verts.layers.deform.verify()
    uv, fuv = bm.loops.layers.uv['UVMap'], bm.loops.layers.uv['FaceUV']
    groups = [g.name for g in body.vertex_groups]
    new_faces = []
    for o in [o for o in col.objects if o.name.startswith(prefix)]:
        pname = o.name[len(prefix):]
        kind, s = (pname[:-2], pname[-1]) if pname[-2:] in ('_l', '_r') else (pname, '')
        motion = rigid_motion(carried[kind] + '_' + s) if kind in carried else Matrix.Identity(4)
        if o['bone'] not in groups:
            groups.append(o['bone'])
        gi = groups.index(o['bone'])
        names.append(pname)
        vmap = {}
        for v in o.data.vertices:
            a_co = o.matrix_world @ v.co
            nv = bm.verts.new(motion @ a_co)
            nv[apose] = a_co
            nv[deform][gi] = 1.0
            vmap[v.index] = nv
        for p in o.data.polygons:
            f = bm.faces.new([vmap[i] for i in p.vertices])
            f[part] = len(names) - 1
            for loop in f.loops:
                loop[fuv].uv = (-1.0, -1.0)
            new_faces.append(f)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    for g in groups:
        ob.vertex_groups.new(name=g)
    ob['parts'] = names
    ob.parent = rig
    mod = ob.modifiers.new('Armature', 'ARMATURE')
    mod.object = rig
    for p in me.polygons:
        p.use_smooth = False
    for m in body.data.materials:
        me.materials.append(m)
    for o in col.objects:
        if o.name.startswith(prefix):
            o.hide_set(True)
    return ob


def layout_uv(ob, kept=None):
    """UVs for the new pieces only: the copied Jade parts keep theirs (pinned, so the painted
    skin and face stay where they are on the page), the new islands are packed around them."""
    import math
    bpy.context.view_layer.objects.active = ob
    for o in bpy.context.view_layer.objects:
        o.select_set(o == ob)
    names = list(ob['parts'])
    kept = {i for i, n in enumerate(names) if n in (KEPT if kept is None else kept)}
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    part = bm.faces.layers.int['part']
    uv = bm.loops.layers.uv['UVMap']
    for f in bm.faces:
        new = f[part] not in kept
        f.select = new
        for l in f.loops:
            l[uv].pin_uv = not new
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.uv_layers.active = ob.data.uv_layers['UVMap']
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='FACE')
    bpy.ops.uv.smart_project(angle_limit=math.radians(50), island_margin=0.012, area_weight=0.0,
                             scale_to_bounds=False)
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.pack_islands(margin=0.008, rotate=True, pin=True, pin_method='LOCKED')
    bpy.ops.object.mode_set(mode='OBJECT')


def dump_triangles(ob, path, kept=None):
    """Triangles of the outfit for legends_executivo_texture.py: UV, A-pose position, normal,
    and whether the piece is new (painted) or a copied Jade part (occluder only)."""
    import json
    from pathlib import Path
    me = ob.data
    me.calc_loop_triangles()
    uv = me.uv_layers['UVMap'].data
    part = me.attributes['part'].data
    ap = me.attributes['apose'].data
    names = list(ob['parts'])
    tris = []
    for t in me.loop_triangles:
        name = names[part[t.polygon_index].value]
        co = [Vector(ap[v].vector) for v in t.vertices]
        n = (co[1] - co[0]).cross(co[2] - co[0]).normalized()
        tris.append({'part': name, 'new': name not in (KEPT if kept is None else kept), 'uv': [list(uv[l].uv) for l in t.loops],
                     'co': [list(c) for c in co], 'n': list(n)})
    Path(path).write_text(json.dumps(tris))
    return len(tris)
