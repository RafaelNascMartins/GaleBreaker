"""X12, boxer outfit: the new pieces, modelled by hand on the Legends references and measured on
the outfit's concept (x12boxe_frente / perfil / costas, cropped to the base crops' scale: the
joints fall on the base's, so the base rig and animations serve unchanged).

Bare skin arms and legs (thin Mega Man / Tifa prisms, a round deltoid), a white crop top, the
bare belly, red shorts (a pelvis piece and a flared leg sleeve per thigh, so a kick doesn't tear
them), white wrist wraps, big red gloves, tall red boots (a shaft on the shin, a block on the
foot) and a dark choker. Head and neck are the base's. Numbers: x from the front crop, y from the
profile crop (front is -y), per height (measure_box colour masks), metres.
"""
import legends_kit as lk
import x12_tronco

AXIS, SIDE = lk.tilted(25)               # forearm / upper arm lean (A-pose), as the base arm
DELT_AXIS, DELT_SIDE = lk.tilted(20)
GLOVE_AXIS, GLOVE_SIDE = lk.tilted(12)

# crop top: z, left half (x, y) front centre, front corner, side, back corner, back centre
TOP = [
    (1.440, [(0, -.058), (.050, -.052), (.068, .0), (.052, .058), (0, .066)]),     # trapezius at the neck base
    (1.405, [(0, -.085), (.120, -.072), (.170, .0), (.120, .090), (0, .105)]),     # shoulder line out to the deltoid (front crop: +-.18 at z 1.40)
    (1.290, [(0, -.152), (.110, -.135), (.142, -.010), (.110, .105), (0, .118)]),   # bust, widest
    (1.190, [(0, -.112), (.080, -.098), (.098, .0), (.080, .098), (0, .110)]),      # under the bust
]
BELLY = [
    (1.205, [(0, -.100), (.072, -.090), (.090, .0), (.072, .098), (0, .112)]),
    (1.080, [(0, -.098), (.075, -.088), (.094, .0), (.075, .100), (0, .114)]),
]
SHORTS = [                               # pelvis: white waistband on top, red below
    (1.110, [(0, -.112), (.090, -.100), (.122, .0), (.090, .110), (0, .122)]),
    (1.050, [(0, -.118), (.100, -.106), (.130, .0), (.100, .116), (0, .128)]),
    (0.920, [(0, -.138), (.120, -.130), (.175, .0), (.120, .150), (0, .160)]),
]
SHORTS_WAISTBAND = (0,)                  # band index painted white
NECK_RING = [(1.425, .052, .056), (1.470, .052, .056)]     # choker (dark metal)


def parts():
    out = {}
    P, F, _ = lk.loft_sym(TOP)
    out['top'] = lk.part(P, F, 'chest', 'cloth')
    P, F, _ = lk.loft_sym(BELLY)
    out['belly'] = lk.part(P, F, 'spine', 'skin')
    P, F, band = lk.loft_sym(SHORTS)
    out['shorts'] = lk.part(P, F, 'hips', ftone=['cloth' if b in SHORTS_WAISTBAND or b == -1 else 'stone' for b in band])
    P, F = lk.prism(x12_tronco.NECK)
    out['neck'] = lk.part(P, F, 'neck', 'skin')
    P, F = lk.prism(NECK_RING, 8)
    out['choker'] = lk.part(P, F, 'neck', 'metal')
    limbs = {
        # deltoid: a round skin ball over the shoulder joint (Mega Man's shoulder sphere, smaller)
        'deltoid_l': ((.215, .015, 1.425), DELT_AXIS, DELT_SIDE,
                      [(0, .040, .045), (.040, .072, .075), (.110, .066, .070), (.170, .045, .050)], 6, 'skin', 'upper_arm_l'),
        'upper_arm_l': ((.262, .020, 1.330), AXIS, SIDE,
                        [(0, .055, .058), (.090, .058, .060), (.170, .050, .053)], 6, 'skin', 'upper_arm_l'),
        'forearm_l': ((.355, .030, 1.185), AXIS, SIDE,
                      [(0, .052, .055), (.080, .062, .062), (.200, .048, .050)], 6, 'skin', 'forearm_l'),
        'wrap_l': ((.430, .035, 1.035), AXIS, SIDE, [(0, .058, .060), (.075, .062, .064)], 8, 'cloth', 'forearm_l'),
        # glove: bigger than the base fist, a chamfered block with a rounded knuckle end
        'glove_l': ((.468, .040, .955), GLOVE_AXIS, GLOVE_SIDE,
                    [(0, .070, .095), (.035, .105, .135), (.140, .105, .132), (.190, .070, .095)], 4, 'stone', 'hand_l'),
        # legs: bare skin, straight prisms leaning out like the base thighs
        'shorts_leg_l': None,
        'thigh_l': None,
        'shin_l': None,
        'boot_shaft_l': None,
    }
    for name, spec in limbs.items():
        if spec is None:
            continue
        o, axis, side, secs, n, tone, bone = spec
        P, F = lk.loft(lk.along(o, axis, side, secs, n, flat_front=(n == 4)))
        out[name] = lk.part(P, F, bone, tone)
    legs = {
        # flared red sleeve of the shorts on each thigh
        'shorts_leg_l': ([(.105, .0, .960, .110, .150), (.150, .005, .770, .118, .160)], 8, 'thigh_l', 'stone'),
        'thigh_l': ([(.120, -.020, .820, .075, .090), (.140, -.020, .700, .072, .088), (.150, -.015, .600, .058, .074)], 6, 'thigh_l', 'skin'),
        'shin_l': ([(.150, -.010, .640, .060, .074), (.165, .012, .500, .085, .088), (.185, .005, .370, .058, .066)], 6, 'shin_l', 'skin'),
        'boot_shaft_l': ([(.185, .000, .370, .058, .068), (.200, -.005, .140, .078, .088)], 8, 'shin_l', 'stone'),
    }
    for name, (secs, n, bone, tone) in legs.items():
        P, F = lk.loft([lk.ring((cx, cy, z), lk.X, lk.FRONT, hx, hy, n) for cx, cy, z, hx, hy in secs])
        out[name] = lk.part(P, F, bone, tone)
    # boot foot: sections along the foot, flat sole, sloped top (concept: sole x .12-.33, toe y -.236)
    rings = []
    for cx, y, z0, z1, hw in [(.225, .105, .0, .170, .090), (.225, -.040, .0, .160, .105),
                              (.225, -.170, .0, .110, .100), (.225, -.236, .0, .065, .085)]:
        zc, hz = (z0 + z1) / 2, (z1 - z0) / 2
        rings.append([(cx - hw, y, z0), (cx + hw, y, z0), (cx + hw, y, zc + hz * .4),
                      (cx + hw * .6, y, z1), (cx - hw * .6, y, z1), (cx - hw, y, zc + hz * .4)])
    P, F = lk.loft(rings)
    out['boot_l'] = lk.part(P, F, 'foot_l', 'stone')
    return out
