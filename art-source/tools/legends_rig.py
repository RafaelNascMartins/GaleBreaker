"""Skeleton of a Legends character (run inside Blender), any character.

    import legends_rig; legends_rig.build('x12_modelo')

The character module gives:
    RIG_SOURCE   (blend path, rig object name): the fighter's rig in the game (same bone names
                 for every fighter, the animations and code IK use them)
    JOINTS       joints in metres, left side (the right mirrors): pelvis, abdomen, chest_top,
                 neck_base, neck_head, head_top, shoulder, elbow, wrist, hand_tip, hip, knee,
                 ankle, toe (model_rig.fit_skeleton)
    UNUSED_BONES bones of the shared rig this fighter doesn't use (removed)
    VERTEX_BONE  optional f(part, (x, y, z)) -> bone name or None: a vertex that follows another
                 bone than its part's (a skirt's hem on the cloth bones), still weight 1
Steps: append the rig as <NAME>_Rig, fit its bones to JOINTS, remove the unused bones, build
<NAME>_Body from <name>_pecas.json (one mesh: UVMap + FaceUV, every vertex weight 1 on its
part's bone: rigid pieces, no blending), bring the A-pose arms down to the animations' rest pose
(model_rig.arms_to_rest; the vertices move, the UVs and the painting stay) and check it.
"""
import importlib
import json

import bpy
from mathutils import Vector

import legends_blender as lb
import model_rig

BODY_COLLECTION = '{}_Corpo'
CENTRE = ('pelvis', 'abdomen', 'chest_top', 'neck_base', 'neck_head', 'head_top')


def joints(m):
    j = {}
    for k, v in m.JOINTS.items():
        if k in CENTRE:
            j[k] = Vector(v)
        else:
            j[k + '_l'] = Vector(v)
            j[k + '_r'] = Vector((-v[0], v[1], v[2]))
    return j


def _collection(name):
    col = bpy.data.collections.get(name)
    if not col:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


def append_rig(m, col):
    name = f'{m.NAME}_Rig'
    old = bpy.data.objects.get(name)
    if old:
        arm = old.data
        bpy.data.objects.remove(old)
        bpy.data.armatures.remove(arm)
    path, obj = m.RIG_SOURCE
    with bpy.data.libraries.load(str(path)) as (src, dst):
        dst.objects = [obj]
    rig = dst.objects[0]
    rig.name = name
    rig.data.name = name
    ad = rig.animation_data                  # keep the fighter's clips (NLA tracks), none active
    if ad:
        ad.action = None
        for t in ad.nla_tracks:
            t.mute = False
        name_clips(rig)
    rig.location, rig.rotation_euler, rig.scale = (0, 0, 0), (0, 0, 0), (1, 1, 1)
    col.objects.link(rig)
    for pb in rig.pose.bones:
        pb.location, pb.rotation_quaternion, pb.rotation_euler, pb.scale = (0, 0, 0), (1, 0, 0, 0), (0, 0, 0), (1, 1, 1)
    return rig


def name_clips(rig):
    """Each NLA track's action takes the track's name (an append brings 'idle.003'); copies of
    the clips no strip uses (earlier appends) are deleted."""
    used = {s.action for t in rig.animation_data.nla_tracks for s in t.strips if s.action}
    names = {t.name for t in rig.animation_data.nla_tracks}
    for act in list(bpy.data.actions):
        base = act.name.split('.')[0]
        if act not in used and base in names and not act.name.endswith(('_generated', '_old')):
            bpy.data.actions.remove(act)
    for t in rig.animation_data.nla_tracks:
        for st in t.strips:
            if st.action and st.action.name != t.name:
                st.action.name = t.name


def prune(rig, names):
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    for n in names:
        eb = rig.data.edit_bones.get(n)
        if eb:
            rig.data.edit_bones.remove(eb)
    bpy.ops.object.mode_set(mode='OBJECT')


def body(m, col, page, atlas):
    """One mesh from the parts: vertices of each part weight 1 on its bone, attribute 'part'."""
    name = f'{m.NAME}_Body'
    old = bpy.data.objects.get(name)
    if old:
        me = old.data
        bpy.data.objects.remove(old)
        bpy.data.meshes.remove(me)
    parts = json.loads((m.SRC / f'{m.NAME}_pecas.json').read_text())
    V, F, UV, FUV, part_of, groups, names = [], [], [], [], [], {}, []
    for pi, (pname, p) in enumerate(parts.items()):
        names.append(pname)
        off = len(V)
        V += [tuple(v) for v in p['v']]
        rule = getattr(m, 'VERTEX_BONE', None)      # per-vertex bone (cloth plates), else the part's
        for k, v in enumerate(p['v']):
            b = (rule(pname, v) if rule else None) or p['bone']
            groups.setdefault(b, []).append(off + k)
        for fi, f in enumerate(p['f']):
            F.append([off + i for i in f])
            UV.append(p['uv'][fi])
            FUV.append(p['fuv'][fi] if 'fuv' in p else [[-1.0, -1.0]] * len(f))
            part_of.append(pi)
    me = bpy.data.meshes.new(name)
    me.from_pydata(V, [], F)
    uv, fuv = me.uv_layers.new(name='UVMap'), me.uv_layers.new(name='FaceUV')
    for poly in me.polygons:
        for j in range(poly.loop_total):
            uv.data[poly.loop_start + j].uv = UV[poly.index][j]
            fuv.data[poly.loop_start + j].uv = FUV[poly.index][j]
    me.uv_layers.active = uv
    me.attributes.new('part', 'INT', 'FACE').data.foreach_set('value', part_of)
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    me.materials.append(lb.face_material(page, atlas))
    me.update()
    ob = bpy.data.objects.new(name, me)
    ob['parts'] = names
    ob['expressao'] = 0
    col.objects.link(ob)
    for bone, idx in groups.items():
        ob.vertex_groups.new(name=bone).add(idx, 1.0, 'REPLACE')
    return ob


def check(rig, ob):
    bones = {b.name for b in rig.data.bones}
    missing = [g.name for g in ob.vertex_groups if g.name not in bones]
    multi = sum(1 for v in ob.data.vertices if len([g for g in v.groups if g.weight > 0]) != 1)
    print(f'{rig.name}: {len(bones)} bones; {ob.name}: {len(ob.data.vertices)} verts, '
          f'groups without a bone {missing}, verts not on exactly one bone {multi}')
    return not missing and not multi


def export_godot(module_name):
    """<NAME>_Rig + <ID>_BodyExport (the body on a plain material with the page) with every NLA
    clip at 60 fps -> godot/assets/characters/<ID>/<ID>.glb; the page and the expression atlas
    are copied to its textures/ as page.png and face.png (the game's Legends material)."""
    import contextlib
    import io
    import shutil
    m = importlib.import_module(module_name)
    root = m.SRC.parents[3]
    out_dir = root / f'godot/assets/characters/{m.ID}'
    (out_dir / 'textures').mkdir(parents=True, exist_ok=True)
    img = bpy.data.images.get(f'{m.NAME}_pagina_256.png')
    if img is not None and img.is_dirty:
        img.save()                            # the user's unsaved painting goes out too
    shutil.copyfile(m.SRC / f'{m.NAME}_pagina_256.png', out_dir / 'textures/page.png')
    shutil.copyfile(m.SRC / f'{m.NAME}_rosto_atlas.png', out_dir / 'textures/face.png')
    rig, body = bpy.data.objects[f'{m.NAME}_Rig'], bpy.data.objects[f'{m.NAME}_Body']
    ad = rig.animation_data
    if ad:
        ad.action = None
        for t in ad.nla_tracks:
            t.mute = False
    for pb in rig.pose.bones:
        pb.location, pb.rotation_quaternion, pb.rotation_euler, pb.scale = (0, 0, 0), (1, 0, 0, 0), (0, 0, 0), (1, 1, 1)
    bpy.context.scene.render.fps = 60
    exp = body.copy()
    exp.data = body.data.copy()
    exp.name = exp.data.name = f'{m.ID}_BodyExport'
    bpy.context.scene.collection.objects.link(exp)
    mat = bpy.data.materials.get(f'{m.NAME}_export') or bpy.data.materials.new(f'{m.NAME}_export')
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    o, bsdf, tex = (nt.nodes.new(t) for t in ('ShaderNodeOutputMaterial', 'ShaderNodeBsdfPrincipled', 'ShaderNodeTexImage'))
    tex.image = bpy.data.images.load(str(m.SRC / f'{m.NAME}_pagina_256.png'), check_existing=True)
    tex.interpolation = 'Closest'
    nt.links.new(tex.outputs[0], bsdf.inputs['Base Color'])
    nt.links.new(bsdf.outputs[0], o.inputs[0])
    exp.data.materials.clear()
    exp.data.materials.append(mat)
    for ob in bpy.context.view_layer.objects:
        ob.select_set(False)
    rig.select_set(True)
    exp.select_set(True)
    path = out_dir / f'{m.ID}.glb'
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', use_selection=True, export_yup=True,
                                      export_apply=False, export_animations=True, export_animation_mode='NLA_TRACKS',
                                      export_skins=True, export_materials='EXPORT')
    finally:
        me = exp.data
        bpy.data.objects.remove(exp)
        bpy.data.meshes.remove(me)
    print('exported', path, len(ad.nla_tracks) if ad else 0, 'clips')
    return path


def rest_ok(m, rig, tol=0.02):
    """The rest pose's leg and spine joints are where JOINTS put them (the arms were brought
    down on purpose): a clip baked into the rest would move them."""
    j = joints(m)
    check_pairs = {'thigh_l': 'hip_l', 'shin_l': 'knee_l', 'foot_l': 'ankle_l', 'thigh_r': 'hip_r',
                   'shin_r': 'knee_r', 'foot_r': 'ankle_r', 'head': 'neck_head'}
    bad = {b: round((rig.data.bones[b].head_local - j[k]).length, 3) for b, k in check_pairs.items()
           if b in rig.data.bones and (rig.data.bones[b].head_local - j[k]).length > tol}
    if bad:
        print('rest pose off its joints (m):', bad)
    return not bad


def build(module_name):
    m = importlib.import_module(module_name)
    col = _collection(BODY_COLLECTION.format(m.NAME.upper()))
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    rig = append_rig(m, col)
    model_rig.fit_skeleton(rig, joints(m))
    prune(rig, m.UNUSED_BONES)
    page, atlas = m.SRC / f'{m.NAME}_pagina_256.png', m.SRC / f'{m.NAME}_rosto_atlas.png'
    ob = body(m, col, page, atlas)
    ob.parent = rig
    mod = ob.modifiers.new(name='Armature', type='ARMATURE')
    mod.object = rig
    # the fighter's clips must not play while the rest pose is baked (they would become the rest)
    ad = rig.animation_data
    mutes = {t.name: t.mute for t in ad.nla_tracks} if ad else {}
    if ad:
        ad.action = None
        for t in ad.nla_tracks:
            t.mute = True
    for pb in rig.pose.bones:
        pb.location, pb.rotation_quaternion, pb.rotation_euler, pb.scale = (0, 0, 0), (1, 0, 0, 0), (0, 0, 0), (1, 1, 1)
    bpy.context.view_layer.update()
    model_rig.arms_to_rest(ob, rig)
    for pb in rig.pose.bones:         # arms_to_rest leaves Euler; the clips are keyed in quaternions
        pb.rotation_mode = 'QUATERNION'
    if ad:
        for t in ad.nla_tracks:
            t.mute = mutes.get(t.name, False)
    ok = check(rig, ob) and rest_ok(m, rig)
    return rig, ob, ok
