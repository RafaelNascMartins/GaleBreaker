"""Skeleton of a Legends character (run inside Blender), any character.

    import legends_rig; legends_rig.build('x12_modelo')

The character module gives:
    RIG_SOURCE   (blend path, rig object name): the fighter's rig in the game (same bone names
                 for every fighter, the animations and code IK use them)
    JOINTS       joints in metres, left side (the right mirrors): pelvis, abdomen, chest_top,
                 neck_base, neck_head, head_top, shoulder, elbow, wrist, hand_tip, hip, knee,
                 ankle, toe (model_rig.fit_skeleton)
    UNUSED_BONES bones of the shared rig this fighter doesn't use (removed)
    SOCKET_AT    optional {socket bone: part}: the bone's head moved to the front of that part
                 (the gun's muzzle for `cannon`)
    PROPS        optional {label: [parts]}: props (a thrown bomb) built as their own objects on their
                 bone, exported as <ID>_<label>Prop on the body's page
    OUTFITS      optional {label: outfit module}: outfits with their own pieces, put on the rig by
                 outfit() and exported as <ID>_<label>Body with textures/page_<label>.png and face_<label>.png
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


def prop_parts(m):
    return {n for names in getattr(m, 'PROPS', {}).values() for n in names}


def body(m, col, page, atlas, only=None, name=None):
    """One mesh from the parts: vertices of each part weight 1 on its bone, attribute 'part'.
    The body leaves the props out; only= builds just those parts (a prop) under name=."""
    name = name or f'{m.NAME}_Body'
    old = bpy.data.objects.get(name)
    if old:
        me = old.data
        bpy.data.objects.remove(old)
        bpy.data.meshes.remove(me)
    parts = json.loads((m.SRC / f'{m.NAME}_pecas.json').read_text())
    if only is not None:
        parts = {k: v for k, v in parts.items() if k in only}
    else:
        parts = {k: v for k, v in parts.items() if k not in prop_parts(m)}
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
    extra = []
    for label, om_name in getattr(m, 'OUTFITS', {}).items():   # outfits with their own pieces
        om = importlib.import_module(om_name)
        src = bpy.data.objects.get(f'{om.NAME}_Body')
        if src is None:
            print('outfit body missing, run legends_rig.outfit first:', om.NAME)
            continue
        oimg = bpy.data.images.get(f'{om.NAME}_pagina_256.png')
        if oimg is not None and oimg.is_dirty:
            oimg.save()
        shutil.copyfile(om.SRC / f'{om.NAME}_pagina_256.png', out_dir / f'textures/page_{label.lower()}.png')
        shutil.copyfile(om.SRC / f'{om.NAME}_rosto_atlas.png', out_dir / f'textures/face_{label.lower()}.png')
        e = src.copy()
        e.data = src.data.copy()
        e.name = e.data.name = f'{m.ID}_{label}Body'
        bpy.context.scene.collection.objects.link(e)
        omat = bpy.data.materials.get(f'{om.NAME}_export') or bpy.data.materials.new(f'{om.NAME}_export')
        omat.use_nodes = True
        ont = omat.node_tree
        ont.nodes.clear()
        o2, b2, t2 = (ont.nodes.new(t) for t in ('ShaderNodeOutputMaterial', 'ShaderNodeBsdfPrincipled', 'ShaderNodeTexImage'))
        t2.image = bpy.data.images.load(str(om.SRC / f'{om.NAME}_pagina_256.png'), check_existing=True)
        t2.interpolation = 'Closest'
        ont.links.new(t2.outputs[0], b2.inputs['Base Color'])
        ont.links.new(b2.outputs[0], o2.inputs[0])
        e.data.materials.clear()
        e.data.materials.append(omat)
        extra.append(e)
    for label in getattr(m, 'PROPS', {}):                  # props on the body's page and material
        src = bpy.data.objects.get(f'{m.NAME}_Prop_{label}')
        if src is None:
            continue
        e = src.copy()
        e.data = src.data.copy()
        e.name = e.data.name = f'{m.ID}_{label}Prop'
        bpy.context.scene.collection.objects.link(e)
        e.data.materials.clear()
        e.data.materials.append(mat)
        extra.append(e)
    for ob in bpy.context.view_layer.objects:
        ob.select_set(False)
    # the copies may inherit "not selectable / hidden" from a scene set up for animating
    for e in [rig, exp] + extra:
        e.hide_select = False
        e.hide_viewport = False
        e.hide_set(False)
    rig.select_set(True)
    exp.select_set(True)
    for e in extra:
        e.select_set(True)
    path = out_dir / f'{m.ID}.glb'
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', use_selection=True, export_yup=True,
                                      export_apply=False, export_animations=True, export_animation_mode='NLA_TRACKS',
                                      export_skins=True, export_materials='EXPORT')
    finally:
        for e in [exp] + extra:
            me = e.data
            bpy.data.objects.remove(e)
            bpy.data.meshes.remove(me)
    print('exported', path, len(ad.nla_tracks) if ad else 0, 'clips')
    return path


def bone_moves(m, base):
    """Each bone's rigid move from A-pose to rest, measured on the base body: its A-pose parts (the
    pieces json, props left out) against its rest mesh, a best-fit rotation per bone."""
    import numpy as np
    pj = json.loads((m.SRC / f'{m.NAME}_pecas.json').read_text())
    a_pose = np.array([v for k, p in pj.items() if k not in prop_parts(m) for v in p['v']])
    rest = np.array([tuple(v.co) for v in base.data.vertices])
    moves = {}
    for g in base.vertex_groups:
        idx = [v.index for v in base.data.vertices if any(e.group == g.index for e in v.groups)]
        if len(idx) < 3:
            continue
        A, B = a_pose[idx], rest[idx]
        ca, cb = A.mean(0), B.mean(0)
        U, _, Vt = np.linalg.svd((A - ca).T @ (B - cb))
        d = np.sign(np.linalg.det(Vt.T @ U.T))
        R = Vt.T @ np.diag([1, 1, d]) @ U.T
        moves[g.name] = (R, ca, cb, float(np.abs((A - ca) @ R.T + cb - B).max()))
    return moves


def apply_moves(ob, moves):
    import numpy as np
    co = np.array([tuple(v.co) for v in ob.data.vertices])
    for g in ob.vertex_groups:
        if g.name not in moves:
            print('bone not on the base body (left in A-pose):', g.name)
            continue
        R, ca, cb, _ = moves[g.name]
        idx = [v.index for v in ob.data.vertices if any(e.group == g.index for e in v.groups)]
        co[idx] = (co[idx] - ca) @ R.T + cb
    ob.data.vertices.foreach_set('co', co.ravel())
    ob.data.update()


def props(m, rig, base, col, page, atlas):
    """The character's props (PROPS {label: [parts]}) as <NAME>_Prop_<label> objects on the rig,
    moved to the rest pose like the bones they sit on."""
    moves = bone_moves(m, base)
    out = []
    for label, names in getattr(m, 'PROPS', {}).items():
        ob = body(m, col, page, atlas, only=set(names), name=f'{m.NAME}_Prop_{label}')
        apply_moves(ob, moves)
        ob.parent = rig
        ob.modifiers.new(name='Armature', type='ARMATURE').object = rig
        out.append(ob)
    return out


def outfit(module_name, outfit_module):
    """An outfit with its own pieces (<outfit>_pecas.json, modelled in A-pose on the base's joints)
    as <OUTFIT NAME>_Body on the base rig. Each bone's rigid move from A-pose to rest is measured
    on the base body (its A-pose parts vs its rest mesh, a best-fit rotation per bone) and applied
    to the outfit's vertices on that bone: same skeleton, animations and hitboxes."""
    import numpy as np
    m, om = importlib.import_module(module_name), importlib.import_module(outfit_module)
    rig, base = bpy.data.objects[f'{m.NAME}_Rig'], bpy.data.objects[f'{m.NAME}_Body']
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    moves = bone_moves(m, base)
    col = base.users_collection[0]
    page, atlas = om.SRC / f'{om.NAME}_pagina_256.png', om.SRC / f'{om.NAME}_rosto_atlas.png'
    ob = body(om, col, page, atlas)
    apply_moves(ob, moves)
    ob.parent = rig
    ob.modifiers.new(name='Armature', type='ARMATURE').object = rig
    worst = max(v[3] for v in moves.values())
    print(f'{ob.name}: {len(ob.data.polygons)} faces on {rig.name}; worst rigid-fit error on the base {worst * 1000:.1f} mm')
    return ob, check(rig, ob)


def _part_points(ob, part_name):
    names = list(ob['parts'])
    pi = names.index(part_name)
    faces = [p for p in ob.data.polygons if ob.data.attributes['part'].data[p.index].value == pi]
    return [ob.data.vertices[i].co.copy() for i in {v for p in faces for v in p.vertices}]


def socket_at(rig, ob, bone_name, part_name):
    """Move a socket bone's head (the game reads sockets at bone heads) to the front of a part of
    the rest body: the gun's muzzle for `cannon`. part_name may be (front part, axis part): the bone
    then points from the axis part's middle through the front part (down the barrel); otherwise it
    keeps its direction. Its pose is untouched, so the mesh doesn't move."""
    from mathutils import Vector
    axis_part = None
    if isinstance(part_name, (tuple, list)):
        part_name, axis_part = part_name
    pts = _part_points(ob, part_name)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    eb = rig.data.edit_bones[bone_name]
    d = (eb.tail - eb.head).normalized()
    if axis_part:
        a = _part_points(ob, axis_part)
        d = (sum(pts, Vector()) / len(pts) - sum(a, Vector()) / len(a)).normalized()
    length = eb.length
    far = max(p.dot(d) for p in pts)
    front = [p for p in pts if p.dot(d) > far - 0.01]
    head = sum(front, Vector()) / len(front)
    eb.head = head
    eb.tail = head + d * length
    bpy.ops.object.mode_set(mode='OBJECT')
    print(f'{bone_name} socket at the front of {part_name}:', tuple(round(c, 3) for c in head))


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
    for bone_name, part_name in getattr(m, 'SOCKET_AT', {}).items():
        socket_at(rig, ob, bone_name, part_name)
    ok = check(rig, ob) and rest_ok(m, rig)
    for p in props(m, rig, ob, col, page, atlas):
        ok = check(rig, p) and ok
    return rig, ob, ok
