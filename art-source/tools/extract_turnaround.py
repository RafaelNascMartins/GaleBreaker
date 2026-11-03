"""Measure a character turnaround so Blender can rebuild it 1:1 (run with system Python + Pillow/numpy).

Inputs (concept-art/characters/<id>/):
  <id>-lowpoly-anime-v3-{frente,perfil,costas}.png   colour views (front, left side, back)
  <id>-rig-cores-v1-{frente,perfil,costas}.png       same views painted per body segment

Outputs:
  art-source/characters/<id>/turnaround.json   per-segment ring slices (metres), joints, projection info
  godot/assets/characters/<id>/textures/{albedo,mask,normal}.png   atlas of the three views

World axes match the Blender builder: X = character's left, -Y = front, Z = up, feet at Z = 0.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
HEIGHT = 1.90
STEP_PX = 18  # vertical spacing of ring slices (about 2.4 cm)

# Segment -> (bone, sample point in the front rig image used to read its legend colour).
# Image left is the character's right in the front view.
SEGMENTS = {
    "head": ("head", (510, 150)), "neck": ("neck", (510, 278)), "chest": ("chest", (510, 420)),
    "abdomen": ("spine", (510, 520)), "pelvis": ("hips", (510, 655)),
    "r_arm": ("upper_arm_r", (352, 420)), "r_forearm": ("forearm_r", (262, 600)), "r_hand": ("hand_r", (168, 780)),
    "l_arm": ("upper_arm_l", (672, 420)), "l_forearm": ("forearm_l", (762, 600)), "l_hand": ("hand_l", (856, 780)),
    "r_thigh": ("thigh_r", (445, 860)), "r_leg": ("shin_r", (405, 1150)), "r_foot": ("foot_r", (365, 1405)),
    "l_thigh": ("thigh_l", (580, 860)), "l_leg": ("shin_l", (615, 1150)), "l_foot": ("foot_l", (650, 1405)),
}
TORSO = ["chest", "abdomen", "pelvis"]


def load(path):
    return np.asarray(Image.open(path).convert("RGB")).astype(np.int32)


def silhouette(img):
    bg = img[5, 5]
    return np.abs(img - bg).sum(axis=2) > 45


def label_map(rig, palette):
    """Nearest legend colour per pixel; outlines, bones and dashes inherit the nearest label."""
    names = list(palette)
    colours = np.array([palette[n] for n in names])
    best = np.full(rig.shape[:2], -1)
    best_d = np.full(rig.shape[:2], 1 << 30)
    for i, colour in enumerate(colours):
        d = ((rig - colour) ** 2).sum(axis=2)
        closer = d < best_d
        best[closer] = i
        best_d[closer] = d[closer]
    labels = np.where(best_d < 55 ** 2, best, -1)
    body = silhouette(rig)
    for _ in range(14):
        missing = (labels < 0) & body
        if not missing.any():
            break
        grown = labels.copy()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            shifted = np.roll(np.roll(labels, dy, axis=0), dx, axis=1)
            take = missing & (grown < 0) & (shifted >= 0)
            grown[take] = shifted[take]
        labels = grown
    return labels, names


def legend_colour(rig, point):
    """Median colour around a point, ignoring the white bone lines, outlines and grey dashes."""
    x, y = point
    patch = rig[y - 14:y + 15, x - 14:x + 15].reshape(-1, 3)
    mx, mn = patch.max(axis=1), patch.min(axis=1)
    keep = (mn < 200) & (mx > 60) & ((mx - mn) > 40)
    return tuple(int(c) for c in np.median(patch[keep], axis=0))


def span(row_mask):
    xs = np.where(row_mask)[0]
    return (int(xs.min()), int(xs.max())) if xs.size else None


def run_through(row_mask, x):
    """Contiguous run of True pixels that contains column x."""
    if x < 0 or x >= row_mask.size or not row_mask[x]:
        return None
    left = x
    while left > 0 and row_mask[left - 1]:
        left -= 1
    right = x
    while right < row_mask.size - 1 and row_mask[right + 1]:
        right += 1
    return left, right


def model_texture(fid):
    """Base colour of the generated model (art-source/characters/<id>/source/<id>_tripo.glb) plus a
    palette mask: jade cloth -> R (primary), cream trim -> G (secondary)."""
    import io
    import struct
    glb = (ROOT / "art-source" / "characters" / fid / "source" / f"{fid}_tripo.glb").read_bytes()
    json_len = struct.unpack("<I", glb[12:16])[0]
    meta = json.loads(glb[20:20 + json_len])
    binary = glb[20 + json_len + 8:]
    view = meta["bufferViews"][meta["images"][0]["bufferView"]]
    start = view.get("byteOffset", 0)
    image = Image.open(io.BytesIO(binary[start:start + view["byteLength"]])).convert("RGB")
    out = ROOT / "godot" / "assets" / "characters" / fid / "textures"
    out.mkdir(parents=True, exist_ok=True)
    image.save(out / "albedo.png")
    rgb = np.asarray(image).astype(np.float32) / 255.0
    mx, mn = rgb.max(axis=2), rgb.min(axis=2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    g_dom = (rgb[..., 1] >= rgb[..., 0]) & (rgb[..., 1] >= rgb[..., 2])
    jade = g_dom & (sat > 0.28) & (mx < 0.7)
    cream = g_dom & (sat <= 0.28) & (mx >= 0.62)
    mask = np.zeros(rgb.shape, np.uint8)
    mask[..., 0] = np.where(jade, 255, 0)
    mask[..., 1] = np.where(cream, 255, 0)
    Image.fromarray(mask).save(out / "mask.png")
    Image.new("RGB", (512, 512), (128, 128, 255)).save(out / "normal.png")
    print("texture:", image.size, "jade %.0f%%" % (jade.mean() * 100), "cream %.0f%%" % (cream.mean() * 100))


def main(fid):
    src = ROOT / "concept-art" / "characters" / fid
    views = {v: load(src / f"{fid}-lowpoly-anime-v3-{v}.png") for v in ("frente", "perfil", "costas")}
    rigs = {v: load(src / f"{fid}-rig-cores-v1-{v}.png") for v in ("frente", "perfil", "costas")}
    palette = {name: legend_colour(rigs["frente"], p) for name, (_, p) in SEGMENTS.items()}
    labels, names = {}, None
    for v in rigs:
        labels[v], names = label_map(rigs[v], palette)
    idx = {n: i for i, n in enumerate(names)}
    masks = {v: silhouette(views[v]) for v in views}

    # Per-view projection: metres per pixel, pixel of X/Y = 0 and of the sole (Z = 0).
    proj = {}
    for v in views:
        ys, xs = np.where(masks[v])
        top, sole = int(ys.min()), int(ys.max())
        pelvis = np.where(labels[v] == idx["pelvis"])
        proj[v] = {"m_per_px": HEIGHT / (sole - top), "centre_px": float(np.median(pelvis[1])), "sole_px": sole}
    fr, sd = proj["frente"], proj["perfil"]

    def z_of(row, view="frente"):
        return (proj[view]["sole_px"] - row) * proj[view]["m_per_px"]

    def row_of(z, view):
        return int(round(proj[view]["sole_px"] - z / proj[view]["m_per_px"]))

    def fx(px):  # front image column -> world X (image left = character right = -X)
        return (px - fr["centre_px"]) * fr["m_per_px"]

    def sy(px):  # side image column -> world Y (face on the image left = -Y)
        return (px - sd["centre_px"]) * sd["m_per_px"]

    lf, ls = labels["frente"], labels["perfil"]
    centre_col = int(round(fr["centre_px"]))
    side_centre = int(round(sd["centre_px"]))

    # Skirt: below the pelvis, as long as the colour view stays filled at the centre line.
    pelvis_rows = np.where((lf == idx["pelvis"]).any(axis=1))[0]
    skirt_top = int(pelvis_rows.max())
    skirt_bottom = skirt_top
    while masks["frente"][skirt_bottom + 1, centre_col]:
        skirt_bottom += 1
    arm_side = np.isin(ls, [idx[n] for n in ("l_arm", "l_forearm", "l_hand")])

    def side_span_for(name, row_f, base):
        row_s = row_of(z_of(row_f), "perfil")
        if not 0 <= row_s < ls.shape[0]:
            return None
        if name.startswith("r_"):
            name = "l_" + name[2:]
        if name in TORSO or name in ("head", "neck", "skirt"):
            run = run_through(masks["perfil"][row_s] & ~arm_side[row_s], side_centre) or run_through(masks["perfil"][row_s], side_centre)
            return run
        return span(ls[row_s] == idx[name])

    segments = {}
    rows_f = {n: np.where((lf == idx[n]).any(axis=1))[0] for n in SEGMENTS}
    for name, (bone, _) in list(SEGMENTS.items()) + [("skirt", ("hips", None))]:
        if name == "skirt":
            r0, r1 = skirt_top, skirt_bottom
        else:
            r0, r1 = int(rows_f[name].min()), int(rows_f[name].max())
        rows = list(range(r0, r1 + 1, STEP_PX))
        if rows[-1] != r1:
            rows.append(r1)
        slices = []
        for r in rows:
            if name == "head" or name in TORSO or name == "skirt":
                f = run_through(masks["frente"][r], centre_col)
            elif name.endswith(("leg", "foot")) and r > skirt_bottom:
                # Below the skirt the colour view shows the trousers/shins/feet.
                own = span(lf[r] == idx[name])
                f = run_through(masks["frente"][r], (own[0] + own[1]) // 2) if own else None
            else:
                f = span(lf[r] == idx[name])
            s = side_span_for(name, r, name)
            if f is None or s is None:
                continue
            slices.append({"z": z_of(r), "x0": fx(f[0]), "x1": fx(f[1] + 1), "y0": sy(s[0]), "y1": sy(s[1] + 1)})
        if len(slices) >= 2:
            segments[name] = {"bone": bone, "slices": slices}

    # Joints: centre of the boundary between two segments (front gives X/Z, side gives Y).
    def boundary(a, b):
        ma = lf == idx[a]
        mb = lf == idx[b]
        near = np.zeros_like(ma)
        for dy, dx in ((3, 0), (-3, 0), (0, 3), (0, -3)):
            near |= np.roll(np.roll(mb, dy, axis=0), dx, axis=1)
        ys, xs = np.where(ma & near)
        if not ys.size:
            ys, xs = np.where(ma)
        row = float(np.median(ys))
        a_side = "l_" + a[2:] if a.startswith("r_") else a
        rs = row_of(z_of(row), "perfil")
        s = span(ls[rs] == idx[a_side]) if 0 <= rs < ls.shape[0] else None
        y = sy((s[0] + s[1]) / 2) if s else 0.0
        return [fx(float(np.median(xs))), y, z_of(row)]

    def extreme(name, which):
        ys, xs = np.where(lf == idx[name])
        row = ys.min() if which == "top" else ys.max()
        cols = xs[ys == row]
        return [fx(float(np.median(cols))), 0.0, z_of(row)]

    joints = {
        "head_top": extreme("head", "top"), "neck_head": boundary("neck", "head"), "chest_neck": boundary("chest", "neck"),
        "abdomen_chest": boundary("abdomen", "chest"), "pelvis_abdomen": boundary("pelvis", "abdomen"),
    }
    for side in "rl":
        joints[f"shoulder_{side}"] = boundary(f"{side}_arm", "chest")
        joints[f"elbow_{side}"] = boundary(f"{side}_arm", f"{side}_forearm")
        joints[f"wrist_{side}"] = boundary(f"{side}_forearm", f"{side}_hand")
        joints[f"hand_tip_{side}"] = extreme(f"{side}_hand", "bottom")
        joints[f"hip_{side}"] = boundary(f"{side}_thigh", "pelvis")
        joints[f"knee_{side}"] = boundary(f"{side}_thigh", f"{side}_leg")
        joints[f"ankle_{side}"] = boundary(f"{side}_leg", f"{side}_foot")
        foot = segments[f"{side}_foot"]["slices"]
        toe_y = min(s["y0"] for s in foot)
        joints[f"toe_{side}"] = [joints[f"ankle_{side}"][0], toe_y, 0.03]

    model_texture(fid)

    width = views["frente"].shape[1]
    data = {
        "fighter": fid, "height": HEIGHT, "segments": segments, "joints": joints, "skirt_rows": [skirt_top, skirt_bottom],
        "projection": {v: {**proj[v], "offset_px": i * width} for i, v in enumerate(("frente", "costas", "perfil"))},
    }
    dest = ROOT / "art-source" / "characters" / fid / "turnaround.json"
    dest.write_text(json.dumps(data, indent=1), encoding="utf-8")
    print(fid, "segments:", sorted(segments), "skirt rows:", skirt_top, skirt_bottom)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "kaze")
