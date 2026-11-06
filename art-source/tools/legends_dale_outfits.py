"""Dale's outfits with their own pieces (Coronel, Physique), built on the base body.

Each outfit is a copy of dale_Body (rest pose, same skeleton and weights): parts the outfit does
not have are deleted, new parts are added on the base bones, and every clothing part gets new
UVs packed around the kept parts (head, ears, neck, fists keep their UVs, so the hand-painted
skin and the face stay exact). Measurements from the outfit crops (dale_outfit_crops.py), which
sit on the base crops' scale: dale_<outfit>_{frente,perfil,costas}.png.

Run in Blender: import legends_dale_outfits as o; o.build_all()
"""
import math

import bmesh
import bpy
from mathutils import Vector

import legends_dale as ld
import legends_model as lm

KEEP = {'head', 'ear_l', 'ear_r', 'neck', 'hand_l', 'hand_r'}


def coat(bm):
    """Coronel's linen coat skirt: from under the waist to the crotch line (hem z 0.90), hugging
    the hips so the trousers read as trousers below it (a wider, longer flare read as an apron);
    open bottom, the legs pass inside."""
    rings = [(1.17, -.25, .25, -.19, .21), (1.02, -.26, .26, -.19, .25), (0.90, -.265, .265, -.18, .26)]
    loops = []
    for z, x0, x1, y0, y1 in rings:
        cx, cy, a, b = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
        loops.append([bm.verts.new((cx + a * u, cy + b * v, z)) for u, v in lm.OCT])
    for r0, r1 in zip(loops, loops[1:]):
        for i in range(8):
            j = (i + 1) % 8
            bm.faces.new((r0[i], r0[j], r1[j], r1[i]))


def bare_foot(mirror):
    """Physique's bare foot: the boot's block lowered to a foot (toes z 0.07, instep 0.13), the
    toe grooves painted. Front x 0.12-0.40, profile y -0.24-0.17 (dale_physique crops)."""
    def build(bm):
        k = -1 if mirror else 1
        x0, x1 = .12, .39
        v = {
            'sb0': (x0, .17, 0), 'sb1': (x1, .17, 0), 'sf1': (x1, -.24, 0), 'sf0': (x0, -.24, 0),
            'st0': (x0 + .01, .17, .06), 'st1': (x1 - .01, .17, .06),
            'toe0': (x0, -.24, .07), 'toe1': (x1, -.24, .07),
            'ins0': (x0 + .02, -.08, .13), 'ins1': (x1 - .04, -.08, .13),
            'sh0': (x0 + .03, .14, .18), 'sh1': (x1 - .05, .14, .18),
        }
        vs = {n: bm.verts.new((k * p[0], p[1], p[2])) for n, p in v.items()}
        faces = [('sb0', 'sf0', 'sf1', 'sb1'), ('sf0', 'toe0', 'toe1', 'sf1'),
                 ('toe0', 'ins0', 'ins1', 'toe1'), ('ins0', 'sh0', 'sh1', 'ins1'),
                 ('sb0', 'sb1', 'st1', 'st0'), ('st0', 'st1', 'sh1', 'sh0'),
                 ('sb1', 'sf1', 'toe1', 'ins1', 'sh1', 'st1'), ('sb0', 'st0', 'sh0', 'ins0', 'toe0', 'sf0')]
        for f in faces:
            bm.faces.new([vs[n] for n in f])
    return build


def mohawk(bm):
    """Physique's crest of hair along the top of the head, front 2.11 m to the crown, thinning back."""
    sections = [(-.11, 2.00, 2.09, .030), (-.02, 2.03, 2.12, .036), (.08, 2.02, 2.10, .034), (.16, 1.97, 2.03, .026)]
    loops = []
    for y, z0, z1, h in sections:
        loops.append([bm.verts.new(p) for p in ((-h, y, z0), (h, y, z0), (h * .5, y, z1), (-h * .5, y, z1))])
    for r0, r1 in zip(loops, loops[1:]):
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((r0[i], r1[i], r1[j], r0[j]))
    bm.faces.new(list(reversed(loops[0])))
    bm.faces.new(loops[-1])


OUTFITS = {
    'Coronel': {'drop': {'belt', 'buckle', 'badge'}, 'add': [('coat', 'hips', coat)]},
    'Physique': {'drop': {'hat', 'badge', 'buckle', 'foot_l', 'foot_r'},
                 'add': [('mohawk', 'head', mohawk), ('foot_l', 'foot_l', bare_foot(False)), ('foot_r', 'foot_r', bare_foot(True))]},
}


def build(name):
    spec = OUTFITS[name]
    base = bpy.data.objects['dale_Body']
    obj_name = f'dale_{name}_Body'
    old = bpy.data.objects.get(obj_name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    ob = base.copy()
    ob.data = base.data.copy()
    ob.name = ob.data.name = obj_name
    base.users_collection[0].objects.link(ob)
    names = list(base['parts'])
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    part = bm.faces.layers.int['part']
    deform = bm.verts.layers.deform.verify()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if names[f[part]] in spec['drop']], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    for pname, bone, builder in spec['add']:
        if pname not in names:
            names.append(pname)
        idx = names.index(pname)
        before = set(bm.faces)
        tmp = bmesh.new()
        builder(tmp)
        bmesh.ops.recalc_face_normals(tmp, faces=tmp.faces)
        bmesh.ops.planar_faces(tmp, faces=tmp.faces, iterations=200, factor=0.5)
        bmesh.ops.triangulate(tmp, faces=tmp.faces)
        vmap = {}
        g = ob.vertex_groups.get(bone) or ob.vertex_groups.new(name=bone)
        for v in tmp.verts:
            nv = bm.verts.new(v.co)
            nv[deform][g.index] = 1.0
            vmap[v] = nv
        for f in tmp.faces:
            nf = bm.faces.new([vmap[v] for v in f.verts])
            nf[part] = idx
            nf.smooth = False
        tmp.free()
    bm.to_mesh(ob.data)
    bm.free()
    ob['parts'] = names
    ob.hide_set(False)
    repack(ob)
    return ob


def repack(ob):
    """New UVs for every clothing part, packed around the kept parts' islands (pinned)."""
    names = list(ob['parts'])
    keep = {names.index(n) for n in KEEP if n in names}
    me = ob.data
    part = me.attributes['part'].data
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(me)
    uv = bm.loops.layers.uv['UVMap']
    pl = bm.faces.layers.int['part']
    for f in bm.faces:
        kept = f[pl] in keep
        f.select = not kept
        for l in f.loops:
            l[uv].pin_uv = kept
    bmesh.update_edit_mesh(me)
    bpy.ops.uv.smart_project(angle_limit=math.radians(50), island_margin=0.012, area_weight=0.0, scale_to_bounds=False)
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.pack_islands(margin=0.008, rotate=True, pin=True, pin_method='LOCKED')
    bm = bmesh.from_edit_mesh(me)
    uv = bm.loops.layers.uv['UVMap']
    for f in bm.faces:
        for l in f.loops:
            l[uv].pin_uv = False
    bmesh.update_edit_mesh(me)
    bpy.ops.object.mode_set(mode='OBJECT')
    ld.face_uv(ob)


def build_all():
    out = {}
    for name in OUTFITS:
        ob = build(name)
        ld.dump_triangles(ob, ld.SRC / f'dale_{name.lower()}_uv_tris.json')
        out[name] = len(ob.data.polygons)
    return out
