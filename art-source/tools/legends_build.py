"""Join a Legends character's hand-modelled pieces, check them, write <name>_pecas.json.

    python art-source/tools/legends_build.py x12_modelo

The character module (e.g. x12_modelo) gives NAME, SRC and PIECES (modules with parts();
optional ASYMMETRIC {part: [(x, y, z) of vertices drawn asymmetric on purpose]}). Left parts `_l` get
their mirrored `_r` copy. The build fails (exit 1) when a rule of the method is broken:
    - a part is not closed (an edge not shared by exactly two faces)
    - a vertex has more than legends_kit.MAX_VALENCE faces around it (fan poles)
    - a centred part is not symmetric (> 1 mm) except its declared asymmetric vertices
It prints faces/triangles per part and the total, to compare with the references.
"""
import importlib
import json
import sys

import numpy as np

import legends_kit as lk


def build(module_name, write=True):
    m = importlib.import_module(module_name)
    parts, asym = {}, {}
    for piece in m.PIECES:
        parts.update(piece.parts())
        asym.update(getattr(piece, 'ASYMMETRIC', {}))
    parts = lk.with_mirrors(parts)
    errors, total = [], 0
    print(f'{m.NAME}: {len(parts)} parts')
    for name, p in sorted(parts.items()):
        P, F = np.array(p['v']), p['f']
        tris, odd, val = lk.stats(P, F)
        total += tris
        line = f'  {name:15s} {len(F):3d} faces {tris:4d} tris  max faces/vertex {val}'
        if odd:
            errors.append(f'{name}: {odd} open edges')
        if val > lk.MAX_VALENCE:
            errors.append(f'{name}: a vertex with {val} faces')
        if not name.endswith(('_l', '_r')):
            keep = np.ones(len(P), bool)
            if name in asym:      # leave out the vertices drawn asymmetric on purpose
                drop = {tuple(np.round(v, 4)) for v in asym[name]}
                keep = np.array([tuple(np.round(v, 4)) not in drop for v in P])
            err = lk.symmetry_error(P[keep])
            line += f'  symmetry {err * 1000:.1f} mm'
            if err > 0.001:
                errors.append(f'{name}: not symmetric ({err * 1000:.1f} mm)')
        print(line)
    print(f'  total {total} tris')
    if errors:
        print('FAILED:\n  ' + '\n  '.join(errors))
        return None
    if write:
        out = m.SRC / f'{m.NAME}_pecas.json'
        out.write_text(json.dumps(parts))
        print('wrote', out)
    return parts


if __name__ == '__main__':
    sys.exit(0 if build(sys.argv[1] if len(sys.argv) > 1 else 'x12_modelo') else 1)
