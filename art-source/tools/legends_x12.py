"""X12 (ex-Tophia, fighter id `tophia`) as Mega Man Legends style rigid parts, base outfit
(orange stone armour, lab cuffs and collar).

References: concept-art/characters/x12/x12-turnaround-psx-v2.png and the 3/4 views in
art-source/characters/tophia/legends/x12_3_4_p1.png (p2 disagrees with the others; visual only).
Height 1.80 m to the top of the hair (MPP = 1.8 / 840 px).
Pipeline:
    concept_facets.py --detail 3 --dark 40    detailed facets of the three crops
    concept_da3.py + concept_fuse.py          visual hull of 5 views (x12_casco.npz / .obj)
    x12_measure.py                            octagon rings per part (x12_aneis.json)
    legends_x12.build()                       the parts in Blender, collection X12_Legends
"""
import json
from pathlib import Path

import bpy
from mathutils import Vector

import legends_model as lm

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'art-source/characters/tophia/legends'
COLLECTION = 'X12_Legends'

STONE = ('x_stone', (0.80, 0.36, 0.16))
METAL = ('x_metal', (0.22, 0.21, 0.23))
SKIN = ('x_skin', (0.93, 0.68, 0.52))
HAIR = ('x_hair', (0.10, 0.09, 0.12))
COLOUR = {'collar': STONE, 'ankle_cuff': METAL, 'wrist_cuff': METAL, 'head': SKIN, 'upper_arm': METAL}


def colour(name):
    return COLOUR.get(name.rsplit('_', 1)[0] if name.endswith(('_l', '_r')) else name, STONE)


def rings_part(rings):
    """Closed loft through world-space rings of 8 vertices, capped at both ends."""
    def build(bm):
        loops = [[bm.verts.new(Vector(p)) for p in r] for r in rings]
        n = len(loops[0])
        for r0, r1 in zip(loops, loops[1:]):
            for i in range(n):
                j = (i + 1) % n
                bm.faces.new((r0[i], r0[j], r1[j], r1[i]))
        bm.faces.new(list(reversed(loops[0])))
        bm.faces.new(loops[-1])
    return build


def build(collection_name=COLLECTION):
    col = bpy.data.collections.get(collection_name)
    if not col:
        col = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(col)
    data = json.loads((SRC / 'x12_aneis.json').read_text())
    total, report = 0, []
    for name, part in data.items():
        sides = [(name, part['rings'])]
        if part['mirror']:
            # the right copy: x mirrored, ring order reversed so faces keep pointing out
            mirrored = [[(-x, y, z) for x, y, z in reversed(r)] for r in part['rings']]
            sides.append((name[:-2] + '_r', mirrored))
        for n, rings in sides:
            tris = lm.part('XL_' + n, rings_part(rings), colour(n), col)
            ob = bpy.data.objects['XL_' + n]
            ob['bone'] = part['bone'] if not n.endswith('_r') else part['bone'][:-2] + '_r'
            total += tris
            report.append(f'{n}:{tris}')
    # Upper arm: hidden under the pauldron in every view, so it is not in the hull; a dark
    # joint (like the elbow band in the drawing) from inside the pauldron to the forearm.
    for side, k in (('l', 1), ('r', -1)):
        n = 'upper_arm_' + side
        tris = lm.part('XL_' + n, lambda bm, k=k: lm.loft(bm, (k * .20, .0, 1.35), (k * .335, 0, 1.18),
                                                        [(0, .065, .07), (1, .06, .065)], lm.OCT), colour(n), col)
        bpy.data.objects['XL_' + n]['bone'] = n
        total += tris
        report.append(f'{n}:{tris}')
    print('TRIS', total, ' '.join(report))
    return total


LIFTED = 'X12_Facetas'
SHARP_DEG = 40        # smooth (Gouraud) shading, hard edges where faces turn more than this


def shade(me, hard=True):
    """Smooth shading like the references; on the stone and metal armour, hard edges where the
    form turns sharply (crisp facets). Skin and hair stay soft."""
    import math
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    if hard:
        me.set_sharp_from_angle(angle=math.radians(SHARP_DEG))


LIFTED_PS1 = 'X12_Facetas_PS1'


def mesh_part(name, part, col):
    """A triangle mesh with a tone per face (hair / skin), flat shaded, as is."""
    me = bpy.data.meshes.get(name)
    if me:
        bpy.data.meshes.remove(me)
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(p) for p in part['v']], [], [tuple(f) for f in part['f']])
    tones = {'hair': HAIR, 'skin': SKIN, 'metal': METAL, 'stone': STONE}
    used = sorted(set(part['ftone']))
    for t in used:
        c = tones[t]
        mat = bpy.data.materials.get('flat_' + c[0]) or bpy.data.materials.new('flat_' + c[0])
        mat.diffuse_color = (*c[1], 1)
        me.materials.append(mat)
    me.polygons.foreach_set('material_index', [used.index(t) for t in part['ftone']])
    shade(me, hard=not ({'skin', 'hair'} & set(part['ftone'])))
    me.update()
    ob = bpy.data.objects.get(name) or bpy.data.objects.new(name, me)
    ob.data = me
    if ob.name not in col.objects:
        col.objects.link(ob)
    ob['bone'] = part['bone']
    return len(part['f'])


def build_lifted(collection_name=LIFTED, source='x12_pecas.json', prefix='XF_'):
    """Carved stones (x12_carve.py): x12_pecas.json keeps every drawn plane (faithful),
    x12_pecas_ps1.json is the same stones reduced to the PS1 budget (build_ps1)."""
    col = bpy.data.collections.get(collection_name)
    if not col:
        col = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(col)
    data = json.loads((SRC / source).read_text())
    total, report, bad = 0, [], 0

    def builder(part):
        def build(bm):
            nonlocal bad
            vs = [bm.verts.new(Vector(p)) for p in part['v']]
            for f in part['f']:
                try:
                    bm.faces.new([vs[i] for i in f])
                except ValueError:
                    bad += 1
        return build
    for name, part in data.items():
        if 'ftone' in part:          # one piece, colour per face (the head)
            total += mesh_part(prefix + name, part, col)
            report.append(f"{name}:{len(part['f'])}")
            continue
        tone = {'hair': HAIR, 'skin': SKIN, 'metal': METAL}.get(part.get('tone'), STONE)
        tris = lm.part(prefix + name, builder(part), tone, col, triangulate=False)
        ob = bpy.data.objects[prefix + name]
        ob['bone'] = part['bone']
        shade(ob.data, hard=part.get('tone') not in ('skin', 'hair'))
        total += tris
        report.append(f'{name}:{tris}')
    print('TRIS', total, 'faces rejected', bad, ' '.join(report))
    return total


def build_ps1():
    return build_lifted(LIFTED_PS1, 'x12_pecas_ps1.json', 'XP_')
