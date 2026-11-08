"""Orsted, gunslinger outfit (fighter id `volt`): the character module for legends_build.py.

Pieces in orsted_pistoleiro (the base's pieces repainted plus the hat, the duster's skirt, the
bandana, the holster, the spurs and the revolver); texture from the outfit's 18 panels
(concept-art/characters/orsted/orsted-pistoleiro-texturas-18-paineis-psx-v1.png); the face page is
the base's expression atlas (copied as orstedpist_rosto_atlas.png).
"""
from pathlib import Path

import orsted_modelo as base
import orsted_pistoleiro

ID = 'volt'
NAME = 'orstedpist'
SRC = base.SRC
HEIGHT = base.HEIGHT
PREFIX = 'OP_'
COLLECTION = 'Orsted_Pistoleiro'
PIECES = [orsted_pistoleiro]
PART_TRANSFORMS = {'head': base.PART_TRANSFORMS['head']}

# UV (legends_uv.py)
UV_METHOD = {'head': 'box', 'chest': 'front_back', 'belly': 'front_back', 'pelvis': 'front_back',
             'coat_skirt': 'front_back', 'pauldron': 'box', 'hand': 'box', 'boot': 'box', 'holster': 'box',
             'bandana_knot': 'box', 'spur': 'box', 'spur_wheel': 'box',
             'rev_cylinder': 'box', 'rev_frame': 'box', 'rev_grip': 'box', 'rev_hammer': 'box', 'rev_guard': 'box',
             'rev_rod': 'box', 'rev_sight': 'box', 'rev_barrel': 'cyl'}
UV_DENSITY = {'chest': 1.5, 'head': 1.6, 'hand': 2.2, 'pauldron': 1.5, 'coat_skirt': 1.2, 'hat_brim': 1.3, 'hat_crown': 1.4}
UV_HIDDEN = {(p, '*') for p in ('upper_arm', 'forearm', 'bracer', 'sleeve_cuff', 'thigh', 'shin', 'boot_shaft',
                                'neck', 'belt', 'hat_band', 'bandana')} | {
    ('chest', 'bottom'), ('belly', 'top'), ('belly', 'bottom'), ('pelvis', 'top'), ('pelvis', 'bottom'),
    ('coat_skirt', 'top'), ('coat_skirt', 'bottom')}

# texture (legends_paint.py): the 18 panels, numbers as printed on the sheet
PANELS = SRC.parents[3] / 'concept-art/characters/orsted/orsted-pistoleiro-texturas-18-paineis-psx-v1.png'
PAINT = {
    # the duster open over the dark vest (panel 1), its back (2); the skirt open in front over the trousers
    ('chest', 'front'): ('panel', 1, (0.0, 0.0, 1.0, 0.70)), ('chest', 'back'): ('panel', 2, (0.0, 0.0, 1.0, 0.70)),
    ('chest', 'top'): ('tone', 'coat'),
    ('belly', 'front'): ('panel', 1, (0.0, 0.70, 1.0, 1.0)), ('belly', 'back'): ('panel', 2, (0.0, 0.70, 1.0, 1.0)),
    ('pelvis', 'front'): ('panel', 10, (0.0, 0.0, 1.0, 0.35)), ('pelvis', 'back'): ('panel', 11, (0.0, 0.0, 1.0, 0.35)),
    ('coat_skirt', 'front'): ('panel', 4, (0.0, 0.0, 0.5, 1.0)), ('coat_skirt', 'back'): ('panel', 4, (0.0, 0.0, 0.5, 1.0)), ('coat_skirt', '*'): ('tone', 'coat'),
    ('belt', 'cyl'): ('panel', 8, (0.0, 0.25, 1.0, 0.75), 'wrap'),
    ('sleeve', 'cyl'): ('panel', 3, (0.1, 0.0, 0.9, 0.72)), ('sleeve_cuff', 'cyl'): ('panel', 3, (0.1, 0.74, 0.9, 0.92), 'wrap'),
    ('upper_arm', 'cyl'): ('tone', 'cream'), ('forearm', 'cyl'): ('tone', 'skin'),
    ('bracer', 'cyl'): ('panel', 12, (0.05, 0.0, 0.95, 0.28), 'wrap'), ('bracer', '*'): ('tone', 'glove'),
    ('hand', '+x'): ('panel', 12, (0.1, 0.25, 0.9, 1.0)), ('hand', '-x'): ('panel', 13, (0.1, 0.1, 0.9, 0.9)),
    ('hand', '*'): ('tone', 'glove'),
    ('pauldron_r', '*'): ('panel', 5),
    ('thigh', 'cyl'): ('panel', 10, (0.5, 0.3, 1.0, 1.0)), ('shin', 'cyl'): ('panel', 11, (0.0, 0.45, 0.5, 1.0)),
    ('boot_shaft', 'cyl'): ('panel', 14, (0.15, 0.0, 0.85, 0.45)),
    ('boot', '-y'): ('panel', 14, (0.05, 0.50, 0.95, 1.0)), ('boot', '+z'): ('tone', 'boot'),
    ('boot', '-z'): ('panel', 16, 'full'), ('boot', '*'): ('panel', 15, (0.0, 0.40, 1.0, 1.0)),
    ('hat_brim', 'cap0'): ('panel', 18, 'full'), ('hat_brim', 'cap1'): ('panel', 18, 'full'), ('hat_brim', '*'): ('tone', 'hat'),
    ('hat_crown', 'cyl'): ('panel', 17, (0.0, 0.0, 1.0, 0.70), 'wrap'), ('hat_crown', '*'): ('tone', 'hat'),
    ('hat_band', '*'): ('tone', 'copper'),
    ('bandana', '*'): ('tone', 'rag'), ('bandana_knot', '*'): ('panel', 6),
    ('holster_r', '*'): ('panel', 9), ('spur', '*'): ('tone', 'copper'), ('spur_wheel', '*'): ('tone', 'copper'),
    ('rev_barrel', '*'): ('tone', 'gunmetal'), ('rev_cylinder', '-z'): ('tone', 'glass'), ('rev_cylinder', '*'): ('tone', 'gunmetal'),
    ('rev_frame', '*'): ('tone', 'copper'), ('rev_grip', '*'): ('tone', 'wood'), ('rev_hammer', '*'): ('tone', 'gunmetal'),
    ('rev_guard', '*'): ('tone', 'copper'), ('rev_rod', '*'): ('tone', 'gunmetal'), ('rev_sight', '*'): ('tone', 'copper'),
    ('neck', '*'): ('tone', 'skin'),
    ('head', '*'): base.PAINT[('head', '*')],
}
# the front faces under the nose stay skin, the mouth is drawn over them (base page fix 2026-11-08)
FACE_PAINT = {('head', fi): ('tone', 'skin') for fi in (76, 77, 78, 79, 84, 85)}
PANEL_FILL = {1: 'coat', 2: 'coat', 3: 'coat', 4: 'coat', 5: 'scrap', 6: 'rag', 7: 'leather', 8: 'leather', 9: 'leather',
              10: 'trousers', 11: 'trousers', 12: 'glove', 13: 'glove', 14: 'boot', 15: 'boot', 16: 'boot', 17: 'hat', 18: 'hat'}
PANEL_FILL_ALL = (126, 125, 126)
PAGE_COLOURS = 20
TONE_PANEL = {'coat': '#c9a46a', 'hat': '#5a3426', 'leather': '#6b3a22', 'trousers': '#4a2a22', 'boot': '#4f2c20',
              'glove': '#5c3324', 'cream': '#efdcb4', 'rag': '#b8302a', 'copper': '#c4693a', 'gunmetal': '#4a4e58',
              'wood': '#7d2f2b', 'scrap': '#7a8494', 'glass': '#22d8ee', 'skin': '#faba78', 'shade': '#c98559',
              'hair': '#dba043', 'hair_hi': '#f4c76c', 'hair_dark': '#5a3a24', 'shirt': '#efdcb4', 'plate': '#7a8494',
              'cloth': '#c9a46a', 'metal': '#4a4e58'}

# face page: the base's expressions and face square
EXPRESSIONS = base.EXPRESSIONS
FACE_BOX = base.FACE_BOX


def VERTEX_BONE(part, v):
    """The duster's skirt below the belt follows the cloth bones: front half robe_front, back
    half robe_back, so a kick lifts the coat instead of passing through it."""
    if part.startswith('coat_skirt') and v[2] < 1.0:
        return 'robe_front' if v[1] < 0 else 'robe_back'
    return None
