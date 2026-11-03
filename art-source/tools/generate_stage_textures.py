"""Stage textures for the three arenas (run with system Python + Pillow).

Splits the painted arena atlases (concept-art/arenas/atlases/atlas-<arena>-v1)
into one PNG per material, so each can repeat with plain UVs, and crops the
painted far backgrounds. Output: godot/assets/environments/<stage>/textures/.
When textures-v2 arrives, point ATLAS at it and keep the same material names.
"""
import json
import unicodedata
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
CONCEPT = ROOT / "concept-art"
ATLAS_DIR = CONCEPT / "arenas" / "atlases"
OUT = ROOT / "godot" / "assets" / "environments"

ATLAS = {"zephyr_dojo": "santuario", "molten_forge": "forja", "storm_market": "bazaar"}
# The atlas cells carry a 1-2 px seam to their neighbours; trim it before saving.
TRIM = 3


def split_atlas(stage):
    name = ATLAS[stage]
    meta = json.loads((ATLAS_DIR / f"atlas-{name}-v1.json").read_text(encoding="utf-8"))
    sheet = Image.open(ATLAS_DIR / f"atlas-{name}-v1.png").convert("RGB")
    out = OUT / stage / "textures"
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for key, cell in meta["regions"].items():
        x, y, w, h = cell["region"]
        tile = sheet.crop((x + TRIM, y + TRIM, x + w - TRIM, y + h - TRIM)).resize((512, 512), Image.Resampling.LANCZOS)
        safe = unicodedata.normalize("NFKD", key).encode("ascii", "ignore").decode()
        tile.save(out / f"{safe}.png")
        written.append(safe)
    return written


def clean_cutout(tile):
    """Hard alpha edge plus colour bleed into the transparent area (no halo under mipmaps)."""
    import numpy as np
    rgba = np.asarray(tile.convert("RGBA")).astype(np.float32)
    inside = (rgba[..., 3] >= 110).astype(np.float32)
    rgb = rgba[..., :3] * inside[..., None]
    filled = rgba[..., :3].copy()
    known = inside.copy()
    # Grow the leaf colour outward with ever wider blurs until every pixel has a neighbour colour.
    for radius in (2, 4, 8, 16, 32, 64):
        blur = lambda a: np.asarray(Image.fromarray(a).filter(ImageFilter.GaussianBlur(radius)), dtype=np.float32)
        weight = blur((inside * 255).astype(np.uint8)) / 255.0
        colour = np.stack([blur(np.clip(rgb[..., c], 0, 255).astype(np.uint8)) for c in range(3)], axis=-1)
        avg = colour / np.maximum(weight[..., None], 1e-3)
        take = (known == 0) & (weight > 0.02)
        filled[take] = avg[take]
        known[take] = 1
    filled[inside == 1] = rgba[..., :3][inside == 1]
    out = np.dstack([np.clip(filled, 0, 255), inside * 255]).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def split_beach():
    """Beach menu materials from concept-art/beach-textures/atlas-praia-v1."""
    src = CONCEPT / "beach-textures"
    meta = json.loads((src / "atlas-praia-v1.json").read_text(encoding="utf-8"))
    sheet = Image.open(src / "atlas-praia-v1.png").convert("RGBA")
    out = OUT / "beach" / "textures"
    out.mkdir(parents=True, exist_ok=True)
    for key, cell in meta["tiles"].items():
        x, y, w, h = cell["region"]
        tile = sheet.crop((x + TRIM, y + TRIM, x + w - TRIM, y + h - TRIM)).resize((512, 512), Image.Resampling.LANCZOS)
        if cell.get("cutout"):
            clean_cutout(tile).save(out / f"{key}.png")
        else:
            # Surfaces must be fully opaque (the atlas stores alpha ~254).
            tile.convert("RGB").save(out / f"{key}.png")
    for name in ("ceu-praia-v1.png", "mar-transicao-v1.png", "telhas-azul-marinho-v1.png"):
        Image.open(src / name).convert("RGB").save(out / name)
    sun_glints().save(out / "glints.png")
    return sorted(meta["tiles"])


def sun_glints():
    """Sparkles of sunlight on the water: small bright horizontal flecks on transparency."""
    import random
    rng = random.Random(77)
    img = Image.new("RGBA", (1024, 1024), (255, 250, 230, 0))
    draw = ImageDraw.Draw(img)
    for _ in range(900):
        x, y = rng.uniform(0, 1024), rng.uniform(0, 1024)
        # Denser along the middle band, where the sun path crosses the bay.
        if abs(x - 512) > rng.uniform(80, 512):
            continue
        # The camera sees the water almost edge-on, so flecks are long in depth (v) to survive foreshortening.
        w, h = rng.uniform(5, 24), rng.uniform(22, 70)
        a = int(rng.uniform(150, 255))
        draw.ellipse([x - w, y - h, x + w, y + h], fill=(255, 250, 225, a))
    return img.filter(ImageFilter.GaussianBlur(0.8))


def zephyr_backdrop():
    # Sky, mountains and cliff pagodas from cenarios-v1, right of the arena label.
    sheet = Image.open(CONCEPT / "cenarios-v1.png").convert("RGB")
    band = sheet.crop((285, 46, 1333, 262))
    band = band.resize((band.width * 2, band.height * 2), Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(1.2))
    band.save(OUT / "zephyr_dojo" / "textures" / "backdrop.png")


def bazaar_corridor_view():
    # The deep hall seen through the middle arch of bazaar-fechado-v1.
    sheet = Image.open(CONCEPT / "arenas" / "bazaar-fechado-v1.png").convert("RGB")
    view = sheet.crop((730, 330, 950, 545))
    view.resize((view.width * 3, view.height * 3), Image.Resampling.LANCZOS).save(OUT / "storm_market" / "textures" / "corridor_view.png")


def main():
    for stage in ATLAS:
        print("stage textures:", stage, split_atlas(stage))
    zephyr_backdrop()
    bazaar_corridor_view()
    print("beach textures:", split_beach())


if __name__ == "__main__":
    main()
