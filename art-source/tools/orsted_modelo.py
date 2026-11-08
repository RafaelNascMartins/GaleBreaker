"""Orsted (ex-Volt, fighter id `volt`): the character module for legends_build.py.

Concept: concept-art/characters/orsted/orsted-turnaround-psx-v1.png, cropped by outfit_crops.py
onto X12's crop grid (figure 840 px) to orsted_frente / perfil / costas; HEIGHT is his height with
the hair spikes (MPP = HEIGHT / 840).
"""
from pathlib import Path

import orsted_cabeca
import orsted_arma
import orsted_bombas
import orsted_braco
import orsted_perna
import orsted_tronco

ID = 'volt'
NAME = 'orsted'
SRC = Path(__file__).resolve().parents[2] / 'art-source/characters/volt/legends'
HEIGHT = 1.86
PREFIX = 'OR_'
COLLECTION = 'Orsted_Facetas'
PIECES = [orsted_cabeca, orsted_tronco, orsted_braco, orsted_perna, orsted_arma, orsted_bombas]
# props (legends_rig): built as their own objects on the hand, not in the body, exported as
# <ID>_<label>Prop and shown by the game only while a clip uses them
PROPS = {'Bomba': ['bomb_body', 'bomb_gem', 'bomb_orb0', 'bomb_orb1', 'bomb_orb2', 'bomb_collar', 'bomb_handle0', 'bomb_handle1',
                   'bomb_handle2', 'bomb_lug', 'bomb_back_gem'],
         'Dinamite': ['dynamite_stick', 'dynamite_cap', 'dynamite_fuse', 'dynamite_spark']}

# UV (legends_uv.py): how each piece is opened; the rest are limbs unrolled as cylinders
UV_METHOD = {'head': 'box', 'chest': 'front_back', 'belly': 'front_back', 'pelvis': 'front_back',
             'chest_plate': 'box', 'knee_plate': 'box', 'pauldron': 'box', 'hand': 'box', 'boot': 'box',
             'pouch': 'box', 'tabard': 'box', 'rag': 'box', 'core': 'box',
             'gun_barrel': 'cyl', 'gun_chamber': 'box', 'gun_ring_back': 'box', 'gun_ring_front': 'box', 'gun_muzzle': 'box',
             'gun_rear': 'box', 'gun_handle_bar': 'box', 'gun_handle_post_back': 'box', 'gun_handle_post_front': 'box',
             'gun_grip': 'box', 'gun_guard': 'box', 'bomb_gem': 'box', 'bomb_collar': 'box', 'bomb_handle0': 'box',
             'bomb_handle1': 'box', 'bomb_handle2': 'box', 'bomb_lug': 'box', 'bomb_back_gem': 'box', 'bomb_orb0': 'box',
             'bomb_orb1': 'box', 'bomb_orb2': 'box', 'dynamite_cap': 'box', 'dynamite_fuse': 'cyl', 'dynamite_spark': 'box'}
UV_DENSITY = {'gun_muzzle': 2.2, 'gun_rear': 2.0, 'gun_chamber': 1.8, 'chest': 1.5, 'head': 1.6, 'hand': 2.4, 'chest_plate': 2.0, 'pauldron': 1.5, 'knee_plate': 1.6}
UV_HIDDEN = {(p, '*') for p in ('upper_arm', 'forearm', 'bracer', 'sleeve_cuff', 'thigh', 'shin', 'boot_shaft',
                                'neck', 'cell', 'belt')} | {
    ('chest', 'bottom'), ('belly', 'top'), ('belly', 'bottom'), ('pelvis', 'top'), ('pelvis', 'bottom'),
    ('chest_plate', '+y'), ('knee_plate', '+y'), ('tabard', '+y'), ('rag', '-y')}

# texture (legends_paint.py): the 20-panel sheet, numbers as printed on it
PANELS = [(SRC.parents[3] / 'concept-art/characters/orsted/orsted-texturas-20-paineis-psx-v1.png', 1),
          (SRC.parents[3] / 'concept-art/characters/orsted/orsted-canhao-mao-texturas-8-paineis-psx-v1.png', 21)]   # the hand cannon: 21-28
PAINT = {
    # hand cannon (panels 21-28): riveted mustard barrel, cyan glass chamber, the muzzle's glowing
    # face, the rear cap with its bolts, the taped grip; rings, posts and guard flat
    ('gun_barrel', 'cyl'): ('panel', 21), ('gun_barrel', '*'): ('tone', 'gunmetal'),
    ('gun_chamber', '+x'): ('panel', 23), ('gun_chamber', '-x'): ('panel', 23), ('gun_chamber', '+z'): ('panel', 23),
    ('gun_chamber', '-z'): ('panel', 23), ('gun_chamber', '*'): ('tone', 'gunmetal'),
    ('gun_ring_back', '*'): ('tone', 'gunmetal'), ('gun_ring_front', '*'): ('tone', 'gunmetal'),
    ('gun_muzzle', '-y'): ('panel', 24), ('gun_muzzle', '*'): ('tone', 'gunmetal'),
    ('gun_rear', '+y'): ('panel', 25), ('gun_rear', '*'): ('panel', 21, (0.0, 0.35, 1.0, 0.65)),
    ('gun_handle_bar', '*'): ('panel', 22, (0.05, 0.40, 0.95, 0.68)), ('gun_handle_post_back', '*'): ('tone', 'copper'),
    ('gun_handle_post_front', '*'): ('tone', 'copper'),
    ('gun_grip', '*'): ('panel', 26), ('gun_guard', '*'): ('tone', 'gunmetal'),
    # bombs (props): flat tones like their concept sheets (slate with a light face, blue gems,
    # copper fittings; the red stick with its grey cap)
    ('bomb_body', '*'): ('tone', 'slate'), ('bomb_handle', '*'): ('tone', 'slate'), ('bomb_lug', '*'): ('tone', 'slate'),
    ('bomb_gem', '-y'): ('panel', 24, (0.15, 0.15, 0.85, 0.85)), ('bomb_gem', '*'): ('tone', 'glass'),
    ('bomb_orb0', '*'): ('tone', 'glass'), ('bomb_orb1', '*'): ('tone', 'glass'), ('bomb_orb2', '*'): ('tone', 'glass'),
    ('bomb_back_gem', '*'): ('tone', 'glass'), ('bomb_collar', '*'): ('tone', 'copper'),
    ('dynamite_stick', '*'): ('tone', 'dynamite'), ('dynamite_cap', '*'): ('tone', 'cap'), ('dynamite_fuse', '*'): ('tone', 'fuse'),
    ('dynamite_spark', '*'): ('tone', 'spark'),
    # shirt: suspenders and their cross strap on the front and the back (panel 2), the open collar
    ('chest', 'front'): ('panel', 2), ('chest', 'back'): ('panel', 2), ('chest', 'top'): ('panel', 20, (0.3, 0.0, 0.7, 0.4)),
    ('belly', 'front'): ('panel', 2, (0.05, 0.75, 0.95, 1.0)), ('belly', 'back'): ('panel', 2, (0.05, 0.75, 0.95, 1.0)),
    ('pelvis', 'front'): ('panel', 11, (0.0, 0.0, 1.0, 0.55)), ('pelvis', 'back'): ('panel', 12, (0.0, 0.0, 0.6, 0.55)),
    ('chest_plate', '-y'): ('panel', 1), ('chest_plate', '*'): ('tone', 'plate'),
    ('cell', 'cyl'): ('panel', 17, (0.25, 0.22, 0.75, 0.45)), ('cell', '*'): ('tone', 'metal'),   # glass body, cyan
    ('cell_cap', '*'): ('tone', 'metal'), ('cell_strap', '*'): ('tone', 'leather'),
    ('core', '-y'): ('panel', 1, (0.37, 0.32, 0.63, 0.68)),   # the glowing rings face front
    ('core', '*'): ('tone', 'metal'),
    ('pauldron_fin_r', '*'): ('tone', 'rust'),
    ('pouch', '-y'): ('panel', 9, (0.02, 0.38, 0.48, 1.0)), ('pouch', '*'): ('tone', 'leather'),
    ('belt', 'cyl'): ('panel', 9, (0.02, 0.07, 0.98, 0.22), 'wrap'),
    ('tabard', '-y'): ('panel', 10), ('tabard', '*'): ('tone', 'plate'),
    ('rag', '+y'): ('panel', 12, (0.55, 0.0, 0.85, 1.0)), ('rag', '*'): ('tone', 'rag'),
    ('sleeve', 'cyl'): ('panel', 4, (0.15, 0.0, 0.85, 0.75)), ('sleeve_cuff', 'cyl'): ('panel', 4, (0.1, 0.75, 0.9, 0.92), 'wrap'),
    ('upper_arm', 'cyl'): ('panel', 5, (0.2, 0.4, 0.8, 1.0)), ('forearm', 'cyl'): ('panel', 6, (0.2, 0.0, 0.8, 0.75)),
    ('bracer', 'cyl'): ('panel', 6, (0.12, 0.82, 0.40, 0.97), 'wrap'),   # the leather beside the rivet ('bracer', '*'): ('tone', 'leather'), ('sleeve_cuff', '*'): ('tone', 'shirt'),
    ('pauldron_r', '*'): ('panel', 3),
    # hand: A-pose, the palm faces the thigh (inner side), the back of the glove out
    # fist: the glove's back over the knuckles outside, the curled finger tips on its end, the
    # palm plain glove
    ('hand', '+x'): ('panel', 7, (0.06, 0.05, 0.94, 0.80)), ('hand', '-z'): ('panel', 7, (0.10, 0.74, 0.90, 0.98)),
    ('hand', '-x'): ('tone', 'glove'), ('hand', '-y'): ('panel', 7, (0.30, 0.30, 0.70, 0.98)),
    ('hand', '+y'): ('panel', 7, (0.30, 0.30, 0.70, 0.98)), ('hand', '*'): ('tone', 'glove'),
    ('thigh', 'cyl'): ('panel', 11, (0.5, 0.2, 1.0, 1.0)), ('shin', 'cyl'): ('panel', 12, (0.0, 0.3, 0.45, 1.0)),
    ('knee_plate', '-y'): ('panel', 13), ('knee_plate', '*'): ('tone', 'plate'),
    ('boot_shaft', 'cyl'): ('panel', 14, (0.2, 0.0, 0.8, 0.45)),
    ('boot', '-y'): ('panel', 14, (0.05, 0.45, 0.95, 1.0)), ('boot', '+z'): ('panel', 14, (0.2, 0.45, 0.8, 0.65)),
    ('boot', '-z'): ('panel', 16, 'full'), ('boot', '*'): ('panel', 15, (0.0, 0.35, 1.0, 1.0)),
    ('neck', '*'): ('tone', 'skin'),
    # head: the geometry decides hair or skin; hair from the hair panels (18 top, 19 side: blond
    # spikes over the dark brown underneath)
    ('head', '*'): ('ftone', {'hair': ('tone', 'hair'), 'hair_hi': ('tone', 'hair_hi'), 'hair_dark': ('tone', 'hair_dark'),
                              'skin': ('tone', 'skin'), 'shade': ('tone', 'shade')}),
}
PANEL_CROP = {1: (0.03, 0.03, 0.97, 0.97), 3: (0.02, 0.03, 0.98, 0.97), 7: (0.08, 0.05, 0.92, 0.97),
              8: (0.03, 0.05, 0.97, 0.97), 10: (0.0, 0.0, 1.0, 0.97), 13: (0.02, 0.02, 0.98, 0.98)}
# the panels sit on the sheet's grey: that grey, flooded in from each panel's border, becomes the material
PANEL_FILL = {1: 'plate', 2: 'shirt', 3: 'plate', 4: 'shirt', 5: 'skin', 6: 'skin', 7: 'skin', 8: 'skin', 9: 'leather',
              10: 'plate', 11: 'trousers', 12: 'trousers', 13: 'plate', 14: 'boot', 15: 'boot', 16: 'boot', 17: 'metal',
              18: 'hair', 19: 'hair', 20: 'shirt', 23: 'gunmetal', 24: 'gunmetal', 25: 'gunmetal', 26: 'gunmetal',
              27: 'gunmetal', 28: 'gunmetal'}
PANEL_FILL_ALL = (154, 154, 154)
PAGE_COLOURS = 20         # shirt, trousers, mustard plates, rust blue, leather, skin, blond and brown hair, cyan
TONE_PANEL = {'shirt': (2, (0.1, 0.3, 0.2, 0.6)), 'trousers': (11, (0.4, 0.5, 0.6, 0.7)), 'plate': (13, (0.6, 0.2, 0.8, 0.4)),
              'leather': '#6d4030', 'skin': (5, (0.3, 0.5, 0.6, 0.8)), 'hair': '#dba043', 'hair_hi': '#f4c76c', 'hair_dark': '#5a3a24',
              'glove': (7, (0.3, 0.3, 0.7, 0.6)), 'boot': (15, (0.6, 0.15, 0.8, 0.3)), 'metal': '#3c4048',
              'rag': '#c0392b', 'gunmetal': '#3b4856', 'copper': '#c4693a', 'gun': '#d99a2b', 'dynamite': '#c62f28', 'fuse': '#7a2020', 'cap': '#8a7a72', 'slate': '#47526b', 'spark': '#ffc23a', 'rust': '#4f6676', 'glass': '#22d8ee', 'shade': '#c98559', 'cloth': (10, (0.3, 0.1, 0.6, 0.4)), 'stone': (2, (0.1, 0.3, 0.2, 0.6))}

# face page (legends_face.py): his 24 expressions; one cell covers this square of the front of
# the head, chin to just above the brows, the eye line at ~43 % from the top (drawn eyes z 1.665)
EXPRESSIONS = SRC.parents[3] / 'concept-art/characters/orsted/orsted-expressoes-24-psx-v1.png'
FACE_BOX = {'x': (-0.1125, 0.1125), 'z': (1.5134, 1.7384)}   # the 25 % bigger head, 2.7 cm lower (PART_TRANSFORMS), then the face 2.7 cm lower still so the eyebrows show under the fringe (2026-11-08)

# placements the user adjusted by hand in Blender on 2026-11-07 (object transforms, shapes untouched;
# legends_build applies them after its checks): the head forward and lower on the neck, the chest
# plate tilted back onto the chest, the core lower and closer, the tank hung closer to the back at a
# slant, the shoulder fin moved forward and in. The head's and core's 4-6 mm sideways drift is zeroed.
# 2026-11-08 the user asked for a symmetric body (except the shoulder plate and the hair): the
# tank, the core and the chest plate keep where he moved them (closer to the back, lower) but lose
# their sideways tilt and drift, as pure moves on the centre line.
_TANK = [[1, 0, 0, 0.0], [0, 1, 0, -0.04947], [0, 0, 1, 0.00718], [0, 0, 0, 1]]
PART_TRANSFORMS = {
    'head': [[1, 0, 0, 0.0], [0, 1, 0, -0.07018], [0, 0, 1, -0.02717], [0, 0, 0, 1]],
    'chest_plate': [[1, 0, 0, 0.0], [0, 1, 0, 0.01994], [0, 0, 1, 0.00171], [0, 0, 0, 1]],
    'core': [[1, 0, 0, 0.0], [0, 1, 0, 0.01862], [0, 0, 1, -0.0298], [0, 0, 0, 1]],
    'cell': _TANK, 'cell_cap_top': _TANK, 'cell_cap_bottom': _TANK, 'cell_strap0': _TANK, 'cell_strap1': _TANK,
    'pauldron_fin_r': [[0.99999, -0.0026, -0.00438, 0.08797], [0.00261, 0.99999, 0.0022, -0.08907],
                       [0.00437, -0.00222, 0.99999, -0.05482], [0, 0, 0, 1]],
}

# skeleton (legends_rig.py): the game's Volt rig (its clips come along); joints read off the
# hand-made parts (left side), the head joint under the grown, forward-moved head
RIG_SOURCE = (SRC.parent / 'volt.blend', 'volt_Rig')
JOINTS = {
    'pelvis': (0, 0, 0.95), 'abdomen': (0, 0, 1.10),            # trouser top / belly
    'chest_top': (0, 0, 1.455), 'neck_base': (0, 0, 1.48),        # shoulder line / collar
    'neck_head': (0, -0.030, 1.515), 'head_top': (0, -0.070, 1.900),   # under the jaw, crown
    'shoulder': (0.225, 0.030, 1.420),                            # inside the sleeve
    'elbow': (0.300, 0.030, 1.215),                               # forearm origin
    'wrist': (0.370, 0.030, 1.040),                               # in the bracer
    'hand_tip': (0.430, 0.030, 0.800),                            # glove end
    'hip': (0.100, 0.015, 0.870), 'knee': (0.160, 0.025, 0.580),  # thigh top / knee plate
    'ankle': (0.185, 0.035, 0.150), 'toe': (0.210, -0.190, 0.030),  # boot shaft end / toe cap
}
# kept from the shared rig: cannon (the energy hand cannon's socket), robe_front / robe_back (the
# mustard cloth and the red rag)
UNUSED_BONES = ['hat', 'sash'] + [f'finger_{d}_{s}' for d in ('index', 'middle', 'ring', 'pinky', 'thumb') for s in 'lr']


def VERTEX_BONE(part, v):
    """The hanging cloths follow the cloth bones below the belt (the mustard cloth robe_front, the
    red rag robe_back): a kick lifts them instead of passing through them."""
    if part == 'tabard' and v[2] < 1.02:
        return 'robe_front'
    if part == 'rag' and v[2] < 1.02:
        return 'robe_back'
    return None

# the game spawns his shots at socket_muzzle = the cannon bone's head: at the muzzle's face
SOCKET_AT = {'cannon': ('gun_muzzle', 'gun_barrel')}   # head at the muzzle's face, pointing down the barrel

# palette outfits (legends_recolor.py), by part islands (orsted_partes_uv.json): his blond hair and
# the yellow plates share a hue, so the head, neck and bare arms are never touched.
RECOLOR_KEEP_PARTS = ('head', 'neck', 'upper_arm', 'forearm', 'bomb', 'dynamite')
RECOLOR = {
    # Invertido: the plates and the cannon steel blue, the slate trims rust orange, the shirt and
    # trousers bone white, the leather straps charcoal, the cyan glow magenta, the red rag teal
    'invertido': [
        {'hue': (175, 200), 'sat': (.6, 1), 'ramp': [(0, '#6a0a50'), (.6, '#d81f96'), (1, '#ff6fd8')]},
        {'hue': (28, 42), 'sat': (.65, 1), 'val': (.5, 1), 'ramp': [(0, '#16284a'), (.45, '#2c5390'), (.8, '#3a6fb0'), (1, '#86afe4')]},
        {'hue': (195, 230), 'sat': (.15, .45), 'ramp': [(0, '#6b3418'), (1, '#c8692e')]},
        {'hue': (8, 28), 'sat': (.5, .7), 'val': (.3, .5), 'ramp': [(0, '#18181c'), (1, '#3b3b42')]},
        {'hue': (0, 10), 'sat': (.6, 1), 'val': (.5, 1), 'ramp': [(0, '#145f63'), (1, '#2aa8a8')]},
        {'hue': (290, 360), 'sat': (0, .2), 'val': (.1, .3),
         'parts': ('chest', 'belly', 'pelvis', 'sleeve', 'thigh', 'shin', 'boot_shaft'),
         'ramp': [(0, '#8c8270'), (.5, '#cbc1ab'), (1, '#ebe3cf')]},
    ],
}

# outfits with their own pieces (legends_rig.outfit / export_godot): the gunslinger (revolver,
# hat, duster) and the mad scientist (lab coat, goggles, tesla backpack)
OUTFITS = {'Pistoleiro': 'orstedpist_modelo', 'Cientista': 'orstedcient_modelo'}
