"""X12, boxer outfit (fighter id `tophia`): the character module for legends_build.py.

The base head (x12_cabeca, its hand-painted page and expression atlas) and the outfit's new
pieces (x12_boxe). Concept: concept-art/characters/x12/x12-boxeadora-turnaround-psx-v1.png,
cropped to x12boxe_frente / perfil / costas at the base crops' scale.
"""
from pathlib import Path

import x12_boxe
import x12_cabeca

ID = 'tophia'
NAME = 'x12boxe'
SRC = Path(__file__).resolve().parents[2] / 'art-source/characters/tophia/legends'
HEIGHT = 1.80
PREFIX = 'XB_'
COLLECTION = 'X12_Boxe'
PIECES = [x12_cabeca, x12_boxe]

# UV (legends_uv.py)
UV_METHOD = {'top': 'front_back', 'belly': 'front_back', 'shorts': 'front_back', 'head': 'box',
             'glove': 'box', 'boot': 'box', 'deltoid': 'cyl'}
UV_DENSITY = {'top': 1.6, 'glove': 2.4, 'head': 1.4, 'shorts': 1.4}
UV_HIDDEN = {(p, '*') for p in ('upper_arm', 'forearm', 'wrap', 'thigh', 'shin', 'boot_shaft', 'neck', 'deltoid', 'shorts_leg')} | {
    ('top', 'top'), ('top', 'bottom'), ('belly', 'top'), ('belly', 'bottom'), ('shorts', 'bottom'), ('choker', '*')}

# texture (legends_paint.py): the outfit's 17 panels; head and neck keep the base's hand painting
PANELS = SRC.parents[3] / 'concept-art/characters/x12/x12-boxeadora-texturas-17-paineis-psx-v1.png'
COPY_FROM = ('x12_modelo', ['head', 'neck'])
PAINT = {
    ('top', 'front'): ('panel', 1), ('top', 'back'): ('panel', 2),
    ('belly', 'front'): ('panel', 16), ('belly', 'back'): ('panel', 14),
    # pelvis: the shorts' outer white stripes run up its sides to the waistband
    ('shorts', 'front'): ('panel', 3, (0.03, 0.0, 0.97, 0.55), ('band', 0.0, 0.06, 'cloth'), ('band', 0.94, 1.0, 'cloth')),
    ('shorts', 'back'): ('panel', 4, (0.03, 0.0, 0.97, 0.55), ('band', 0.0, 0.06, 'cloth'), ('band', 0.94, 1.0, 'cloth')),
    ('shorts', 'top'): ('tone', 'cloth'),
    # leg sleeve: the shorts' front panel (her side), the white stripe on the front-outer corner
    ('shorts_leg', 'cyl'): ('panel', 3, (0.52, 0.45, 0.97, 0.97), ('band', 0.24, 0.33, 'cloth')),
    ('deltoid_l', 'cyl'): ('panel', 17, (0.0, 0.0, 1.0, 0.75), 'wrap', ('turn', 0.35)),
    ('deltoid_r', 'cyl'): ('panel', 12, (0.25, 0.0, 0.75, 1.0)),
    ('upper_arm', 'cyl'): ('panel', 12, (0.25, 0.0, 0.75, 1.0)), ('forearm', 'cyl'): ('panel', 13, (0.25, 0.0, 0.75, 1.0)),
    ('wrap', 'cyl'): ('panel', 8, (0.0, 0.45, 1.0, 0.98)),
    ('glove', '+x'): ('panel', 6), ('glove', '-x'): ('panel', 7, 'mirror'), ('glove', '*'): ('panel', 6, (0.2, 0.2, 0.8, 0.8)),
    ('thigh', 'cyl'): ('panel', 14, (0.2, 0.0, 0.8, 1.0)), ('shin', 'cyl'): ('panel', 15, (0.2, 0.0, 0.8, 1.0)),
    ('boot_shaft', 'cyl'): ('panel', 9, (0.08, 0.0, 0.92, 0.72), 'wrap'),
    ('boot', '+z'): ('panel', 9, (0.1, 0.76, 0.9, 0.95)), ('boot', '-y'): ('panel', 9, (0.1, 0.80, 0.9, 0.98)),
    ('boot', '-z'): ('panel', 11, 'full'), ('boot', '*'): ('panel', 10),
    ('choker', '*'): ('tone', 'metal'),
}
# bare shoulders: the top's trapezius band (z 1.405-1.44, faces 0-7) and its upper side faces
# (armholes, above the armpit, z 1.29-1.405) are skin; the straps run on the front/back faces
FACE_PAINT = {('top', fi): ('tone', 'skin') for fi in (*range(8), 9, 10, 13, 14)}
PANEL_CROP = {1: (0.04, 0.02, 0.96, 0.97), 2: (0.04, 0.02, 0.96, 0.97), 3: (0.03, 0.03, 0.97, 0.97),
              4: (0.03, 0.03, 0.97, 0.97), 6: (0.03, 0.03, 0.97, 0.97), 9: (0.08, 0.0, 0.92, 0.98),
              10: (0.0, 0.0, 1.0, 0.98)}
PANEL_FILL = {1: 'skin', 2: 'skin', 3: 'stone', 4: 'stone', 5: 'stone', 6: 'stone', 7: 'stone',
              9: 'stone', 10: 'stone'}
TONE_PANEL = {'stone': (6, (0.3, 0.3, 0.7, 0.7)), 'metal': '#3a3a40',
              'skin': (14, (0.3, 0.3, 0.7, 0.7)), 'cloth': (1, (0.3, 0.75, 0.7, 0.9)), 'hair': (11, (0.3, 0.3, 0.7, 0.7))}

# face page: the base's expressions and face square
EXPRESSIONS = SRC.parents[3] / 'concept-art/characters/x12/x12-expressoes-24-psx-v1.png'
FACE_BOX = {'x': (-0.1095, 0.1095), 'z': (1.470, 1.689)}
