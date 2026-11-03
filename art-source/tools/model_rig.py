"""Rig a generated character model (art-source/characters/<id>/source/<id>_tripo.glb) to the
fighter skeleton, so it plays the same 27 clips as the procedural fighters.

1. Import and scale the model to the fighter height (front faces -Y, feet at Z = 0).
2. Move the skeleton's joints to the circles of the rig guide (rig_joints.json).
3. Skin by distance to the bones, with soft blends at the joints and the skirt.
4. Bring the A-pose arms down to the skeleton's usual rest pose and apply it as rest.
"""
import json
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
CORE_BONES = ["hips", "spine", "chest", "neck", "head",
              "shoulder_l", "upper_arm_l", "forearm_l", "hand_l", "shoulder_r", "upper_arm_r", "forearm_r", "hand_r",
              "thigh_l", "shin_l", "foot_l", "thigh_r", "shin_r", "foot_r"]
# Rest direction of the upper arm in the procedural skeleton (slightly out from the body).
REST_ARM = {"l": Vector((0.06, 0.0, -0.32)).normalized(), "r": Vector((-0.06, 0.0, -0.32)).normalized()}


def joints(fid, height):
    data = json.loads((ROOT / "art-source" / "characters" / fid / "rig_joints.json").read_text(encoding="utf-8"))
    fi, si = data["front_image"], data["side_image"]
    fs = height / (fi["sole"] - fi["top"])
    ss = height / (si["sole"] - si["top"])
    fcx = (fi["bbox_x"][0] + fi["bbox_x"][1]) / 2
    scx = (si["bbox_x"][0] + si["bbox_x"][1]) / 2
    out = {}
    for name, (px, py) in data["front"].items():
        side_key = name if name in data["side"] else name.rsplit("_", 1)[0]
        y = (data["side"][side_key] - scx) * ss
        out[name] = Vector(((px - fcx) * fs, y, (fi["sole"] - py) * fs))
    return out


def import_model(fid, height):
    path = ROOT / "art-source" / "characters" / fid / "source" / f"{fid}_tripo.glb"
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    new = [o for o in bpy.data.objects if o not in before]
    mesh = next(o for o in new if o.type == "MESH")
    for o in new:
        if o is not mesh:
            bpy.data.objects.remove(o, do_unlink=True)
    mesh.parent = None
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action="DESELECT")
    mesh.select_set(True)
    bpy.context.view_layer.objects.active = mesh
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    zs = [v.co.z for v in mesh.data.vertices]
    scale = height / (max(zs) - min(zs))
    mesh.scale = (scale, scale, scale)
    mesh.location.z = -min(zs) * scale
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    mesh.name = f"{fid}_Body"
    return mesh


def flat_face(mesh, fid):
    """Replace the sculpted eyes, brows and nose with one flat skin patch, then project a second UV
    (FaceUV) from the front so the expression atlas can be drawn over the face in Godot."""
    face = json.loads((ROOT / "art-source" / "characters" / fid / "rig_joints.json").read_text(encoding="utf-8"))["face"]
    half, patch_half, front_y = face["half_width"], face["patch_half_width"], face["front_y"]
    z0, z1 = face["z"]
    bm = bmesh.new()
    bm.from_mesh(mesh.data)
    # The generated mesh is split at every UV seam; weld it so the face hole has one border.
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    uv = bm.loops.layers.uv.active

    def in_face(co):
        return z0 < co.z < z1 and abs(co.x) < patch_half and co.y < front_y

    # Plain skin: the forehead just above the patch.
    forehead = min((f for f in bm.faces if abs(f.calc_center_median().x) < 0.03 and f.calc_center_median().z > z1
                    and f.normal.y < -0.5), key=lambda f: f.calc_center_median().z)
    skin_uv = sum((l[uv].uv for l in forehead.loops), Vector((0, 0))) / len(forehead.loops)

    # Eyes, eye frames and brows are separate pieces laid over the shell: drop every piece that sits
    # entirely inside the face box, then close the holes they leave in the shell.
    parts, seen = [], set()
    for v in bm.verts:
        if v in seen:
            continue
        stack, part = [v], []
        seen.add(v)
        while stack:
            x = stack.pop()
            part.append(x)
            for e in x.link_edges:
                o = e.other_vert(x)
                if o not in seen:
                    seen.add(o)
                    stack.append(o)
        parts.append(part)
    pieces = [p for p in parts if all(in_face(v.co) for v in p)]
    bmesh.ops.delete(bm, geom=[v for p in pieces for v in p], context="VERTS")
    border = [e for e in bm.edges if e.is_boundary and all(in_face(v.co) for v in e.verts)]
    filled = bmesh.ops.holes_fill(bm, edges=border, sides=0)["faces"]
    patch = bmesh.ops.triangulate(bm, faces=filled, quad_method="BEAUTY", ngon_method="BEAUTY")["faces"]

    # Pull the front of the face onto one plane (fitted to the shell's face verts) so expressions
    # read cleanly; the blend fades out toward the cheeks and the jaw.
    face_verts = [v for v in bm.verts if in_face(v.co)]
    plane_y = sum(v.co.y for v in face_verts) / max(len(face_verts), 1)
    for v in face_verts:
        edge = min(1.0, (patch_half - abs(v.co.x)) / 0.03, (v.co.z - z0) / 0.03, (z1 - v.co.z) / 0.03)
        v.co.y += (plane_y - v.co.y) * max(edge, 0.0)
    for f in {f for v in face_verts for f in v.link_faces} | set(patch):
        f.smooth = False

    # Every front face triangle becomes plain skin (the generated texture paints eyes and brows on
    # the shell too); the features come only from the expression atlas.
    face_uv = bm.loops.layers.uv.new("FaceUV")
    flat = bm.faces.layers.int.new("flat_face")
    for f in bm.faces:
        c = f.calc_center_median()
        facing = f.normal.y < -0.2 and c.y < 0 and abs(c.x) < half and c.z > face["decal_bottom"]
        front = facing and c.z < face["decal_bottom"] + 2 * half
        f[flat] = int(facing)
        for l in f.loops:
            p = l.vert.co
            l[face_uv].uv = ((p.x + half) / (2 * half), (p.z - face["decal_bottom"]) / (2 * half)) if front else (-1.0, -1.0)
            if facing:  # the forehead too: the generated texture paints light streaks there
                l[uv].uv = skin_uv
    bm.to_mesh(mesh.data)
    bm.free()
    mesh.data.uv_layers.active_index = 0
    print(f"flat face: {len(patch)} triangles, {len(border)} border edges")


def face_normals(mesh):
    """Point every corner of the face and forehead straight forward so the toon bands never cut
    across them (the head keeps its facets on the top and sides)."""
    me = mesh.data
    flat = me.attributes["flat_face"].data
    normals = [Vector(c.vector) for c in me.corner_normals]
    for poly in me.polygons:
        if flat[poly.index].value:
            for li in poly.loop_indices:
                normals[li] = Vector((0.0, -1.0, 0.0))
    me.normals_split_custom_set(normals)


def fit_skeleton(arm_obj, j):
    """Move the existing bones (names and hierarchy unchanged) onto the guide's joints."""
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm_obj.data.edit_bones

    def place(name, head, tail):
        if name in eb:
            eb[name].use_connect = False
            eb[name].head = head
            eb[name].tail = tail

    chest_mid = j["abdomen"].lerp(j["chest_top"], 0.5)
    place("hips", j["pelvis"], j["abdomen"])
    place("spine", j["abdomen"], chest_mid)
    place("chest", chest_mid, j["neck_base"])
    place("neck", j["neck_base"], j["neck_head"])
    place("head", j["neck_head"], j["head_top"])
    place("hat", j["head_top"] - Vector((0, 0, 0.06)), j["head_top"] + Vector((0, -0.1, 0.02)))
    for s, sx in (("l", 1), ("r", -1)):
        shoulder = j[f"shoulder_{s}"]
        place(f"shoulder_{s}", Vector((sx * 0.05, shoulder.y, shoulder.z)), shoulder)
        place(f"upper_arm_{s}", shoulder, j[f"elbow_{s}"])
        place(f"forearm_{s}", j[f"elbow_{s}"], j[f"wrist_{s}"])
        place(f"hand_{s}", j[f"wrist_{s}"], j[f"hand_tip_{s}"])
        tip = j[f"hand_tip_{s}"]
        for i, digit in enumerate(["index", "middle", "ring", "pinky"]):
            base = j[f"wrist_{s}"].lerp(tip, 0.55) + Vector((sx * (1.5 - i) * 0.012, -0.01, 0))
            place(f"finger_{digit}_{s}", base, base.lerp(tip, 0.9) + Vector((0, 0, -0.01)))
        place(f"finger_thumb_{s}", j[f"wrist_{s}"] + Vector((0, -0.03, -0.02)), j[f"wrist_{s}"] + Vector((sx * 0.01, -0.06, -0.06)))
        place(f"thigh_{s}", j[f"hip_{s}"], j[f"knee_{s}"])
        place(f"shin_{s}", j[f"knee_{s}"], j[f"ankle_{s}"])
        place(f"foot_{s}", j[f"ankle_{s}"], j[f"toe_{s}"])
        place(f"robe_side_{s}", Vector((sx * 0.17, 0.0, j["pelvis"].z)), Vector((sx * 0.26, 0.02, j[f"knee_{s}"].z - 0.05)))
        place(f"wrap_tail_{s}", j[f"wrist_{s}"] + Vector((0, 0, 0.05)), j[f"wrist_{s}"] + Vector((sx * 0.05, -0.05, -0.12)))
    knee_z = j["knee_l"].z
    place("robe_front", Vector((0, -0.1, j["pelvis"].z)), Vector((0, -0.14, knee_z)))
    place("robe_back", Vector((0, 0.1, j["pelvis"].z)), Vector((0, 0.14, knee_z)))
    place("sash", Vector((0.08, -0.12, j["pelvis"].z + 0.04)), Vector((0.1, -0.14, knee_z + 0.15)))
    place("sash_tail", Vector((0, 0.12, j["pelvis"].z + 0.04)), Vector((0.03, 0.16, knee_z + 0.05)))
    wrist = j["wrist_r"]
    place("cannon", wrist, wrist + Vector((0, -0.35, 0)))
    bpy.ops.object.mode_set(mode="OBJECT")


def segment_distance(p, a, b):
    ab = b - a
    t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-9)))
    return (p - (a + ab * t)).length


def skin(mesh, arm_obj, j):
    bones = {b.name: (arm_obj.matrix_world @ b.head_local, arm_obj.matrix_world @ b.tail_local) for b in arm_obj.data.bones if b.name in CORE_BONES}
    groups = {name: mesh.vertex_groups.new(name=name) for name in bones}
    for extra in ("robe_front", "robe_back"):
        groups[extra] = mesh.vertex_groups.new(name=extra)
    pelvis_z = j["pelvis"].z
    hem_z = (j["knee_l"].z + j["knee_r"].z) / 2 - 0.12
    from mathutils import kdtree
    tree = kdtree.KDTree(len(mesh.data.vertices))
    for v in mesh.data.vertices:
        tree.insert(v.co, v.index)
    tree.balance()

    def is_outer_layer(p, bone):
        a, b = bone
        ab = b - a
        t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-9)))
        axis_point = a + ab * t
        inward = axis_point - p
        dist = inward.length
        if dist < 0.05:
            return False
        inward.normalize()
        for step in (0.025, 0.04, 0.055):
            if step >= dist - 0.03:
                break
            if tree.find_range(p + inward * step, 0.012):
                return True
        return False
    for v in mesh.data.vertices:
        p = v.co
        dist = sorted((segment_distance(p, a, b), name) for name, (a, b) in bones.items())
        # Keep the two closest bones; blend them by inverse distance (soft joints).
        (d0, n0), (d1, n1) = dist[0], dist[1]
        w0, w1 = 1.0 / (d0 ** 4 + 1e-9), 1.0 / (d1 ** 4 + 1e-9)
        total = w0 + w1
        weights = {n0: w0 / total, n1: w1 / total}
        # The skirt is an outer layer over the trousers: a vertex is skirt when more surface lies
        # between it and the leg bone. Skirt hangs from the hips and the front/back cloth bones;
        # the trousers keep following the leg, so a kick slips out from under the skirt.
        if hem_z < p.z < pelvis_z and n0.startswith(("thigh", "shin")) and is_outer_layer(p, bones[n0]):
            cloth = "robe_front" if p.y < 0 else "robe_back"
            weights = {"hips": 0.6, cloth: 0.4}
        for name, w in weights.items():
            if w > 0.01:
                groups[name].add([v.index], w, "REPLACE")


def arms_to_rest(mesh, arm_obj):
    """Rotate the A-pose upper arms down, bake that into the mesh and make it the rest pose."""
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="POSE")
    for s in ("l", "r"):
        pb = arm_obj.pose.bones[f"upper_arm_{s}"]
        current = (pb.tail - pb.head).normalized()
        pb.rotation_mode = "QUATERNION"
        world_rot = current.rotation_difference(REST_ARM[s])
        basis = pb.bone.matrix_local.to_3x3()
        local = (basis.inverted() @ world_rot.to_matrix() @ basis).to_quaternion()
        pb.rotation_quaternion = local
    bpy.context.view_layer.update()
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.context.view_layer.objects.active = mesh
    bpy.ops.object.modifier_apply(modifier="Armature")
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="POSE")
    bpy.ops.pose.select_all(action="SELECT")
    bpy.ops.pose.armature_apply(selected=False)
    for pb in arm_obj.pose.bones:
        pb.rotation_mode = "XYZ"
    bpy.ops.object.mode_set(mode="OBJECT")
    mod = mesh.modifiers.new(name="Armature", type="ARMATURE")
    mod.object = arm_obj


def build_model_fighter(fid, arm_obj, material, height):
    j = joints(fid, height)
    mesh = import_model(fid, height)
    flat_face(mesh, fid)
    fit_skeleton(arm_obj, j)
    mesh.data.materials.clear()
    mesh.data.materials.append(material)
    skin(mesh, arm_obj, j)
    mesh.parent = arm_obj
    mod = mesh.modifiers.new(name="Armature", type="ARMATURE")
    mod.object = arm_obj
    arms_to_rest(mesh, arm_obj)
    face_normals(mesh)
    return mesh
