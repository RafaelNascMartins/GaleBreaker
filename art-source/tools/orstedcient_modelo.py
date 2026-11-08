"""Orsted, mad scientist outfit (fighter id `volt`): the character module for legends_build.py.

Pieces in orsted_cientista (the base's pieces repainted, the energy cannon and the back tank as the
tesla coil backpack, plus the long lab coat's skirt, the turtleneck collar, the welding goggles
and the coil's ball); texture from the outfit's 17 panels
(concept-art/characters/orsted/orsted-cientista-maluco-texturas-17-paineis-psx-v1.png) and the
cannon's 8 panels (21-28, as the base); the face page is the base's expression atlas.
"""
import orsted_modelo as base
import orsted_cientista

ID = 'volt'
NAME = 'orstedcient'
SRC = base.SRC
HEIGHT = base.HEIGHT
PREFIX = 'OC_'
COLLECTION = 'Orsted_Cientista'
PIECES = [orsted_cientista]
_TANK = base.PART_TRANSFORMS['cell']
PART_TRANSFORMS = {'head': base.PART_TRANSFORMS['head'], 'cell': _TANK, 'cell_cap_top': _TANK, 'cell_cap_bottom': _TANK,
                   'cell_strap0': _TANK, 'cell_strap1': _TANK, 'coil_ball': _TANK, 'coil_spark': _TANK}

# UV (legends_uv.py)
UV_METHOD = {k: v for k, v in base.UV_METHOD.items() if k.startswith('gun_') or k in ('head', 'chest', 'belly', 'pelvis', 'hand', 'boot')}
UV_METHOD.update({'coat_skirt': 'front_back', 'lens': 'box', 'coil_ball': 'box', 'coil_spark': 'box'})
UV_DENSITY = {'gun_muzzle': 2.2, 'gun_rear': 2.0, 'gun_chamber': 1.8, 'chest': 1.5, 'head': 1.6, 'hand': 2.2, 'coat_skirt': 1.2}
UV_HIDDEN = {(p, '*') for p in ('upper_arm', 'bracer', 'sleeve_cuff', 'thigh', 'shin', 'boot_shaft', 'neck', 'belt', 'collar')} | {
    ('chest', 'bottom'), ('belly', 'top'), ('belly', 'bottom'), ('pelvis', 'top'), ('pelvis', 'bottom'),
    ('coat_skirt', 'top'), ('coat_skirt', 'bottom')}

# texture (legends_paint.py): the 17 panels, then the cannon's 8 as 21-28
PANELS = [(SRC.parents[3] / 'concept-art/characters/orsted/orsted-cientista-maluco-texturas-17-paineis-psx-v1.png', 1),
          (SRC.parents[3] / 'concept-art/characters/orsted/orsted-canhao-mao-texturas-8-paineis-psx-v1.png', 21)]
PAINT = {k: v for k, v in base.PAINT.items() if k[0].startswith('gun_')}
PAINT.update({
    # the lab coat open over the turtleneck, the chest battery and the suspenders (1), its back (2)
    ('chest', 'front'): ('panel', 1, (0.0, 0.0, 1.0, 0.72)), ('chest', 'back'): ('panel', 2, (0.0, 0.0, 1.0, 0.72)),
    ('chest', 'top'): ('tone', 'coat'),
    ('belly', 'front'): ('panel', 1, (0.0, 0.72, 1.0, 1.0)), ('belly', 'back'): ('panel', 2, (0.0, 0.72, 1.0, 1.0)),
    ('pelvis', 'front'): ('panel', 10, (0.0, 0.0, 1.0, 0.35)), ('pelvis', 'back'): ('panel', 11, (0.0, 0.0, 1.0, 0.35)),
    ('coat_skirt', 'front'): ('panel', 4, (0.0, 0.0, 0.5, 1.0)),
    ('coat_skirt', 'back'): ('panel', 4, (0.0, 0.0, 0.5, 1.0)), ('coat_skirt', '*'): ('tone', 'coat'),
    ('belt', 'cyl'): ('panel', 10, (0.0, 0.0, 1.0, 0.10), 'wrap'),
    ('sleeve', 'cyl'): ('panel', 3, (0.1, 0.0, 0.9, 0.62)), ('sleeve_cuff', 'cyl'): ('panel', 3, (0.1, 0.62, 0.9, 0.95), 'wrap'),
    ('upper_arm', 'cyl'): ('tone', 'coat'), ('forearm', 'cyl'): ('panel', 7, (0.25, 0.0, 0.75, 1.0)),
    ('bracer', '*'): ('tone', 'rubber'),
    ('hand', '+x'): ('panel', 8, (0.1, 0.1, 0.9, 0.95)), ('hand', '-x'): ('panel', 9, (0.1, 0.1, 0.9, 0.9)),
    ('hand', '*'): ('tone', 'rubber'),
    ('thigh', 'cyl'): ('panel', 10, (0.5, 0.3, 1.0, 1.0)), ('shin', 'cyl'): ('panel', 11, (0.0, 0.45, 0.5, 1.0)),
    ('boot_shaft', 'cyl'): ('panel', 12, (0.2, 0.0, 0.8, 0.40)),
    ('boot', '-y'): ('panel', 12, (0.05, 0.45, 0.95, 1.0)), ('boot', '+z'): ('tone', 'rubber'),
    ('boot', '-z'): ('panel', 14, 'full'), ('boot', '*'): ('panel', 13, (0.0, 0.35, 1.0, 1.0)),
    # the back tank as the tesla coil: copper coils round it, dark caps, leather straps, brass ball
    ('cell', 'cyl'): ('panel', 15, (0.30, 0.15, 0.70, 0.45), 'wrap'), ('cell', '*'): ('tone', 'metal'),
    ('cell_cap', '*'): ('tone', 'metal'), ('cell_strap', '*'): ('tone', 'leather'), ('coil_ball', '*'): ('tone', 'brass'), ('coil_spark', '*'): ('tone', 'glass'),
    ('collar', '*'): ('panel', 6, (0.2, 0.05, 0.8, 0.30), 'wrap'),
    ('goggle_strap', '*'): ('tone', 'leather'),
    ('lens', '-y'): ('panel', 16, (0.16, 0.30, 0.46, 0.72)), ('lens', '*'): ('tone', 'brass'),
    ('neck', '*'): ('tone', 'skin'),
    ('head', '*'): base.PAINT[('head', '*')],
})
FACE_PAINT = {('head', fi): ('tone', 'skin') for fi in (76, 77, 78, 79, 84, 85)}
PANEL_FILL = {1: 'coat', 2: 'coat', 3: 'coat', 4: 'coat', 5: 'coat', 6: 'rubber', 7: 'rubber', 8: 'rubber', 9: 'rubber',
              10: 'trousers', 11: 'trousers', 12: 'rubber', 13: 'rubber', 14: 'rubber', 15: 'metal', 16: 'leather', 17: 'hair',
              23: 'gunmetal', 24: 'gunmetal', 25: 'gunmetal', 26: 'gunmetal', 27: 'gunmetal', 28: 'gunmetal'}
PANEL_FILL_ALL = (169, 167, 171)
PAGE_COLOURS = 20
TONE_PANEL = {'coat': '#e8e4e8', 'rubber': '#2e2c30', 'trousers': '#5e5c64', 'leather': '#6b3a22', 'brass': '#c9962e',
              'metal': '#3c4048', 'copper': '#c4693a', 'gunmetal': '#3b4856', 'gun': '#d99a2b', 'glass': '#22d8ee',
              'skin': '#faba78', 'shade': '#c98559', 'hair': '#dba043', 'hair_hi': '#f4c76c', 'hair_dark': '#5a3a24',
              'shirt': '#2e2c30', 'glove': '#2e2c30', 'boot': '#2e2c30', 'plate': '#c9962e', 'cloth': '#e8e4e8'}

EXPRESSIONS = base.EXPRESSIONS
FACE_BOX = base.FACE_BOX


def VERTEX_BONE(part, v):
    """The lab coat's skirt below the belt follows the cloth bones (front robe_front, back robe_back)."""
    if part.startswith('coat_skirt') and v[2] < 1.0:
        return 'robe_front' if v[1] < 0 else 'robe_back'
    return None
