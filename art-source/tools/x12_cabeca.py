"""X12's head, modelled by hand on the Legends references (docs/estudos/legends-modelagem.md).

One closed piece: face, ears and hair (the painting splits them later). Built like Mega Man's
and Tifa's heads: hair as the skull's shell with the fringe, sideburns and nape hanging as
lips over the face (the fringe asymmetric, as drawn); a face with a 7-vertex centre line (forehead, brow, eye band, nose base,
nose tip, mouth, chin), 1-2 faces per eye band, a nose tip ~2 cm out, the mouth and chin going
back; the ear a small plate. Left half listed, right half the exact mirror (centre vertices at
x = 0). Every coordinate is measured on the concept crops (x12_frente / x12_perfil /
x12_costas, MPP 1.8/840; x from the front, y from the profile, front is -y), at the drawing's
scale: her drawn head is 19 % of her height, the adult Legends proportion (Tifa ~18 %).
"""
import legends_kit as lk

# name: (x, y, z) metres; x = 0 names are on the centre line
V = {
    # crown and skull shell (hair): top, ring A (upper skull), ring B (widest, hair outline)
    'T0': (0.0, 0.01, 1.800),
    'A0': (0.0, -0.130, 1.765), 'A1': (0.100, -0.095, 1.765), 'A2': (0.150, 0.020, 1.755),
    'A3': (0.105, 0.130, 1.745), 'A4': (0.0, 0.160, 1.745),
    'B0': (0.0, -0.175, 1.690),     # fringe front (profile: y -0.18 at z 1.66-1.70)
    'B1': (0.125, -0.135, 1.675),
    'B2': (0.175, 0.000, 1.665),    # side spike of the front outline (x 0.17-0.18 at z 1.66)
    'B3': (0.130, 0.145, 1.645),
    'B4': (0.0, 0.180, 1.630),      # back-most (profile y 0.18 at z 1.64)
    'BL': (0.080, 0.165, 1.575),    # lower back of the hair (a row between B and the nape, no fan)
    'BC': (0.0, 0.175, 1.565),
    # hair edge, from the front centre round to the nape (tips and notches of the drawings)
    'N2': (0.105, -0.105, 1.645),   # temple notch
    'S1': (0.098, -0.075, 1.545),   # sideburn tip, beside the cheek (front rows 128-130)
    'N3': (0.130, 0.025, 1.610),    # over the ear (profile)
    'NE': (0.135, 0.075, 1.600),    # over the back of the ear (the ear stays visible, profile)
    'S2': (0.100, 0.090, 1.480),    # behind the ear, down to the neck (profile tip 24-26)
    'BK': (0.125, 0.135, 1.555),    # back tip (profile 28-30, back view tip 10)
    'NP1': (0.050, 0.115, 1.478),   # nape tips and notch (back view 13-19)
    'NN': (0.025, 0.120, 1.495),
    'NP0': (0.0, 0.120, 1.475),
    # skin under the hair lips
    'FH': (0.0, -0.119, 1.662),     # forehead (under the fringe)
    'E1': (0.085, -0.098, 1.625),   # eye band, outer top
    'TP': (0.105, -0.035, 1.585),   # side of the face, in front of the ear
    'ER1': (0.118, 0.030, 1.605),   # ear (profile cols 233-249, rows 100-138)
    'ER2': (0.128, 0.065, 1.590),
    'ER0': (0.108, 0.025, 1.540),
    'ER3': (0.120, 0.060, 1.535),
    'NK': (0.075, 0.080, 1.500),    # back of the neck under the hair
    'NC': (0.0, 0.095, 1.490),
    # face (front: half widths per row; profile: front line)
    'BR': (0.0, -0.121, 1.637),     # brow
    'EB': (0.0, -0.118, 1.590),     # between the eyes
    'NB': (0.0, -0.122, 1.565),     # nose base / under the eyes
    'NT': (0.0, -0.140, 1.552),     # nose tip (profile y -0.134 .. -0.14)
    'NS': (0.020, -0.120, 1.550),   # nose wing
    'MO': (0.0, -0.108, 1.522),     # mouth
    'CH': (0.0, -0.092, 1.472),     # chin
    'E2': (0.085, -0.088, 1.560),   # cheekbone (eye band, outer bottom)
    'CK': (0.074, -0.078, 1.515),   # cheek at the mouth
    'JW': (0.045, -0.070, 1.485),   # jaw (front half width 0.057 at z 1.50, 0.029 at 1.48)
    'JB': (0.070, 0.000, 1.500),    # jaw back, under the ear
    'BOT1': (0.0, -0.035, 1.462),   # under the jaw
    'BOT2': (0.0, 0.050, 1.470),    # under the skull (the neck goes in here)
}

# left-half faces, outward winding is fixed afterwards (consistent orientation of the mesh)
F_LEFT = [
    # crown and skull
    ('T0', 'A0', 'A1'), ('T0', 'A1', 'A2'), ('T0', 'A2', 'A3'), ('T0', 'A3', 'A4'),
    ('A0', 'B0', 'B1', 'A1'), ('A1', 'B1', 'B2', 'A2'), ('A2', 'B2', 'B3', 'A3'), ('A3', 'B3', 'B4', 'A4'),
    # hair outline down to the edge (fringe, side, back, nape)
    ('B1', 'N2', 'S1'), ('B1', 'S1', 'B2'), ('B2', 'S1', 'N3'),
    ('B2', 'N3', 'NE'), ('B2', 'NE', 'B3'), ('B3', 'NE', 'S2'), ('B3', 'S2', 'BK'),
    ('B3', 'BL', 'BC', 'B4'), ('B3', 'BK', 'BL'), ('BL', 'BK', 'NP1'), ('BL', 'NP1', 'NN'),
    ('BL', 'NN', 'BC'), ('BC', 'NN', 'NP0'),
    # hair lips: the edge back to the skin (underside of fringe, sideburn, nape)
    ('N2', 'E1', 'TP'), ('N2', 'TP', 'S1'), ('S1', 'TP', 'N3'), ('N3', 'TP', 'ER1'),
    ('N3', 'ER1', 'ER2'), ('N3', 'ER2', 'NE'), ('NE', 'ER2', 'S2'), ('S2', 'ER2', 'NK'), ('S2', 'NK', 'BK'),
    ('BK', 'NK', 'NP1'), ('NP1', 'NK', 'NN'), ('NN', 'NK', 'NC'), ('NN', 'NC', 'NP0'),
    # face
    ('FH', 'BR', 'E1'),
    ('BR', 'EB', 'E1'), ('EB', 'E2', 'E1'), ('EB', 'NB', 'E2'),          # eye band: 3 faces
    ('NB', 'NS', 'E2'), ('NB', 'NT', 'NS'), ('NT', 'MO', 'NS'),          # nose
    ('NS', 'MO', 'CK'), ('NS', 'CK', 'E2'),                              # cheek
    ('MO', 'CH', 'JW'), ('MO', 'JW', 'CK'),                              # mouth, chin
    ('E1', 'E2', 'TP'), ('E2', 'CK', 'TP'),                              # side of the face
    ('CK', 'JW', 'JB'), ('CK', 'JB', 'TP'),
    ('TP', 'JB', 'ER0'), ('TP', 'ER0', 'ER1'),
    ('ER1', 'ER0', 'ER3'), ('ER1', 'ER3', 'ER2'),                        # ear plate
    ('ER2', 'ER3', 'NK'), ('JB', 'ER3', 'ER0'),
    # underside
    ('CH', 'BOT1', 'JW'), ('JW', 'BOT1', 'JB'), ('JB', 'BOT1', 'BOT2'),
    ('JB', 'BOT2', 'ER3'), ('ER3', 'BOT2', 'NK'), ('NK', 'BOT2', 'NC'),
]

# The fringe is NOT symmetric (like Mega Man's tips): drawn on the front crop, from her right
# temple (image left) to her left temple. Absolute coordinates; "'" names are the mirrored side.
V_FRINGE = {
    'R1': (-0.073, -0.125, 1.623),  # tip (front col 296, row 93)
    'R2': (-0.060, -0.130, 1.646),  # notch (302, 82)
    'R3': (-0.039, -0.135, 1.627),  # tip (312, 91)
    'R4': (-0.028, -0.135, 1.680),  # high notch (317, 66)
    'C1': (-0.019, -0.137, 1.627),  # centre lock between the brows (321, 91)
    'L1': (0.032, -0.126, 1.697),   # forehead peak: the skin shows highest here (345, 58)
    'L2': (0.060, -0.130, 1.684),   # (358, 64)
    'L3': (0.086, -0.120, 1.638),   # lock over her left eye (370, 86)
}
F_FRINGE = [
    # hair: ring B down to the fringe
    ("B1'", "N2'", 'R1'), ("B1'", 'R1', 'R2'), ("B1'", 'R2', 'B0'), ('B0', 'R2', 'R3'), ('B0', 'R3', 'R4'),
    ('B0', 'R4', 'C1'), ('B0', 'C1', 'L1'), ('B0', 'L1', 'B1'), ('B1', 'L1', 'L2'), ('B1', 'L2', 'L3'),
    ('B1', 'L3', 'N2'),
    # lips: the fringe's edge back to the forehead and eye band
    ("N2'", "E1'", 'R1'), ('R1', "E1'", 'R2'), ('R2', "E1'", 'R3'), ('R3', "E1'", 'FH'), ('R3', 'FH', 'R4'),
    ('R4', 'FH', 'C1'), ('C1', 'FH', 'L1'), ('L1', 'FH', 'E1'), ('L1', 'E1', 'L2'), ('L2', 'E1', 'L3'),
    ('L3', 'E1', 'N2'),
]

# NK, NC: the back of the neck under the nape; the hair's underside there is dark (Mega Man)
HAIR = set(V_FRINGE) | {'NK', 'NC', 'T0', 'A0', 'A1', 'A2', 'A3', 'A4', 'B0', 'B1', 'B2', 'B3', 'B4', 'BL', 'BC',
        'N2', 'S1', 'N3', 'NE', 'S2', 'BK', 'NP1', 'NN', 'NP0'}


def parts():
    P, F, names = lk.named(V, F_LEFT, V_FRINGE, F_FRINGE)
    # a face is hair when most of its corners are hair: the hair's edges (fringe, sideburns, nape)
    # and the undersides of the locks over the skin are hair, like Mega Man's blades
    tone = ['hair' if 2 * sum(names[i].rstrip("'") in HAIR for i in f) > len(f) else 'skin' for f in F]
    return {'head': lk.part(P, F, 'head', ftone=tone)}


# the fringe is drawn asymmetric on purpose: legends_build leaves these out of the symmetry check
ASYMMETRIC = {'head': list(V_FRINGE.values())}
