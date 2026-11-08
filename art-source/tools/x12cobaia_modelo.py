"""X12, guinea pig outfit (Weapon X-inspired; fighter id `tophia`): the character module for
legends_build.py.

The base head (x12_cabeca, its hand-painted page and expression atlas) inside the outfit's helmet,
and the outfit's new pieces (x12_cobaia). Concept:
concept-art/characters/x12/x12-cobaia-uniforme-botas-referencia-psx-v4.png, cropped by
outfit_crops.py (--scale-from shoulder) to x12cobaia_frente / perfil / costas; texture panels
concept-art/characters/x12/x12-cobaia-texturas-17-paineis-psx-v1.png.
"""
from pathlib import Path

import x12_cabeca
import x12_cobaia

ID = 'tophia'
NAME = 'x12cobaia'
SRC = Path(__file__).resolve().parents[2] / 'art-source/characters/tophia/legends'
HEIGHT = 1.80
PREFIX = 'XC_'
COLLECTION = 'X12_Cobaia'
PIECES = [x12_cabeca, x12_cobaia]

# UV (legends_uv.py)
UV_METHOD = {'suit_top': 'front_back', 'suit_belly': 'front_back', 'suit_hips': 'front_back', 'head': 'box',
             'helmet': 'box', 'glove': 'box', 'boot': 'box', 'pouch_hip': 'box', 'pouch_thigh': 'box'}
UV_DENSITY = {'suit_top': 1.5, 'glove': 2.2, 'head': 1.4, 'helmet': 1.5, 'suit_hips': 1.3}
UV_HIDDEN = {(p, '*') for p in ('upper_arm', 'forearm', 'cuff', 'thigh', 'knee_band', 'boot_shaft', 'neck',
                                'deltoid', 'chest_strap', 'belt', 'cables')} | {
    ('suit_top', 'top'), ('suit_top', 'bottom'), ('suit_belly', 'top'), ('suit_belly', 'bottom'),
    ('suit_hips', 'bottom'), ('suit_hips', 'top')}

# texture (legends_paint.py): the outfit's 17 panels; the head keeps the base's hand painting
PANELS = SRC.parents[3] / 'concept-art/characters/x12/x12-cobaia-texturas-17-paineis-psx-v1.png'
COPY_FROM = ('x12_modelo', ['head'])
CABLE_BANDS = (('vband', 0.30, 0.38, 'red'), ('vband', 0.38, 0.46, 'green'), ('vband', 0.46, 0.54, 'yellow'))
PAINT = {
    # the harness straps run over the shoulders down to the chest strap (front crop x .055-.085)
    ('suit_top', 'front'): ('panel', 1, (0.06, 0.0, 0.94, 0.62), ('band', 0.25, 0.33, 'leather'), ('band', 0.67, 0.75, 'leather')),
    ('suit_top', 'back'): ('panel', 2, (0.06, 0.0, 0.94, 0.62)),
    ('suit_belly', 'front'): ('panel', 1, (0.12, 0.62, 0.88, 1.0)), ('suit_belly', 'back'): ('panel', 2, (0.12, 0.62, 0.88, 1.0)),
    ('suit_hips', 'front'): ('panel', 3, (0.03, 0.0, 0.97, 0.45)), ('suit_hips', 'back'): ('panel', 4, (0.03, 0.0, 0.97, 0.45)),
    ('thigh', 'cyl'): ('panel', 3, (0.52, 0.40, 0.97, 1.0)),
    ('deltoid', 'cyl'): ('panel', 1, (0.06, 0.25, 0.30, 0.60)),
    # black sleeves with the coloured cable rings wound round them (concept: on the upper arm and the elbow)
    ('upper_arm', 'cyl'): ('panel', 5, (0.35, 0.3, 0.65, 0.7), *CABLE_BANDS),
    ('forearm', 'cyl'): ('panel', 5, (0.35, 0.3, 0.65, 0.7), ('vband', 0.22, 0.30, 'red'), ('vband', 0.30, 0.38, 'yellow')),
    ('forearm_r', 'cyl'): ('panel', 5, (0.35, 0.3, 0.65, 0.7), ('vband', 0.22, 0.30, 'red'), ('vband', 0.30, 0.38, 'yellow'),
                           ('vband', 0.78, 0.92, 'white')),                         # the ID band on her right wrist
    ('cuff', 'cyl'): ('panel', 17, (0.03, 0.05, 0.97, 0.30), 'wrap'),
    ('glove', '+x'): ('panel', 7), ('glove', '-x'): ('panel', 8, 'mirror'), ('glove', '*'): ('panel', 7, (0.2, 0.15, 0.8, 0.55)),
    ('knee_band', 'cyl'): ('panel', 9, (0.22, 0.0, 0.78, 0.14), 'wrap'),
    ('boot_shaft', 'cyl'): ('panel', 9, (0.22, 0.14, 0.78, 0.70)),
    ('boot', '+z'): ('tone', 'black'), ('boot', '-y'): ('panel', 9, (0.2, 0.80, 0.8, 1.0)),
    ('boot', '-z'): ('panel', 11, 'full'), ('boot', '*'): ('panel', 10, (0.0, 0.3, 1.0, 1.0)),
    ('helmet', '-y'): ('panel', 12), ('helmet', '+x'): ('panel', 13), ('helmet', '-x'): ('panel', 13, 'mirror'),
    ('helmet', '+y'): ('panel', 14, (0.05, 0.45, 0.95, 1.0)), ('helmet', '+z'): ('panel', 14, (0.08, 0.05, 0.92, 0.45)),
    ('helmet', '-z'): ('tone', 'metal'),
    ('cables', 'cyl'): ('panel', 5, (0.2, 0.2, 0.8, 0.8), ('band', 0.40, 0.47, 'red'), ('band', 0.50, 0.57, 'green'),
                        ('band', 0.60, 0.67, 'yellow')),
    ('chest_strap', 'cyl'): ('panel', 6, (0.03, 0.47, 0.97, 0.62), 'wrap'),
    ('belt', 'cyl'): ('panel', 6, (0.03, 0.73, 0.97, 0.88), 'wrap'),
    ('pouch_hip', '-y'): ('panel', 16, (0.05, 0.05, 0.38, 0.62)), ('pouch_thigh', '+x'): ('panel', 16, (0.62, 0.05, 0.97, 0.62)),
    ('pouch_hip', '*'): ('tone', 'purple'), ('pouch_thigh', '*'): ('tone', 'purple'),
    ('neck', '*'): ('tone', 'black'),
}
PANEL_CROP = {1: (0.03, 0.0, 0.97, 0.97), 2: (0.03, 0.0, 0.97, 0.97)}
PANEL_FILL = {1: 'cloth', 2: 'cloth', 3: 'cloth', 4: 'cloth', 7: 'grey', 8: 'grey', 9: 'black', 10: 'black',
              12: 'metal', 13: 'metal', 14: 'metal'}
PAGE_COLOURS = 24          # suit, black, leather, grey metal, purple, red/green/yellow cables, skin and hair
TONE_PANEL = {'cloth': (1, (0.12, 0.40, 0.32, 0.55)), 'black': '#2b2a30', 'leather': '#4a3a34', 'metal': '#5d5a66',
              'grey': '#a8a8b4', 'purple': '#5f4a7c', 'red': '#d9302b', 'green': '#5ac23a', 'yellow': '#e6d23c',
              'white': '#ecebe4', 'stone': '#2b2a30', 'skin': (1, (0.12, 0.40, 0.32, 0.55)), 'hair': '#26201f'}

# face page: the base's expressions and face square
EXPRESSIONS = SRC.parents[3] / 'concept-art/characters/x12/x12-expressoes-24-psx-v1.png'
FACE_BOX = {'x': (-0.1095, 0.1095), 'z': (1.470, 1.689)}
