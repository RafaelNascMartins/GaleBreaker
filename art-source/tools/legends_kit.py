"""Building blocks for Legends-style characters modelled by hand (no Blender needed).

The method (docs/estudos/legends-modelagem.md, skill legends-character): every piece is built
like the matching piece of the references (Mega Man, Roll, Tifa) and only its sizes come from
the character's concept. A character is a set of piece modules (e.g. x12_cabeca, x12_tronco,
x12_braco, x12_perna), each with a `parts()` returning {name: part}, and a character module
(e.g. x12_modelo) listing them; legends_build.py joins, checks and writes them.

A part is a dict: {'bone', 'tone' or 'ftone' (one tone per face), 'v': [[x, y, z]], 'f': [[i]]}
in metres, Blender axes (front is -y, her left is +x). Faces are n-gons (quads/triangles).

Shapes here:
    named(V, F, ...)   explicit mesh by named vertices, left half mirrored (heads, odd shapes)
    loft_sym(sections) symmetric trunk pieces through 5-point half sections (chest, skirt)
    loft(rings)        any chain of rings (limbs), see ring() and along()
    prism(levels)      short centred n-gon column (neck)
All caps are closed as strips, never fans, and every result is wound outward.
"""
import numpy as np

X, Y, Z = np.eye(3)
FRONT = -Y
# comparison renders (legends_blender.compare, legends_compare.sheet), for a 1.80 m character:
# region -> (camera height, ortho scale = frame height in metres)
REGIONS = {'corpo': (0.95, 2.05), 'cabeca': (1.63, 0.6), 'tronco': (1.42, 0.9), 'braco': (1.17, 1.25),
           'perna': (0.45, 1.0)}
VIEWS = {'frente': ((0, -1), 0), 'perfil': ((1, 0), 90), 'tres4': ((0.7071, -0.7071), 45), 'costas': ((0, 1), 180)}
MAX_VALENCE = 9          # Mega Man reaches 10 at one or two points; we stay under it


# ---------------------------------------------------------------- orientation and checks
def orient(P, faces):
    """Consistent winding over a closed mesh (flood through shared edges), outward by the sign
    of the enclosed volume."""
    P = np.asarray(P, float)
    edge_faces = {}
    for k, f in enumerate(faces):
        for a, b in zip(f, f[1:] + f[:1]):
            edge_faces.setdefault(frozenset((a, b)), []).append(k)
    out, done = [list(f) for f in faces], {0}
    stack = [0]
    while stack:
        k = stack.pop()
        f = out[k]
        for a, b in zip(f, f[1:] + f[:1]):
            for j in edge_faces[frozenset((a, b))]:
                if j in done:
                    continue
                g = list(faces[j])
                out[j] = g if (b, a) in list(zip(g, g[1:] + g[:1])) else g[::-1]
                done.add(j)
                stack.append(j)
    vol = sum(np.dot(P[f[0]], np.cross(P[f[k]], P[f[k + 1]])) for f in out for k in range(1, len(f) - 1))
    return out if vol > 0 else [f[::-1] for f in out]


def stats(P, F):
    """(triangles, odd edges, max faces per vertex)."""
    edges, val = {}, np.zeros(len(P), int)
    for f in F:
        for a, b in zip(f, f[1:] + f[:1]):
            edges[frozenset((a, b))] = edges.get(frozenset((a, b)), 0) + 1
        for i in f:
            val[i] += 1
    return sum(len(f) - 2 for f in F), sum(1 for c in edges.values() if c != 2), int(val.max())


def symmetry_error(P, Q=None):
    """Largest distance from a mirrored vertex of P to the nearest vertex of Q (Q = P for a
    centred part, the partner part for a left/right pair)."""
    P = np.asarray(P, float)
    Q = P if Q is None else np.asarray(Q, float)
    return float(max(np.min(np.linalg.norm(Q - m, axis=1)) for m in P * [-1, 1, 1]))


def ring_order(ring):
    """Strip order across a closed ring: first, second, last, third, second last..."""
    n = len(ring)
    order, a, c = [ring[0]], 1, n - 1
    while a <= c:
        order.append(ring[a])
        if a != c:
            order.append(ring[c])
        a, c = a + 1, c - 1
    return order


def cap(ring):
    o = ring_order(ring)
    return [o[k:k + 3] for k in range(len(o) - 2)]


# ---------------------------------------------------------------- shapes
def ring(c, u, v, hu, hv, n, flat_front=None):
    """n-gon around centre c in the plane of directions u, v, extents exactly hu (along u) and
    hv (along v). A vertex points along +v, or (n = 4, 8, or flat_front) an edge does."""
    flat = (n in (4, 8)) if flat_front is None else flat_front
    a = 2 * np.pi * np.arange(n) / n + (np.pi / n if flat else 0.0)
    su, cv = np.abs(np.sin(a)).max(), np.abs(np.cos(a)).max()
    return [np.asarray(c, float) + u * hu * np.sin(t) / su + v * hv * np.cos(t) / cv for t in a]


def tilted(deg):
    """Axis (down) and side (out, her left) of a limb leaning `deg` out from the vertical in
    the front view."""
    t = np.radians(deg)
    return np.array([np.sin(t), 0.0, -np.cos(t)]), np.array([np.cos(t), 0.0, np.sin(t)])


def along(origin, axis, side, sections, n, flat_front=None):
    """Rings along a limb: sections [(distance along the axis, half side, half front)]."""
    return [ring(np.asarray(origin, float) + axis * t, side, FRONT, hs, hf, n, flat_front)
            for t, hs, hf in sections]


def loft(rings):
    """Closed mesh through a chain of rings of equal size, caps as strips."""
    n = len(rings[0])
    P, idx = [], []
    for r in rings:
        idx.append(list(range(len(P), len(P) + n)))
        P += [np.asarray(p, float) for p in r]
    F = [[r0[i], r0[(i + 1) % n], r1[(i + 1) % n], r1[i]] for r0, r1 in zip(idx, idx[1:]) for i in range(n)]
    F += cap(idx[0]) + cap(idx[-1])
    P = np.array(P)
    return P, orient(P, F)


def loft_sym(sections, zfix=None):
    """Symmetric trunk piece through sections (z, [5 left-half (x, y)]: front centre, front
    corner, side, back corner, back centre; the centre ones at x = 0). zfix {(section, point):
    z} moves single points (a V at the front). Returns P, F and each face's band (the section
    gap it spans; -1 and len(sections) for the caps), for per-band tones."""
    P, rings = [], []
    for k, (z, half) in enumerate(sections):
        pts = [(x, y, (zfix or {}).get((k, i), z)) for i, (x, y) in enumerate(half)]
        full = pts + [(-x, y, z_) for x, y, z_ in reversed(pts[1:-1])]
        rings.append(list(range(len(P), len(P) + len(full))))
        P += full
    n = len(rings[0])
    F, band = [], []
    for k, (r0, r1) in enumerate(zip(rings, rings[1:])):
        for i in range(n):
            F.append([r0[i], r0[(i + 1) % n], r1[(i + 1) % n], r1[i]])
            band.append(k)
    for r, b in ((rings[0], -1), (rings[-1], len(rings))):
        for f in cap(r):
            F.append(f)
            band.append(b)
    P = np.array(P, float)
    return P, orient(P, F), band


def prism(levels, n=6, centre=(0.0, 0.0)):
    """Centred n-gon column: levels [(z, half width, half depth)]."""
    return loft([ring((centre[0], centre[1], z), X, FRONT, hx, hy, n, flat_front=False) for z, hx, hy in levels])


def named(V, F, extra_V=None, extra_F=None):
    """Explicit mesh: V {name: (x, y, z)} for her left half and the centre line (x = 0), F
    faces by name; the right half is mirrored ("name'"). extra_V / extra_F: asymmetric
    vertices and faces (absolute, not mirrored; may use mirrored names). Returns P, F, names."""
    names, P = [], []
    for n, p in V.items():
        names.append(n)
        P.append(p)
        if p[0] != 0:
            names.append(n + "'")
            P.append((-p[0], p[1], p[2]))
    for n, p in (extra_V or {}).items():
        names.append(n)
        P.append(p)
    idx = {n: i for i, n in enumerate(names)}
    mir = lambda n: n if V[n][0] == 0 else n + "'"
    faces = []
    for f in F:
        faces.append([idx[n] for n in f])
        faces.append([idx[mir(n)] for n in reversed(f)])
    faces += [[idx[n] for n in f] for f in (extra_F or [])]
    P = np.array(P, float)
    return P, orient(P, faces), names


# ---------------------------------------------------------------- parts
def part(P, F, bone, tone='stone', ftone=None):
    d = {'bone': bone, 'v': np.round(P, 4).tolist(), 'f': [list(map(int, f)) for f in F]}
    if ftone is not None:
        d['ftone'] = list(ftone)
    else:
        d['tone'] = tone
    return d


def mirrored(name, p):
    """(right name, right part) of a left part `<name>_l`: x mirrored, faces re-wound, bone _r."""
    P = np.array(p['v']) * [-1, 1, 1]
    q = dict(p, v=np.round(P, 4).tolist(), f=orient(P, [f[::-1] for f in p['f']]))
    if q['bone'].endswith('_l'):
        q['bone'] = q['bone'][:-2] + '_r'
    return name[:-2] + '_r', q


def with_mirrors(parts):
    """Adds the right copy of every `_l` part."""
    out = dict(parts)
    for n, p in parts.items():
        if n.endswith('_l'):
            r, q = mirrored(n, p)
            out[r] = q
    return out
