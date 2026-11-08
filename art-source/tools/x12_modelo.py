"""X12 (ex-Tophia, fighter id `tophia`), base outfit: the character module for legends_build.py.

Pieces are modelled by hand on the Legends references (Mega Man, Tifa) and measured on the
concept crops in art-source/characters/tophia/legends (x12_frente / perfil / costas).
"""
from pathlib import Path

import x12_braco
import x12_cabeca
import x12_perna
import x12_tronco

ID = 'tophia'
NAME = 'x12'
SRC = Path(__file__).resolve().parents[2] / 'art-source/characters/tophia/legends'
HEIGHT = 1.80
PREFIX = 'XF_'                 # object names in Blender (collection COLLECTION)
COLLECTION = 'X12_Facetas'
PIECES = [x12_cabeca, x12_tronco, x12_braco, x12_perna]


def HAIR_MASK(view):
    """The drawn hair of a concept crop (dark paint and its highlights, not eyes or brows)."""
    import x12_head
    return x12_head.hair_mask(view)

# UV (legends_uv.py): how each piece is opened; the rest are limbs unrolled as cylinders
UV_METHOD = {'head': 'box', 'chest': 'front_back', 'collar': 'front_back', 'skirt': 'front_back',
             'pauldron': 'box', 'fist': 'box', 'boot': 'box'}
# details on one side only (concept): "X12" on her left pauldron, the white band on her right
# forearm; these right parts keep their own islands instead of reusing the left ones
UV_OWN = {'pauldron_r', 'forearm_r'}
UV_DENSITY = {'chest': 1.6, 'fist': 2.8, 'head': 1.4, 'pauldron': 1.4}    # px/cm, default 1.2
# islands hidden inside other parts (they get almost no pixels): limb ends, the chest under the
# collar and inside the skirt, the skirt's waist, the collar's underside
UV_HIDDEN = {(p, '*') for p in ('upper_arm', 'forearm', 'wrist_cuff', 'thigh', 'shin', 'ankle_cuff', 'neck')} | {
    ('chest', 'top'), ('chest', 'bottom'), ('skirt', 'top'), ('skirt', 'bottom'), ('collar', 'bottom')}

# texture (legends_paint.py): the 20-panel sheet; panel numbers as printed on it
PANELS = [(SRC.parents[3] / 'concept-art/characters/x12/x12-texturas-20-paineis-psx-v1.png', 1),
          (SRC.parents[3] / 'concept-art/characters/x12/x12-texturas-paineis-21-24-psx-v1.png', 21)]
STONE_BAND = (0.0, 0.25, 1.0, 0.62)     # plain stone strip of the collar panel (18)
METAL_BAND = (0.0, 0.66, 1.0, 0.86)     # its studded metal band
PAINT = {
    ('chest', 'front'): ('panel', 1), ('chest', 'back'): ('panel', 2),
    ('collar', 'front'): ('panel', 18), ('collar', 'back'): ('panel', 18), ('collar', 'top'): ('tone', 'stone'),
    ('skirt', 'front'): ('panel', 10), ('skirt', 'back'): ('panel', 11),
    ('pauldron_l', '+x'): ('panel', 4),            # the "X12" (her left, outer side)
    ('pauldron', '*'): ('panel', 5),
    ('upper_arm', 'cyl'): ('panel', 24),
    ('forearm_l', 'cyl'): ('panel', 6), ('forearm_r', 'cyl'): ('panel', 7),   # 7: the white band
    ('wrist_cuff', 'cyl'): ('panel', 18, METAL_BAND), ('ankle_cuff', 'cyl'): ('panel', 18, METAL_BAND),
    # fist, like Mega Man's: every face painted for its role. A-pose: the fingers face out and
    # down (concept profile), so the outer face is the back of the hand over the finger row,
    # the end below has the finger tips curling under, the inner face the curled fingers, the
    # front and back faces the thumb and little-finger sides (plain plate with its outline)
    ('fist', '+x'): ('panel', 8),
    ('fist', '-z'): ('panel', 8, (0.04, 0.55, 0.96, 0.96)),
    ('fist', '-x'): ('panel', 8, (0.04, 0.55, 0.96, 0.96), 'mirror'),
    ('fist', '-y'): ('panel', 8, (0.02, 0.06, 0.40, 0.96)),
    ('fist', '+y'): ('panel', 8, (0.60, 0.06, 0.98, 0.96), 'mirror'),
    ('fist', '*'): ('panel', 8, (0.15, 0.10, 0.85, 0.42)),
    ('thigh', 'cyl'): ('panel', 13), ('shin', 'cyl'): ('panel', 14),
    ('boot', '+z'): ('panel', 16), ('boot', '-z'): ('panel', 17, 'full'),
    # head: the geometry decides (each face is hair or skin); hair faces take the concept's hair
    # colours (projected, other colours become the hair tone), skin faces plain skin (eyes,
    # brows and mouth come from the expression atlas)
    ('head', '+z'): ('ftone', {'hair': ('panel', 21), 'skin': ('tone', 'skin')}),   # top of the head
    ('head', '-z'): ('tone', 'skin'),
    ('head', '-y'): ('ftone', {'hair': ('view', 'frente', 'only'), 'skin': ('tone', 'skin')}),
    ('head', '+y'): ('ftone', {'hair': ('view', 'costas', 'only'), 'skin': ('tone', 'skin')}),
    ('head', '+x'): ('ftone', {'hair': ('view', 'perfil', 'only'), 'skin': ('tone', 'skin')}),
    ('head', '-x'): ('ftone', {'hair': ('view', 'perfil', 'only'), 'skin': ('tone', 'skin')}),
    ('neck', 'cyl'): ('panel', 23),
}
# the painted part on each panel (fractions), so the panels' dark background is not wrapped on
PANEL_CROP = {1: (0.04, 0.10, 0.96, 0.90), 2: (0.04, 0.10, 0.96, 0.90), 3: (0.08, 0.05, 0.97, 0.95),
              4: (0.03, 0.03, 0.97, 0.97), 5: (0.03, 0.03, 0.97, 0.97), 6: (0.12, 0.10, 0.88, 0.92),
              7: (0.08, 0.00, 0.92, 0.80), 8: (0.04, 0.08, 0.96, 0.96), 13: (0.12, 0.10, 0.88, 0.92),
              14: (0.08, 0.16, 0.92, 0.95), 16: (0.03, 0.10, 0.97, 0.97),
              23: (0.0, 0.0, 1.0, 0.86), 24: (0.0, 0.04, 1.0, 0.86)}     # 22 (fringe) unused: hand-painted
TONE_PANEL = {'stone': (5, (0.3, 0.3, 0.7, 0.7)), 'metal': (18, METAL_BAND), 'skin': (19, (0.0, 0.55, 0.2, 0.9)),
              'hair': (20, (0.3, 0.3, 0.7, 0.7))}

# face page (legends_face.py): the 24 expressions; one cell covers this square of the front of
# the head. The cells run from just above the brows to the chin with the eyes at ~43 % from the
# top: chin z 1.47 and eye line z 1.595 (concept front) give a 0.219 m square.
EXPRESSIONS = SRC.parents[3] / 'concept-art/characters/x12/x12-expressoes-24-psx-v1.png'
FACE_BOX = {'x': (-0.1095, 0.1095), 'z': (1.470, 1.689)}

# skeleton (legends_rig.py): the game's X12 rig (its 27 clips come along); joints read off the hand-made parts (left side)
RIG_SOURCE = (SRC.parent / 'tophia.blend', 'tophia_Rig')
JOINTS = {
    'pelvis': (0, 0, 0.95), 'abdomen': (0, 0, 1.13),           # chest bottom / skirt waist
    'chest_top': (0, 0, 1.395), 'neck_base': (0, 0, 1.42),       # under the collar band
    'neck_head': (0, 0, 1.47), 'head_top': (0, 0, 1.80),         # chin pivot (HEAD_PIVOT), crown
    'shoulder': (0.255, 0.02, 1.37),                             # inside the pauldron, upper arm top
    'elbow': (0.355, 0.037, 1.185),                              # forearm origin
    'wrist': (0.454, 0.037, 0.972),                              # forearm end, in the cuff
    'hand_tip': (0.505, 0.04, 0.759),                            # fist end
    'hip': (0.115, 0.0, 0.86), 'knee': (0.16, 0.0, 0.62),        # thigh top / shin top
    'ankle': (0.225, 0.0, 0.26), 'toe': (0.24, -0.30, 0.03),     # ankle cuff / boot toe
}
UNUSED_BONES = ['hat', 'cannon', 'sash'] + \
    [f'finger_{d}_{s}' for d in ('index', 'middle', 'ring', 'pinky', 'thumb') for s in 'lr']


def VERTEX_BONE(part, v):
    """The skirt's hem follows the cloth bones (front plate robe_front, back plate robe_back),
    its waist the hips: a high kick lifts the plate instead of passing through it."""
    if part == 'skirt' and v[2] < 0.9:
        return 'robe_front' if v[1] < 0 else 'robe_back'
    return None

# palette outfits (legends_recolor.py): a new page from the hand-painted one, only the stone and
# its amber veins recoloured (skin, hair, metal and face stay)
RECOLOR = {
    # Obsidian: black volcanic glass with cold violet highlights; the veins glow violet
    'obsidiana': [
        {'hue': (4, 23), 'sat': (.55, 1), 'ramp': [(0, '#07060a'), (.4, '#120f19'), (.75, '#211c2e'), (.92, '#3a3352'), (1, '#8d7fc4')]},
        {'hue': (30, 48), 'sat': (.8, 1), 'ramp': [(0, '#8c4dff'), (1, '#d9b3ff')]},
    ],
}

# outfits with their own pieces (legends_rig.outfit / export_godot): the boxer and the guinea pig
OUTFITS = {'Boxe': 'x12boxe_modelo', 'Cobaia': 'x12cobaia_modelo'}
