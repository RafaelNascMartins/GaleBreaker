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


def clean_cutout(tile, threshold=110):
    """Hard alpha edge plus colour bleed into the transparent area (no halo under mipmaps)."""
    import numpy as np
    rgba = np.asarray(tile.convert("RGBA")).astype(np.float32)
    inside = (rgba[..., 3] >= threshold).astype(np.float32)
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


FOREST_UI_PIECES = {"slider", "toggle-ligado", "toggle-desligado", "botao-neutro", "botao-selecionado", "botao-hover",
                    "painel-pergaminho", "selo-confirmar", "cantoneira-latao"}


def split_forest():
    """Forest passage and quest board (concept-art/floresta-atlas): one PNG per atlas cell.

    Materials are opaque; vegetation and board props are cut out with a hard edge
    (their generated alpha has a wide yellow-green fringe, hence the higher threshold).
    Board UI widgets also go to godot/assets/ui/board for the options screen.
    """
    src = CONCEPT / "floresta-atlas"
    meta = json.loads((src / "manifest.json").read_text(encoding="utf-8"))
    out = OUT / "beach" / "textures" / "forest"
    ui_out = ROOT / "godot" / "assets" / "ui" / "board"
    out.mkdir(parents=True, exist_ok=True)
    ui_out.mkdir(parents=True, exist_ok=True)
    written = []
    for atlas in meta["atlases"]:
        sheet = Image.open(src / atlas["file"]).convert("RGBA")
        opaque = atlas.get("mode") == "RGB"
        for cell in atlas["cells"]:
            x, y, w, h = cell["rect_px"]
            tile = sheet.crop((x + TRIM, y + TRIM, x + w - TRIM, y + h - TRIM))
            name = cell["id"]
            if opaque:
                tile.convert("RGB").resize((512, 512), Image.Resampling.LANCZOS).save(out / f"{name}.png")
            else:
                clean = clean_cutout(tile, 140)
                bbox = clean.getchannel("A").getbbox()
                if bbox:
                    clean = clean.crop(bbox)
                clean.save(out / f"{name}.png")
                if name in FOREST_UI_PIECES:
                    clean.save(ui_out / f"{name}.png")
            written.append(name)
    light_shaft().save(out / "raio.png")
    return written


def split_garage():
    """Training garage (concept-art/ui/atlas-treino-garagem-v1): materials as opaque PNGs for the
    beach scene, the paint inscriptions (already alpha) for the gate menu in godot/assets/ui/garage."""
    src = CONCEPT / "ui" / "atlas-treino-garagem-v1"
    meta = json.loads((src / "manifest.json").read_text(encoding="utf-8"))
    out = OUT / "beach" / "textures" / "garage"
    ui_out = ROOT / "godot" / "assets" / "ui" / "garage"
    out.mkdir(parents=True, exist_ok=True)
    ui_out.mkdir(parents=True, exist_ok=True)
    written = []
    for atlas in meta["atlases"]:
        if atlas["file"].startswith("extra-v1"):
            continue  # split below from extra-v1/textures
        sheet = Image.open(src / atlas["file"]).convert("RGBA")
        opaque = "materiais" in atlas["file"]
        for cell in atlas["cells"]:
            name = cell["id"]
            if opaque:
                x, y, w, h = cell["rect_px"]
                tile = sheet.crop((x + TRIM, y + TRIM, x + w - TRIM, y + h - TRIM))
                tile.convert("RGB").resize((512, 512), Image.Resampling.LANCZOS).save(out / f"{name}.png")
            else:
                x, y, w, h = cell["opaque_content_rect_px"]
                pad = 6
                ink = sheet.crop((x - pad, y - pad, x + w + pad, y + h + pad))
                ink.save(ui_out / f"{name}.png")
            written.append(name)
    # Extra details (extra-v1): already split into textures/ (surfaces RGB, cut-outs RGBA).
    extra = src / "extra-v1" / "textures"
    (out / "extra").mkdir(exist_ok=True)
    for png in extra.glob("*.png"):
        name = png.stem.split("_", 1)[1]
        Image.open(png).save(out / "extra" / f"{name}.png")
        written.append("extra/" + name)
    # The roof timbers read too red under the warm light: a paler, less saturated beam wood.
    from PIL import ImageEnhance as _E
    beam = Image.open(out / "madeira-viga.png").convert("RGB")
    beam = _E.Brightness(_E.Color(beam).enhance(0.5)).enhance(1.12)
    beam.save(out / "madeira-viga.png")
    # The concept floor is a warm light grey: lift the dark oily concrete toward it.
    from PIL import ImageEnhance
    floor = Image.open(out / "extra" / "concreto-oleo-pegadas.png").convert("RGB")
    floor = ImageEnhance.Brightness(floor).enhance(1.55)
    warm = Image.new("RGB", floor.size, (255, 226, 190))
    Image.blend(floor, Image.composite(floor, warm, Image.new("L", floor.size, 160)), 1.0).save(out / "extra" / "concreto-oleo-pegadas.png")
    # The glass of the window cut-out (foliage outside), for the modelled 3D windows.
    window = Image.open(out / "extra" / "janela-interior.png").convert("RGB")
    window.crop((64, 102, 246, 228)).save(out / "extra" / "janela-vidro.png")
    return written


PATIO_SEAMLESS = {"calcamento-pedras", "reboco-branco", "reboco-envelhecido", "alvenaria-calcario", "pedra-degraus"}


def seamless(tile):
    """Make a texture repeat without a visible seam: blend it with a copy shifted by half a tile,
    weighted so the original wins in the middle and the shifted copy (whose own seam sits in the
    middle, hidden) wins at the borders, where it continues into the next tile."""
    import numpy as np
    a = np.asarray(tile).astype(np.float32)
    h, w = a.shape[:2]
    shifted = np.roll(np.roll(a, h // 2, 0), w // 2, 1)
    yy = np.abs(np.linspace(-1, 1, h))[:, None]
    xx = np.abs(np.linspace(-1, 1, w))[None, :]
    weight = np.clip(1.0 - np.maximum(xx, yy), 0, 1) ** 0.6
    weight = np.clip(weight * 1.6, 0, 1)[..., None]
    return Image.fromarray((a * weight + shifted * (1 - weight)).astype(np.uint8))


def split_patio():
    """Arcade village patio (concept-art/ui/atlas-patio-casas-v1): surfaces as opaque PNGs, the
    cut-outs cleaned (their alpha carries stray specks: hard edge, keep only large pieces)."""
    import numpy as np
    import cv2
    src = CONCEPT / "ui" / "atlas-patio-casas-v1"
    meta = json.loads((src / "manifest.json").read_text(encoding="utf-8"))
    out = OUT / "beach" / "textures" / "patio"
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for atlas in meta["atlases"]:
        sheet = Image.open(src / atlas["file"]).convert("RGBA")
        cutouts = "recortes" in atlas["file"]
        for cell in atlas["cells"]:
            name = cell["id"]
            if not cutouts:
                x, y, w, h = cell["rect_px"]
                tile = sheet.crop((x + TRIM, y + TRIM, x + w - TRIM, y + h - TRIM))
                tile = tile.convert("RGB").resize((512, 512), Image.Resampling.LANCZOS)
                if name in PATIO_SEAMLESS:
                    tile = seamless(tile)
                tile.save(out / f"{name}.png")
            else:
                x, y, w, h = cell["rect_px"]
                tile = clean_cutout(sheet.crop((x, y, x + w, y + h)), 170)
                rgba = np.array(tile)
                solid = (rgba[..., 3] > 0).astype(np.uint8)
                count, labels, stats, _ = cv2.connectedComponentsWithStats(solid, connectivity=8)
                if count > 1:
                    biggest = stats[1:, cv2.CC_STAT_AREA].max()
                    keep = np.zeros_like(solid, bool)
                    for i in range(1, count):
                        if stats[i, cv2.CC_STAT_AREA] >= biggest * 0.06:
                            keep |= labels == i
                    rgba[..., 3] = np.where(keep, rgba[..., 3], 0)
                clean = Image.fromarray(rgba, "RGBA")
                bbox = clean.getchannel("A").getbbox()
                if bbox:
                    clean = clean.crop(bbox)
                clean.save(out / f"{name}.png")
            written.append(name)
    # The fighter's wanted-style poster, painted in the concept (until each fighter has its own
    # poster art, the ones not drawn yet fall back to the portrait in Godot).
    poster = Image.open(src / "concept-patio-babuin-v6.png").convert("RGB").crop((1100, 166, 1240, 343))
    posters = ROOT / "godot" / "assets" / "ui" / "posters"
    posters.mkdir(parents=True, exist_ok=True)
    poster.resize((poster.width * 3, poster.height * 3), Image.Resampling.LANCZOS).save(posters / "kaze.png")
    return written


def light_shaft():
    """Soft vertical sunbeam for the clearing (additive)."""
    import numpy as np
    w, h = 128, 512
    x = np.linspace(-1, 1, w)[None, :]
    y = np.linspace(0, 1, h)[:, None]
    alpha = np.exp(-(x / 0.45) ** 2) * (0.75 - 0.6 * y) * 0.32
    rgba = np.zeros((h, w, 4), np.uint8)
    rgba[..., 0], rgba[..., 1], rgba[..., 2] = 255, 236, 170
    rgba[..., 3] = (alpha * 255).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")


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
    print("forest textures:", split_forest())
    print("garage textures:", split_garage())
    print("patio textures:", split_patio())


if __name__ == "__main__":
    main()
