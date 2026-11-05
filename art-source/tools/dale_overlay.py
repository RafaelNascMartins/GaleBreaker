"""Overlay the Dale model's edges (dumped by Blender to dale_edges.json) on the three crops,
for checking the model against the turnaround. python dale_overlay.py"""
import json
from pathlib import Path

import cv2
import numpy as np

SRC = Path(__file__).resolve().parents[2] / 'art-source/characters/ignis/legends'
MPP = 2.05 / 933
H = 1002


def main():
    edges = json.loads((SRC / 'dale_edges.json').read_text())
    for view in ('frente', 'perfil', 'costas'):
        img = cv2.imread(str(SRC / f'dale_{view}.png'))
        img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST)
        for a, b in edges:
            pts = []
            for p in (a, b):
                h = {'frente': p[0], 'costas': -p[0], 'perfil': p[1]}[view]
                pts.append((int((h / MPP + 330) * 2), int((H - p[2] / MPP) * 2)))
            cv2.line(img, pts[0], pts[1], (0, 255, 255), 1, cv2.LINE_AA)
        cv2.imwrite(str(SRC / f'dale_{view}_modelo.png'), img)


if __name__ == '__main__':
    main()
