"""Low-poly rigid-part modelling in the Mega Man Legends (PS1) style.

Each body part is one closed mesh lofted through a few polygon rings between two
joints, so it can later follow exactly one bone. Positions are in metres, Blender
axes: +X character left, -Y front, +Z up.
"""
import bmesh
import bpy
from mathutils import Vector

# Unit cross-sections, (side, depth) in [-1, 1]; -depth faces the part's front.
OCT = [(-.41, -1), (.41, -1), (1, -.41), (1, .41), (.41, 1), (-.41, 1), (-1, .41), (-1, -.41)]
HEX = [(-.5, -1), (.5, -1), (1, 0), (.5, 1), (-.5, 1), (-1, 0)]
BOX = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
# Wide flat front for faces and chests, round back.
FACE = [(-.72, -1), (.72, -1), (1, -.45), (1, .35), (.62, 1), (-.62, 1), (-1, .35), (-1, -.45)]
FACE6 = [(-.7, -1), (.7, -1), (1, 0), (.7, 1), (-.7, 1), (-1, 0)]
# Flat sole for feet (depth axis points up along a foot).
SOLE = [(-1, -1), (1, -1), (1, .2), (.55, 1), (-.55, 1), (-1, .2)]


def frame(p0, p1, side=Vector((1, 0, 0)), back=Vector((0, 1, 0))):
    """Right-handed frame along p0->p1: local X stays near `side`, local Y near `back`."""
    z = (Vector(p1) - Vector(p0)).normalized()
    x = side - z * side.dot(z)
    if x.length < 1e-4:
        x = back.cross(z)
    x.normalize()
    y = z.cross(x)
    if y.dot(back) < 0:
        x, y = -x, -y
    return x, y, z


def loft(bm, p0, p1, rings, shape=OCT, cap0=True, cap1=True, side=Vector((1, 0, 0)), back=Vector((0, 1, 0))):
    """Rings are (t, half_side, half_depth[, shift_side, shift_depth]) along p0->p1."""
    p0, p1 = Vector(p0), Vector(p1)
    x, y, z = frame(p0, p1, side, back)
    loops = []
    for ring in rings:
        t, a, b = ring[:3]
        sx, sy = (ring[3], ring[4]) if len(ring) > 3 else (0.0, 0.0)
        c = p0.lerp(p1, t) + x * sx + y * sy
        loops.append([bm.verts.new(c + x * (a * u) + y * (b * v)) for u, v in shape])
    n = len(shape)
    for r0, r1 in zip(loops, loops[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((r0[i], r0[j], r1[j], r1[i]))
    if cap0:
        bm.faces.new(list(reversed(loops[0])))
    if cap1:
        bm.faces.new(loops[-1])
    return loops


def stack(bm, rings, shape=HEX, cap0=True, cap1=True):
    """Loft through rings (z, x0, x1, y0, y1[, tilt]): extents measured on a turnaround, so the
    front and profile silhouettes follow the drawing. `tilt` (dz per metre of x) leans a ring
    the way a drawn facet line crosses the limb, e.g. a knee crease higher on the inside."""
    loops = []
    for ring in sorted(rings):
        z, x0, x1, y0, y1 = ring[:5]
        tilt = ring[5] if len(ring) > 5 else 0.0
        cx, cy, a, b = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
        loops.append([bm.verts.new((cx + a * u, cy + b * v, z + tilt * a * u)) for u, v in shape])
    n = len(shape)
    for r0, r1 in zip(loops, loops[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((r0[i], r0[j], r1[j], r1[i]))
    if cap0:
        bm.faces.new(list(reversed(loops[0])))
    if cap1:
        bm.faces.new(loops[-1])


def tilted(bm, rings, direction, shape=HEX, cap0=True, cap1=True, side=Vector((1, 0, 0)), back=Vector((0, 1, 0))):
    """Loft through rings (cx, cy, cz, half_side, half_depth) that all lie perpendicular to
    `direction`, the way a drawn limb's facet lines cross it."""
    d = Vector(direction).normalized()
    x, y, _ = frame(Vector((0, 0, 0)), d, side, back)
    loops = [[bm.verts.new(Vector(c[:3]) + x * (c[3] * u) + y * (c[4] * v)) for u, v in shape] for c in rings]
    n = len(shape)
    for r0, r1 in zip(loops, loops[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((r0[i], r0[j], r1[j], r1[i]))
    if cap0:
        bm.faces.new(list(reversed(loops[0])))
    if cap1:
        bm.faces.new(loops[-1])


def poly(bm, verts, faces, mirror=False):
    """Explicit mesh: verts {name: (x, y, z)} in centimetres, faces as name tuples (n-gons).
    Used where the drawing's facets are read vertex by vertex."""
    vs = {k: bm.verts.new(((-v[0] if mirror else v[0]) / 100, v[1] / 100, v[2] / 100)) for k, v in verts.items()}
    for f in faces:
        bm.faces.new([vs[k] for k in f])


def ring_scaled(ring, z, k):
    """A ring moved to height z and shrunk by k about its centre (for tucks into a parent)."""
    _, x0, x1, y0, y1 = ring
    cx, cy, a, b = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2 * k, (y1 - y0) / 2 * k
    return (z, cx - a, cx + a, cy - b, cy + b)


def mirror_ring(ring):
    z, x0, x1, y0, y1 = ring[:5]
    return (z, -x1, -x0, y0, y1) + ((-ring[5],) if len(ring) > 5 else ())


def ball(bm, centre, r, sides=6):
    """Faceted bead: two cones of `sides` triangles each."""
    import math
    c = Vector(centre)
    ring = [bm.verts.new(c + Vector((math.cos(a) * r, 0, math.sin(a) * r)))
            for a in (i * 2 * math.pi / sides for i in range(sides))]
    front, rear = bm.verts.new(c + Vector((0, -r, 0))), bm.verts.new(c + Vector((0, r * .6, 0)))
    for i in range(sides):
        j = (i + 1) % sides
        bm.faces.new((ring[i], ring[j], front))
        bm.faces.new((ring[j], ring[i], rear))


def part(name, build, colour, collection):
    """Create one rigid part object from a bmesh builder; returns its triangle count."""
    me = bpy.data.meshes.get(name)
    if me:
        bpy.data.meshes.remove(me)
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    build(bm)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # Flatten every authored polygon, so it reads as one drawn facet after triangulation
    # instead of folding along its diagonals (a fold shows as an extra facet or a groove).
    bmesh.ops.planar_faces(bm, faces=bm.faces, iterations=200, factor=0.5)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    tris = len(bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.get(name) or bpy.data.objects.new(name, me)
    ob.data = me
    if ob.name not in collection.objects:
        collection.objects.link(ob)
    mat = bpy.data.materials.get('flat_' + colour[0]) or bpy.data.materials.new('flat_' + colour[0])
    mat.diffuse_color = (*colour[1], 1)
    me.materials.append(mat)
    for poly in me.polygons:
        poly.use_smooth = False
    return tris


def mirror_x(p):
    return (-p[0], p[1], p[2])
