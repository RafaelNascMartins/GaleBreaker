"""X12's face and neck on the Mega Man topology (the source of truth for Legends heads).

Mega Man's face (concept-art/referencias/Megaman.obj) is ~25 vertices: a centre line
(forehead, brow, eye band, nose, nose tip, mouth, chin) and a few per side (eye corner, temple,
cheek, jaw, under the chin), eyes and mouth painted, plus a small ear. We take exactly those
faces (the head's skin faces, by the texture colour), make them symmetric, and move every
vertex to X12's measurements:

    height  piecewise between landmarks (Mega Man's -> X12's, LANDMARKS)
    width   x times the ratio of the faces' half widths at those heights (HALF_WIDTH)
    depth   the profile's front line at the new height (PROFILE_FRONT) plus the vertex's depth
            behind Mega Man's front line, times DEPTH

X12's numbers come from her front and profile crops (face skin outline per row).
The neck is a 6-sided column from inside the collar to under the jaw.

    python art-source/tools/x12_face.py      -> part dicts used by x12_sculpt.py
"""
import cv2
import numpy as np

from x12_lift import ROOT

REF = ROOT / 'concept-art/referencias'

# Mega Man z -> X12 z (m, both 1.80 m tall): forehead top, brow, eye band top, eye band
# bottom (nose base), nose tip, mouth, chin
LANDMARKS = [(1.344, 1.475), (1.393, 1.525), (1.442, 1.555), (1.473, 1.565),
             (1.537, 1.616), (1.581, 1.645), (1.612, 1.680)]
# X12 face half width (front crop, face skin outline) by height
HALF_WIDTH = [(1.471, 0.012), (1.480, 0.029), (1.497, 0.057), (1.514, 0.074), (1.531, 0.080),
              (1.557, 0.083), (1.591, 0.090), (1.625, 0.089), (1.651, 0.076), (1.680, 0.068)]
# X12 profile front line (y, face forward is -y) by height
PROFILE_FRONT = [(1.471, -0.089), (1.488, -0.100), (1.514, -0.102), (1.522, -0.106),
                 (1.531, -0.125), (1.548, -0.132), (1.557, -0.134), (1.565, -0.119),
                 (1.591, -0.110), (1.608, -0.115), (1.643, -0.119), (1.680, -0.119)]
EAR_Y0, EAR_SQUASH = 0.02, 0.35   # behind y0 depths are squashed (ear back at y ~0.063)
DEPTH = 1.15          # X12's face is a little deeper from nose to ear than Mega Man's
# The drawn head is 0.345 m (19 % of her height); Mega Man's is 0.456 m (25 %). The user wants
# the Legends proportion: the head (face, hair) is scaled HEAD_SCALE about the chin/neck joint.
HEAD_SCALE = 1.0   # the drawn head (19 %) is already the adult Legends proportion (Tifa)
HEAD_PIVOT = np.array([0.0, 0.0, 1.47])


def head_xform(P):
    return HEAD_PIVOT + (np.asarray(P, float) - HEAD_PIVOT) * HEAD_SCALE


NECK = dict(z0=1.40, z1=1.50, rx=0.042, ry=0.045, cy=0.0)


def load_obj(name):
    """Vertices (Blender axes, 1.80 m tall, centred in x and y, feet at 0), faces with their
    mean texture colour."""
    V, T, F = [], [], []
    for line in open(REF / f'{name}.obj'):
        p = line.split()
        if not p:
            continue
        if p[0] == 'v':
            V.append([float(x) for x in p[1:4]])
        elif p[0] == 'vt':
            T.append([float(x) for x in p[1:3]])
        elif p[0] == 'f':
            F.append([(int(q.split('/')[0]) - 1, int(q.split('/')[1]) - 1) for q in p[1:]])
    V = np.array(V)
    P = np.stack([-V[:, 0], V[:, 2], V[:, 1]], 1)       # OBJ y-up, facing +z -> Blender, facing -y
    P = P * (1.8 / np.ptp(P[:, 2]))
    P[:, 2] -= P[:, 2].min()
    P[:, 0] -= (P[:, 0].min() + P[:, 0].max()) / 2
    P[:, 1] -= (P[:, 1].min() + P[:, 1].max()) / 2
    img = cv2.imread(str(REF / f'{name}.png'))[..., ::-1] / 255.0
    T = np.array(T)
    faces = []
    for f in F:
        tri = T[[t for _, t in f]]
        c = tri.mean(0)
        samples = [c] + [c + (t - c) * 0.7 for t in tri]          # centre and towards each corner
        cols = [img[int((1 - u[1]) * (img.shape[0] - 1)), int(u[0] * (img.shape[1] - 1))] for u in samples]
        faces.append(([v for v, _ in f], cols))
    return P, faces


def tone(cols):
    """armour (blue), hair (every sample dark brown) or skin (face, eyes, mouth, ears: a face
    with any skin, eye white or iris sample; an eye's pupil alone is dark)."""
    def one(c):
        if c[2] > c[0] + 0.2:
            return 'armour'
        if c.max() < 0.42 and abs(c[0] - c[2]) < 0.15 and c[0] < 0.4:
            return 'hair'
        return 'skin'
    t = [one(c) for c in cols]
    if 'skin' in t:
        return 'skin'
    return 'armour' if 'armour' in t else 'hair'


def symmetric(P, ids):
    """Each vertex and its mirror partner get mirrored mean positions; vertices near the centre
    line go onto it."""
    Q = P.copy()
    sub = P[ids]
    for i in ids:
        p = P[i]
        if abs(p[0]) < 0.006:
            Q[i, 0] = 0
            continue
        m = sub[np.argmin(np.linalg.norm(sub - p * [-1, 1, 1], axis=1))]
        if np.linalg.norm(m - p * [-1, 1, 1]) < 0.02:
            Q[i] = (p + m * [-1, 1, 1]) / 2
    return Q


def _interp(table, z):
    a = np.array(table)
    return np.interp(z, a[:, 0], a[:, 1])


def face_part():
    P, faces = load_obj('Megaman')
    skin = [f for f, c in faces if tone(c) == 'skin' and P[f, 2].min() > 1.25]
    ids = sorted({v for f in skin for v in f})
    P = symmetric(P, ids)
    S = P[ids]
    # Mega Man's half width and front line by height, from his own face vertices
    zs = np.linspace(S[:, 2].min(), S[:, 2].max(), 24)
    face_only = S[np.abs(S[:, 0]) < 0.15]                 # not the ears
    half_mm = np.array([np.abs(face_only[np.abs(face_only[:, 2] - z) < 0.03, 0]).max(initial=0) for z in zs])
    ok = half_mm > 0.03
    half_mm = np.interp(zs, zs[ok], half_mm[ok])
    centre = S[np.abs(S[:, 0]) < 0.004]
    centre = centre[np.argsort(centre[:, 2])]
    out = {}
    for i in ids:
        x, y, z = P[i]
        z2 = _interp(LANDMARKS, z)
        w_mm = np.interp(z, zs, half_mm)
        x2 = x * _interp(HALF_WIDTH, z2) / w_mm
        y_front_mm = np.interp(z, centre[:, 2], centre[:, 1])
        y2 = _interp(PROFILE_FRONT, z2) + (y - y_front_mm) * DEPTH
        if y2 > EAR_Y0:              # behind the cheek: X12's ear is small and round
            y2 = EAR_Y0 + (y2 - EAR_Y0) * EAR_SQUASH
        out[i] = (x2, y2, z2)
    remap = {i: k for k, i in enumerate(ids)}
    return {'bone': 'head', 'tone': 'skin',
            'v': head_xform([out[i] for i in ids]).round(4).tolist(),
            'f': [[remap[v] for v in f] for f in skin]}


def neck_part(n=6):
    a = np.radians(np.arange(n) * 360 / n + 30)
    ring = lambda z: [[NECK['rx'] * np.sin(t), NECK['cy'] - NECK['ry'] * np.cos(t), z] for t in a]
    v = ring(NECK['z0']) + ring(NECK['z1'])
    f = [[k, (k + 1) % n, n + (k + 1) % n, n + k] for k in range(n)]
    f.append(list(range(n))[::-1])
    f.append(list(range(n, 2 * n)))
    return {'bone': 'neck', 'tone': 'skin', 'v': np.round(v, 4).tolist(), 'f': f}


if __name__ == '__main__':
    f = face_part()
    print('face', len(f['v']), 'verts', len(f['f']), 'faces')
