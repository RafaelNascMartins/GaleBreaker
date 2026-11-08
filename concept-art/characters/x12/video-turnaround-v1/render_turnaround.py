"""Isolated X12 presentation render; reads model/reference sources without changing them."""
import bpy
import bmesh
import json
import math
import sys
from pathlib import Path
from mathutils import Vector
import numpy as np

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
SRC = ROOT / 'art-source/characters/tophia/legends'
MPP = 1.8 / 840
H = 851
TOP = H * MPP
MODE = sys.argv[-1] if sys.argv[-1] in ('preview', 'video') else 'preview'
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 4
scene.cycles.use_denoising = False
scene.render.resolution_x = 1280
scene.render.resolution_y = 1280
scene.render.resolution_percentage = 100
scene.render.film_transparent = False
scene.view_settings.view_transform = 'Standard'
scene.view_settings.look = 'None'
scene.view_settings.exposure = 0
scene.view_settings.gamma = 1
world = bpy.data.worlds.new('Flat grey')
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.21586,)*3 + (1,)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = 1
scene.world = world

images, pixels = [], []
for view in ('frente', 'perfil', 'costas'):
    im = bpy.data.images.load(str(SRC / ('x12_' + view + '.png')))
    images.append(im)
    a = np.empty(len(im.pixels), dtype=np.float32)
    im.pixels.foreach_get(a)
    pixels.append(a.reshape(im.size[1], im.size[0], 4))

BASE = {'stone': (0.55, .13, .035, 1), 'metal': (.075, .066, .08, 1),
        'skin': (.92, .52, .22, 1), 'hair': (.035, .028, .045, 1)}

def uv(p, view):
    x, y, z = p
    if view == 0:
        return (x / MPP + 330) / 660, z / TOP
    if view == 2:
        return (-x / MPP + 330) / 660, z / TOP
    return (y / MPP + 220) / 440, z / TOP

def sample(p, view):
    u, v = uv(p, view)
    a = pixels[view]
    return a[min(a.shape[0]-1, max(0, round(v*(a.shape[0]-1)))),
             min(a.shape[1]-1, max(0, round(u*(a.shape[1]-1)))), :3]

materials = {}
flat_materials = {}
for tone, base in BASE.items():
    for view in range(3):
        mat = bpy.data.materials.new(tone + '_' + str(view))
        mat.use_nodes = True
        nt = mat.node_tree
        nt.nodes.clear()
        out = nt.nodes.new('ShaderNodeOutputMaterial')
        emission = nt.nodes.new('ShaderNodeEmission')
        tex = nt.nodes.new('ShaderNodeTexImage')
        tex.image = images[view]
        tex.interpolation = 'Closest'
        tex.extension = 'EXTEND'
        sep = nt.nodes.new('ShaderNodeSeparateColor')
        sep.mode = 'HSV'
        nt.links.new(tex.outputs['Color'], sep.inputs[0])
        grey = nt.nodes.new('ShaderNodeMath')
        grey.operation = 'LESS_THAN'
        grey.inputs[1].default_value = .15
        nt.links.new(sep.outputs[1], grey.inputs[0])
        bright = nt.nodes.new('ShaderNodeMath')
        bright.operation = 'GREATER_THAN'
        bright.inputs[1].default_value = .12
        nt.links.new(sep.outputs[2], bright.inputs[0])
        mask = nt.nodes.new('ShaderNodeMath')
        mask.operation = 'MULTIPLY'
        nt.links.new(grey.outputs[0], mask.inputs[0])
        nt.links.new(bright.outputs[0], mask.inputs[1])
        mix = nt.nodes.new('ShaderNodeMixRGB')
        mix.inputs[2].default_value = base
        nt.links.new(mask.outputs[0], mix.inputs[0])
        nt.links.new(tex.outputs['Color'], mix.inputs[1])
        if tone == 'hair':
            # Projected skin must not appear in the hair's silhouette at oblique angles.
            hair_mask = nt.nodes.new('ShaderNodeMath')
            hair_mask.operation = 'GREATER_THAN'
            hair_mask.inputs[1].default_value = .25
            nt.links.new(sep.outputs[1], hair_mask.inputs[0])
            combine = nt.nodes.new('ShaderNodeMath')
            combine.operation = 'MAXIMUM'
            nt.links.new(mask.outputs[0], combine.inputs[0])
            nt.links.new(hair_mask.outputs[0], combine.inputs[1])
            nt.links.new(combine.outputs[0], mix.inputs[0])
        nt.links.new(mix.outputs[0], emission.inputs['Color'])
        nt.links.new(emission.outputs[0], out.inputs['Surface'])
        materials[tone, view] = mat

data = json.loads((SRC / 'x12_pecas.json').read_text())
head_rings = json.loads((SRC / 'x12_aneis.json').read_text())['head']['rings']
head_v = [p for ring in head_rings for p in ring]
head_f = []
for ri in range(len(head_rings)-1):
    for j in range(8):
        head_f.append([ri*8+j, ri*8+(j+1)%8, (ri+1)*8+(j+1)%8, (ri+1)*8+j])
head_f += [list(reversed(range(8))), list(range((len(head_rings)-1)*8, len(head_v)))]
data['head'] = {'v':head_v, 'f':head_f, 'tone':'skin'}
for name, part in data.items():
    me = bpy.data.meshes.new(name)
    me.from_pydata(part['v'], [], part['f'] if name == 'head' else [])
    bm = bmesh.new()
    bm.from_mesh(me)
    if name != 'head':
        hull = bmesh.ops.convex_hull(bm, input=list(bm.verts), use_existing_faces=False)
        discard = list(set(hull.get('geom_interior', []) + hull.get('geom_unused', [])))
        if discard:
            bmesh.ops.delete(bm, geom=discard, context='VERTS')
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.update()
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    tones = [part.get('tone', 'stone')] * len(me.polygons)
    if 'ftone' in part:
        original_v = np.array(part['v'])
        original_centres = np.array([original_v[f].mean(0) for f in part['f']])
        tones = [part['ftone'][int(np.argmin(np.sum((original_centres - np.array(p.center)) ** 2, axis=1)))] for p in me.polygons]
    slots = [(tone, vi) for tone in BASE for vi in range(3)]
    for slot in slots:
        me.materials.append(materials[slot])
    for tone, base in BASE.items():
        for step in range(4):
            key = (tone, step)
            if key not in flat_materials:
                m = bpy.data.materials.new('Side_' + tone + str(step))
                m.use_nodes = True
                nt = m.node_tree
                nt.nodes.clear()
                output = nt.nodes.new('ShaderNodeOutputMaterial')
                em = nt.nodes.new('ShaderNodeEmission')
                factor = .65 + step * .12
                em.inputs['Color'].default_value = tuple(c * factor for c in base[:3]) + (1,)
                nt.links.new(em.outputs[0], output.inputs['Surface'])
                flat_materials[key] = m
            me.materials.append(flat_materials[key])
    layer = me.uv_layers.new(name='Reference projection')
    for poly in me.polygons:
        tone = tones[poly.index]
        centre = poly.center
        n = poly.normal
        scores = [max(0., -n.y), 0., max(0., n.y)]
        # Prefer the front/back paintings for horizontal planes, where a normal gives no yaw.
        scores[0 if centre.y < 0 else 2] += abs(n.z) * .35
        # Profile crop has an overlapping arm: avoid projecting it onto torso/inner limb faces.
        if tone == 'skin':
            scores = [1., 0., 0.] if centre.y < 0 else [0., 0., 1.]
        if abs(n.y) < .1:
            scores[0 if centre.y < 0 else 2] += .1
        for vi in range(3):
            c = sample(centre, vi)
            saturation = float(c.max() - c.min())
            if tone in ('stone', 'skin') and saturation < .14:
                scores[vi] *= .03
            if tone == 'hair' and float(c.max()) > .4:
                scores[vi] *= .01
        vi = max(range(3), key=lambda k: scores[k])
        poly.material_index = slots.index((tone, vi))
        use_flat = abs(n.y) < .68
        if name == 'head':
            use_flat = abs(n.z) > .75 or n.y > -.65
            if use_flat:
                tone = 'hair' if centre.z > 1.63 else 'skin'
        if use_flat:
            level = min(3, max(0, int((n.z * .4 + n.x * -.2 + .5) * 4)))
            poly.material_index = len(slots) + list(BASE).index(tone) * 4 + level
        poly.use_smooth = False
        for li in poly.loop_indices:
            p = me.vertices[me.loops[li].vertex_index].co
            layer.data[li].uv = uv(p, vi)

cam_data = bpy.data.cameras.new('Orthographic turnaround')
cam = bpy.data.objects.new('Orthographic turnaround', cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 2.11
target = Vector((0, 0, .91))

def angle(deg):
    t = math.radians(deg)
    cam.location = (5 * math.sin(t), -5 * math.cos(t), .91)
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()

scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.render.image_settings.color_depth = '8'
if MODE == 'preview':
    scene.render.resolution_percentage = 50
    for deg in (0, 45, 90, 180, 270, 315):
        angle(deg)
        scene.render.filepath = str(OUT / ('preview_%03d.png' % deg))
        bpy.ops.render.render(write_still=True)
else:
    scene.render.fps = 30
    scene.frame_start = 1
    scene.frame_end = 240
    # Camera orbits only: no character object, joint or vertex is animated.
    for i in range(241):
        scene.frame_set(i + 1)
        angle(i * 360 / 240)
        cam.keyframe_insert('location', frame=i+1)
        cam.keyframe_insert('rotation_euler', frame=i+1)
    if cam.animation_data:
        action = cam.animation_data.action
        for layer_ in action.layers:
            for strip in layer_.strips:
                for channelbag in strip.channelbags:
                    for curve in channelbag.fcurves:
                        for k in curve.keyframe_points:
                            k.interpolation = 'LINEAR'
    scene.frame_set(1)
    (OUT / 'frames').mkdir(exist_ok=True)
    scene.render.filepath = str(OUT / 'frames' / 'x12_')
    bpy.ops.render.render(animation=True)
print('X12_RENDER_COMPLETE', MODE, flush=True)
