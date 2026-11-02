import bpy
import bmesh
import math
import sys
from mathutils import Vector, Euler, Matrix
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
ART_SRC = ROOT / "art-source"
GODOT = ROOT / "godot"

# UV strip centers for the 8 vertical strips in our 1024x1024 texture:
# 0: skin_base, 1: skin_sunburn, 2: primary, 3: secondary, 4: accent, 5: hair, 6: leather, 7: dark
def zone_u(zone_idx: int) -> float:
    return (zone_idx + 0.5) / 8.0


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps = 60


def make_fighter_material(fighter_id: str):
    mat = bpy.data.materials.new(name=f"{fighter_id}_mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.75
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    tex_dir = GODOT / "assets" / "characters" / fighter_id / "textures"
    albedo_path = tex_dir / "albedo.png"
    normal_path = tex_dir / "normal.png"

    if albedo_path.exists():
        tex_img = nodes.new("ShaderNodeTexImage")
        tex_img.image = bpy.data.images.load(str(albedo_path))
        links.new(tex_img.outputs["Color"], bsdf.inputs["Base Color"])

    if normal_path.exists():
        norm_img = nodes.new("ShaderNodeTexImage")
        norm_img.image = bpy.data.images.load(str(normal_path))
        norm_img.image.colorspace_settings.name = "Non-Color"
        norm_map = nodes.new("ShaderNodeNormalMap")
        links.new(norm_img.outputs["Color"], norm_map.inputs["Color"])
        links.new(norm_map.outputs["Normal"], bsdf.inputs["Normal"])

    return mat


class MeshBuilder:
    def __init__(self):
        self.bm = bmesh.new()
        self.uv_layer = self.bm.loops.layers.uv.new("UVMap")
        self.deform_layer = self.bm.verts.layers.deform.new()
        self.group_map = {}

    def group_index(self, name: str) -> int:
        if name not in self.group_map:
            self.group_map[name] = len(self.group_map)
        return self.group_map[name]

    def _tag_verts(self, verts, bone_name: str, zone_idx: int, bevel_segments: int = 1):
        if bevel_segments > 0 and len(verts) >= 8:
            # Subtle bevel for smoother silhouettes
            edges = list({e for v in verts for e in v.link_edges if e.verts[0] in verts and e.verts[1] in verts})
            try:
                res = bmesh.ops.bevel(
                    self.bm,
                    geom=edges,
                    offset=0.012,
                    segments=bevel_segments,
                    profile=0.5,
                    affect='EDGES'
                )
                verts = [v for v in ( list(verts) + list(res.get("verts", [])) ) if v.is_valid]
            except Exception:
                pass

        g_idx = self.group_index(bone_name)
        u_center = zone_u(zone_idx)
        for v in verts:
            v[self.deform_layer][g_idx] = 1.0
            for loop in v.link_loops:
                # Map U within the zone strip, V along Z height + X wrap
                u_off = ((v.co.x + v.co.y) * 0.15) % 0.06 - 0.03
                v_coord = (v.co.z * 0.45) % 0.9 + 0.05
                loop[self.uv_layer].uv = (u_center + u_off, v_coord)

    def add_box(self, bone: str, zone: int, center, size, rot_deg=(0, 0, 0), taper_top=1.0, bevel=1):
        mat = Euler([math.radians(a) for a in rot_deg], 'XYZ').to_matrix().to_4x4()
        res = bmesh.ops.create_cube(self.bm, size=1.0)
        verts = res["verts"]
        for v in verts:
            v.co.x *= size[0] * (taper_top if v.co.z > 0 else 1.0)
            v.co.y *= size[1] * (taper_top if v.co.z > 0 else 1.0)
            v.co.z *= size[2]
            v.co = (mat @ v.co) + Vector(center)
        self._tag_verts(verts, bone, zone, bevel_segments=bevel)

    def add_limb(self, bone: str, zone: int, p0, p1, r0: float, r1: float, segments=10):
        p0, p1 = Vector(p0), Vector(p1)
        vec = p1 - p0
        length = vec.length
        if length < 0.001:
            return
        mid = (p0 + p1) * 0.5
        rot = Vector((0, 0, 1)).rotation_difference(vec.normalized()).to_matrix().to_4x4()
        res = bmesh.ops.create_cone(
            self.bm,
            cap_ends=True,
            cap_tris=True,
            segments=segments,
            radius1=r0,
            radius2=r1,
            depth=length
        )
        verts = res["verts"]
        for v in verts:
            v.co = (rot @ v.co) + mid
        self._tag_verts(verts, bone, zone, bevel_segments=0)

    def add_sphere(self, bone: str, zone: int, center, scale, segments=12, ring_count=8):
        res = bmesh.ops.create_uvsphere(
            self.bm,
            u_segments=segments,
            v_segments=ring_count,
            radius=1.0
        )
        verts = res["verts"]
        for v in verts:
            v.co.x *= scale[0]
            v.co.y *= scale[1]
            v.co.z *= scale[2]
            v.co += Vector(center)
        self._tag_verts(verts, bone, zone, bevel_segments=0)

    def add_rock(self, bone, zone, center, scale, seed=0):
        import random
        rng = random.Random(seed)
        res=bmesh.ops.create_icosphere(self.bm,subdivisions=1,radius=1.0)
        for vert in res['verts']:
            radius=rng.uniform(.88,1.12)
            vert.co=Vector((vert.co.x*scale[0]*radius,vert.co.y*scale[1]*radius,vert.co.z*scale[2]*radius))+Vector(center)
        self._tag_verts(res['verts'],bone,zone,bevel_segments=0)

    def build_object(self, name: str, arm_obj, material):
        bmesh.ops.triangulate(self.bm, faces=self.bm.faces)
        mesh = bpy.data.meshes.new(name + "_Mesh")
        self.bm.to_mesh(mesh)
        self.bm.free()

        for poly in mesh.polygons:
            poly.use_smooth = True

        obj = bpy.data.objects.new(name, mesh)
        bpy.context.collection.objects.link(obj)

        # Create vertex groups matching group_map order
        inv_map = {idx: gname for gname, idx in self.group_map.items()}
        for idx in range(len(inv_map)):
            obj.vertex_groups.new(name=inv_map[idx])

        obj.data.materials.append(material)
        obj.parent = arm_obj
        mod = obj.modifiers.new(name="Armature", type='ARMATURE')
        mod.object = arm_obj
        return obj


def create_humanoid_armature(fighter_id: str, scale_cfg: dict):
    arm_data = bpy.data.armatures.new(f"{fighter_id}_Armature")
    arm_obj = bpy.data.objects.new(f"{fighter_id}_Rig", arm_data)
    bpy.context.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')

    eb = arm_data.edit_bones
    h = scale_cfg.get("height", 1.85)
    w = scale_cfg.get("shoulder_w", 0.24)
    hip_w = scale_cfg.get("hip_w", 0.13)
    hunch = scale_cfg.get("hunch", 0.0)

    def add_bone(name, head, tail, parent=None):
        b = eb.new(name)
        b.head = Vector(head)
        b.tail = Vector(tail)
        if parent:
            b.parent = eb[parent]
        return b

    # Root at ground center, facing -Y in Blender (+Z in Godot)
    add_bone("root", (0, 0, 0), (0, -0.2, 0))
    add_bone("hips", (0, 0, h * 0.50), (0, 0, h * 0.58), "root")
    add_bone("spine", (0, 0, h * 0.58), (0, -hunch * 0.4, h * 0.70), "hips")
    add_bone("chest", (0, -hunch * 0.4, h * 0.70), (0, -hunch, h * 0.83), "spine")
    add_bone("neck", (0, -hunch, h * 0.83), (0, -hunch * 1.2, h * 0.88), "chest")
    add_bone("head", (0, -hunch * 1.2, h * 0.88), (0, -hunch * 1.2, h * 1.0), "neck")
    add_bone("hat", (0, -hunch * 1.2, h * 0.96), (0, -hunch * 1.2 - 0.12, h * 1.03), "head")

    # Auxiliary tunic/sash bones
    add_bone("robe_front", (0, -0.10, h * 0.52), (0, -0.13, h * 0.25), "hips")
    add_bone("robe_back", (0, 0.10, h * 0.52), (0, 0.13, h * 0.25), "hips")
    add_bone("sash", (-hip_w - 0.04, -0.06, h * 0.52), (-hip_w - 0.08, -0.08, h * 0.28), "hips")
    if fighter_id == "kaze":
        # Loose cloth that trails behind the monk: side robe panels and the sash tail.
        for side_name, sx in [("l", 1.0), ("r", -1.0)]:
            add_bone(f"robe_side_{side_name}", (sx * (hip_w + 0.07), 0.0, h * 0.52), (sx * (hip_w + 0.16), 0.02, h * 0.17), "hips")
        add_bone("sash_tail", (0.0, 0.14, h * 0.53), (0.04, 0.25, h * 0.22), "hips")

    for side_name, sx in [("l", 1.0), ("r", -1.0)]:
        sh_x = sx * w
        el_x = sx * (w + 0.06)
        wr_x = sx * (w + 0.08)
        sh_z = h * 0.80
        el_z = h * 0.63
        wr_z = h * 0.47

        add_bone(f"shoulder_{side_name}", (sx * 0.08, -hunch, sh_z), (sh_x, -hunch, sh_z), "chest")
        add_bone(f"upper_arm_{side_name}", (sh_x, -hunch, sh_z), (el_x, -hunch * 0.5, el_z), f"shoulder_{side_name}")
        add_bone(f"forearm_{side_name}", (el_x, -hunch * 0.5, el_z), (wr_x, -hunch * 0.8 - 0.05, wr_z), f"upper_arm_{side_name}")
        add_bone(f"hand_{side_name}", (wr_x, -hunch * 0.8 - 0.05, wr_z), (wr_x, -hunch * 0.8 - 0.12, wr_z - 0.08), f"forearm_{side_name}")
        if fighter_id == "kaze":
            add_bone(f"wrap_tail_{side_name}", (wr_x, -hunch * 0.8 - 0.05, wr_z + 0.05), (wr_x + sx * 0.05, -0.13, wr_z - 0.15), f"forearm_{side_name}")

        # Separate digit bones allow open palms and Tophia's V-sign.
        palm_z=.84 if fighter_id in ['kaze','volt'] else .83 if fighter_id=='tophia' else .78
        spacing=.016 if fighter_id=='kaze' else .030
        finger_z=palm_z-(.025 if fighter_id=='kaze' else .04)
        for index,digit in enumerate(['index','middle','ring','pinky']):
            fx=wr_x+sx*(1.5-index)*spacing
            length=.075 if fighter_id=='kaze' else .09
            add_bone(f'finger_{digit}_{side_name}',(fx,-.09,finger_z),(fx,-.09,finger_z-length),f'hand_{side_name}')
        add_bone(f'finger_thumb_{side_name}',(wr_x+sx*.028,-.08,palm_z+.01),(wr_x+sx*.055,-.09,palm_z-.025),f'hand_{side_name}')

        lx = sx * hip_w
        add_bone(f"thigh_{side_name}", (lx, 0, h * 0.50), (lx * 1.05, -0.02, h * 0.27), "hips")
        add_bone(f"shin_{side_name}", (lx * 1.05, -0.02, h * 0.27), (lx * 1.05, 0.0, h * 0.05), f"thigh_{side_name}")
        add_bone(f"foot_{side_name}", (lx * 1.05, 0.0, h * 0.05), (lx * 1.05, -0.18, h * 0.02), f"shin_{side_name}")

    # Handheld cannon bone for Volt (and right-hand weapon socket)
    wr_r = (-w - 0.08, -hunch * 0.8 - 0.05, h * 0.47)
    add_bone("cannon", wr_r, (wr_r[0], wr_r[1] - 0.35, wr_r[2]), "hand_r")

    bpy.ops.object.mode_set(mode='OBJECT')
    return arm_obj


def build_kaze_mesh(mb: MeshBuilder):
    # V2 Kaze (menu-pausa-v2): tall bald monk, sleeveless layered jade robe with flowing panels, jade beads with tassel,
    # wide baggy trousers, wrist wraps and crisscross ankle wraps, barefoot.
    h = 1.90
    # Torso & sleeveless jade monk vest (Zone 2 primary jade, Zone 3 light jade lapel)
    mb.add_limb("hips", 2, (0, 0, 0.88), (0, 0, 1.08), 0.17, 0.16, 12)
    mb.add_limb("spine", 2, (0, 0, 1.06), (0, 0, 1.32), 0.16, 0.20, 12)
    mb.add_limb("chest", 2, (0, 0, 1.30), (0, 0, 1.56), 0.20, 0.23, 12)
    # Crossed monk lapels (Zone 3) and exposed muscular upper chest V-neck (Zone 0 skin)
    mb.add_box("chest", 3, (0.04, -0.14, 1.43), (0.26, 0.12, 0.28), rot_deg=(0, 12, 0))
    mb.add_box("chest", 3, (-0.05, -0.155, 1.40), (0.20, 0.07, 0.30), rot_deg=(0, -16, 0))
    mb.add_box("chest", 0, (0, -0.15, 1.52), (0.12, 0.10, 0.13))
    # Waist sash (Zone 6) with darker leather belt knot
    mb.add_limb("hips", 6, (0, 0, 0.95), (0, 0, 1.04), 0.185, 0.185, 12)
    # Layered lower robe: long front panels, side panels that flare outward, back panel and trailing sash.
    mb.add_box("robe_front", 2, (0, -0.145, 0.64), (0.30, 0.05, 0.62), taper_top=0.85)
    mb.add_box("robe_front", 3, (0.03, -0.165, 0.60), (0.16, 0.04, 0.58), taper_top=0.8)
    mb.add_box("robe_front", 3, (-0.07, -0.158, 0.55), (0.10, 0.035, 0.50), taper_top=0.8)
    mb.add_box("robe_front", 6, (0.0, -0.172, 0.34), (0.30, 0.045, 0.035))  # hem trim
    mb.add_box("robe_back", 2, (0, 0.14, 0.64), (0.32, 0.05, 0.62), taper_top=0.85)
    for side_name, sx in [("l", 1.0), ("r", -1.0)]:
        mb.add_box(f"robe_side_{side_name}", 2, (sx * 0.215, -0.01, 0.66), (0.05, 0.24, 0.58), rot_deg=(0, sx * 9, 0), taper_top=0.8)
        mb.add_box(f"robe_side_{side_name}", 3, (sx * 0.235, -0.02, 0.60), (0.04, 0.20, 0.46), rot_deg=(0, sx * 11, 0), taper_top=0.75)
        mb.add_box(f"robe_side_{side_name}", 6, (sx * 0.255, -0.02, 0.36), (0.04, 0.22, 0.03), rot_deg=(0, sx * 12, 0))
    mb.add_box("sash_tail", 3, (0.02, 0.19, 0.74), (0.09, 0.03, 0.46), rot_deg=(8, 0, 0), taper_top=0.9)
    mb.add_box("sash_tail", 6, (0.02, 0.215, 0.50), (0.09, 0.03, 0.04))
    # Jade prayer beads hanging on the right hip (`sash` bone, Zone 4 accent), pendant and tassel
    for i in range(9):
        mb.add_sphere("sash", 4, (-0.17 - i * 0.008, -0.085, 0.94 - i * 0.055), (0.034, 0.034, 0.034), 8, 6)
    mb.add_sphere("sash", 4, (-0.245, -0.09, 0.43), (0.05, 0.03, 0.06), 8, 6)
    mb.add_box("sash", 3, (-0.245, -0.09, 0.30), (0.035, 0.035, 0.16), taper_top=1.3)

    # Bald monk head & neck (Zone 0 skin, NO hair/headband!)
    mb.add_limb("neck", 0, (0, 0, 1.55), (0, 0, 1.66), 0.075, 0.07, 10)
    mb.add_sphere("head", 0, (0, -0.01, 1.77), (0.115, 0.135, 0.145), 14, 10)
    # Subtle ears, nose, brow & eyes
    mb.add_box("head", 0, (0, -0.14, 1.76), (0.035, 0.04, 0.05))
    for sx in (-1.0, 1.0):
        mb.add_sphere("head", 0, (sx * 0.115, 0.0, 1.76), (0.022, 0.035, 0.045), 8, 6)

    # Muscular bare arms + jade wrist wraps with trailing tails + barefoot legs
    for side_name, sx in [("l", 1.0), ("r", -1.0)]:
        sh_x = sx * 0.24
        el_x = sx * 0.30
        wr_x = sx * 0.32
        mb.add_sphere(f"shoulder_{side_name}", 0, (sh_x, 0, 1.50), (0.10, 0.10, 0.10), 10, 8)
        mb.add_limb(f"upper_arm_{side_name}", 0, (sh_x, 0, 1.50), (el_x, 0, 1.20), 0.09, 0.072, 10)
        mb.add_limb(f"forearm_{side_name}", 0, (el_x, 0, 1.20), (wr_x, -0.03, 1.02), 0.072, 0.060, 10)
        # Jade wrist wraps (Zone 6) with a light trailing tail on the `wrap_tail` bone
        mb.add_limb(f"forearm_{side_name}", 6, (wr_x, -0.03, 1.05), (wr_x, -0.05, 0.90), 0.070, 0.060, 10)
        mb.add_box(f"wrap_tail_{side_name}", 3, (wr_x + sx * 0.05, -0.10, 0.80), (0.035, 0.015, 0.20), rot_deg=(0, sx * 10, 0), taper_top=1.2)
        # Open monk palm / hand (Zone 0 skin)
        mb.add_box(f"hand_{side_name}", 0, (wr_x, -0.08, 0.84), (0.05, 0.09, 0.11))

        # Wide baggy trousers (Zone 2): billowing thighs, gathered at the ankle
        lx = sx * 0.13
        mb.add_limb(f"thigh_{side_name}", 2, (lx, 0, 0.94), (lx * 1.05, -0.02, 0.50), 0.155, 0.185, 10)
        mb.add_limb(f"shin_{side_name}", 2, (lx * 1.05, -0.02, 0.52), (lx * 1.05, 0, 0.26), 0.18, 0.125, 10)
        # Crisscross ankle wraps (Zone 6 leather + Zone 3 light bands)
        mb.add_limb(f"shin_{side_name}", 6, (lx * 1.05, 0, 0.26), (lx * 1.05, 0, 0.09), 0.078, 0.064, 10)
        for k in range(3):
            mb.add_limb(f"shin_{side_name}", 3, (lx * 1.05 - 0.07, -0.01, 0.12 + k * 0.045), (lx * 1.05 + 0.07, -0.01, 0.145 + k * 0.045), 0.012, 0.012, 6)
        # Barefoot feet (Zone 0 skin!)
        mb.add_box(f"foot_{side_name}", 0, (lx * 1.05, -0.08, 0.045), (0.095, 0.22, 0.065), taper_top=0.85)


def build_ignis_mesh(mb: MeshBuilder):
    # V2 Ignis: Massive hunched country cowboy, brown cowboy hat, shirtless with the whole upper body SUNBURNT pink-red (Zone 1), blue jeans (Zone 2), brown boots (Zone 6).
    # Broad shirtless torso: pale chest/belly (Zone 0) + sunburned upper back/traps (Zone 1)
    mb.add_limb("hips", 2, (0, 0, 0.88), (0, 0, 1.06), 0.24, 0.23, 12)
    # Leather belt + brass buckle (Zone 6 & Zone 4)
    mb.add_limb("hips", 6, (0, 0, 0.96), (0, 0, 1.04), 0.248, 0.248, 12)
    mb.add_box("hips", 4, (0, -0.24, 1.00), (0.11, 0.05, 0.08))

    # Sunburnt belly & chest (Zone 1), same pink-red as head and arms (menu-pausa-v2)
    mb.add_limb("spine", 1, (0, -0.03, 1.04), (0, -0.07, 1.34), 0.26, 0.31, 12)
    mb.add_limb("chest", 1, (0, -0.07, 1.32), (0, -0.14, 1.60), 0.30, 0.34, 12)
    mb.add_box("chest", 1, (-0.12, -0.25, 1.44), (0.20, 0.15, 0.18))
    mb.add_box("chest", 1, (0.12, -0.25, 1.44), (0.20, 0.15, 0.18))
    # Sunburned upper traps/hunched shoulders (Zone 1)
    mb.add_sphere("chest", 1, (0, -0.06, 1.62), (0.32, 0.24, 0.16), 12, 8)

    # Sunburned head (Zone 1) + full brown beard (Zone 5) + Cowboy Hat (`hat` bone, Zone 3)
    mb.add_limb("neck", 1, (0, -0.14, 1.56), (0, -0.19, 1.68), 0.11, 0.10, 10)
    mb.add_sphere("head", 1, (0, -0.20, 1.76), (0.13, 0.14, 0.14), 12, 10)
    # Beard & mustache (Zone 5)
    mb.add_sphere("head", 5, (0, -0.24, 1.68), (0.142, 0.14, 0.12), 10, 8)
    for sx in (-1.0, 1.0):
        mb.add_box("head", 5, (sx * 0.05, -0.32, 1.78), (0.05, 0.03, 0.018))
    # Cowboy Hat (`hat` bone: wide curved brim + pinched crown + leather band)
    mb.add_limb("hat", 3, (0, -0.20, 1.84), (0, -0.20, 1.87), 0.29, 0.27, 16)
    mb.add_box("hat", 3, (-0.22, -0.20, 1.88), (0.08, 0.42, 0.04), rot_deg=(0, 22, 0))
    mb.add_box("hat", 3, (0.22, -0.20, 1.88), (0.08, 0.42, 0.04), rot_deg=(0, -22, 0))
    mb.add_limb("hat", 6, (0, -0.20, 1.86), (0, -0.20, 1.90), 0.148, 0.145, 12)
    mb.add_limb("hat", 3, (0, -0.20, 1.86), (0, -0.20, 2.02), 0.142, 0.11, 12)

    # Massive SUNBURNED shoulders, biceps, forearms &rawler fists (Zone 1 `skin_sunburn`!)
    for side_name, sx in [("l", 1.0), ("r", -1.0)]:
        sh_x = sx * 0.33
        el_x = sx * 0.40
        wr_x = sx * 0.42
        mb.add_sphere(f"shoulder_{side_name}", 1, (sh_x, -0.12, 1.54), (0.19, 0.17, 0.17), 12, 8)
        mb.add_limb(f"upper_arm_{side_name}", 1, (sh_x, -0.12, 1.54), (el_x, -0.08, 1.20), 0.16, 0.13, 10)
        mb.add_limb(f"forearm_{side_name}", 1, (el_x, -0.08, 1.20), (wr_x, -0.14, 0.88), 0.135, 0.105, 10)
        mb.add_box(f"hand_{side_name}", 1, (wr_x, -0.16, 0.78), (0.14, 0.15, 0.16))

        # Worn blue denim jeans (Zone 2) + brown work boots (Zone 6)
        lx = sx * 0.16
        mb.add_limb(f"thigh_{side_name}", 2, (lx, 0, 0.94), (lx * 1.06, -0.02, 0.50), 0.17, 0.145, 10)
        mb.add_limb(f"shin_{side_name}", 2, (lx * 1.06, -0.02, 0.52), (lx * 1.06, 0, 0.14), 0.145, 0.15, 10)
        mb.add_box(f"foot_{side_name}", 6, (lx * 1.06, -0.09, 0.07), (0.14, 0.27, 0.13), taper_top=0.88)


def build_tophia_mesh(mb: MeshBuilder):
    # V4/V5 Tophia: Full chunky orange sandstone knight armor (Zone 2 & Zone 3), only head exposed (Zone 0) with short straight black hair (Zone 5). Rigid armor segments!
    # Stone cuirass, gorget collar & waist tassets
    mb.add_box("hips", 2, (0, 0, 0.92), (0.34, 0.25, 0.18), taper_top=0.9)
    mb.add_box("spine", 3, (0, 0, 1.12), (0.28, 0.22, 0.20))
    mb.add_box("chest", 2, (0, -0.02, 1.36), (0.40, 0.30, 0.28), taper_top=1.12)
    mb.add_box("chest", 2, (0, -0.15, 1.37), (0.30, 0.12, 0.22), rot_deg=(8, 0, 0))
    # High stone knight gorget around neck (Zone 2)
    mb.add_limb("chest", 2, (0, -0.01, 1.48), (0, -0.01, 1.60), 0.16, 0.18, 8)
    # Stone waist tassets (`robe_front`, `robe_back`, Zone 2 & 3)
    mb.add_box("robe_front", 2, (0, -0.15, 0.76), (0.20, 0.07, 0.28), taper_top=1.2)
    mb.add_box("robe_back", 2, (0, 0.14, 0.76), (0.26, 0.07, 0.28), taper_top=1.2)

    # Exposed head (Zone 0 skin) + short straight black hair (Zone 5)
    mb.add_limb("neck", 0, (0, 0, 1.50), (0, 0, 1.62), 0.068, 0.065, 8)
    mb.add_sphere("head", 0, (0, -0.01, 1.71), (0.11, 0.125, 0.13), 12, 10)
    # Short straight black hair locks framing face
    mb.add_sphere("head", 5, (0, 0.01, 1.75), (0.122, 0.135, 0.115), 12, 8)
    for sx in (-1.0, 1.0):
        mb.add_box("head", 5, (sx * 0.095, -0.05, 1.71), (0.04, 0.09, 0.13), rot_deg=(0, sx * 10, 0))

    # Faceted sandstone pauldrons, gauntlets, thigh plates, greaves & stone boots
    for side_name, sx in [("l", 1.0), ("r", -1.0)]:
        sh_x = sx * 0.25
        el_x = sx * 0.31
        wr_x = sx * 0.33
        mb.add_box(f"shoulder_{side_name}", 2, (sh_x, 0, 1.47), (0.19, 0.21, 0.18), rot_deg=(0, sx * -15, 0))
        mb.add_box(f"upper_arm_{side_name}", 3, (sh_x * 1.08, 0, 1.28), (0.14, 0.14, 0.24))
        mb.add_box(f"forearm_{side_name}", 2, (el_x, -0.03, 1.02), (0.17, 0.18, 0.28), taper_top=0.82)
        mb.add_box(f"hand_{side_name}", 2, (wr_x, -0.06, 0.83), (0.15, 0.16, 0.10))

        lx = sx * 0.14
        mb.add_box(f"thigh_{side_name}", 2, (lx * 1.05, -0.01, 0.72), (0.22, 0.23, 0.38), taper_top=1.12)
        mb.add_box(f"shin_{side_name}", 2, (lx * 1.08, -0.01, 0.32), (0.20, 0.22, 0.38), taper_top=0.85)
        mb.add_box(f"foot_{side_name}", 2, (lx * 1.08, -0.09, 0.075), (0.16, 0.28, 0.14), taper_top=0.82)


def build_volt_mesh(mb: MeshBuilder):
    # V4/V5 Volt: Young inventor with singed blond hair (Zone 5), asymmetrical scrap armor (Zone 2 yellow, Zone 3 blue-grey), cyan chest core & back battery canister (Zone 4), handheld scrap cannon (`cannon` bone)!
    mb.add_limb("hips", 3, (0, 0, 0.88), (0, 0, 1.05), 0.17, 0.16, 10)
    mb.add_limb("hips", 6, (0, 0, 0.95), (0, 0, 1.02), 0.18, 0.18, 10)
    # Red waist rag (`robe_front`, Zone 7)
    mb.add_box("robe_front", 7, (0.04, -0.14, 0.75), (0.12, 0.04, 0.32), taper_top=0.8)

    mb.add_limb("spine", 6, (0, 0, 1.04), (0, 0, 1.28), 0.15, 0.18, 10)
    mb.add_box("chest", 2, (0, -0.01, 1.38), (0.34, 0.24, 0.26))
    # Glowing cyan circular chest core (Zone 4 accent)
    mb.add_sphere("chest", 4, (0.02, -0.14, 1.38), (0.055, 0.03, 0.055), 10, 8)
    # Vertical cyan battery canister on back (Zone 4 accent + Zone 6 caps)
    mb.add_limb("chest", 4, (0, 0.17, 1.24), (0, 0.17, 1.52), 0.065, 0.065, 10)
    mb.add_box("chest", 6, (0, 0.17, 1.54), (0.15, 0.12, 0.05))
    mb.add_box("chest", 6, (0, 0.17, 1.22), (0.15, 0.12, 0.05))

    # Head + spiky messy blond hair with singed dark tips (Zone 5)
    mb.add_limb("neck", 0, (0, 0, 1.50), (0, 0, 1.62), 0.068, 0.065, 8)
    mb.add_sphere("head", 0, (0, -0.01, 1.71), (0.11, 0.125, 0.13), 12, 10)
    # Blond locks and singed tips are built by character_polish.

    # Asymmetrical scrap pauldrons, bare upper arms, scrap bracers, patched cargo pants & boots
    for side_name, sx in [("l", 1.0), ("r", -1.0)]:
        sh_x = sx * 0.23
        el_x = sx * 0.29
        wr_x = sx * 0.31
        p_zone = 2 if side_name == "l" else 3
        mb.add_box(f"shoulder_{side_name}", p_zone, (sh_x, 0, 1.46), (0.16, 0.18, 0.14), rot_deg=(0, sx * -12, 0))
        mb.add_limb(f"upper_arm_{side_name}", 0, (sh_x, 0, 1.44), (el_x, 0, 1.18), 0.072, 0.062, 10)
        mb.add_box(f"forearm_{side_name}", 3, (el_x, -0.03, 1.02), (0.11, 0.12, 0.22))
        mb.add_box(f"hand_{side_name}", 6, (wr_x, -0.06, 0.84), (0.08, 0.09, 0.10))

        lx = sx * 0.13
        mb.add_limb(f"thigh_{side_name}", 3, (lx, 0, 0.92), (lx * 1.05, -0.02, 0.50), 0.125, 0.11, 10)
        # Knee pad (Zone 2 / Zone 4)
        mb.add_box(f"shin_{side_name}", 2, (lx * 1.05, -0.10, 0.48), (0.12, 0.08, 0.14))
        mb.add_limb(f"shin_{side_name}", 3, (lx * 1.05, -0.01, 0.48), (lx * 1.05, 0, 0.14), 0.105, 0.095, 10)
        mb.add_box(f"foot_{side_name}", 2, (lx * 1.05, -0.08, 0.07), (0.12, 0.25, 0.13), taper_top=0.85)

    # HANDHELD SCRAP CANNON (`cannon` bone parented to `hand_r` at (-0.31, -0.05, 0.87))
    cx, cy, cz = -0.31, -0.18, 0.87
    # Rear grip & housing (Zone 6 & Zone 2)
    mb.add_box("cannon", 6, (cx, cy + 0.10, cz - 0.08), (0.07, 0.09, 0.16), rot_deg=(18, 0, 0))
    mb.add_box("cannon", 2, (cx, cy + 0.04, cz + 0.02), (0.15, 0.22, 0.16))
    # Glowing cyan plasma chamber in middle of cannon (Zone 4 accent!)
    mb.add_limb("cannon", 4, (cx, cy - 0.06, cz + 0.02), (cx, cy - 0.22, cz + 0.02), 0.068, 0.068, 10)
    # Heavy yellow/blue scrap barrel & muzzle ring (Zone 2 & Zone 3)
    mb.add_limb("cannon", 2, (cx, cy - 0.20, cz + 0.02), (cx, cy - 0.38, cz + 0.02), 0.085, 0.082, 12)
    mb.add_limb("cannon", 4, (cx, cy - 0.38, cz + 0.02), (cx, cy - 0.41, cz + 0.02), 0.072, 0.072, 12)


def animate_fighter(arm_obj, fighter_id: str):
    """Creates all 27 required in-place combat & movement animations with character-specific GDD v0.9 attack poses."""
    arm_obj.animation_data_create()
    pb = arm_obj.pose.bones
    clip_context = {'name':'idle'}
    for b in pb:
        b.rotation_mode = 'XYZ'

    def reset_pose():
        for b in pb:
            b.location = (0, 0, 0)
            b.rotation_euler = (0, 0, 0)
            b.scale = (1, 1, 1)

    def set_rot(bname: str, rx=0.0, ry=0.0, rz=0.0):
        if bname in pb:
            # Author poses in character space, then conjugate into the bone's rest
            # basis. A humanoid's local Y runs along each bone, not world Y.
            joint = bname.startswith(('upper_arm_', 'forearm_', 'hand_', 'thigh_', 'shin_'))
            rot = Euler((math.radians(-rx if joint else rx), math.radians(ry), math.radians(rz)), 'XYZ').to_matrix()
            basis = pb[bname].bone.matrix_local.to_3x3()
            pb[bname].rotation_euler = (basis.inverted() @ rot @ basis).to_euler('XYZ')

    def set_loc(bname: str, x=0.0, y=0.0, z=0.0):
        if bname in pb:
            pb[bname].location = pb[bname].bone.matrix_local.to_3x3().inverted() @ Vector((x,y,z))

    def key_all(frame: int):
        from character_polish import finalize_pose
        finalize_pose(arm_obj, fighter_id, clip_context['name'], frame)
        for b in pb:
            b.keyframe_insert(data_path="location", frame=frame)
            b.keyframe_insert(data_path="rotation_euler", frame=frame)

    def apply_base_stance():
        reset_pose()
        if fighter_id == "kaze":
            # Upright disciplined monk stance, front palm raised
            set_rot("chest", 4, 0, -10)
            set_rot("upper_arm_l", 35, 15, -15)
            set_rot("forearm_l", 55, 0, 0)
            set_rot("upper_arm_r", -15, -15, 10)
            set_rot("forearm_r", 70, 0, 0)
            set_rot("thigh_l", 12, 0, 0)
            set_rot("shin_l", -14, 0, 0)
            set_rot("thigh_r", -10, 0, 0)
            set_rot("shin_r", -10, 0, 0)
        elif fighter_id == "ignis":
            # Heavy hunched cowboy brawler guard
            set_rot("spine", 12, 0, 0)
            set_rot("chest", 14, 0, -8)
            set_rot("head", -16, 0, 8)
            set_rot("upper_arm_l", 40, 20, -20)
            set_rot("forearm_l", 75, 0, 0)
            set_rot("upper_arm_r", 32, -20, 20)
            set_rot("forearm_r", 75, 0, 0)
            set_rot("thigh_l", 18, 0, -6)
            set_rot("shin_l", -20, 0, 0)
            set_rot("thigh_r", -14, 0, 6)
            set_rot("shin_r", -16, 0, 0)
        elif fighter_id == "tophia":
            # Grounded martial stone knight stance
            set_rot("chest", 6, 0, -12)
            set_rot("upper_arm_l", 30, 18, -18)
            set_rot("forearm_l", 65, 0, 0)
            set_rot("upper_arm_r", 20, -18, 18)
            set_rot("forearm_r", 60, 0, 0)
            set_rot("thigh_l", 20, 0, -8)
            set_rot("shin_l", -22, 0, 0)
            set_rot("thigh_r", -16, 0, 8)
            set_rot("shin_r", -18, 0, 0)
        else:  # volt
            # Agile crouched scrap-gunner stance aiming handheld cannon forward
            set_rot("spine", 10, 0, 0)
            set_rot("chest", 8, 0, 10)
            set_rot("upper_arm_r", 55, -10, 10)
            set_rot("forearm_r", 35, 0, 0)
            set_rot("upper_arm_l", 25, 18, -15)
            set_rot("forearm_l", 50, 0, 0)
            set_rot("thigh_l", 22, 0, -6)
            set_rot("shin_l", -24, 0, 0)
            set_rot("thigh_r", -18, 0, 6)
            set_rot("shin_r", -20, 0, 0)

    def make_clip(name: str, end_frame: int, builder_fn):
        clip_context['name'] = name
        act = bpy.data.actions.new(name=name)
        act.use_fake_user = True
        arm_obj.animation_data.action = act
        builder_fn()
        if hasattr(arm_obj.animation_data, "action_slot") and len(act.slots) > 0:
            arm_obj.animation_data.action_slot = act.slots[0]
        track = arm_obj.animation_data.nla_tracks.new()
        track.name = name
        strip = track.strips.new(name, 0, act)
        strip.frame_start = 0
        strip.frame_end = end_frame
        if hasattr(strip, "action_slot") and len(act.slots) > 0:
            strip.action_slot = act.slots[0]
        track.mute = False

    # 1. idle (frames 0..40)
    def build_idle():
        apply_base_stance()
        key_all(0)
        apply_base_stance()
        set_loc("hips", 0, 0, -0.03)
        set_rot("robe_front", 6, 0, 0)
        set_rot("sash", 0, 8, 0)
        key_all(20)
        apply_base_stance()
        key_all(40)
    make_clip("idle", 40, build_idle)

    # 2. walk_forward & walk_back (frames 0..24)
    for wname, dir_sign in [("walk_forward", 1.0), ("walk_back", -1.0)]:
        def build_walk(s=dir_sign):
            for f, ph in [(0, 0.0), (6, math.pi * 0.5), (12, math.pi), (18, math.pi * 1.5), (24, math.pi * 2.0)]:
                apply_base_stance()
                sw = math.sin(ph) * 28.0 * s
                set_rot("thigh_l", sw, 0, 0)
                set_rot("shin_l", -abs(sw) * 0.6, 0, 0)
                set_rot("thigh_r", -sw, 0, 0)
                set_rot("shin_r", -abs(sw) * 0.6, 0, 0)
                set_rot("upper_arm_l", 30 - sw * 0.5, 12, -12)
                set_rot("upper_arm_r", 30 + sw * 0.5, -12, 12)
                set_loc("hips", 0, 0, abs(math.cos(ph)) * 0.03)
                key_all(f)
        make_clip(wname, 24, build_walk)

    # 3. crouch, jump_start, jump_air, jump_land, dash
    def build_crouch():
        apply_base_stance()
        set_loc("hips", 0, 0, -0.32)
        set_rot("thigh_l", 55, 0, -10)
        set_rot("shin_l", -65, 0, 0)
        set_rot("thigh_r", 50, 0, 10)
        set_rot("shin_r", -60, 0, 0)
        set_rot("spine", 18, 0, 0)
        key_all(0)
        key_all(10)
    make_clip("crouch", 10, build_crouch)

    def build_jump_start():
        apply_base_stance()
        set_loc("hips", 0, 0, -0.22)
        key_all(0)
        apply_base_stance()
        set_loc("hips", 0, 0, 0.08)
        set_rot("thigh_l", -20, 0, 0)
        set_rot("thigh_r", 25, 0, 0)
        key_all(8)
    make_clip("jump_start", 8, build_jump_start)

    def build_jump_air():
        apply_base_stance()
        set_rot("thigh_l", 38, 0, 0)
        set_rot("shin_l", -45, 0, 0)
        set_rot("thigh_r", -18, 0, 0)
        set_rot("shin_r", -30, 0, 0)
        set_rot("upper_arm_l", 50, 20, -25)
        set_rot("upper_arm_r", 45, -20, 25)
        key_all(0)
        key_all(16)
    make_clip("jump_air", 16, build_jump_air)

    def build_jump_land():
        build_crouch()
        apply_base_stance()
        key_all(8)
    make_clip("jump_land", 8, build_jump_land)

    def build_dash():
        apply_base_stance()
        set_rot("spine", 26, 0, 0)
        set_rot("chest", 18, 0, 0)
        set_rot("thigh_l", 35, 0, 0)
        set_rot("thigh_r", -35, 0, 0)
        set_rot("robe_back", -32, 0, 0)
        key_all(0)
        key_all(10)
    make_clip("dash", 10, build_dash)

    # 4. GDD v0.9 16 ATTACK SHEETS (light_1, light_2, light_3, heavy, elemental, ultimate) + down_punch, air_punch, sweep
    # Standardized phase frames on timeline (0..24):
    # Frame 0..6: Startup (PREPARAÇÃO)
    # Frame 6..12: Active (EXECUÇÃO / CONTATO)
    # Frame 12..24: Recovery (IMPACTO / RECUPERAÇÃO)
    def build_attack_clip(name: str, prep_fn, active_fn, recov_fn=None):
        def _fn():
            apply_base_stance()
            key_all(0)
            apply_base_stance()
            prep_fn()
            key_all(4)
            apply_base_stance()
            active_fn()
            key_all(6)
            # Contact is held through the active window, then the body follows
            # through instead of snapping from the wind-up after damage starts.
            key_all(10)
            set_rot('robe_back', -18, 0, 3)
            set_rot('sash', -12, 8, 0)
            key_all(12)
            apply_base_stance()
            if recov_fn:
                recov_fn()
            key_all(18)
            apply_base_stance()
            key_all(24)
        make_clip(name, 24, _fn)

    # LIGHT 1 (J1)
    def l1_prep():
        if fighter_id == "kaze":
            # Palma de Jade J1: Coils right palm at hip
            set_rot("chest", 6, 0, 22)
            set_rot("upper_arm_r", -25, -15, 15)
            set_rot("forearm_r", 65, 0, 0)
        elif fighter_id == "ignis":
            # Soco de Roça J1: Winds back right arm
            set_rot("chest", 12, 0, 28)
            set_rot("upper_arm_r", -35, -20, 25)
            set_rot("forearm_r", 70, 0, 0)
        elif fighter_id == "tophia":
            # Punho de Arenito J1: Pulls right stone gauntlet back
            set_rot("chest", 8, 0, 25)
            set_rot("upper_arm_r", -30, -15, 20)
            set_rot("forearm_r", 65, 0, 0)
        else:  # volt
            # Tiro de Sucata J1: Standing cannon aim
            set_rot("chest", 5, 0, -10)
            set_rot("upper_arm_r", 68, 0, 0)
            set_rot("forearm_r", 20, 0, 0)

    def l1_act():
        if fighter_id == "kaze":
            # Forward open palm strike
            set_rot("chest", 8, 0, -28)
            set_rot("upper_arm_r", 88, 0, -10)
            set_rot("forearm_r", 8, 0, 0)
            set_rot("hand_r", -55, 0, 0)
        elif fighter_id == "ignis":
            # Heavy right straight punch
            set_rot("chest", 16, 0, -32)
            set_rot("upper_arm_r", 85, 0, -12)
            set_rot("forearm_r", 10, 0, 0)
        elif fighter_id == "tophia":
            # Right sandstone straight punch
            set_rot("chest", 10, 0, -30)
            set_rot("upper_arm_r", 86, 0, -10)
            set_rot("forearm_r", 10, 0, 0)
        else:  # volt
            # Standing cannon shot with recoil kick
            set_rot("chest", -6, 0, -15)
            set_rot("upper_arm_r", 82, 0, 0)
            set_rot("forearm_r", 15, 0, 0)
    build_attack_clip("light_1", l1_prep, l1_act)

    # LIGHT 2 (J2)
    def l2_prep():
        if fighter_id == "kaze":
            # Palma de Jade J2: Twin palms coiled at different heights
            set_rot("chest", 5, 0, -18)
            set_rot("upper_arm_l", 30, 15, -15)
            set_rot("upper_arm_r", 10, -15, 15)
        elif fighter_id == "ignis":
            # Soco de Roça J2: Left shoulder coiled, right arm hidden behind torso
            set_rot("chest", 14, 0, -25)
            set_rot("upper_arm_r", -48, -25, 20)
        elif fighter_id == "tophia":
            # Punho de Arenito J2: Left gauntlet lowered for rising cross
            set_rot("chest", 12, 0, -28)
            set_rot("upper_arm_l", -25, 20, -15)
        else:  # volt
            # Tiro de Sucata J2: Crouched low cannon aim
            set_loc("hips", 0, 0, -0.26)
            set_rot("thigh_l", 45, 0, 0)
            set_rot("shin_l", -50, 0, 0)
            set_rot("thigh_r", 42, 0, 0)
            set_rot("shin_r", -48, 0, 0)

    def l2_act():
        if fighter_id == "kaze":
            # Twin vertical palms (left high, right mid-low)
            set_rot("chest", 8, 0, 18)
            set_rot("upper_arm_l", 105, 0, 8)
            set_rot("forearm_l", 10, 0, 0)
            set_rot("upper_arm_r", 65, 0, -8)
            set_rot("forearm_r", 12, 0, 0)
        elif fighter_id == "ignis":
            # Left punch forward while right arm stays tucked behind back
            set_rot("chest", 16, 0, 35)
            set_rot("upper_arm_l", 88, 0, 12)
            set_rot("forearm_l", 10, 0, 0)
            set_rot("upper_arm_r", -55, -30, 25)
            set_rot("forearm_r", 45, 0, 0)
        elif fighter_id == "tophia":
            # Left rising cross punch with torso rotation
            set_rot("chest", 6, 0, 34)
            set_rot("upper_arm_l", 96, 0, 14)
            set_rot("forearm_l", 18, 0, 0)
        else:  # volt
            # Crouched low handheld cannon shot
            set_loc("hips", 0, 0, -0.26)
            set_rot("thigh_l", 45, 0, 0)
            set_rot("shin_l", -50, 0, 0)
            set_rot("thigh_r", 42, 0, 0)
            set_rot("shin_r", -48, 0, 0)
            set_rot("upper_arm_r", 78, 0, 0)
            set_rot("forearm_r", 10, 0, 0)
    build_attack_clip("light_2", l2_prep, l2_act)

    # LIGHT 3 (J3)
    def l3_prep():
        if fighter_id == "kaze":
            # Palma de Jade J3: Coils right knee high for front push kick
            set_rot("thigh_r", 75, 0, 0)
            set_rot("shin_r", -85, 0, 0)
        elif fighter_id == "ignis":
            # Soco de Roça J3: Both arms raised high above head for downward slam
            set_rot("spine", -12, 0, 0)
            set_rot("upper_arm_l", 155, 10, 15)
            set_rot("upper_arm_r", 155, -10, -15)
        elif fighter_id == "tophia":
            # Punho de Arenito J3: Lifts front armored boot high for stomp
            set_rot("thigh_r", 70, 0, 0)
            set_rot("shin_r", -60, 0, 0)
        else:  # volt
            # Tiro de Sucata J3: Braces handheld cannon in BOTH hands
            set_rot("upper_arm_r", 75, -15, -15)
            set_rot("upper_arm_l", 75, 15, 25)

    def l3_act():
        if fighter_id == "kaze":
            # Extended barefoot front kick
            set_rot("spine", -14, 0, 0)
            set_rot("thigh_r", 92, 0, 0)
            set_rot("shin_r", -5, 0, 0)
            set_rot("foot_r", -35, 0, 0)
        elif fighter_id == "ignis":
            # Two-handed overhead downward smash toward ground
            set_rot("spine", 28, 0, 0)
            set_rot("chest", 22, 0, 0)
            set_rot("upper_arm_l", 55, 0, 18)
            set_rot("upper_arm_r", 55, 0, -18)
            set_rot("forearm_l", 20, 0, 0)
            set_rot("forearm_r", 20, 0, 0)
        elif fighter_id == "tophia":
            # Heavy front stone boot stomp into floor
            set_loc("hips", 0, -0.08, -0.10)
            set_rot("thigh_r", 35, 0, 0)
            set_rot("shin_r", -25, 0, 0)
            set_rot("chest", 16, 0, 0)
        else:  # volt
            # Braced two-handed cyan burst with recoil lean
            set_rot("spine", -12, 0, 0)
            set_rot("upper_arm_r", 86, -12, -12)
            set_rot("upper_arm_l", 86, 12, 22)
    build_attack_clip("light_3", l3_prep, l3_act)

    # HEAVY (Chute do Vendaval / Marreta Caipira / Martelo de Pedra / Disparo Carregado)
    def heavy_prep():
        if fighter_id == "kaze":
            # Chute do Vendaval: Coils leg and twists hip
            set_rot("hips", 0, 0, 35)
            set_rot("thigh_r", 65, 25, 20)
            set_rot("shin_r", -80, 0, 0)
        elif fighter_id == "ignis":
            # Marreta Caipira: Plants boots and raises clasped fists high overhead
            set_rot("spine", -16, 0, 0)
            set_rot("upper_arm_l", 160, 0, 22)
            set_rot("upper_arm_r", 160, 0, -22)
        elif fighter_id == "tophia":
            # Martelo de Pedra: Pulls orange stone gauntlet back at shoulder
            set_rot("chest", -10, 0, 42)
            set_rot("upper_arm_r", 135, -20, 15)
            set_rot("forearm_r", 55, 0, 0)
        else:  # volt
            # Disparo Carregado: Braces cannon with both hands as orb swells
            set_rot("chest", 6, 0, -10)
            set_rot("upper_arm_r", 78, -10, -15)
            set_rot("upper_arm_l", 78, 10, 25)

    def heavy_act():
        if fighter_id == "kaze":
            # Powerful barefoot horizontal side kick
            set_rot("hips", 0, 22, -45)
            set_rot("spine", -18, -15, 0)
            set_rot("thigh_r", 88, -30, -20)
            set_rot("shin_r", 0, 0, 0)
        elif fighter_id == "ignis":
            # Slams both clasped fists down toward ground
            set_loc("hips", 0, -0.10, -0.18)
            set_rot("spine", 34, 0, 0)
            set_rot("chest", 24, 0, 0)
            set_rot("upper_arm_l", 48, 0, 22)
            set_rot("upper_arm_r", 48, 0, -22)
        elif fighter_id == "tophia":
            # Overhead downward stone hammer punch
            set_loc("hips", 0, -0.08, -0.12)
            set_rot("chest", 24, 0, -38)
            set_rot("upper_arm_r", 65, 0, -15)
            set_rot("forearm_r", 12, 0, 0)
        else:  # volt
            # Fires large slow cyan orb, leaning back strongly from recoil
            set_rot("spine", -18, 0, 0)
            set_rot("chest", -12, 0, 0)
            set_rot("upper_arm_r", 92, -10, -12)
            set_rot("upper_arm_l", 92, 10, 22)
    build_attack_clip("heavy", heavy_prep, heavy_act)

    # ELEMENTAL (Rajada de Vento / Pisada da Fornalha / Erupção Rochosa / Curto-Circuito)
    def elem_prep():
        if fighter_id == "kaze":
            # Rajada de Vento: Gather swirling air between open palms at waist/chest
            set_rot("upper_arm_l", 25, 25, 20)
            set_rot("forearm_l", 75, 0, 0)
            set_rot("upper_arm_r", 25, -25, -20)
            set_rot("forearm_r", 75, 0, 0)
        elif fighter_id == "ignis":
            # Pisada da Fornalha: Raises bent right knee high, boot glowing warm orange
            set_rot("thigh_r", 82, 0, 0)
            set_rot("shin_r", -75, 0, 0)
            set_rot("spine", -8, 0, 0)
        elif fighter_id == "tophia":
            # Erupção Rochosa: Kneels and prepares to touch ground with stone gauntlet
            set_loc("hips", 0, 0, -0.25)
            set_rot("thigh_l", 55, 0, 0)
            set_rot("shin_l", -65, 0, 0)
            set_rot("upper_arm_r", 110, 0, 0)
        else:  # volt
            # Curto-Circuito: Lowers cannon and taps salvaged chest battery
            set_rot("upper_arm_r", 20, 0, 15)
            set_rot("upper_arm_l", 65, 25, 35)
            set_rot("forearm_l", 85, 0, 0)

    def elem_act():
        if fighter_id == "kaze":
            # Both palms push forward releasing jade wind wave
            set_rot("chest", 14, 0, 0)
            set_rot("upper_arm_l", 88, 0, 8)
            set_rot("forearm_l", 5, 0, 0)
            set_rot("upper_arm_r", 88, 0, -8)
            set_rot("forearm_r", 5, 0, 0)
            set_rot("hand_l", -60, 0, 0)
            set_rot("hand_r", -60, 0, 0)
        elif fighter_id == "ignis":
            # Stomps boot down with radial fire/dust burst
            set_loc("hips", 0, -0.08, -0.14)
            set_rot("thigh_r", 28, 0, 0)
            set_rot("shin_r", -20, 0, 0)
            set_rot("chest", 18, 0, 0)
        elif fighter_id == "tophia":
            # Kneeling ground touch sending orange rock spires forward
            set_loc("hips", 0, -0.05, -0.34)
            set_rot("spine", 28, 0, 0)
            set_rot("thigh_l", 68, 0, 0)
            set_rot("shin_l", -75, 0, 0)
            set_rot("upper_arm_r", 52, 0, 0)
        else:  # volt
            # Short circular electric pulse expanding around body
            set_rot("spine", -14, 0, 0)
            set_rot("chest", -12, 0, 0)
            set_rot("upper_arm_l", 45, 45, -35)
            set_rot("upper_arm_r", 45, -45, 35)
    build_attack_clip("elemental", elem_prep, elem_act)

    # ULTIMATE (Tufão Celestial / Fúria do Meio-Dia / Colosso de Terra / Sobrecarga Total)
    def ult_prep():
        if fighter_id == "kaze":
            # Tufão Celestial: Low grounded stance gathering wind
            set_loc("hips", 0, 0, -0.26)
            set_rot("thigh_l", 48, 0, -12)
            set_rot("shin_l", -52, 0, 0)
            set_rot("thigh_r", 48, 0, 12)
            set_rot("shin_r", -52, 0, 0)
            set_rot("upper_arm_l", 15, 20, -25)
            set_rot("upper_arm_r", 15, -20, 25)
        elif fighter_id == "ignis":
            # Fúria do Meio-Dia: Tips cowboy hat and crouches loading legs
            set_loc("hips", 0, 0, -0.24)
            set_rot("thigh_l", 45, 0, 0)
            set_rot("shin_l", -50, 0, 0)
            set_rot("upper_arm_r", 115, -20, -25)
            set_rot("forearm_r", 75, 0, 0)
            set_rot("hat", 10, 0, 0)
        elif fighter_id == "tophia":
            # Colosso de Terra: Plants stone boots and crosses armored arms
            set_loc("hips", 0, 0, -0.14)
            set_rot("upper_arm_l", 70, 20, 38)
            set_rot("forearm_l", 65, 0, 0)
            set_rot("upper_arm_r", 70, -20, -38)
            set_rot("forearm_r", 65, 0, 0)
        else:  # volt
            # Sobrecarga Total: Plants feet wide and braces cannon with both hands charging bright cyan
            set_loc("hips", 0, 0, -0.16)
            set_rot("thigh_l", 30, 0, -14)
            set_rot("thigh_r", -22, 0, 14)
            set_rot("upper_arm_r", 80, -12, -15)
            set_rot("upper_arm_l", 80, 12, 25)

    def ult_act():
        if fighter_id == "kaze":
            # Rises sweeping both arms upward in spiral creating towering jade tornado
            set_loc("hips", 0, 0, 0.06)
            set_rot("spine", -12, 0, 0)
            set_rot("upper_arm_l", 148, 15, -18)
            set_rot("upper_arm_r", 148, -15, 18)
        elif fighter_id == "ignis":
            # Explosive braced shoulder charge with huge orange sunburst
            set_loc("hips", 0, -0.18, -0.08)
            set_rot("spine", 28, 0, -32)
            set_rot("chest", 22, 0, -28)
            set_rot("upper_arm_r", 65, 0, -30)
            set_rot("forearm_r", 85, 0, 0)
        elif fighter_id == "tophia":
            # Punches forward projecting colossal orange stone fist
            set_loc("hips", 0, -0.14, -0.08)
            set_rot("chest", 14, 0, -36)
            set_rot("upper_arm_r", 90, 0, -8)
            set_rot("forearm_r", 5, 0, 0)
        else:  # volt
            # Fires huge horizontal cyan beam, recoiling strongly with boots skidding
            set_loc("hips", 0, 0.10, -0.14)
            set_rot("spine", -22, 0, 0)
            set_rot("chest", -16, 0, 0)
            set_rot("upper_arm_r", 95, -10, -12)
            set_rot("upper_arm_l", 95, 10, 22)
    build_attack_clip("ultimate", ult_prep, ult_act)

    # Contextual variants: down_punch (low launcher), air_punch, sweep
    def dp_prep():
        set_loc("hips", 0, 0, -0.28)
        set_rot("thigh_l", 50, 0, 0)
        set_rot("shin_l", -55, 0, 0)
        set_rot("upper_arm_r", -25, 0, 0)
    def dp_act():
        set_loc("hips", 0, 0, 0.04)
        set_rot("chest", -12, 0, -28)
        set_rot("upper_arm_r", 125, 0, -10)
        set_rot("forearm_r", 25, 0, 0)
    build_attack_clip("down_punch", dp_prep, dp_act)

    def ap_prep():
        set_rot("thigh_l", 40, 0, 0)
        set_rot("upper_arm_r", 115, 0, 0)
    def ap_act():
        set_rot("chest", 18, 0, -25)
        set_rot("upper_arm_r", 55, 0, -10)
        set_rot("thigh_r", 65, 0, 0)
    build_attack_clip("air_punch", ap_prep, ap_act)

    def sw_prep():
        set_loc("hips", 0, 0, -0.34)
        set_rot("hips", 0, 0, 30)
    def sw_act():
        set_loc("hips", 0, 0, -0.36)
        set_rot("hips", 0, 0, -40)
        set_rot("thigh_r", 78, -20, -25)
        set_rot("shin_r", 0, 0, 0)
    build_attack_clip("sweep", sw_prep, sw_act)

    # 5. Defensive, reaction & presentation animations:
    # guard_high, guard_low, parry, hit, knockdown, get_up, ko, victory, select, breaker
    def build_guard_high():
        apply_base_stance()
        set_rot("upper_arm_l", 75, 20, 25)
        set_rot("forearm_l", 85, 0, 0)
        set_rot("upper_arm_r", 75, -20, -25)
        set_rot("forearm_r", 85, 0, 0)
        key_all(0)
        key_all(10)
    make_clip("guard_high", 10, build_guard_high)

    def build_guard_low():
        build_crouch()
        set_rot("upper_arm_l", 70, 20, 25)
        set_rot("forearm_l", 85, 0, 0)
        set_rot("upper_arm_r", 70, -20, -25)
        set_rot("forearm_r", 85, 0, 0)
        key_all(0)
        key_all(10)
    make_clip("guard_low", 10, build_guard_low)

    def build_parry():
        apply_base_stance()
        set_rot("chest", -8, 0, -32)
        set_rot("upper_arm_l", 95, 35, -30)
        set_rot("forearm_l", 20, 0, 0)
        key_all(0)
        key_all(16)
    make_clip("parry", 16, build_parry)

    def build_hit():
        apply_base_stance()
        set_rot("spine", -22, 0, 12)
        set_rot("chest", -18, 0, 10)
        set_rot("head", -20, 0, 0)
        set_rot("upper_arm_l", 20, 30, -35)
        set_rot("upper_arm_r", 20, -30, 35)
        key_all(0)
        apply_base_stance()
        key_all(16)
    make_clip("hit", 16, build_hit)

    def build_knockdown():
        build_hit()
        reset_pose()
        set_loc("hips", 0, 0.35, -0.78)
        set_rot("hips", -78, 0, 0)
        set_rot("upper_arm_l", 30, 0, -40)
        set_rot("upper_arm_r", 30, 0, 40)
        key_all(12)
        key_all(24)
    make_clip("knockdown", 24, build_knockdown)

    def build_get_up():
        build_knockdown()
        apply_base_stance()
        key_all(18)
    make_clip("get_up", 18, build_get_up)

    def build_ko():
        build_knockdown()
        key_all(30)
    make_clip("ko", 30, build_ko)

    def build_victory():
        apply_base_stance()
        key_all(0)
        reset_pose()
        if fighter_id == "tophia":
            # V5 Tophia signature victory/presentation pose: smiling, one leg raised, peace sign!
            set_rot("thigh_l", 55, 0, -15)
            set_rot("shin_l", -70, 0, 0)
            set_rot("upper_arm_r", 115, -15, -20)
            set_rot("forearm_r", 55, 0, 0)
        elif fighter_id == "ignis":
            # Tips cowboy hat and flexes
            set_rot("upper_arm_r", 110, -15, -25)
            set_rot("forearm_r", 75, 0, 0)
            set_rot("upper_arm_l", 85, 25, -20)
            set_rot("forearm_l", 80, 0, 0)
        elif fighter_id == "kaze":
            # Calm monk bow with palm salute
            set_rot("spine", 12, 0, 0)
            set_rot("upper_arm_l", 55, 20, 25)
            set_rot("forearm_l", 75, 0, 0)
            set_rot("upper_arm_r", 55, -20, -25)
            set_rot("forearm_r", 75, 0, 0)
        else:
            # Volt raises scrap cannon triumphantly
            set_rot("upper_arm_r", 145, 0, 10)
            set_rot("forearm_r", 15, 0, 0)
        key_all(20)
        key_all(40)
    make_clip("victory", 40, build_victory)

    make_clip("select", 40, build_victory)

    def build_breaker():
        apply_base_stance()
        set_rot("spine", -18, 0, 0)
        set_rot("upper_arm_l", 90, 45, -45)
        set_rot("upper_arm_r", 90, -45, 45)
        key_all(0)
        apply_base_stance()
        key_all(16)
    make_clip("breaker", 16, build_breaker)

    # Set default active action to idle
    arm_obj.animation_data.action = bpy.data.actions["idle"]


FIGHTER_SCALES = {
    "kaze": {"height": 1.90, "shoulder_w": 0.24, "hip_w": 0.13, "hunch": 0.0, "builder": build_kaze_mesh},
    "ignis": {"height": 1.96, "shoulder_w": 0.33, "hip_w": 0.16, "hunch": 0.14, "builder": build_ignis_mesh},
    "tophia": {"height": 1.78, "shoulder_w": 0.25, "hip_w": 0.14, "hunch": 0.0, "builder": build_tophia_mesh},
    "volt": {"height": 1.78, "shoulder_w": 0.23, "hip_w": 0.13, "hunch": 0.05, "builder": build_volt_mesh},
}


def build_and_export_fighter(fighter_id: str):
    clear_scene()
    cfg = FIGHTER_SCALES[fighter_id]
    arm_obj = create_humanoid_armature(fighter_id, cfg)
    mat = make_fighter_material(fighter_id)
    mb = MeshBuilder()
    cfg["builder"](mb)
    from character_polish import add_model_detail
    add_model_detail(mb, fighter_id)
    mesh_obj = mb.build_object(f"{fighter_id}_Body", arm_obj, mat)
    animate_fighter(arm_obj, fighter_id)

    blend_path = ART_SRC / "characters" / fighter_id / f"{fighter_id}.blend"
    glb_path = GODOT / "assets" / "characters" / fighter_id / f"{fighter_id}.glb"
    blend_path.parent.mkdir(parents=True, exist_ok=True)
    glb_path.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    bpy.ops.export_scene.gltf(
        filepath=str(glb_path),
        export_format='GLB',
        export_yup=True,
        export_apply=False,
        export_animations=True,
        export_animation_mode='NLA_TRACKS',
        export_skins=True,
        export_materials='EXPORT',
    )
    print(f"Exported fighter {fighter_id}: {blend_path.name} -> {glb_path} (tris: {len(mesh_obj.data.polygons)})")


def make_simple_mat(name: str, rgb, emission_strength=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.7
        if emission_strength > 0 and "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (*rgb, 1.0)
            bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat


def add_stage_box(name: str, loc, scale, mat):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    return obj


def add_stage_cyl(name: str, loc, r1, r2, depth, mat, vertices=12):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=r1, radius2=r2, depth=depth, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(mat)
    return obj


def build_and_export_stages():
    # Remember: in Blender, X is stage left/right (-11..+11), -Y is camera forward (+Z in Godot), +Y is background (-Z in Godot), +Z is height (+Y in Godot)!
    stages = [
        ("zephyr", "zephyr_dojo"),
        ("forge", "molten_forge"),
        ("bazaar", "storm_market"),
    ]
    for blend_folder, stage_id in stages:
        clear_scene()
        out_dir = GODOT / "assets" / "environments" / stage_id
        out_dir.mkdir(parents=True, exist_ok=True)

        if stage_id == "zephyr_dojo":
            stone = make_simple_mat("stone", (0.76, 0.79, 0.83))
            trim = make_simple_mat("trim", (0.16, 0.40, 0.31))
            wood = make_simple_mat("wood", (0.52, 0.20, 0.22))
            roof = make_simple_mat("roof", (0.14, 0.22, 0.26))
            blossom = make_simple_mat("blossom", (0.96, 0.66, 0.78), 0.15)
            mountain = make_simple_mat("mountain", (0.34, 0.46, 0.58))

            # Sanctuary stone floor (Y=0 top surface in Godot -> Z=0 top surface in Blender)
            add_stage_box("Floor", (0, 0, -0.28), (22.5, 9.2, 0.56), stone)
            add_stage_box("FrontTrim", (0, -4.2, -0.02), (22.6, 0.25, 0.18), trim)
            add_stage_box("BackSteps", (0, 3.8, 0.25), (22.5, 1.4, 0.50), stone)
            # Torii Gate in background (+Y in Blender = -Z in Godot)
            for sx in (-6.5, 6.5):
                add_stage_cyl(f"ToriiPillar_{sx}", (sx, 4.2, 2.6), 0.32, 0.28, 5.2, wood)
            add_stage_box("ToriiLint1", (0, 4.2, 4.8), (15.5, 0.5, 0.42), wood)
            add_stage_box("ToriiLint2", (0, 4.2, 5.35), (17.2, 0.85, 0.36), roof)
            # Cherry trees & pagoda silhouette
            for sx in (-10.2, -4.5, 4.8, 10.2):
                add_stage_cyl(f"Trunk_{sx}", (sx, 5.2, 1.6), 0.22, 0.16, 3.2, wood)
                add_stage_cyl(f"Crown_{sx}", (sx, 5.2, 3.6), 1.65, 0.4, 1.8, blossom)
            for idx, (mx, my, mh) in enumerate([(-11, 14, 7.5), (-3, 16, 9.0), (5, 15, 8.2), (12, 14, 7.0)]):
                add_stage_cyl(f"Mountain_{idx}", (mx, my, mh * 0.4), mh * 0.7, 0.4, mh, mountain, 8)

        elif stage_id == "molten_forge":
            basalt = make_simple_mat("basalt", (0.14, 0.13, 0.14))
            lava = make_simple_mat("lava", (0.96, 0.30, 0.08), 0.85)
            iron = make_simple_mat("iron", (0.20, 0.18, 0.20))
            eclipse = make_simple_mat("eclipse", (0.82, 0.12, 0.10), 0.9)

            add_stage_box("ForgeFloor", (0, 0, -0.28), (22.5, 9.2, 0.56), basalt)
            add_stage_box("LavaTrim", (0, -4.2, -0.02), (22.6, 0.25, 0.18), lava)
            add_stage_box("LavaLake", (0, 8.0, -0.65), (48.0, 28.0, 0.15), lava)
            # Colossal Anvil in background
            add_stage_box("AnvilBase", (0, 5.5, 1.3), (3.4, 1.8, 2.6), iron)
            add_stage_box("AnvilTop", (0, 5.5, 3.1), (6.2, 2.2, 1.3), iron)
            for sx in (-9.0, -4.8, 4.8, 9.0):
                add_stage_box(f"ForgePillar_{sx}", (sx, 4.5, 2.8), (0.85, 0.85, 5.6), iron)
                add_stage_cyl(f"ForgeFlame_{sx}", (sx, 4.5, 5.8), 0.55, 0.1, 0.9, lava, 8)
            add_stage_cyl("BloodSun", (0, 16.0, 8.5), 2.6, 2.6, 0.3, eclipse, 16)

        else:  # storm_market (Golden Bazaar)
            sand = make_simple_mat("sand", (0.78, 0.56, 0.30))
            tile = make_simple_mat("tile", (0.14, 0.36, 0.56))
            gold = make_simple_mat("gold", (0.94, 0.74, 0.26), 0.2)
            carpet = make_simple_mat("carpet", (0.58, 0.16, 0.24))

            add_stage_box("BazaarFloor", (0, 0, -0.28), (22.5, 9.2, 0.56), sand)
            add_stage_box("TileTrim", (0, -4.2, -0.02), (22.6, 0.28, 0.18), tile)
            for rx in (-6.0, 0.0, 6.0):
                add_stage_box(f"Carpet_{rx}", (rx, 0, 0.02), (3.2, 5.5, 0.04), carpet)
            for ax in range(-10, 11, 5):
                add_stage_box(f"Col_{ax}", (ax, 4.4, 2.6), (0.65, 0.65, 5.2), sand)
                add_stage_box(f"Arch_{ax}", (ax, 4.4, 5.0), (4.4, 0.8, 0.65), tile)
                add_stage_cyl(f"Lamp_{ax}", (ax, 3.2, 4.1), 0.28, 0.15, 0.65, gold, 10)

        from stage_polish import enhance_stage
        enhance_stage(stage_id,add_stage_box,add_stage_cyl,make_simple_mat)
        blend_path = ART_SRC / "environments" / blend_folder / f"{blend_folder}.blend"
        bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
        bpy.ops.export_scene.gltf(
            filepath=str(out_dir / "stage.glb"),
            export_format='GLB',
            export_yup=True,
            export_materials='EXPORT',
        )

        # Build intact prop (`prop_intact.glb`)
        clear_scene()
        if stage_id == "zephyr_dojo":
            pmat = make_simple_mat("prop_jade", (0.20, 0.55, 0.42), 0.25)
            wmat = make_simple_mat("prop_wood", (0.48, 0.34, 0.20))
            add_stage_box("CrateBody", (0, 0, 0.38), (0.58, 0.58, 0.72), wmat)
            add_stage_cyl("LanternTop", (0, 0, 0.82), 0.38, 0.12, 0.22, pmat, 8)
        elif stage_id == "molten_forge":
            imat = make_simple_mat("prop_iron", (0.22, 0.20, 0.22))
            fmat = make_simple_mat("prop_fire", (0.98, 0.38, 0.10), 0.8)
            add_stage_cyl("BrazierBase", (0, 0, 0.32), 0.32, 0.24, 0.64, imat, 10)
            add_stage_cyl("BrazierBowl", (0, 0, 0.68), 0.24, 0.38, 0.25, fmat, 10)
        else:
            gmat = make_simple_mat("prop_brass", (0.90, 0.68, 0.22), 0.25)
            smat = make_simple_mat("prop_spice", (0.72, 0.22, 0.28))
            add_stage_box("SpiceCrate", (0, 0, 0.35), (0.60, 0.56, 0.68), gmat)
            add_stage_cyl("SpiceMound", (0, 0, 0.75), 0.26, 0.05, 0.22, smat, 10)

        bpy.ops.export_scene.gltf(
            filepath=str(out_dir / "prop_intact.glb"),
            export_format='GLB',
            export_yup=True,
            export_materials='EXPORT',
        )

        # Build broken prop (`prop_broken.glb`)
        clear_scene()
        bmat = make_simple_mat("broken_mat", (0.45, 0.38, 0.32))
        for i, (dx, dy, rz) in enumerate([(-0.22, -0.12, 25), (0.20, 0.14, -35), (0.0, -0.18, 50)]):
            obj = add_stage_box(f"Shard_{i}", (dx, dy, 0.08), (0.26, 0.14, 0.10), bmat)
            obj.rotation_euler = (0.2, -0.15, math.radians(rz))
        bpy.ops.export_scene.gltf(
            filepath=str(out_dir / "prop_broken.glb"),
            export_format='GLB',
            export_yup=True,
            export_materials='EXPORT',
        )
        print(f"Exported stage & props for {stage_id}")

    # Also save standardized `art-source/renders/portraits.blend`
    clear_scene()
    bpy.ops.object.camera_add(location=(0, -2.2, 1.72), rotation=(math.radians(88), 0, 0))
    bpy.ops.object.light_add(type='AREA', location=(-1.2, -1.8, 2.2))
    bpy.ops.wm.save_as_mainfile(filepath=str(ART_SRC / "renders" / "portraits.blend"))


if __name__ == "__main__":
    fighter_ids = [sys.argv[sys.argv.index('--fighter') + 1]] if '--fighter' in sys.argv else ["kaze", "ignis", "tophia", "volt"]
    if '--stages-only' not in sys.argv:
        for fid in fighter_ids:
            build_and_export_fighter(fid)
    if '--characters-only' not in sys.argv:
        build_and_export_stages()
    print("ALL BLENDER ASSETS BUILT AND EXPORTED SUCCESSFULLY.")
