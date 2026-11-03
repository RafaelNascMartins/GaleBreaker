"""Arenas from the refined concepts in concept-art/arenas/:
santuario-refinado-v1, forja-sol-vermelho-v1 and bazaar-fechado-v1.

Blender axes: X is left/right, -Y faces the camera, +Y is background, +Z is up.
Fighters stand on Y=0, Z=0 and are held inside |x| <= GaleCombat.EDGE (6.5).
Textures come from generate_stage_textures.py (one PNG per atlas material).

Node names Godot relies on (they are never merged):
  Blocker_L / Blocker_R   corner obstacles just beyond the walls
  Barrier_L / Barrier_R   forge heat curtain (faded in by proximity)
  Banner_*                cloth that sways (origin at its hanging edge)
  Crowd_*                 bazaar spectators (origin at the feet)
  Backdrop                painted far background, rendered unshaded
Materials named glow_* are rendered unshaded in Godot (lava, fire, lamps, glass).
"""
import math
import random
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
ENV = ROOT / "godot" / "assets" / "environments"
# x_min, x_max, y_front, y_back of the walkable floor.
STAGE_FLOOR = {"zephyr_dojo": (-8.6, 8.6, -4.6, 4.2), "molten_forge": (-7.6, 7.6, -4.6, 3.8), "storm_market": (-9.6, 9.6, -14.0, 16.6)}
KEEP_PREFIXES = ("Blocker_", "Barrier_", "Banner_", "Crowd_", "Backdrop", "QuestBoardPanel")


class Kit:
    def __init__(self, stage: str):
        self.stage = stage
        self.mats = {}
        self.rng = random.Random(sum(map(ord, stage)))

    # --- materials -------------------------------------------------------
    def mat(self, name, rgb, emit=0.0):
        """Flat colour authored in sRGB (converted to the linear factor glTF expects)."""
        if name in self.mats:
            return self.mats[name]
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        rgb = tuple(c ** 2.2 for c in rgb)
        bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.75
        if emit > 0:
            bsdf.inputs["Emission Color"].default_value = (*rgb, 1.0)
            bsdf.inputs["Emission Strength"].default_value = emit
        self.mats[name] = m
        return m

    def tex(self, name, filename, meters=0.0, emit=0.0):
        """Painted texture; meters > 0 projects world-space UVs so one tile covers that many metres."""
        if name in self.mats:
            return self.mats[name]
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        nodes, links = m.node_tree.nodes, m.node_tree.links
        bsdf = nodes.get("Principled BSDF")
        image = nodes.new("ShaderNodeTexImage")
        image.image = bpy.data.images.load(str(ENV / self.stage / "textures" / filename))
        links.new(image.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.8
        if emit > 0:
            links.new(image.outputs["Color"], bsdf.inputs["Emission Color"])
            bsdf.inputs["Emission Strength"].default_value = emit
        m["uv_m"] = meters
        self.mats[name] = m
        return m

    # --- primitives (rot in degrees) ------------------------------------
    def _finish(self, obj, name, mat, rot):
        obj.name = name
        obj.rotation_euler = tuple(math.radians(a) for a in rot)
        obj.data.materials.append(mat)
        meters = float(mat.get("uv_m", 0.0))
        if meters > 0:
            box_uv(obj, meters)
        return obj

    def box(self, name, loc, size, mat, rot=(0, 0, 0)):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
        obj = bpy.context.active_object
        obj.scale = size
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        return self._finish(obj, name, mat, rot)

    def cyl(self, name, loc, r1, r2, depth, mat, verts=12, rot=(0, 0, 0)):
        bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=depth, location=loc)
        return self._finish(bpy.context.active_object, name, mat, rot)

    def ball(self, name, loc, scale, mat, subdiv=1, rot=(0, 0, 0)):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdiv, radius=1.0, location=loc)
        obj = bpy.context.active_object
        obj.scale = scale
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        return self._finish(obj, name, mat, rot)

    def ring(self, name, loc, major, minor, mat, rot=(0, 0, 0)):
        bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=20, minor_segments=6, location=loc)
        return self._finish(bpy.context.active_object, name, mat, rot)

    def beam(self, name, a, b, r, mat, verts=8):
        a, b = Vector(a), Vector(b)
        vec = b - a
        obj = self.cyl(name, (a + b) * 0.5, r, r, vec.length, mat, verts)
        obj.rotation_mode = "QUATERNION"
        obj.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(vec)
        return obj

    def panel(self, name, center, w, h, mat, facing="front", rot_z=0.0):
        """Flat quad with 0..1 UVs; 'front' faces the camera (-Y), 'up' faces +Z, '+x'/'-x' face along X."""
        bpy.ops.mesh.primitive_plane_add(size=1.0, location=center)
        obj = bpy.context.active_object
        obj.scale = (w, h, 1)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        rot = {"front": (90, 0, rot_z), "up": (0, 0, rot_z), "+x": (90, 0, 90), "-x": (90, 0, -90)}[facing]
        return self._finish(obj, name, mat, rot)

    def arch(self, name, cx, y, spring_z, radius, depth, mats, segments=15, rise=0.9, band=0.42):
        """Semicircular arch of wedge voussoirs that meet edge to edge (no gaps), alternating mats."""
        def point(t, r):
            return (cx - math.cos(t) * r, spring_z + math.sin(t) * r * rise)
        for j in range(segments):
            t0, t1 = math.pi * j / segments, math.pi * (j + 1) / segments
            outline = [point(t0, radius), point(t1, radius), point(t1, radius + band), point(t0, radius + band)]
            self.prism(name, outline, y, depth, mats[j % len(mats)])

    def prism(self, name, outline_xz, y, depth, mat):
        """Convex polygon in the XZ plane extruded along Y, centred on y."""
        import bmesh
        bm = bmesh.new()
        front = [bm.verts.new((x, y - depth / 2, z)) for x, z in outline_xz]
        back = [bm.verts.new((x, y + depth / 2, z)) for x, z in outline_xz]
        bm.faces.new(front[::-1])
        bm.faces.new(back)
        n = len(outline_xz)
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((front[i], front[j], back[j], back[i]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        obj = bpy.data.objects.new(name, me)
        bpy.context.collection.objects.link(obj)
        return self._finish(obj, name, mat, (0, 0, 0))

    def cut_arch(self, wall, cx, y, spring_z, radius, rise=0.9):
        """Boolean-cut a round-topped opening through a wall object."""
        round_top = self.cyl("Cutter", (cx, y, spring_z), radius, radius, 4.0, wall.data.materials[0], 32, rot=(90, 0, 0))
        # Rotated 90° about X, the cylinder's local Y is world Z: squash it to the arch rise.
        round_top.scale = (1.0, rise, 1.0)
        lower = self.box("Cutter", (cx, y, spring_z / 2 - 0.05), (radius * 2, 4.0, spring_z + 0.1), wall.data.materials[0])
        for cutter in (round_top, lower):
            mod = wall.modifiers.new("cut", "BOOLEAN")
            mod.operation = "DIFFERENCE"
            mod.object = cutter
            bpy.context.view_layer.objects.active = wall
            bpy.ops.object.modifier_apply(modifier=mod.name)
            bpy.data.objects.remove(cutter, do_unlink=True)
        box_uv(wall, float(wall.data.materials[0].get("uv_m", 1.0)) or 1.0)

    # --- grouping --------------------------------------------------------
    def group(self, name, objs, origin=None):
        bpy.ops.object.select_all(action="DESELECT")
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        if len(objs) > 1:
            bpy.ops.object.join()
        obj = bpy.context.active_object
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        if origin is not None:
            bpy.context.scene.cursor.location = origin
            bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
        obj.name = name
        return obj

    def collect(self, fn):
        """Run fn() and return the objects it created."""
        before = set(bpy.data.objects)
        fn()
        return [o for o in bpy.data.objects if o not in before]


def box_uv(obj, meters):
    """World-space box projection, so texel density is the same on every piece."""
    bpy.context.view_layer.update()
    mw = obj.matrix_world
    rot = mw.to_3x3()
    me = obj.data
    if not me.uv_layers:
        me.uv_layers.new()
    uv = me.uv_layers.active.data
    for poly in me.polygons:
        n = rot @ poly.normal
        axis = max(range(3), key=lambda i: abs(n[i]))
        for li in poly.loop_indices:
            co = mw @ me.vertices[me.loops[li].vertex_index].co
            u, v = (co.y, co.z) if axis == 0 else (co.x, co.z) if axis == 1 else (co.x, co.y)
            uv[li].uv = (u / meters, v / meters)


def merge_by_material():
    groups = {}
    for o in list(bpy.data.objects):
        if o.type != "MESH" or o.name.startswith(KEEP_PREFIXES):
            continue
        groups.setdefault(o.data.materials[0].name, []).append(o)
    for name, objs in groups.items():
        bpy.ops.object.select_all(action="DESELECT")
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        if len(objs) > 1:
            bpy.ops.object.join()
        bpy.context.active_object.name = "Stage_" + name


# --- shared pieces -----------------------------------------------------------
def floor(k, base_mat, under_mat):
    x0, x1, yf, yb = STAGE_FLOOR[k.stage]
    w, d = x1 - x0, yb - yf
    cx, cy = (x0 + x1) / 2, (yf + yb) / 2
    k.panel("Floor", (cx, cy, 0.0), w, d, base_mat, "up")
    k.box("FloorSlab", (cx, cy, -0.32), (w, d, 0.62), under_mat)


def backdrop(k, z_bottom=-7.0, radius=46.0, a_left=158.0, a_right=22.0, segments=40, filename="backdrop.png", height=None, v_rows=None):
    """Painted horizon on a curved band around the back of the arena (no flat poster edges).

    v_rows [(z, v), ...] maps image rows to heights piecewise, e.g. to pull a sky's
    clouds down to the horizon instead of stretching the image linearly.
    """
    import bmesh
    image = bpy.data.images.load(str(ENV / k.stage / "textures" / filename))
    span = math.radians(a_left - a_right)
    if height is None:
        height = radius * span * image.size[1] / image.size[0]
    if v_rows is None:
        v_rows = [(z_bottom, 0.0), (z_bottom + height, 1.0)]
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    columns = []
    for i in range(segments + 1):
        a = math.radians(a_left) - span * i / segments
        x, y = math.cos(a) * radius, math.sin(a) * radius
        columns.append(([bm.verts.new((x, y, z)) for z, _ in v_rows], i / segments))
    for (c0, u0), (c1, u1) in zip(columns, columns[1:]):
        for r in range(len(v_rows) - 1):
            v0, v1 = v_rows[r][1], v_rows[r + 1][1]
            face = bm.faces.new((c0[r], c1[r], c1[r + 1], c0[r + 1]))
            for loop, uv in zip(face.loops, ((u0, v0), (u1, v0), (u1, v1), (u0, v1))):
                loop[uv_layer].uv = uv
    # Faces point toward the arena centre.
    for face in bm.faces:
        face.normal_update()
        if face.normal.dot(-face.calc_center_median()) < 0:
            face.normal_flip()
    me = bpy.data.meshes.new("Backdrop")
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new("Backdrop", me)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(k.tex("backdrop", filename))


def surroundings(k, ground_mat, sea_mat, peak_mat, ground_radius=0.0, sea_z=-6.0, peak_radius=60.0, skip_back=True):
    """Close the world in every direction: a plateau, a sea to the horizon and a ring of peaks."""
    if ground_radius > 0:
        k.cyl("Plateau", (0, 0, -0.4), ground_radius, ground_radius * 0.94, 0.74, ground_mat, 48)
        k.cyl("PlateauSkirt", (0, 0, (sea_z - 0.77) / 2), ground_radius * 0.94, ground_radius * 0.7, abs(sea_z) - 0.6, ground_mat, 48)
    k.cyl("Sea", (0, 0, sea_z), 260, 260, 0.2, sea_mat, 64)
    for i in range(26):
        a = i * math.tau / 26
        x, y = math.cos(a) * peak_radius, math.sin(a) * peak_radius
        if skip_back and y > 30:
            continue  # the painted backdrop covers the far side
        r = k.rng.uniform(0.85, 1.15)
        height = k.rng.uniform(16, 30)
        k.cyl("Peak", (x * r, y * r, sea_z + height / 2), k.rng.uniform(9, 13), k.rng.uniform(0.6, 2.0), height, peak_mat, 7, rot=(k.rng.uniform(-6, 6), k.rng.uniform(-6, 6), k.rng.uniform(0, 360)))


def banner(k, name, top, w, h, mat):
    """Cloth panel whose origin is its top edge, so Godot can sway it."""
    obj = k.panel(name, (top[0], top[1], top[2] - h / 2), w, h, mat, "front")
    return k.group(name, [obj], origin=top)


def chain(k, a, b, mat, links=14):
    a, b = Vector(a), Vector(b)
    d = (b - a).normalized()
    side = d.cross(Vector((0, 1, 0)))
    if side.length < 0.01:
        side = Vector((1, 0, 0))
    for i in range(links):
        obj = k.ring("ChainLink", a.lerp(b, (i + 0.5) / links), 0.2, 0.06, mat)
        obj.rotation_mode = "QUATERNION"
        axis = side if i % 2 else d.cross(side)
        obj.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(axis)


def chest(k, center, size, wood, panel_mat, brass):
    cx, cy, cz = center
    w, d, h = size
    k.box("ChestBody", center, size, wood)
    k.box("ChestPanel", (cx, cy - d / 2 - 0.01, cz), (w * 0.62, 0.03, h * 0.62), panel_mat)
    k.ring("ChestHandle", (cx, cy - d / 2 - 0.05, cz), min(w, h) * 0.13, 0.025, brass, rot=(90, 0, 0))
    for ex in (-w / 2, w / 2):
        for ez in (-h / 2, h / 2):
            k.box("ChestCorner", (cx + ex * 0.96, cy - d / 2, cz + ez * 0.94), (0.16, 0.06, 0.16), brass)
    k.box("ChestBand", (cx, cy, cz + h / 2 - 0.03), (w + 0.02, d + 0.02, 0.07), brass)


# --- Santuário refinado ------------------------------------------------------
def build_zephyr(k):
    floor_mat = k.tex("piso_calcario", "piso_calcario.png", 2.0)
    stone = k.tex("pedra_estrutural", "pedra_estrutural.png", 1.5)
    red = k.tex("madeira_vermelha", "madeira_vermelha.png", 1.4)
    brass = k.tex("latao", "latao.png", 1.0)
    roof = k.tex("telhas", "telhas_azul_ardosia.png", 1.4)
    crate = k.tex("madeira_caixas", "madeira_caixas.png", 0.9)
    bark = k.tex("casca_cerejeira", "casca_cerejeira.png", 1.2)
    blossom = k.tex("flores_cerejeira", "flores_cerejeira.png", 1.4)
    moss = k.tex("pedra_musgo", "pedra_musgo.png", 2.5)
    medallion = k.tex("medalhao_piso", "medalhao_piso.png")
    flag = k.tex("estandarte_vento", "estandarte_vento.png")
    black = k.mat("laca_preta", (0.10, 0.10, 0.11))
    jade = k.mat("jade", (0.16, 0.40, 0.30))
    lamp = k.mat("glow_lamp", (1.0, 0.82, 0.48), 1.2)
    wall = k.mat("parede_templo", (0.90, 0.85, 0.74))
    floor(k, floor_mat, stone)
    k.panel("Medallion", (0, -0.5, 0.012), 4.4, 4.4, medallion, "up")
    backdrop(k)
    surroundings(k, stone, k.mat("glow_mist", (0.86, 0.92, 0.98)), moss, ground_radius=30.0, sea_z=-7.0)

    # Terrace, railing with brass caps, stair and lanterns.
    k.box("Terrace", (0, 5.2, 0.28), (17.2, 2.0, 0.56), stone)
    k.box("TerraceStep", (0, 4.15, 0.12), (17.2, 0.3, 0.24), stone)
    for i in range(13):
        x = -6.6 + i * 1.1
        if abs(x) < 1.8:
            continue
        k.box("RailPost", (x, 6.0, 1.05), (0.16, 0.16, 1.0), red)
        k.cyl("RailCap", (x, 6.0, 1.62), 0.13, 0.02, 0.2, brass, 4, rot=(0, 0, 45))
    for z in (0.9, 1.4):
        for sx in (-1, 1):
            k.box("Rail", (sx * 4.2, 6.0, z), (4.9, 0.1, 0.1), red)
    for i in range(9):
        k.box("Stair", (0, 6.4 + i * 0.42, 0.56 + i * 0.2), (3.2, 0.42, 0.2), stone)
    for sx in (-1, 1):
        k.box("StairWall", (sx * 1.75, 8.1, 1.3), (0.35, 3.8, 1.6), stone)
    for x in (-4.6, -2.4, 2.4, 4.6):
        k.box("LanternBase", (x, 5.3, 0.72), (0.5, 0.5, 0.32), stone)
        k.box("LanternPost", (x, 5.3, 1.1), (0.2, 0.2, 0.5), stone)
        k.box("LanternLight", (x, 5.3, 1.55), (0.42, 0.42, 0.4), lamp)
        k.cyl("LanternCap", (x, 5.3, 1.88), 0.5, 0.06, 0.3, black, 4, rot=(0, 0, 45))
        k.cyl("LanternFinial", (x, 5.3, 2.1), 0.06, 0.02, 0.2, brass, 6)

    # Torii gate on an upper platform at the top of the stair.
    k.box("UpperPlatform", (0, 12.4, 1.2), (12.0, 4.8, 2.4), stone)
    for sx in (-1, 1):
        k.box("ToriiBase", (sx * 3.3, 10.6, 2.6), (1.0, 1.0, 0.8), black)
        k.box("ToriiBaseBand", (sx * 3.3, 10.6, 3.0), (1.04, 1.04, 0.12), brass)
        k.cyl("ToriiPillar", (sx * 3.3, 10.6, 6.0), 0.38, 0.34, 6.4, red, 16)
    k.box("ToriiNuki", (0, 10.6, 7.7), (8.8, 0.4, 0.46), red)
    k.box("ToriiShimaki", (0, 10.6, 8.55), (9.8, 0.55, 0.32), red)
    k.box("ToriiKasagi", (0, 10.6, 8.92), (10.4, 0.7, 0.34), black)
    for sx in (-1, 1):
        k.box("ToriiTip", (sx * 5.5, 10.6, 9.15), (1.1, 0.7, 0.3), black, rot=(0, sx * -16, 0))
    k.box("ToriiStrut", (0, 10.6, 8.1), (0.45, 0.42, 0.9), red)
    k.panel("ToriiPlaque", (0, 10.38, 8.15), 0.9, 0.9, medallion, "front")

    # Banner poles and the massive lacquered pillars that frame the corners.
    for sx, side in ((-1, "L"), (1, "R")):
        k.cyl("BannerPole", (sx * 4.3, 4.7, 3.3), 0.08, 0.07, 6.6, red, 8)
        k.box("BannerArm", (sx * 4.0, 4.7, 6.45), (0.8, 0.08, 0.08), red)
        k.ball("BannerTassel", (sx * 3.6, 4.65, 6.3), (0.06, 0.06, 0.18), brass)
        banner(k, "Banner_" + side, (sx * 3.95, 4.62, 6.4), 1.1, 3.0, flag)
        k.box("PillarFoot", (sx * 7.0, 3.6, 0.55), (1.6, 1.6, 1.1), stone)
        k.box("PillarFootTrim", (sx * 7.0, 3.6, 1.15), (1.5, 1.5, 0.14), brass)
        k.box("Pillar", (sx * 7.0, 3.6, 4.9), (1.15, 1.15, 7.4), red)
        k.box("PillarBand", (sx * 7.0, 3.6, 7.6), (1.22, 1.22, 0.28), brass)
        k.box("PillarCap", (sx * 7.0, 3.6, 8.85), (1.7, 1.7, 0.5), brass)

    # Pagodas, cherry trees and mossy cliffs behind the terrace.
    for px, py, s in [(-10.0, 12.5, 1.0), (10.0, 12.5, 1.0)]:
        k.box("PagodaPlinth", (px, py, 0.6 * s), (4.2 * s, 3.2 * s, 1.2 * s), stone)
        k.box("PagodaWall", (px, py, 2.4 * s), (3.6 * s, 2.6 * s, 2.4 * s), wall)
        for c in range(5):
            k.box("PagodaPost", (px - 1.6 * s + c * 0.8 * s, py - 1.32 * s, 2.4 * s), (0.18 * s, 0.1, 2.4 * s), red)
        for tier in range(2):
            z = (3.9 + tier * 2.0) * s
            k.cyl("PagodaRoof", (px, py, z), (3.4 - tier * 0.9) * s, (0.9 - tier * 0.3) * s, 0.9 * s, roof, 4, rot=(0, 0, 45))
            if tier == 0:
                k.box("PagodaStory", (px, py, z + 1.0 * s), (2.2 * s, 1.8 * s, 1.2 * s), red)
        k.cyl("PagodaFinial", (px, py, 7.7 * s), 0.1 * s, 0.02, 1.0 * s, brass, 6)
    for tx, ty, s in [(-6.6, 8.6, 1.0), (6.9, 8.9, 1.05), (-12.4, 9.0, 1.2), (12.6, 9.2, 1.2), (-4.0, 15.0, 0.9), (4.4, 15.5, 0.9)]:
        k.cyl("SakuraTrunk", (tx, ty, 1.5 * s), 0.26 * s, 0.14 * s, 3.0 * s, bark, 8)
        k.beam("SakuraBranch", (tx, ty, 2.4 * s), (tx + 0.9 * s, ty - 0.2, 3.3 * s), 0.09 * s, bark)
        k.beam("SakuraBranch", (tx, ty, 2.6 * s), (tx - 0.8 * s, ty + 0.1, 3.5 * s), 0.08 * s, bark)
        for j in range(10):
            a = j * 2.39
            r = (0.5 + k.rng.random() * 0.9) * s
            k.ball("SakuraCrown", (tx + math.cos(a) * r, ty + math.sin(a) * r * 0.5, (3.3 + k.rng.random() * 1.1) * s),
                   ((0.55 + k.rng.random() * 0.35) * s,) * 3, blossom, 2)
    for i in range(7):
        x = -15 + i * 5
        k.ball("Cliff", (x, 20 + k.rng.random() * 3, -1.0), (3.4, 2.4, 3.0 + k.rng.random() * 2), moss, 1)
    for sx in (-1, 1):
        for i in range(6):
            k.ball("FlowerBush", (sx * (5.6 + i * 0.25), 4.45 + (i % 2) * 0.1, 0.25), (0.32, 0.22, 0.26), blossom, 1)

    # Corner blockers: two stacked chests with jade panels, as in the concept.
    for sx, side in ((-1, "L"), (1, "R")):
        def stack(sx=sx):
            cx = sx * 7.8
            chest(k, (cx, 0.2, 0.5), (1.2, 1.1, 1.0), crate, jade, brass)
            chest(k, (cx + sx * 0.05, 0.25, 1.45), (1.05, 0.95, 0.9), crate, jade, brass)
        k.group("Blocker_" + side, k.collect(stack))


# --- Forja do sol vermelho ---------------------------------------------------
def build_forge(k):
    floor_mat = k.tex("piso_basalto", "piso_basalto.png", 2.0)
    basalt = k.tex("parede_basalto", "parede_basalto.png", 2.5)
    lava = k.tex("glow_lava", "lava.png", 3.0, 1.5)
    lava_fall = k.tex("glow_lava_vertical", "lava_vertical.png", 2.0, 1.5)
    crust = k.tex("crosta_vulcanica", "crosta_vulcanica.png", 2.5)
    iron = k.tex("ferro", "ferro.png", 1.2)
    brass = k.tex("latao", "latao.png", 1.0)
    bricks = k.tex("tijolos_escuros", "tijolos_escuros.png", 1.4)
    flag = k.tex("estandarte_fogo", "estandarte_fogo.png")
    vent = k.tex("glow_abertura", "abertura_forja.png", 0.0, 1.0)
    sun = k.tex("glow_sol", "sol_vermelho.png", 0.0, 1.0)
    fire = k.mat("glow_fire", (1.0, 0.42, 0.08), 2.0)
    rune = k.mat("rune", (1.0, 0.48, 0.12), 1.4)
    floor(k, floor_mat, basalt)
    x0, x1, yf, yb = STAGE_FLOOR[k.stage]

    # Precipice: basalt cliffs under the bridge, lava far below and behind.
    for sx in (-1, 1):
        k.box("Cliff", (sx * (x1 - 0.7), 0, -5.0), (1.4, yb - yf, 9.4), basalt)
    k.box("FrontCliff", (0, yf + 0.3, -4.5), (x1 * 2, 0.6, 8.4), basalt)
    surroundings(k, basalt, lava, basalt, sea_z=-2.6, peak_radius=55.0, skip_back=False)
    for i in range(16):
        k.ball("CrustIsland", (k.rng.uniform(-24, 24), k.rng.uniform(6, 26), -2.5), (k.rng.uniform(1, 2.6), k.rng.uniform(0.8, 1.8), 0.4), crust, 1)

    # Bridge rims with brass brackets (the corner blockers) and the heat curtain.
    for sx, side in ((-1, "L"), (1, "R")):
        def rim(sx=sx):
            x = sx * 7.3
            k.box("Rim", (x, (yf + yb) / 2, 0.25), (0.5, yb - yf, 0.5), iron)
            for y in (-3.8, -2.0, -0.2, 1.6, 3.2):
                k.box("RimBracket", (x, y, 0.32), (0.62, 0.32, 0.62), brass)
            k.box("RimPost", (x, yb - 0.3, 0.75), (0.5, 0.5, 1.5), iron)
            k.box("RimPostCap", (x, yb - 0.3, 1.55), (0.6, 0.6, 0.12), brass)
        k.group("Blocker_" + side, k.collect(rim))
        k.panel("Barrier_" + side, (sx * 6.95, -0.2, 2.0), 7.6, 4.0, rune, "-x" if sx > 0 else "+x")
    k.box("FrontRim", (0, yf + 0.1, 0.12), (x1 * 2, 0.3, 0.24), iron)

    # Cracked basalt blocks along the back edge, between the pillars.
    for i in range(7):
        x = -4.2 + i * 1.4
        k.box("BackBlock", (x, 4.5, 0.42), (1.05, 0.9, 0.84), basalt, rot=(0, k.rng.uniform(-6, 6), k.rng.uniform(-8, 8)))
        k.box("BackCrack", (x, 4.04, 0.45), (0.8, 0.03, 0.06), lava, rot=(0, k.rng.uniform(-25, 25), 0))

    # Brick pillars with banners, braziers and great chains.
    for sx, side in ((-1, "L"), (1, "R")):
        px = sx * 5.6
        k.box("Pillar", (px, 4.6, 5.5), (1.7, 1.7, 11.0), bricks)
        for z in (2.4, 7.0):
            k.box("PillarBand", (px, 4.6, z), (1.84, 1.84, 0.34), brass)
        banner(k, "Banner_" + side, (px, 3.72, 6.6), 1.15, 3.2, flag)
        k.box("BrazierBlock", (px, 3.1, 0.5), (1.0, 1.0, 1.0), iron)
        k.cyl("BrazierBowl", (px, 3.1, 1.25), 0.45, 0.72, 0.5, brass, 12)
        for j in range(4):
            a = j * math.pi / 2 + 0.4
            k.cyl("BrazierFlame", (px + math.cos(a) * 0.22, 3.1 + math.sin(a) * 0.22, 1.9), 0.25, 0.02, 0.95, fire, 6)
        chain(k, (px, 4.6, 10.2), (sx * 15.0, 5.5, 4.0), iron, 22)

    # Hanging cage lantern.
    chain(k, (0.9, 5.4, 14.0), (0.9, 5.4, 9.0), iron, 12)
    k.ring("CageTop", (0.9, 5.4, 8.8), 0.5, 0.05, iron)
    k.ring("CageBottom", (0.9, 5.4, 7.5), 0.5, 0.05, iron)
    for j in range(8):
        a = j * math.pi / 4
        k.beam("CageBar", (0.9 + math.cos(a) * 0.5, 5.4 + math.sin(a) * 0.5, 7.5), (0.9 + math.cos(a) * 0.5, 5.4 + math.sin(a) * 0.5, 8.8), 0.03, iron)
    k.box("CageGlow", (0.9, 5.4, 7.9), (0.34, 0.34, 0.42), fire)

    # Fortress with glowing vents, lava falls and the red sun in a black sky.
    for fx, fy, w, h in [(-14, 24, 7, 8), (-6, 28, 6, 11), (2, 26, 9, 13), (11, 24, 7, 9), (18, 27, 6, 7)]:
        k.box("Fortress", (fx, fy, -1.4 + h / 2), (w, 3.0, h), bricks)
        for c in range(int(w)):
            k.box("Battlement", (fx - w / 2 + 0.5 + c, fy - 0.1, -1.4 + h + 0.35), (0.5, 3.1, 0.7), bricks)
        for wx in range(2):
            k.panel("Vent", (fx - w * 0.2 + wx * w * 0.4, fy - 1.52, -1.4 + h * 0.6), 0.7, 2.0, vent, "front")
        k.panel("LavaFall", (fx + w * 0.3, fy - 1.55, -1.4 + h * 0.4), 1.2, h * 0.8, lava_fall, "front")
    k.panel("Sun", (-1.5, 46, 11.5), 15, 15, sun, "front")
    for sx in (-1, 1):
        for i in range(3):
            k.ball("SideCrag", (sx * (11 + i * 3), 10 + i * 3, 0.5), (2.2, 2.0, 3.5 + i), basalt, 1)
            k.panel("SideFall", (sx * (11 + i * 3) - sx * 1.0, 10 + i * 3 - 2.0, 1.5), 0.9, 4.5, lava_fall, "front")


# --- Bazar fechado -----------------------------------------------------------
PALETTE = [(0.62, 0.14, 0.16), (0.16, 0.28, 0.56), (0.86, 0.66, 0.22), (0.20, 0.44, 0.34), (0.50, 0.22, 0.48), (0.88, 0.82, 0.70), (0.72, 0.36, 0.14)]
SKIN = [(0.88, 0.70, 0.56), (0.74, 0.52, 0.38), (0.55, 0.37, 0.26), (0.40, 0.26, 0.18)]


def person(k, idx, feet, scale, cheer):
    rng = k.rng
    c = rng.randrange(len(PALETTE))
    cloth = k.mat("cloth_%d" % c, PALETTE[c])
    cloth2 = k.mat("cloth_%d" % (idx % len(PALETTE)), PALETTE[idx % len(PALETTE)])
    skin = k.mat("skin_%d" % (idx % len(SKIN)), SKIN[idx % len(SKIN)])
    dark = k.mat("trousers", (0.16, 0.13, 0.12))
    x, y, z = feet
    s = scale

    def build():
        for sx in (-1, 1):
            k.box("Leg", (x + sx * 0.08 * s, y, z + 0.32 * s), (0.12 * s, 0.13 * s, 0.64 * s), dark)
        k.cyl("Robe", (x, y, z + 0.8 * s), 0.26 * s, 0.19 * s, 0.7 * s, cloth, 10)
        k.cyl("Torso", (x, y, z + 1.33 * s), 0.2 * s, 0.17 * s, 0.42 * s, cloth2 if idx % 3 == 0 else cloth, 10)
        for sx in (-1, 1):
            if cheer and (sx == 1 or idx % 2 == 0):
                k.beam("Arm", (x + sx * 0.2 * s, y, z + 1.5 * s), (x + sx * 0.34 * s, y - 0.05, z + 2.05 * s), 0.055 * s, cloth)
                k.ball("Hand", (x + sx * 0.35 * s, y - 0.05, z + 2.1 * s), (0.06 * s,) * 3, skin)
            else:
                k.beam("Arm", (x + sx * 0.2 * s, y, z + 1.5 * s), (x + sx * 0.26 * s, y - 0.04, z + 1.0 * s), 0.055 * s, cloth)
        k.ball("Head", (x, y, z + 1.72 * s), (0.13 * s, 0.13 * s, 0.15 * s), skin, 2)
        hat = idx % 4
        if hat == 0:
            k.ball("Turban", (x, y, z + 1.83 * s), (0.16 * s, 0.16 * s, 0.1 * s), cloth2, 1)
        elif hat == 1:
            k.cyl("Fez", (x, y, z + 1.9 * s), 0.1 * s, 0.08 * s, 0.14 * s, k.mat("fez_red", (0.66, 0.10, 0.10)), 10)
        elif hat == 2:
            k.ball("Scarf", (x, y + 0.02, z + 1.74 * s), (0.155 * s, 0.15 * s, 0.17 * s), cloth, 1)
        else:
            k.ball("Hair", (x, y + 0.02, z + 1.79 * s), (0.135 * s, 0.13 * s, 0.1 * s), k.mat("hair", (0.12, 0.09, 0.07)), 1)
    k.group("Crowd_%02d" % idx, k.collect(build), origin=feet)


def cart(k, sx, side, wood, iron, jute, spice, rug):
    cx = sx * 8.0

    def build():
        k.box("CartBed", (cx, 0, 0.95), (2.2, 1.6, 0.18), wood)
        for dy in (-0.75, 0.75):
            k.box("CartSide", (cx, dy, 1.25), (2.2, 0.08, 0.45), wood)
        k.box("CartEnd", (cx - sx * 1.06, 0, 1.25), (0.08, 1.6, 0.45), wood)
        for wx in (-0.6, 0.6):
            for wy in (-0.86, 0.86):
                k.cyl("Wheel", (cx + wx, wy, 0.55), 0.55, 0.55, 0.1, wood, 14, rot=(90, 0, 0))
                k.ring("WheelRim", (cx + wx, wy, 0.55), 0.53, 0.04, iron, rot=(90, 0, 0))
                k.cyl("WheelHub", (cx + wx, wy - 0.06 * (1 if wy < 0 else -1), 0.55), 0.1, 0.1, 0.12, iron, 8, rot=(90, 0, 0))
        k.beam("Shaft", (cx + sx * 1.0, -0.5, 0.95), (cx + sx * 2.6, -0.5, 0.45), 0.06, wood)
        k.beam("Shaft", (cx + sx * 1.0, 0.5, 0.95), (cx + sx * 2.6, 0.5, 0.45), 0.06, wood)
        for i in range(3):
            sack_x = cx - 0.6 + i * 0.55
            k.ball("Sack", (sack_x, -0.2 + (i % 2) * 0.4, 1.45), (0.32, 0.3, 0.3), jute, 1)
            k.cyl("SpiceHeap", (sack_x, -0.2 + (i % 2) * 0.4, 1.78), 0.22, 0.02, 0.18, spice, 10)
        k.cyl("RugRoll", (cx + 0.1, 0.4, 1.72), 0.18, 0.18, 1.9, rug, 12, rot=(0, 90, 0))
    k.group("Blocker_" + side, k.collect(build))


def build_bazaar(k):
    floor_mat = k.tex("piso_calcario", "piso_calcario.png", 1.6)
    wall = k.tex("parede_arenito", "parede_arenito.png", 2.0)
    tile = k.tex("azulejo_cobalto", "azulejo_cobalto.png", 0.8)
    brass = k.tex("latao", "latao.png", 1.0)
    carpet = k.tex("tapete_central", "tapete_central.png")
    crimson = k.tex("tecido_carmesim", "tecido_carmesim.png", 1.5)
    navy = k.tex("tecido_azul_marinho", "tecido_azul_marinho.png", 1.5)
    wood = k.tex("madeira_carrinhos", "madeira_carrinhos.png", 1.0)
    glass = k.tex("glow_vitral", "vitral.png", 0.0, 0.8)
    frieze = k.tex("friso_azul_dourado", "friso_azul_dourado.png", 1.2)
    jute = k.tex("juta", "juta.png", 0.6)
    spice = k.tex("especiaria_amarela", "especiaria_amarela.png", 0.5)
    view = k.tex("glow_corridor", "corridor_view.png", 0.0, 0.6)
    cream = k.mat("pedra_creme", (0.93, 0.87, 0.74))
    cobalt = k.mat("cobalto", (0.16, 0.24, 0.52))
    iron = k.mat("ferro", (0.22, 0.20, 0.20))
    lamp = k.mat("glow_lamp", (1.0, 0.76, 0.36), 1.4)
    floor(k, floor_mat, wall)
    k.panel("Carpet", (0, -0.7, 0.012), 8.6, 5.2, carpet, "up")

    # The hall is a closed box (floor, walls, ceiling, front and back), so no view leaves the map.
    k.box("Ceiling", (0, 1.3, 9.8), (19.9, 31.2, 0.4), wall)
    for sx, side in ((-1, "L"), (1, "R")):
        k.box("SideWall", (sx * 9.8, 1.3, 4.9), (0.4, 31.2, 9.8), wall)
    k.box("BackWall", (0, 16.8, 4.9), (19.9, 0.4, 9.8), wall)
    k.box("FrontWall", (0, -14.2, 4.9), (19.9, 0.4, 9.8), wall)

    # Back arcade: one solid wall with three round-topped openings, wedge arches
    # striped cobalt and cream, tiled columns and brass capitals.
    col_y = 5.4
    arcade = k.box("ArcadeWall", (0, col_y, 4.9), (19.6, 0.8, 9.8), wall)
    for cx, r in ((-5.15, 1.95), (0.0, 2.2), (5.15, 1.95)):
        k.cut_arch(arcade, cx, col_y, 4.3, r)
        k.arch("ArchStone", cx, col_y - 0.48, 4.3, r, 0.18, [cobalt, cream])
    for cx in (-7.6, -2.7, 2.7, 7.6):
        k.box("ColumnBase", (cx, col_y - 0.2, 0.3), (1.2, 1.0, 0.6), cream)
        k.box("Column", (cx, col_y - 0.15, 2.3), (1.0, 0.9, 3.4), wall)
        k.panel("ColumnTile", (cx, col_y - 0.61, 2.3), 0.76, 3.0, tile, "front")
        k.box("ColumnCap", (cx, col_y - 0.15, 4.15), (1.3, 1.1, 0.35), brass)
    k.panel("Frieze", (0, col_y - 0.41, 7.05), 19.0, 0.55, frieze, "front")
    for i in range(6):
        x = -6.25 + i * 2.5
        k.panel("StainedGlass", (x, col_y - 0.41, 8.2), 1.2, 1.5, glass, "front")
        k.arch("WindowArch", x, col_y - 0.45, 8.95, 0.6, 0.1, [cream], 7, 1.0, 0.12)
    for cx in (-4.5, 4.5):
        k.panel("VaultStar", (cx, 1.0, 9.59), 3.2, 3.2, tile, "up", rot_z=45)

    # Tiled dado, drapes and wall lamps on the side walls.
    for sx, side in ((-1, "L"), (1, "R")):
        wx = sx * 9.6
        k.panel("SideDado", (wx - sx * 0.01, 0.4, 0.9), 9.6, 1.4, tile, "-x" if sx > 0 else "+x")
        banner(k, "Banner_" + side, (wx - sx * 0.2, 3.6, 7.6), 0.9, 2.8, crimson)
        k.beam("LampArm", (wx, 1.0, 5.6), (wx - sx * 0.8, 1.0, 5.6), 0.04, iron)
        k.cyl("WallLamp", (wx - sx * 0.8, 1.0, 5.1), 0.22, 0.18, 0.6, lamp, 8)

    # Market bays behind the side arches: counters, awnings, jars and fabrics.
    for sx in (-1, 1):
        bx = sx * 5.15
        # Closes the bay from the corridor wall to the side wall, so no sky shows through.
        k.box("BayBack", (sx * 6.25, 8.0, 4.8), (6.8, 0.4, 9.6), wall)
        k.box("Counter", (bx, 6.6, 0.5), (3.6, 0.9, 1.0), wood)
        k.box("Awning", (bx, 6.2, 3.3), (4.0, 1.6, 0.06), crimson if sx > 0 else navy, rot=(-16, 0, 0))
        for i in range(4):
            k.cyl("SpiceBowl", (bx - 1.2 + i * 0.8, 6.55, 1.08), 0.28, 0.18, 0.16, brass, 12)
            k.cyl("SpiceCone", (bx - 1.2 + i * 0.8, 6.55, 1.3), 0.26, 0.02, 0.3, spice if i % 2 else crimson, 10)
        for i in range(3):
            k.cyl("Jar", (bx - 1.6 + i * 1.6, 5.9, 0.35), 0.2, 0.14, 0.7, brass, 10)
        for j in range(3):
            k.box("FabricStack", (bx + sx * 1.6, 7.6, 0.4 + j * 0.25), (0.9, 0.6, 0.22), navy if j % 2 else crimson)

    # Crowd corridor behind the middle arch.
    for sx in (-1, 1):
        k.box("CorridorWall", (sx * 2.9, 11.0, 3.4), (0.5, 11.0, 6.8), wall)
        k.panel("CorridorDado", (sx * 2.64, 11.0, 0.8), 11.0, 1.2, tile, "-x" if sx > 0 else "+x")
    k.box("CorridorRoof", (0, 11.0, 6.9), (6.4, 11.0, 0.3), wall)
    k.panel("CorridorView", (0, 16.4, 2.6), 5.4, 5.2, view, "front")
    k.box("Balustrade", (0, 6.15, 0.5), (5.2, 0.3, 1.0), cream)
    for i in range(9):
        k.cyl("Baluster", (-2.2 + i * 0.55, 6.0, 0.45), 0.08, 0.1, 0.8, brass, 8)
    k.box("BalustradeRail", (0, 6.0, 0.95), (5.2, 0.36, 0.1), brass)
    idx = 0
    for row in range(4):
        y = 6.9 + row * 1.25
        z = row * 0.38
        if row:
            k.box("Stand", (0, y, z / 2), (5.2, 1.25, z), wall)
        for col in range(6):
            x = -2.2 + col * 0.88 + (0.44 if row % 2 else 0)
            if abs(x) > 2.3:
                continue
            person(k, idx, (x + k.rng.uniform(-0.1, 0.1), y + k.rng.uniform(-0.1, 0.1), z), k.rng.uniform(0.85, 1.08), k.rng.random() < 0.35)
            idx += 1
    for ly in (9.0, 12.5):
        k.cyl("CorridorLamp", (0, ly, 5.6), 0.2, 0.16, 0.5, lamp, 8)

    # Great hanging lantern over the carpet.
    k.beam("LanternChain", (0, 1.8, 9.4), (0, 1.8, 6.8), 0.03, brass)
    k.cyl("LanternBody", (0, 1.8, 6.3), 0.4, 0.3, 0.9, lamp, 8)
    k.cyl("LanternTop", (0, 1.8, 6.9), 0.45, 0.06, 0.35, brass, 8)
    k.cyl("LanternBottom", (0, 1.8, 5.75), 0.06, 0.3, 0.25, brass, 8)

    for sx, side in ((-1, "L"), (1, "R")):
        cart(k, sx, side, wood, iron, jute, spice, navy)


# --- Praia do menu principal (concept-art/ui/menu-principal-praia-v1.png) -------
# Framed for the fixed menu camera: Blender (1.2, -12.2, 2.8) looking along +Y.
SHORE = [(7.5, -40), (6.5, -12), (5.0, -4), (3.5, 4), (2.0, 14), (0.5, 24), (-1.5, 33), (-5, 42), (-10, 52), (-18, 62), (-30, 72), (-60, 90)]


def flat_mesh(k, name, rows, mat, uvs=None):
    """Quad strip from paired vertex rows [(a, b), ...]; optional explicit per-vertex UVs."""
    import bmesh
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    verts = [(bm.verts.new(a), bm.verts.new(b)) for a, b in rows]
    for i in range(len(verts) - 1):
        (a0, b0), (a1, b1) = verts[i], verts[i + 1]
        face = bm.faces.new((a0, b0, b1, a1))
        if uvs:
            for loop, uv in zip(face.loops, (uvs[i][0], uvs[i][1], uvs[i + 1][1], uvs[i + 1][0])):
                loop[uv_layer].uv = uv
    for face in bm.faces:
        face.normal_update()
        if face.normal.z < 0:
            face.normal_flip()
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)
    if uvs:
        obj.data.materials.append(mat)
        return obj
    return k._finish(obj, name, mat, (0, 0, 0))


def card(k, name, center, w, h, mat, rot):
    """Alpha-cut foliage card (cutout_* material), rotation in degrees."""
    obj = k.panel(name, center, w, h, mat, "up")
    obj.rotation_euler = tuple(math.radians(a) for a in rot)
    return obj


def palm(k, base, lean, height, trunk, fronds, nut):
    pts = []
    for i in range(8):
        t = i / 7
        pts.append(Vector((base[0] + lean[0] * t * t, base[1] + lean[1] * t * t, base[2] + height * t)))
    for a, b in zip(pts, pts[1:]):
        k.beam("PalmTrunk", a, b, 0.2 - 0.07 * ((a.z - base[2]) / height), trunk)
    top = pts[-1]
    for j in range(9):
        yaw = j * 40 + k.rng.uniform(-10, 10)
        d = Vector((math.cos(math.radians(yaw)), math.sin(math.radians(yaw)), 0))
        card(k, "PalmFrond", top + d * 1.5 - Vector((0, 0, 0.45)), 3.4, 1.4, fronds, (0, k.rng.uniform(22, 38), yaw))
    for j in range(3):
        a = j * 2.1
        k.ball("Coconut", (top.x + math.cos(a) * 0.22, top.y + math.sin(a) * 0.22, top.z - 0.25), (0.16, 0.16, 0.17), nut, 1)


def house(k, x, y, z, w, d, h, walls, roof, wood, glass, pots, flowers, balcony=False):
    k.box("HouseWall", (x, y, z + h / 2), (w, d, h), walls)
    obj = k.cyl("HouseRoof", (x, y, z + h + 0.55), 1.0, 0.25, 1.1, roof, 4, rot=(0, 0, 45))
    obj.scale = ((w + 0.6) / 1.414, (d + 0.6) / 1.414, 1.0)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    box_uv(obj, 1.2)
    k.box("Door", (x - w * 0.25, y - d / 2 - 0.02, z + 0.9), (0.8, 0.05, 1.8), wood)
    for wx in (0.1, 0.35):
        k.box("Window", (x + w * wx, y - d / 2 - 0.02, z + h * 0.62), (0.6, 0.05, 0.7), glass)
        k.box("Shutter", (x + w * wx - 0.42, y - d / 2 - 0.03, z + h * 0.62), (0.22, 0.04, 0.75), wood)
    if balcony:
        k.box("Balcony", (x + w * 0.22, y - d / 2 - 0.45, z + h * 0.42), (1.8, 0.9, 0.12), wood)
        for i in range(6):
            k.box("BalconyRail", (x + w * 0.22 - 0.85 + i * 0.34, y - d / 2 - 0.88, z + h * 0.42 + 0.35), (0.06, 0.06, 0.6), wood)
        k.box("BalconyTop", (x + w * 0.22, y - d / 2 - 0.88, z + h * 0.42 + 0.66), (1.8, 0.08, 0.08), wood)
    for px in (-w * 0.42, w * 0.42):
        k.box("FlowerPot", (x + px, y - d / 2 - 0.3, z + 0.2), (0.4, 0.4, 0.4), pots)
        card(k, "PotFlowers", (x + px, y - d / 2 - 0.32, z + 0.55), 0.8, 0.8, flowers, (90, 0, 0))


def build_beach(k):
    sand = k.tex("areia", "areia.png", 3.0)
    rock = k.tex("pedras", "pedras.png", 2.2)
    bricks = k.tex("tijolos_brancos", "tijolos_brancos.png", 1.4)
    tiles = k.tex("telhas", "telhas-azul-marinho-v1.png", 1.2)
    palm_bark = k.tex("palmeira_tronco", "palmeira_tronco.png", 1.0)
    tree_bark = k.tex("arvore_tronco", "arvore_tronco.png", 1.5)
    planks = k.tex("madeira_barco", "madeira_barco.png", 1.0)
    grass = k.tex("grama", "grama.png", 3.0)
    seabed = k.tex("leito_areia", "areia.png", 3.0)
    water = k.mat("water_toon", (0.2, 0.6, 0.8))
    leaves = k.tex("cutout_folhas", "folhas.png")
    fronds = k.tex("cutout_palmeira", "palmeira_folhas.png")
    flowers = k.tex("cutout_flores", "flores.png")
    corals = k.tex("cutout_corais", "corais.png")
    glass = k.mat("janela", (0.16, 0.30, 0.34))
    pots = k.mat("terracota", (0.72, 0.36, 0.22))
    nut = k.mat("coco", (0.45, 0.30, 0.14))
    sail = k.mat("vela", (0.93, 0.88, 0.76))

    # Land to the left of the shoreline; the seabed slopes down from it under a
    # transparent water surface, so the toon water shader can read the depth.
    flat_mesh(k, "Sand", [((x - 0.4, y, 0.0), (-220.0, y, 0.0)) for x, y in SHORE], sand)
    near, far = [], []
    for i, (x, y) in enumerate(SHORE):
        prev, nxt = SHORE[max(i - 1, 0)], SHORE[min(i + 1, len(SHORE) - 1)]
        n = Vector((nxt[1] - prev[1], -(nxt[0] - prev[0]), 0)).normalized()
        shore = Vector((x - 0.4, y, 0.0))
        mid = Vector((x, y, 0.0)) + n * SEABED_SHELF + Vector((0, 0, -SEABED_SHELF_DEPTH))
        out = Vector((x, y, 0.0)) + n * SEABED_DROP + Vector((0, 0, -SEABED_DEPTH))
        near.append((tuple(shore), tuple(mid)))
        far.append((tuple(mid), tuple(out)))
    flat_mesh(k, "SeabedShelf", near, seabed)
    flat_mesh(k, "SeabedSlope", far, seabed)
    k.cyl("SeabedDeep", (0, 60, -SEABED_DEPTH - 0.05), 260, 260, 0.1, seabed, 64)
    water_rows = [((x - 0.6, y, WATER_Z), (260.0, y, WATER_Z)) for x, y in SHORE]
    water_rows.append(((-260.0, 260.0, WATER_Z), (260.0, 260.0, WATER_Z)))
    flat_mesh(k, "WaterSurface", water_rows, water)
    # Clouds occupy the top half of the painted sky: bring them down to 3-20 degrees of elevation.
    backdrop(k, radius=200.0, a_left=190.0, a_right=-10.0, segments=64, filename="ceu-praia-v1.png", v_rows=[(-6.0, 0.0), (10.0, 0.5), (75.0, 1.0)])

    # Hill with white houses and navy roofs, a stone wall and steps.
    k.ball("Hill", (-13, 42, -4.0), (18, 13, 11), grass, 2)
    k.ball("HillLow", (-6, 33, -2.5), (9, 6.5, 4.6), grass, 2)
    k.box("SeaWall", (-6.5, 28.0, 0.6), (8.0, 1.0, 1.2), rock)
    for i in range(6):
        k.box("Steps", (-2.6, 28.6 + i * 0.5, 0.15 + i * 0.32), (1.8, 0.5, 0.32), rock)
    house(k, -7.6, 31.0, 1.2, 5.0, 3.8, 3.8, bricks, tiles, planks, glass, pots, flowers, balcony=True)
    house(k, -5.4, 38.5, 2.8, 4.4, 3.4, 3.4, bricks, tiles, planks, glass, pots, flowers)
    house(k, -12.6, 37.5, 3.8, 5.2, 4.0, 4.0, bricks, tiles, planks, glass, pots, flowers, balcony=True)
    house(k, -7.6, 44.0, 5.4, 4.4, 3.4, 3.4, bricks, tiles, planks, glass, pots, flowers)

    # Palms along the beach.
    for base, lean, h in [((-3.5, 18.0, 0), (2.2, 1.0), 8.5), ((-6.0, 26.0, 0), (-1.0, 0.8), 9.2), ((-1.8, 28.5, 0), (1.6, 0.5), 7.6), ((-2.6, 44.0, 2.0), (1.0, 0.0), 7.0)]:
        palm(k, base, lean, h, palm_bark, fronds, nut)

    # Pier with crates and the moored sailing boat.
    pier_y = 33.0
    k.box("PierDeck", (5.0, pier_y, 0.75), (13.0, 1.8, 0.16), planks)
    for i in range(7):
        for dy in (-0.85, 0.85):
            k.cyl("PierPost", (-1.0 + i * 2.0, pier_y + dy, 0.0), 0.12, 0.12, 1.7, planks, 8)
    for cx, cz in [(9.8, 1.15), (10.6, 1.15), (10.2, 1.85)]:
        k.box("Crate", (cx, pier_y + 0.2, cz), (0.7, 0.7, 0.7), planks)
    hull = [(-2.2, 0.9), (2.4, 1.1), (1.6, -0.2), (-1.7, -0.2)]
    k.prism("BoatHull", [(12.5 + x, z) for x, z in hull], 35.2, 1.6, planks)
    k.box("BoatDeck", (12.6, 35.2, 0.98), (3.6, 1.4, 0.08), planks)
    k.cyl("Mast", (12.3, 35.2, 3.5), 0.08, 0.06, 5.0, planks, 8)
    k.beam("Boom", (12.3, 35.2, 2.0), (14.4, 35.2, 2.1), 0.05, planks)
    k.cyl("FurledSail", (13.3, 35.2, 2.25), 0.16, 0.12, 2.0, sail, 8, rot=(0, 88, 0))
    k.prism("Sail", [(12.4, 2.4), (12.4, 5.6), (14.2, 2.5)], 35.2, 0.04, sail)

    # Islets on the horizon.
    stone = k.mat("rocha_ilha", (0.62, 0.58, 0.52))
    stone_dark = k.mat("rocha_ilha_escura", (0.46, 0.44, 0.40))
    for ix, iy, s in [(40, 150, 1.0), (56, 164, 1.5), (72, 142, 0.8), (27, 172, 0.7), (88, 158, 0.6)]:
        k.ball("Islet", (ix, iy, 1.5 * s), (4.5 * s, 3.8 * s, 9.0 * s), stone, 1, rot=(0, k.rng.uniform(-12, 12), k.rng.uniform(0, 360)))
        k.ball("IsletSpur", (ix + 4.0 * s, iy - 1.0, 0.5 * s), (2.8 * s, 2.4 * s, 4.5 * s), stone_dark, 1, rot=(0, 14, k.rng.uniform(0, 360)))
        k.ball("IsletSpur", (ix - 3.6 * s, iy + 0.5, 0.2 * s), (2.2 * s, 2.0 * s, 3.0 * s), stone_dark, 1)
        for j in range(4):
            k.ball("IsletGreen", (ix + k.rng.uniform(-1.6, 1.6) * s, iy + k.rng.uniform(-1, 1) * s, (8.6 + k.rng.uniform(-0.6, 0.4)) * s),
                   (1.4 * s, 1.2 * s, 0.7 * s), grass, 1)

    # Framing tree on the left: thick trunk, branches arching over the top, leaf clusters.
    trunk_pts = [(-3.4, -4.0, 0.0), (-3.2, -3.6, 2.4), (-2.4, -3.0, 4.6)]
    for a, b in zip(trunk_pts, trunk_pts[1:]):
        k.beam("TreeTrunk", a, b, 0.62, tree_bark, 10)
    branch_ends = [(2.8, -2.0, 6.9), (-0.8, 0.8, 7.4), (5.8, 1.2, 7.1), (-4.0, -6.5, 5.2)]
    for end in branch_ends:
        k.beam("TreeBranch", trunk_pts[-1], end, 0.26, tree_bark, 8)
        for j in range(11):
            off = Vector((k.rng.uniform(-1.6, 1.6), k.rng.uniform(-1.4, 1.4), k.rng.uniform(-0.7, 0.6)))
            card(k, "TreeLeaf", Vector(end) + off, 1.7, 1.7, leaves, (k.rng.uniform(40, 140), k.rng.uniform(-30, 30), k.rng.uniform(0, 360)))
    for j in range(14):
        card(k, "CanopyLeaf", (k.rng.uniform(-3.5, 2.5), k.rng.uniform(-9.5, -6.0), k.rng.uniform(4.8, 6.0)), 1.5, 1.5, leaves,
             (k.rng.uniform(60, 120), k.rng.uniform(-30, 30), k.rng.uniform(0, 360)))

    # Foreground: orange rocks at the water's edge, hibiscus and leafy bushes on the left, corals in the shallows.
    for rx, ry, s in [(4.6, -7.2, 1.2), (5.8, -5.4, 0.9), (3.7, -8.8, 0.7), (6.4, -8.2, 1.0)]:
        k.ball("ShoreRock", (rx, ry, 0.15 * s), (0.9 * s, 0.8 * s, 0.6 * s), rock, 1, rot=(0, 0, k.rng.uniform(0, 360)))
    for bx, by in [(-2.7, -8.0), (-1.6, -9.2), (-3.4, -6.8)]:
        for j in range(5):
            card(k, "BushLeaf", (bx + k.rng.uniform(-0.4, 0.4), by + k.rng.uniform(-0.3, 0.3), 0.45 + j * 0.06), 1.1, 1.1, leaves,
                 (k.rng.uniform(55, 90), 0, k.rng.uniform(0, 360)))
        card(k, "Hibiscus", (bx + 0.2, by - 0.35, 0.75), 0.7, 0.7, flowers, (80, 0, k.rng.uniform(-20, 20)))
    for cx, cy in [(8.0, -2.0), (10.5, 2.5), (9.0, 6.5), (12.0, -5.0)]:
        # Corals rest on the seabed and are seen through the water.
        card(k, "Coral", (cx, cy, seabed_z(cx, cy) + 0.04), 1.6, 1.6, corals, (0, 0, k.rng.uniform(0, 360)))
    vegetation(k, leaves, fronds, flowers, rock, grass)
    # Sun path toward the back-right of the bay, where the light comes from.
    k.panel("SunGlints", (20, 52, 0.06), 26, 44, k.tex("glint_sol", "glints.png"), "up", rot_z=-18)
    foliage_wall(k, leaves, fronds, flowers, tree_bark)
    forest(k, sand)


WATER_Z = 0.05
SEABED_SHELF, SEABED_SHELF_DEPTH = 7.0, 0.9
SEABED_DROP, SEABED_DEPTH = 30.0, 4.0


def seabed_z(x, y):
    """Approximate seabed height at a point offshore."""
    dist = max(0.0, x - shore_x(y))
    if dist < SEABED_SHELF:
        return -SEABED_SHELF_DEPTH * dist / SEABED_SHELF
    t = min(1.0, (dist - SEABED_SHELF) / (SEABED_DROP - SEABED_SHELF))
    return -SEABED_SHELF_DEPTH - (SEABED_DEPTH - SEABED_SHELF_DEPTH) * t


def shore_x(y):
    """Shoreline x at depth y (linear between SHORE points)."""
    for (x0, y0), (x1, y1) in zip(SHORE, SHORE[1:]):
        if y0 <= y <= y1:
            return x0 + (x1 - x0) * (y - y0) / (y1 - y0)
    return SHORE[-1][0]


def foliage_wall(k, leaves, fronds, flowers, bark):
    """Cover the whole left third of the menu frame with foliage, as in the concept."""
    rng = k.rng
    # A second, darker tree behind the framing trunk.
    k.beam("BackTrunk", (-6.5, 4.0, 0.0), (-5.6, 4.6, 5.5), 0.5, bark, 10)
    k.beam("BackBranch", (-5.6, 4.6, 5.0), (-2.0, 3.0, 8.4), 0.22, bark, 8)
    # Layers of leaves from the ground to the top of the frame, between the camera and the hill.
    for layer, y in enumerate((-6.5, -3.5, -0.5, 3.0, 7.0)):
        d = y + 12.2
        left = 1.2 - 0.72 * d - 1.0
        right = 1.2 - 0.30 * d
        top = 2.8 + 0.42 * d + 1.0
        cols = max(3, int((right - left) / 0.9))
        rows = max(4, int(top / 0.9))
        for c in range(cols):
            for r in range(rows):
                x = left + (c + rng.random()) * (right - left) / cols
                z = (r + rng.random()) * top / rows
                # Thin out the middle band a little so the menu text stays readable.
                if 1.8 < z < top - 2.2 and rng.random() < 0.45:
                    continue
                size = rng.uniform(1.2, 2.0) * (1.0 + layer * 0.15)
                mat = fronds if rng.random() < 0.25 else leaves
                card(k, "WallLeaf", (x, y + rng.uniform(-0.6, 0.6), z), size, size, mat,
                     (rng.uniform(60, 120), rng.uniform(-35, 35), rng.uniform(0, 360)))
                if z < 2.0 and rng.random() < 0.12:
                    card(k, "WallFlower", (x, y - 0.4, z + 0.3), 0.7, 0.7, flowers, (85, 0, rng.uniform(-30, 30)))
    # Canopy closing the top-left corner above the title.
    for j in range(30):
        card(k, "TopLeftLeaf", (rng.uniform(-6.5, 0.5), rng.uniform(-8.5, -1.0), rng.uniform(5.6, 7.8)), 1.8, 1.8, leaves,
             (rng.uniform(70, 110), rng.uniform(-30, 30), rng.uniform(0, 360)))


def vegetation(k, leaves, fronds, flowers, rock, grass):
    """Dense left side as in the concept: grass beds, bushes, rocks, flowers and tall fronds."""
    rng = k.rng
    # Grass beds under everything, from the camera to the hill.
    for i in range(14):
        y = rng.uniform(-11.5, 30.0)
        x = rng.uniform(-9.0, min(shore_x(y) - 3.5, -0.5))
        r = rng.uniform(0.7, 1.6)
        k.cyl("GrassBed", (x, y, 0.012), r, r * 0.9, 0.02, grass, 9, rot=(0, 0, rng.uniform(0, 360)))
    for i in range(70):
        # Denser near the camera, where the concept frame is fullest.
        y = -11.5 + (rng.random() ** 1.6) * 40.0
        frame_left = 1.2 - 0.62 * (y + 12.2)
        x = rng.uniform(max(frame_left - 1.5, -12.0), min(shore_x(y) - 2.5, -0.3))
        kind = rng.random()
        near = 1.0 if y < -3 else 1.4
        if kind < 0.45:
            for j in range(rng.randint(5, 9)):
                card(k, "Bush", (x + rng.uniform(-0.5, 0.5), y + rng.uniform(-0.4, 0.4), rng.uniform(0.25, 0.95) * near),
                     rng.uniform(0.9, 1.5) * near, rng.uniform(0.9, 1.5) * near, leaves,
                     (rng.uniform(50, 100), rng.uniform(-25, 25), rng.uniform(0, 360)))
        elif kind < 0.62:
            for j in range(rng.randint(4, 7)):
                card(k, "GrassBlade", (x + rng.uniform(-0.3, 0.3), y + rng.uniform(-0.3, 0.3), 0.45 * near), 1.4 * near, 0.5 * near, fronds,
                     (rng.uniform(65, 95), rng.uniform(-60, -20), rng.uniform(0, 360)))
        elif kind < 0.80:
            card(k, "Flower", (x, y, rng.uniform(0.3, 0.9)), 0.7 * near, 0.7 * near, flowers, (rng.uniform(65, 95), 0, rng.uniform(-40, 40)))
            card(k, "FlowerLeaf", (x + 0.2, y + 0.15, 0.35), 0.9, 0.9, leaves, (rng.uniform(55, 90), 0, rng.uniform(0, 360)))
        else:
            s = rng.uniform(0.35, 0.9)
            k.ball("LeftRock", (x, y, 0.1 * s), (s, s * 0.9, s * 0.6), rock, 1, rot=(0, 0, rng.uniform(0, 360)))
    # Tall fronds right at the bottom-left corner of the frame.
    for j in range(10):
        card(k, "CornerFrond", (rng.uniform(-3.4, -1.2), rng.uniform(-10.6, -9.2), rng.uniform(0.6, 1.6)), 2.6, 1.1, fronds,
             (rng.uniform(70, 100), rng.uniform(-50, -15), rng.uniform(-60, 60)))


# --- Floresta e quadro de opções (concept-art/floresta-atlas, ui/quest-board-opcoes-floresta-v2) ---
# The clearing sits behind the foliage wall on the left of the menu frame. The menu
# camera flies through the corridor along CamPath_* and stops at CamBoard, facing the
# board (which faces +X). Godot overlays the options UI on QuestBoardPanel.
BOARD = Vector((-24.0, 1.0, 0.0))
CORRIDOR_Y = 1.0


def marker(name, loc):
    empty = bpy.data.objects.new(name, None)
    empty.location = loc
    bpy.context.collection.objects.link(empty)
    return empty


def forest_tex(k, name, meters=0.0, emit=0.0):
    return k.tex(name, "forest/" + name + ".png", meters, emit)


def forest_card(k, name, center, size, mat, rot):
    return card(k, name, center, size[0], size[1], mat, rot)


def big_tree(k, base, height, radius, bark, moss, root_mat, leaf_mats, lean=(0.0, 0.0)):
    """Thick trunk with flaring roots, a moss band and a cluster canopy."""
    bx, by, bz = base
    top = Vector((bx + lean[0], by + lean[1], bz + height))
    k.beam("ForestTrunk", (bx, by, bz - 0.3), top, radius, bark, 12)
    k.cyl("TrunkFlare", (bx, by, bz + 0.35), radius * 1.9, radius, 0.9, bark, 12)
    k.beam("TrunkMoss", (bx, by, bz + 0.6), (bx + lean[0] * 0.2, by + lean[1] * 0.2, bz + 2.2), radius * 1.03, moss, 12)
    for j in range(5):
        a = j * 2 * math.pi / 5 + k.rng.uniform(-0.3, 0.3)
        d = Vector((math.cos(a), math.sin(a), 0))
        forest_card(k, "Root", Vector((bx, by, bz + 0.25)) + d * (radius * 1.8), (2.2, 1.0), root_mat,
                    (k.rng.uniform(70, 90), 0, math.degrees(a) + 90))
    for j in range(4):
        a = j * math.pi / 2 + k.rng.uniform(0, 1)
        end = top + Vector((math.cos(a) * 3.0, math.sin(a) * 3.0, k.rng.uniform(0.5, 1.8)))
        k.beam("ForestBranch", top - Vector((0, 0, 1.0)), end, radius * 0.35, bark, 8)
        for n in range(9):
            off = Vector((k.rng.uniform(-1.8, 1.8), k.rng.uniform(-1.8, 1.8), k.rng.uniform(-0.8, 0.8)))
            forest_card(k, "Canopy", end + off, (2.4, 2.4), leaf_mats[n % len(leaf_mats)],
                        (k.rng.uniform(20, 160), k.rng.uniform(-40, 40), k.rng.uniform(0, 360)))


def undergrowth(k, center, spread, count, mats, scale=1.0):
    for n in range(count):
        x = center[0] + k.rng.uniform(-spread[0], spread[0])
        y = center[1] + k.rng.uniform(-spread[1], spread[1])
        s = k.rng.uniform(0.9, 1.6) * scale
        forest_card(k, "Undergrowth", (x, y, 0.45 * s), (1.3 * s, 1.3 * s), mats[n % len(mats)],
                    (k.rng.uniform(65, 100), k.rng.uniform(-20, 20), k.rng.uniform(0, 360)))


def quest_board(k):
    """Roofed wooden notice board facing +X, centred on BOARD (see the v2 concept)."""
    wood = forest_tex(k, "madeira-quadro", 1.2)
    stone = forest_tex(k, "pedra-fundacao", 1.0)
    brass = forest_tex(k, "latao", 0.6)
    tiles = forest_tex(k, "telhas-azul-marinho", 0.9)
    parchment = k.tex("cutout_painel", "forest/painel-pergaminho.png")
    banner_mat = k.tex("cutout_estandarte", "forest/estandarte-jade.png")
    lantern = k.tex("cutout_lanterna", "forest/lanterna.png")
    vine = k.tex("cutout_cipo", "forest/cipo.png")
    bx, by = BOARD.x, BOARD.y
    for side in (-1, 1):
        py = by + side * 2.05
        k.box("BoardStone", (bx, py, 0.2), (0.75, 0.75, 0.4), stone)
        k.box("BoardPost", (bx, py, 1.95), (0.32, 0.32, 3.5), wood)
        k.beam("BoardBrace", (bx, py, 1.0), (bx, py + side * 0.75, 0.05), 0.09, wood)
        for z in (1.05, 3.0):
            k.box("BoardCorner", (bx + 0.12, py, z), (0.1, 0.42, 0.34), brass)
        # Jade banners hang from the posts and sway (Banner_ prefix).
        top = (bx + 0.22, py + side * 0.05, 2.95)
        obj = k.panel("Banner_Board", (top[0], top[1], top[2] - 0.85), 0.55, 1.7, banner_mat, "+x")
        k.group("Banner_Board%d" % (side + 1), [obj], origin=top)
    # Backing boards, top beam with the carved wind emblem, bottom rail.
    k.box("BoardBack", (bx - 0.04, by, 2.05), (0.12, 3.8, 2.15), wood)
    k.box("BoardTopBeam", (bx, by, 3.25), (0.3, 4.6, 0.36), wood)
    k.box("BoardBottomRail", (bx, by, 0.92), (0.24, 4.1, 0.2), wood)
    k.ring("BoardEmblem", (bx + 0.17, by, 3.25), 0.16, 0.035, brass, rot=(0, 90, 0))
    # The parchment the options are drawn on (kept as its own node for Godot).
    panel = k.panel("QuestBoardPanel", (bx + 0.04, by, 2.06), 3.45, 1.95, parchment, "+x")
    panel.name = "QuestBoardPanel"
    # Tiled roof: a gable extruded along the board, with upturned ridge tips.
    k.prism("BoardRoof", [(bx - 1.05, 3.4), (bx + 1.05, 3.4), (bx, 3.95)], by, 5.6, tiles)
    k.box("BoardRidge", (bx, by, 3.98), (0.22, 5.7, 0.14), wood)
    for side in (-1, 1):
        k.box("RidgeTip", (bx, by + side * 2.9, 4.08), (0.22, 0.4, 0.22), wood, rot=(side * 25, 0, 0))
    # Lantern on the left (screen) post, vines over the top beam.
    k.beam("LanternHook", (bx + 0.1, by - 2.05, 3.0), (bx + 0.45, by - 2.05, 3.0), 0.03, brass)
    k.panel("BoardLantern", (bx + 0.5, by - 2.05, 2.62), 0.45, 0.8, lantern, "+x")
    for n in range(4):
        forest_card(k, "BoardVine", (bx + 0.22, by - 1.5 + n * 1.0, 3.32), (0.55, 0.62), vine, (90, 0, 90))


def forest(k, sand_dark):
    bark = forest_tex(k, "casca-arvore", 1.6)
    moss = forest_tex(k, "musgo-na-casca", 1.4)
    path_mat = forest_tex(k, "caminho-arenoso", 2.0)
    soil = forest_tex(k, "terra-umida", 3.0)
    litter = forest_tex(k, "serrapilheira", 2.5)
    rock = forest_tex(k, "pedra-laranja", 1.0)
    seat = forest_tex(k, "madeira-banco", 0.8)
    stone = forest_tex(k, "pedra-fundacao", 1.0)
    cut = lambda name: k.tex("cutout_" + name, "forest/" + name + ".png")
    leaves = [cut("monstera"), cut("folha-bananeira"), cut("folha-larga"), cut("galho-folhas")]
    ground_plants = [cut("samambaia-touceira"), cut("arbusto"), cut("tufo-grama"), cut("samambaia-folha"), cut("monstera")]
    flowers = [cut("hibisco"), cut("flores-brancas")]
    root_mat = cut("raiz")
    hanging = cut("folhagem-pendente")
    dry = cut("folha-seca")

    # Forest floor: leaf litter over the clearing and corridor, a sandy path through it.
    k.box("ForestFloor", (-17.0, 1.0, 0.012), (24.0, 24.0, 0.02), litter)
    k.box("ClearingSoil", (-21.5, 1.0, 0.018), (9.0, 9.0, 0.02), soil)
    for (a, b) in [((-3.0, -8.0), (-8.0, CORRIDOR_Y)), ((-8.0, CORRIDOR_Y), (-20.5, CORRIDOR_Y))]:
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, 0.024)
        length = math.dist(a, b)
        ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        k.box("ForestPath", mid, (length + 1.0, 2.0, 0.02), path_mat, rot=(0, 0, ang))
    for n in range(10):
        x = k.rng.uniform(-20, -6)
        forest_card(k, "DryLeaf", (x, CORRIDOR_Y + k.rng.uniform(-1, 1), 0.04), (0.35, 0.35), dry, (0, 0, k.rng.uniform(0, 360)))
    for x, y in [(-11.5, CORRIDOR_Y - 0.7), (-15.5, CORRIDOR_Y + 0.9), (-19.0, CORRIDOR_Y - 1.1), (-22.0, CORRIDOR_Y + 2.6)]:
        k.ball("PathRock", (x, y, 0.08), (0.45, 0.32, 0.18), rock, 1, rot=(0, 0, k.rng.uniform(0, 360)))

    # Two great trunks frame the corridor entrance (as in the passage concept), more trees around the clearing.
    big_tree(k, (-9.5, CORRIDOR_Y - 3.3, 0), 9.0, 0.85, bark, moss, root_mat, leaves, lean=(-0.5, -0.8))
    big_tree(k, (-10.5, CORRIDOR_Y + 3.6, 0), 9.5, 0.9, bark, moss, root_mat, leaves, lean=(-0.6, 1.0))
    for (x, y, h, r) in [(-15, -5.0, 10, 0.6), (-15.5, 7.5, 10, 0.65), (-21, -5.5, 11, 0.7), (-20, 8.0, 11, 0.7),
                         (-28, -3.5, 12, 0.8), (-28.5, 5.5, 12, 0.8), (-31, 1.0, 13, 0.9), (-25, -9, 11, 0.7),
                         (-25, 11, 11, 0.7), (-17, 12, 10, 0.6), (-17, -10, 10, 0.6), (-33, -7, 12, 0.8), (-33, 9, 12, 0.8)]:
        big_tree(k, (x, y, 0), h, r, bark, moss, root_mat, leaves)

    # Dense undergrowth: walls along the corridor and around the clearing, closing every gap.
    for (cx, cy, sx, sy, n) in [(-6.5, CORRIDOR_Y - 3.0, 2.0, 1.2, 14), (-6.5, CORRIDOR_Y + 3.0, 2.0, 1.2, 14),
                                (-13.0, CORRIDOR_Y - 2.6, 3.0, 1.0, 18), (-13.0, CORRIDOR_Y + 2.6, 3.0, 1.0, 18),
                                (-21.0, CORRIDOR_Y - 5.5, 4.5, 1.5, 22), (-21.0, CORRIDOR_Y + 5.5, 4.5, 1.5, 22),
                                (-27.5, CORRIDOR_Y, 2.0, 7.0, 34)]:
        undergrowth(k, (cx, cy), (sx, sy), n, ground_plants, 1.3)
    for (cx, cy) in [(-12.0, CORRIDOR_Y - 1.6), (-14.5, CORRIDOR_Y + 1.7), (-18.5, CORRIDOR_Y - 2.4), (-17.5, CORRIDOR_Y + 2.9)]:
        undergrowth(k, (cx, cy), (0.6, 0.4), 4, flowers, 0.9)
    for n in range(26):
        x = k.rng.uniform(-30, -8)
        y = k.rng.choice([k.rng.uniform(-10, -3), k.rng.uniform(5, 12)])
        forest_card(k, "HangingLeaves", (x, y, k.rng.uniform(4.5, 7.5)), (1.6, 2.2), hanging, (90, 0, k.rng.uniform(0, 360)))
    # Big leaves right beside the camera path, so the flight brushes through them.
    for (x, y, z, yaw) in [(-4.2, -6.4, 2.2, 30), (-5.6, -4.0, 1.4, -20), (-7.2, -1.2, 2.6, 60), (-8.6, 2.4, 1.6, -40),
                           (-9.6, -0.3, 2.9, 15), (-12.6, 2.1, 2.3, -60), (-13.4, -0.4, 1.4, 40)]:
        forest_card(k, "PassLeaf", (x, y, z), (2.2, 2.2), leaves[0 if yaw > 0 else 1], (k.rng.uniform(60, 110), k.rng.uniform(-30, 30), yaw))

    # Closed backdrop of foliage behind and above the clearing, so no sky shows through the trunks.
    for n in range(120):
        x = k.rng.uniform(-36, -27)
        y = k.rng.uniform(-11, 13)
        forest_card(k, "BackFoliage", (x, y, k.rng.uniform(0.5, 11.0)), (3.2, 3.2), leaves[n % len(leaves)],
                    (k.rng.uniform(70, 110), k.rng.uniform(-30, 30), 90 + k.rng.uniform(-35, 35)))
    for n in range(70):
        forest_card(k, "Canopy", (k.rng.uniform(-30, -9), k.rng.uniform(-9, 11), k.rng.uniform(7.5, 10.5)), (3.4, 3.4),
                    leaves[n % len(leaves)], (k.rng.uniform(-25, 25), k.rng.uniform(-25, 25), k.rng.uniform(0, 360)))
    quest_board(k)
    # Bench to the right of the board (screen right = +Y when facing the board).
    bx, by = BOARD.x + 1.6, BOARD.y + 4.2
    for dy in (-0.75, 0.75):
        k.box("BenchLeg", (bx, by + dy, 0.25), (0.45, 0.32, 0.5), stone)
    k.box("BenchSeat", (bx, by, 0.55), (0.6, 2.0, 0.12), seat)
    k.box("BenchBack", (bx - 0.28, by, 0.95), (0.1, 2.0, 0.55), seat, rot=(0, -10, 0))
    # Light shafts falling into the clearing.
    shaft = k.tex("glint_raio", "forest/raio.png")
    for (x, y) in [(-25.5, 3.6), (-26.0, -2.4)]:
        obj = k.panel("LightShaft", (x, y, 5.0), 1.4, 9.0, shaft, "+x")
        obj.rotation_euler = (math.radians(90), math.radians(-24), math.radians(90))

    # Camera markers for the flight into the clearing and the arcade select spot.
    for n, loc in enumerate([(1.2, -12.2, 2.8), (-1.5, -9.0, 2.3), (-5.0, -4.0, 1.9), (-8.0, CORRIDOR_Y, 1.8),
                             (-12.5, CORRIDOR_Y, 1.95), (-16.0, CORRIDOR_Y, 2.3)]):
        marker("CamPath_%d" % n, loc)
    marker("BoardLook", (BOARD.x, BOARD.y, 2.06))


BUILDERS = {"zephyr_dojo": build_zephyr, "molten_forge": build_forge, "storm_market": build_bazaar, "beach": build_beach}


def build_stage(stage_id: str):
    k = Kit(stage_id)
    BUILDERS[stage_id](k)
    merge_by_material()
