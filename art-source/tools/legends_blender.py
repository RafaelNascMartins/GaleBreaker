"""Blender side of the hand-modelled Legends workflow (any character).

    load_parts(json_path, collection, prefix)   the parts of <name>_pecas.json as objects
    load_refs()                                  the reference models in collection Ref_Legends
    compare(prefix, out_dir, region)             untextured + wire renders of the character and
                                                 Mega Man in 4 views (legends_compare.py makes the
                                                 sheets with the concept)

Run inside Blender with art-source/tools on sys.path. Preview materials are flat colours per
tone; shading is smooth (Gouraud, like the references) with hard edges on armour only.
"""
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector

import legends_kit as lk

ROOT = Path(__file__).resolve().parents[2]
REF = ROOT / 'concept-art/referencias'
REF_COLLECTION = 'Ref_Legends'
REF_MODELS = {'Megaman': -1.2, 'Roll_(Cutscene)': -2.2, 'Old_Man': -3.2, 'Wily_the_Boatshop_Owner': -4.2}
TONES = {'stone': (0.80, 0.36, 0.16), 'metal': (0.22, 0.21, 0.23), 'skin': (0.93, 0.68, 0.52),
         'hair': (0.10, 0.09, 0.12), 'cloth': (0.55, 0.55, 0.60)}
SOFT = ('skin', 'hair')            # no hard edges on these
SHARP_DEG = 40
VIEWS, REGIONS = lk.VIEWS, lk.REGIONS


def _collection(name):
    col = bpy.data.collections.get(name)
    if not col:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


def _material(tone):
    rgb = TONES.get(tone, TONES['stone'])
    mat = bpy.data.materials.get('flat_x_' + tone) or bpy.data.materials.new('flat_x_' + tone)
    mat.diffuse_color = (*rgb, 1)
    return mat


def page_material(page_path):
    """Preview material of a painted page: the texture as emission (no light, the shading is
    painted), nearest sampling like the PS1."""
    name = 'page_' + Path(page_path).stem
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    tex = nt.nodes.new('ShaderNodeTexImage')
    img = bpy.data.images.load(str(page_path), check_existing=True)
    if not img.is_dirty:          # never drop paint the user has not saved yet
        img.reload()
    tex.image, tex.interpolation = img, 'Closest'
    em, out = nt.nodes.new('ShaderNodeEmission'), nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(tex.outputs[0], em.inputs[0])
    nt.links.new(em.outputs[0], out.inputs[0])
    return mat


def face_material(page_path, atlas_path, grid=(6, 4)):
    """Page material plus the expression atlas through FaceUV (where FaceUV >= 0): the cell is
    the object's 'expressao' property (0..23, row by row from the top-left), like the game."""
    name = 'face_' + Path(page_path).stem
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    N = nt.nodes.new
    page = N('ShaderNodeTexImage')
    page.image = bpy.data.images.load(str(page_path), check_existing=True)
    page.interpolation = 'Closest'
    uv_page, uv_face = N('ShaderNodeUVMap'), N('ShaderNodeUVMap')
    uv_page.uv_map, uv_face.uv_map = 'UVMap', 'FaceUV'
    nt.links.new(uv_page.outputs[0], page.inputs[0])
    attr = N('ShaderNodeAttribute')
    attr.attribute_type, attr.attribute_name = 'OBJECT', 'expressao'
    cols, rows = grid
    # cell (col, row from the top) -> offset in the atlas (v up)
    col = N('ShaderNodeMath'); col.operation = 'MODULO'; col.inputs[1].default_value = cols
    row = N('ShaderNodeMath'); row.operation = 'DIVIDE'; row.inputs[1].default_value = cols
    rowf = N('ShaderNodeMath'); rowf.operation = 'FLOOR'
    vrow = N('ShaderNodeMath'); vrow.operation = 'SUBTRACT'; vrow.inputs[0].default_value = rows - 1
    nt.links.new(attr.outputs['Fac'], col.inputs[0]); nt.links.new(attr.outputs['Fac'], row.inputs[0])
    nt.links.new(row.outputs[0], rowf.inputs[0]); nt.links.new(rowf.outputs[0], vrow.inputs[1])
    sep = N('ShaderNodeSeparateXYZ'); nt.links.new(uv_face.outputs[0], sep.inputs[0])
    cu = N('ShaderNodeMath'); cu.operation = 'ADD'
    cv = N('ShaderNodeMath'); cv.operation = 'ADD'
    clu = N('ShaderNodeClamp'); clv = N('ShaderNodeClamp')
    for c in (clu, clv):
        c.inputs[1].default_value, c.inputs[2].default_value = 0.002, 0.998
    nt.links.new(sep.outputs[0], clu.inputs[0]); nt.links.new(sep.outputs[1], clv.inputs[0])
    nt.links.new(col.outputs[0], cu.inputs[0]); nt.links.new(clu.outputs[0], cu.inputs[1])
    nt.links.new(vrow.outputs[0], cv.inputs[0]); nt.links.new(clv.outputs[0], cv.inputs[1])
    du = N('ShaderNodeMath'); du.operation = 'DIVIDE'; du.inputs[1].default_value = cols
    dv = N('ShaderNodeMath'); dv.operation = 'DIVIDE'; dv.inputs[1].default_value = rows
    nt.links.new(cu.outputs[0], du.inputs[0]); nt.links.new(cv.outputs[0], dv.inputs[0])
    comb = N('ShaderNodeCombineXYZ')
    nt.links.new(du.outputs[0], comb.inputs[0]); nt.links.new(dv.outputs[0], comb.inputs[1])
    face = N('ShaderNodeTexImage')
    face.image = bpy.data.images.load(str(atlas_path), check_existing=True)
    face.image.reload()
    face.interpolation, face.extension = 'Closest', 'CLIP'
    nt.links.new(comb.outputs[0], face.inputs[0])
    on = N('ShaderNodeMath'); on.operation = 'GREATER_THAN'; on.inputs[1].default_value = -0.5
    nt.links.new(sep.outputs[0], on.inputs[0])
    alpha = N('ShaderNodeMath'); alpha.operation = 'MULTIPLY'
    nt.links.new(on.outputs[0], alpha.inputs[0]); nt.links.new(face.outputs['Alpha'], alpha.inputs[1])
    mix = N('ShaderNodeMix'); mix.data_type = 'RGBA'
    nt.links.new(alpha.outputs[0], mix.inputs['Factor'])
    nt.links.new(page.outputs['Color'], mix.inputs[6]); nt.links.new(face.outputs['Color'], mix.inputs[7])
    em, out = N('ShaderNodeEmission'), N('ShaderNodeOutputMaterial')
    nt.links.new(mix.outputs[2], em.inputs[0]); nt.links.new(em.outputs[0], out.inputs[0])
    nt.nodes.active = page            # Texture Paint keeps painting the body page
    return mat


def load_parts(json_path, collection, prefix, page=None, atlas=None):
    """One object per part, origin at the world origin, custom property 'bone'. With `page`
    (and 'uv' in the parts), the painted page is applied through the UVs."""
    col = _collection(collection)
    for o in list(col.objects):
        if o.name.startswith(prefix):
            me = o.data
            bpy.data.objects.remove(o)
            bpy.data.meshes.remove(me)
    data = json.loads(Path(json_path).read_text())
    total = 0
    for name, p in data.items():
        me = bpy.data.meshes.new(prefix + name)
        me.from_pydata([tuple(v) for v in p['v']], [], [tuple(f) for f in p['f']])
        tones = p.get('ftone') or [p.get('tone', 'stone')] * len(p['f'])
        used = sorted(set(tones))
        if page and 'uv' in p:
            face = atlas and 'fuv' in p
            me.materials.append(face_material(page, atlas) if face else page_material(page))
            layer = me.uv_layers.new(name='UVMap')
            for poly in me.polygons:
                for j in range(poly.loop_total):
                    layer.data[poly.loop_start + j].uv = p['uv'][poly.index][j]
            if face:
                fl = me.uv_layers.new(name='FaceUV')
                for poly in me.polygons:
                    for j in range(poly.loop_total):
                        fl.data[poly.loop_start + j].uv = p['fuv'][poly.index][j]
                me.uv_layers.active = layer
        else:
            for t in used:
                me.materials.append(_material(t))
            me.polygons.foreach_set('material_index', [used.index(t) for t in tones])
        me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
        if not set(used) & set(SOFT):
            me.set_sharp_from_angle(angle=math.radians(SHARP_DEG))
        me.update()
        ob = bpy.data.objects.new(prefix + name, me)
        ob['bone'] = p['bone']
        if atlas and 'fuv' in p:
            ob['expressao'] = 0
        col.objects.link(ob)
        total += sum(len(f) - 2 for f in p['f'])
    print('loaded', len(data), 'parts', total, 'tris')
    return total


def load_refs():
    """Reference models 1.80 m tall, facing -y, side by side at negative x, textured."""
    col = _collection(REF_COLLECTION)
    for name, xoff in REF_MODELS.items():
        if bpy.data.objects.get('REF_' + name):
            continue
        before = set(bpy.data.objects)
        bpy.ops.wm.obj_import(filepath=str(REF / f'{name}.obj'))
        new = [o for o in bpy.data.objects if o not in before]
        img = bpy.data.images.load(str(REF / f'{name}.png'), check_existing=True)
        mat = bpy.data.materials.new('ref_' + name)
        mat.use_nodes = True
        nt = mat.node_tree
        nt.nodes.clear()
        tex = nt.nodes.new('ShaderNodeTexImage')
        tex.image, tex.interpolation = img, 'Closest'
        em, out = nt.nodes.new('ShaderNodeEmission'), nt.nodes.new('ShaderNodeOutputMaterial')
        nt.links.new(tex.outputs[0], em.inputs[0])
        nt.links.new(em.outputs[0], out.inputs[0])
        for o in new:
            for c in o.users_collection:
                c.objects.unlink(o)
            col.objects.link(o)
            o.name = 'REF_' + name
            o.data.materials.clear()
            o.data.materials.append(mat)
            o.rotation_euler[2] += math.pi
            bpy.context.view_layer.update()
            bb = [o.matrix_world @ v.co for v in o.data.vertices]
            s = 1.8 / (max(v.z for v in bb) - min(v.z for v in bb))
            o.scale = (s, s, s)
            bpy.context.view_layer.update()
            bb = [o.matrix_world @ v.co for v in o.data.vertices]
            lo = Vector([min(getattr(v, a) for v in bb) for a in 'xyz'])
            hi = Vector([max(getattr(v, a) for v in bb) for a in 'xyz'])
            o.location += Vector((xoff - (lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z))


def _camera():
    cam = bpy.data.objects.get('LEGENDS_cam')
    if not cam:
        cam = bpy.data.objects.new('LEGENDS_cam', bpy.data.cameras.new('LEGENDS_cam'))
        bpy.context.scene.collection.objects.link(cam)
    cam.data.type = 'ORTHO'
    return cam


def compare(prefix, out_dir, region='corpo', refs=('Megaman',)):
    """Renders <out_dir>/<region>_<who>_<view>[_arame].png for the character (objects named
    prefix*) and each reference, untextured smooth grey + wire, 700x700 (corpo 560x900)."""
    sc = bpy.context.scene
    cam = _camera()
    old = (sc.camera, sc.render.resolution_x, sc.render.resolution_y, sc.render.engine,
           sc.display.shading.color_type, sc.render.filepath)
    try:
        sc.render.engine = 'BLENDER_WORKBENCH'
    except TypeError:
        pass
    sc.camera = cam
    z, scale = REGIONS[region]
    sc.render.resolution_x, sc.render.resolution_y = (560, 900) if region == 'corpo' else (700, 700)
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    hidden = {o.name: o.hide_render for o in meshes}
    grey = bpy.data.materials.get('legends_grey') or bpy.data.materials.new('legends_grey')
    grey.diffuse_color = (0.7, 0.7, 0.7, 1)
    wire_mat = bpy.data.materials.get('legends_wire') or bpy.data.materials.new('legends_wire')
    wire_mat.diffuse_color = (0.0, 0.85, 0.85, 1)
    temp = []

    def copy(o, wire):
        c = o.copy()
        c.data = o.data.copy()
        bpy.context.scene.collection.objects.link(c)
        if wire:
            m = c.modifiers.new('w', 'WIREFRAME')
            m.thickness, m.use_replace = 0.0015 / o.scale[0], True
            c.data.materials.clear()
            c.data.materials.append(wire_mat)
        temp.append(c)
        return c
    who = [(prefix.rstrip('_').lower(), 0.0, [o for o in meshes if o.name.startswith(prefix)], False)]
    for r in refs:
        o = bpy.data.objects.get('REF_' + r)
        if o:
            g = copy(o, False)
            g.data.materials.clear()
            g.data.materials.append(grey)
            for p in g.data.polygons:
                p.use_smooth = True
            who.append((r.lower(), REF_MODELS[r], [g], True))
    try:
        sc.display.shading.color_type = 'MATERIAL'
        for key, x, obs, _ in who:
            wires = [copy(o, True) for o in obs]
            for wire in (False, True):
                show = set(obs) | (set(wires) if wire else set())
                for o in bpy.data.objects:
                    if o.type == 'MESH':
                        o.hide_render = o not in show
                for v, ((dx, dy), ang) in VIEWS.items():
                    cam.location = (x + 5 * dx, 5 * dy, z)
                    cam.rotation_euler = (math.pi / 2, 0, math.radians(ang))
                    cam.data.ortho_scale = scale
                    sc.render.filepath = str(Path(out_dir) / f'{region}_{key}_{v}{"_arame" if wire else ""}.png')
                    bpy.ops.render.render(write_still=True)
    finally:
        for c in temp:
            me = c.data
            bpy.data.objects.remove(c)
            bpy.data.meshes.remove(me)
        for o in meshes:
            if o.name in bpy.data.objects:
                bpy.data.objects[o.name].hide_render = hidden[o.name]
        (sc.camera, sc.render.resolution_x, sc.render.resolution_y, sc.render.engine,
         sc.display.shading.color_type, sc.render.filepath) = old
