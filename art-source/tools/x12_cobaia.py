"""X12, guinea pig outfit (Weapon X-inspired): the new pieces, by hand on the Legends references,
measured on the outfit's concept (x12cobaia_frente / perfil / costas, outfit_crops.py at the base
crops' scale, matched on the shoulder line: the helmet is taller than her hair).

A cream lab jumpsuit (chest with the zipper, belly, hips, wide suit legs), a dark turtleneck, short
cream sleeves over the deltoids, black long sleeves, dark studded cuffs, big grey gloves, a grey
knee band, tall black boots with a grey toe cap, a chest strap and a belt (the harness), a pouch
on her right hip and one on her left thigh, a bulky grey helmet whose red visor covers the eyes
(mouth and chin stay visible: the expression atlas still shows below it) and a bundle of cables
from the helmet down her back. The base head is kept inside the helmet. The concept's arms are
spread wider than the base A-pose: the arm pieces follow the base's arm axes (same rig), only
their thickness comes from the concept. Numbers in metres; front is -y, her left is +x.
"""
import numpy as np

import legends_kit as lk
import x12_boxe

AXIS, SIDE = x12_boxe.AXIS, x12_boxe.SIDE
DELT_AXIS, DELT_SIDE = x12_boxe.DELT_AXIS, x12_boxe.DELT_SIDE
GLOVE_AXIS, GLOVE_SIDE = x12_boxe.GLOVE_AXIS, x12_boxe.GLOVE_SIDE

SUIT_TOP = x12_boxe.TOP                  # chest: the boxer's top with the shoulder line out to the deltoid
SUIT_BELLY = x12_boxe.BELLY
SUIT_HIPS = x12_boxe.SHORTS
TURTLENECK = [(1.380, .056, .060), (1.520, .056, .060)]
CHEST_STRAP = ((0.0, -.012), [(1.315, .160, .156), (1.265, .158, .152)])     # under the bust (front crop z 1.27-1.30)
BELT = ((0.0, .005), [(1.140, .136, .130), (1.085, .140, .134)])
# helmet: front edge just under the eyes (base eye band z 1.60-1.63), the back over the nape hair
HELMET = [
    (1.860, [(0, -.150), (.115, -.140), (.150, .0), (.115, .150), (0, .160)]),
    (1.800, [(0, -.200), (.155, -.185), (.200, .0), (.155, .190), (0, .210)]),
    (1.595, [(0, -.205), (.160, -.190), (.205, .0), (.160, .195), (0, .215)]),
]
HELMET_ZFIX = {(2, 2): 1.610, (2, 3): 1.625, (2, 4): 1.630}
CABLES = [(0, .215, 1.680), (0, .245, 1.500), (0, .205, 1.300)]               # profile: helmet back down to the chest strap
HIP_POUCH = ((-.150, -.055), (1.110, 1.020), (.032, .028))                     # her right hip (front crop x -.17..-.12)
THIGH_POUCH = ((.235, -.010), (0.900, 0.790), (.022, .045))                    # outer side of her left thigh


def box(centre, z, half):
    (cx, cy), (z1, z0), (hx, hy) = centre, z, half
    return lk.prism([(z1, hx, hy), (z0, hx, hy)], 4, centre=(cx, cy))


ASYMMETRIC = {}


def parts():
    out = {}
    P, F, _ = lk.loft_sym(SUIT_TOP)
    out['suit_top'] = lk.part(P, F, 'chest', 'cloth')
    P, F, _ = lk.loft_sym(SUIT_BELLY)
    out['suit_belly'] = lk.part(P, F, 'spine', 'cloth')
    P, F, _ = lk.loft_sym(SUIT_HIPS)
    out['suit_hips'] = lk.part(P, F, 'hips', 'cloth')
    P, F = lk.prism(TURTLENECK)
    out['neck'] = lk.part(P, F, 'neck', 'black')
    for name, ((cx, cy), levels), bone in (('chest_strap', CHEST_STRAP, 'chest'), ('belt', BELT, 'hips')):
        P, F = lk.prism(levels, 8, centre=(cx, cy))
        out[name] = lk.part(P, F, bone, 'leather')
    P, F, _ = lk.loft_sym(HELMET, HELMET_ZFIX)
    out['helmet'] = lk.part(P, F, 'head', 'metal')
    P, F = lk.loft([lk.ring(c, lk.X, lk.FRONT, .045, .030, 6) for c in CABLES])
    out['cables'] = lk.part(P, F, 'chest', 'black')
    for name, spec, bone in (('pouch_hip', HIP_POUCH, 'hips'), ('pouch_thigh', THIGH_POUCH, 'thigh_l')):
        P, F = box(*spec)
        out[name] = lk.part(P, F, bone, 'purple')
        ASYMMETRIC[name] = [tuple(v) for v in np.round(P, 4)]
    limbs = {
        # short cream sleeve over the deltoid, a little fuller than the bare shoulder
        'deltoid_l': ((.215, .015, 1.425), DELT_AXIS, DELT_SIDE,
                      [(0, .046, .050), (.040, .080, .083), (.115, .074, .077), (.175, .052, .056)], 6, 'cloth', 'upper_arm_l'),
        'upper_arm_l': ((.262, .020, 1.330), AXIS, SIDE,
                        [(0, .057, .060), (.090, .060, .062), (.170, .052, .055)], 6, 'black', 'upper_arm_l'),
        'forearm_l': ((.355, .030, 1.185), AXIS, SIDE,
                      [(0, .054, .057), (.080, .062, .062), (.200, .050, .052)], 6, 'black', 'forearm_l'),
        'cuff_l': ((.425, .035, 1.045), AXIS, SIDE, [(0, .064, .066), (.080, .066, .068)], 8, 'leather', 'forearm_l'),
        'glove_l': ((.468, .040, .955), GLOVE_AXIS, GLOVE_SIDE,
                    [(0, .066, .088), (.030, .098, .125), (.130, .098, .122), (.180, .066, .088)], 4, 'grey', 'hand_l'),
    }
    for name, (o, axis, side, secs, n, tone, bone) in limbs.items():
        P, F = lk.loft(lk.along(o, axis, side, secs, n, flat_front=(n == 4)))
        out[name] = lk.part(P, F, bone, tone)
    legs = {
        # wide suit leg down past the knee band (front crop: thigh x .03-.24 at z .84)
        'thigh_l': ([(.122, -.020, .925, .097, .108), (.138, -.020, .760, .094, .102), (.153, -.015, .700, .084, .093)], 8, 'thigh_l', 'cloth'),
        'knee_band_l': ([(.155, -.014, .745, .094, .100), (.157, -.014, .685, .094, .100)], 8, 'shin_l', 'grey'),     # front crop: grey z .68-.74
        # tall black boot (front crop x .07-.25, profile y -.12..+.06 at z .6; -.094..+.077 at .3)
        'boot_shaft_l': ([(.158, -.022, .700, .086, .092), (.168, -.020, .450, .083, .086), (.178, -.008, .125, .080, .086)], 8, 'shin_l', 'black'),
    }
    for name, (secs, n, bone, tone) in legs.items():
        P, F = lk.loft([lk.ring((cx, cy, z), lk.X, lk.FRONT, hx, hy, n) for cx, cy, z, hx, hy in secs])
        out[name] = lk.part(P, F, bone, tone)
    # boot foot: flat sole, sloped top, grey toe cap painted (profile: toe y -.26, heel y +.10)
    rings = []
    for cx, y, z0, z1, hw in [(.20, .100, .0, .150, .088), (.20, -.040, .0, .140, .108),
                              (.20, -.180, .0, .100, .110), (.20, -.262, .0, .060, .092)]:
        zc, hz = (z0 + z1) / 2, (z1 - z0) / 2
        rings.append([(cx - hw, y, z0), (cx + hw, y, z0), (cx + hw, y, zc + hz * .4),
                      (cx + hw * .6, y, z1), (cx - hw * .6, y, z1), (cx - hw, y, zc + hz * .4)])
    P, F = lk.loft(rings)
    out['boot_l'] = lk.part(P, F, 'foot_l', 'black')
    return out
