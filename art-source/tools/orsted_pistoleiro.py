"""Orsted, gunslinger outfit (fighter id `volt`): the pieces, on the base's joints and scale.

Concept: concept-art/characters/orsted/orsted-pistoleiro-turnaround-psx-v1.png (18 texture panels
in orsted-pistoleiro-texturas-18-paineis-psx-v1.png). The base pieces that the outfit only
repaints come from the base modules unchanged (head, shirt trunk = the coat's top with the vest
painted inside, neck, belt, sleeves, arms, fists = gloves, legs, boots, the right shoulder plate =
the scrap plate), so the rig, animations and hitboxes serve as they are. New pieces:
    - the wide-brim hat (brim, crown, copper band) on the head bone, over the hair;
    - the duster's skirt from the belt to mid-thigh (its hem on the cloth bones: a kick lifts it);
    - the red bandana round the neck with its knot hanging in front;
    - the empty holster on the right thigh; the copper spurs on the boot heels;
    - the revolver (orsted-revolver-5-vistas-psx-v1.png, ~0.36 m: octagonal gunmetal barrel, the
      cylinder in a copper frame, the reddish wooden grip leaning back, hammer, guard, sight) on
      the `cannon` bone, held as a pistol grip like the cannon (orsted_arma.to_world's mapping).
"""
import numpy as np

import legends_kit as lk
import orsted_arma
import orsted_braco
import orsted_cabeca
import orsted_perna
import orsted_tronco

TRONCO = ('chest', 'belly', 'pelvis', 'neck', 'belt')
BRACO = ('sleeve_l', 'sleeve_cuff_l', 'upper_arm_l', 'forearm_l', 'bracer_l', 'hand_l', 'pauldron_r')
PERNA = ('thigh_l', 'shin_l', 'boot_shaft_l', 'boot_l')

# hat: on the head (crown of the hair z ~1.90, the head joint's column y -0.07); the brim rides
# at the brow line over the hair's sides, the crown above it, a copper band at its foot
HAT_C = (0.0, -0.060)
BRIM = [(1.815, .275, .255), (1.795, .285, .265)]
CROWN = [(2.000, .110, .098), (1.960, .140, .128), (1.835, .150, .140)]
BAND = [(1.860, .156, .146), (1.828, .156, .146)]
# the duster's skirt, hung from under the belt to mid-thigh, flaring, OPEN in front: two flaps
# (his left one here, the right one its mirror) from the front opening round the side to the
# back's middle (a slit there, like panel 4); each a thin shell, so nothing hangs between the legs
SKIRT = [
    (1.060, [(.060, -.128), (.150, -.118), (.182, .0), (.150, .118), (.004, .126)]),
    (0.850, [(.075, -.140), (.172, -.130), (.236, .0), (.172, .138), (.004, .148)]),
    (0.620, [(.090, -.150), (.192, -.140), (.262, .0), (.192, .150), (.004, .160)]),
]
FLAP_T = 0.012


def flap(sections, t=FLAP_T):
    """A thin open shell through (z, [outer (x, y) from the front edge round to the back]): each
    ring is the outer line and the same line t further in, closed; caps as strips across t."""
    rings = []
    for z, pts in sections:
        outer = [np.array((x, y, z)) for x, y in pts]
        inner = [p - t * np.array((p[0], p[1], 0.0)) / max(np.hypot(p[0], p[1]), 1e-6) for p in outer]
        rings.append(outer + inner[::-1])
    return lk.loft(rings)
# bandana: a ring round the neck and the knot's triangle in front of the collar
BANDANA = [(1.530, .066, .066), (1.475, .078, .078)]
KNOT = ((0.0, -0.088), [(1.495, .065, .016), (1.385, .008, .008)])
# holster: a box on the outside of the right thigh (thigh x -0.10..-0.16, z 0.87..0.58)
HOLSTER_R = ((-0.205, 0.010), (0.840, 0.640), (0.026, 0.046))
# spur: a short neck behind the heel and its wheel
SPUR_L = ((0.185, 0.128), (0.090, 0.062), (0.010, 0.030))
WHEEL_L = ((0.185, 0.168, 0.076), 0.028)

# revolver, in the gun's frame (f along the barrel from the top of the grip, s across, z up over
# the grip): octagon sections (f0, f1), (half s, half z), centre z
REV_SECTIONS = {
    'rev_cylinder': ((0.000, 0.084), (0.046, 0.040), 0.000),
    'rev_barrel': ((0.084, 0.310), (0.026, 0.026), 0.012),
}
# boxes: centre (f, s, z), half size (f, s, z), lean about s (deg, + leans the bottom back)
REV_BOXES = {
    'rev_frame': ((0.042, 0.0, 0.002), (0.056, 0.036, 0.052), 0),
    'rev_grip': ((-0.030, 0.0, -0.060), (0.026, 0.021, 0.060), 28),
    'rev_hammer': ((-0.022, 0.0, 0.060), (0.016, 0.008, 0.018), -25),
    'rev_guard': ((0.030, 0.0, -0.068), (0.030, 0.006, 0.016), 0),
    'rev_rod': ((0.130, 0.0, -0.022), (0.040, 0.010, 0.008), 0),
    'rev_sight': ((0.292, 0.0, 0.044), (0.012, 0.005, 0.009), 0),
}
REV_GRIP_LOCAL = np.array([-0.030, 0.0, -0.060])


def rev_world(P):
    """Gun frame -> body, the grip's centre in the right fist (orsted_arma's pistol grip)."""
    P = np.asarray(P, float) - REV_GRIP_LOCAL
    a, t = orsted_arma.HAND_AXIS_R, orsted_arma.THUMB_SIDE
    S = np.cross(t, a)
    return orsted_arma.FIST_R + np.outer(P[:, 0], a) + np.outer(P[:, 1], S) + np.outer(P[:, 2], t)


def _box(c, h, lean):
    (cf, cs, cz), (hf, hs, hz) = c, h
    corners = np.array([[sf * hf, ss * hs, sz * hz] for sz in (1, -1) for sf, ss in ((1, 1), (1, -1), (-1, -1), (-1, 1))])
    t = np.radians(lean)
    R = np.array([[np.cos(t), 0, np.sin(t)], [0, 1, 0], [-np.sin(t), 0, np.cos(t)]])
    corners = corners @ R.T + [cf, cs, cz]
    return lk.loft([corners[:4], corners[4:]])


def parts():
    out = {k: v for k, v in orsted_cabeca.parts().items()}
    t, b, p = orsted_tronco.parts(), orsted_braco.parts(), orsted_perna.parts()
    out.update({k: t[k] for k in TRONCO})
    out.update({k: b[k] for k in BRACO})
    out.update({k: p[k] for k in PERNA})
    cx, cy = HAT_C
    for name, levels, tone in (('hat_brim', BRIM, 'hat'), ('hat_crown', CROWN, 'hat'), ('hat_band', BAND, 'copper')):
        P, F = lk.prism(levels, 8, centre=(cx, cy))
        out[name] = lk.part(P, F, 'head', tone)
    P, F = flap(SKIRT)
    out['coat_skirt_l'] = lk.part(P, F, 'hips', 'coat')
    P, F = lk.prism(BANDANA, 8)
    out['bandana'] = lk.part(P, F, 'neck', 'rag')
    (kx, ky), levels = KNOT
    P, F = lk.prism(levels, 4, centre=(kx, ky))
    out['bandana_knot'] = lk.part(P, F, 'chest', 'rag')
    P, F = orsted_tronco.box(*HOLSTER_R)
    out['holster_r'] = lk.part(P, F, 'thigh_r', 'leather')
    P, F = orsted_tronco.box(*SPUR_L)
    out['spur_l'] = lk.part(P, F, 'foot_l', 'copper')
    (wx, wy, wz), r = WHEEL_L
    P, F = lk.loft([lk.ring((wx + dx, wy, wz), np.array([0, 1.0, 0]), np.array([0, 0, 1.0]), r, r, 6, flat_front=False)
                    for dx in (-.006, .006)])
    out['spur_wheel_l'] = lk.part(P, F, 'foot_l', 'copper')
    for name, ((f0, f1), (hs, hz), zc) in REV_SECTIONS.items():
        P, F = orsted_arma.octagon_prism(f0, f1, hs, hz, zc)
        P = rev_world(P)
        out[name] = lk.part(P, lk.orient(P, F), 'cannon', 'gunmetal')
    for name, (c, h, lean) in REV_BOXES.items():
        P, F = _box(c, h, lean)
        P = rev_world(P)
        tone = 'wood' if name == 'rev_grip' else 'copper' if name in ('rev_frame', 'rev_guard', 'rev_sight') else 'gunmetal'
        out[name] = lk.part(P, lk.orient(P, F), 'cannon', tone)
    return out


# one-sided on purpose: the holster, the revolver (right hand) and the scrap plate (right shoulder)
ASYMMETRIC = dict(orsted_cabeca.ASYMMETRIC)
for _n, _p in parts().items():
    if _n.startswith(('rev_', 'holster', 'pauldron')):
        ASYMMETRIC[_n] = [tuple(v) for v in np.round(_p['v'], 4)]
