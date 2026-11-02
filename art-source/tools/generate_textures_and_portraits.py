from pathlib import Path
import math
import random
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

ROOT = Path(__file__).resolve().parents[2]
CONCEPT = ROOT / "concept-art"
GODOT = ROOT / "godot"

def hex_rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def lerp_color(c1, c2, t: float):
    t = max(0.0, min(1.0, t))
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

def generate_fighter_textures(fighter_id: str, cfg: dict):
    out_dir = GODOT / "assets" / "characters" / fighter_id / "textures"
    out_dir.mkdir(parents=True, exist_ok=True)
    size = 1024
    tile = size // 4  # 256x256 per UV tile in 4x4 grid

    albedo = Image.new("RGBA", (size, size), (128, 128, 128, 255))
    mask = Image.new("RGBA", (size, size), (0, 0, 0, 255))
    height_map = Image.new("L", (size, size), 128)

    adraw = ImageDraw.Draw(albedo)
    mdraw = ImageDraw.Draw(mask)
    hdraw = ImageDraw.Draw(height_map)

    rng = random.Random(hash(fighter_id) & 0xFFFFFFFF)

    def fill_tile(col: int, row: int, base_hex: str, mask_rgb=(0, 0, 0), pattern="smooth", secondary_hex=None):
        # Note: In UV coordinates (u, v), v=0 is bottom in OpenGL/glTF or top in image.
        # To make UV mapping completely independent of V-flip, we fill BOTH (col, row) from top AND (col, 3-row) or we use row symmetrically!
        # Even better: we have 8 zones, so if we place zone i at column (i % 4), and span vertically or mirror top/bottom rows, V-flip can NEVER miss the tile!
        pass

    # Let's use 8 vertical strips across U (0..7), each 128px wide and full 1024px tall!
    # Why vertical strips across U? Because U is never flipped between Blender, glTF, and Godot (only V can be flipped 1-V)!
    # With vertical strips along U, any V in [0, 1] hits the exact right material zone AND gets vertical gradient/detail!
    strip_w = size // 8  # 128px wide per zone, 8 zones total

    zones = [
        # Zone 0: Base skin (pale chest for Ignis, normal skin for others)
        ("skin_base", cfg["skin_base"], (0, 0, 0), "skin"),
        # Zone 1: Sunburn / secondary skin (red sunburned skin for Ignis; warm shaded skin for others)
        ("skin_sunburn", cfg["skin_sunburn"], (0, 0, 0), "sunburn" if fighter_id == "ignis" else "skin"),
        # Zone 2: Primary outfit / armor (Mask R = 255)
        ("primary", cfg["primary"], (255, 0, 0), cfg["primary_pattern"]),
        # Zone 3: Secondary outfit / trim (Mask G = 255)
        ("secondary", cfg["secondary"], (0, 255, 0), cfg["secondary_pattern"]),
        # Zone 4: Accent / elemental glow (Mask B = 255)
        ("accent", cfg["accent"], (0, 0, 255), "glow"),
        # Zone 5: Hair / beard / dark detail (Mask = 0)
        ("hair", cfg["hair"], (0, 0, 0), "hair"),
        # Zone 6: Leather / wraps / boots / cables (Mask = 0, preserves natural leather/boots)
        ("leather", cfg["leather"], (0, 0, 0), "leather"),
        # Zone 7: Eyes / dark metallic / buckle detail (Mask = 0)
        ("dark", cfg["dark"], (0, 0, 0), "metal"),
    ]

    for idx, (name, hex_col, m_col, pat) in enumerate(zones):
        x0 = idx * strip_w
        x1 = x0 + strip_w
        c_base = hex_rgb(hex_col)
        c_dark = lerp_color(c_base, (10, 12, 15), 0.28)
        c_light = lerp_color(c_base, (255, 250, 240), 0.22)

        adraw.rectangle([x0, 0, x1 - 1, size - 1], fill=(*c_base, 255))
        mdraw.rectangle([x0, 0, x1 - 1, size - 1], fill=(*m_col, 255))
        hdraw.rectangle([x0, 0, x1 - 1, size - 1], fill=128)

        # Add rich procedural texture & normal height details per pattern
        for _ in range(360):
            px = rng.randint(x0 + 4, x1 - 5)
            py = rng.randint(4, size - 5)
            if pat == "sunburn":
                # Mottled sunburn blotches & pores on Ignis's arms/head/shoulders
                r = rng.randint(6, 22)
                blotch = lerp_color(c_base, (196, 78, 68), rng.uniform(0.10, 0.40))
                adraw.ellipse([px - r, py - r, px + r, py + r], fill=(*blotch, 255))
                hdraw.ellipse([px - 2, py - 2, px + 2, py + 2], fill=rng.randint(118, 138))
                # Short dark body-hair strokes across the whole sunburnt torso/arms.
                if rng.random() < 0.55:
                    hx = px + rng.randint(-10, 10)
                    hy = py + rng.randint(-10, 10)
                    adraw.line([hx, hy, hx + rng.randint(-3, 3), hy + rng.randint(5, 11)], fill=(128, 66, 52, 255), width=1)
            elif pat == "skin":
                r = rng.randint(8, 24)
                tone = lerp_color(c_base, c_light if rng.random() > 0.5 else c_dark, rng.uniform(0.04, 0.12))
                adraw.ellipse([px - r, py - r, px + r, py + r], fill=(*tone, 255))
            elif pat == "robe":
                # Woven cloth folds & subtle gold-jade embroidery lines
                h = rng.randint(25, 90)
                fold = c_dark if rng.random() > 0.45 else c_light
                adraw.line([px, py, px, min(size - 1, py + h)], fill=(*fold, 255), width=rng.randint(2, 4))
                hdraw.line([px, py, px, min(size - 1, py + h)], fill=155 if fold == c_light else 100, width=3)
            elif pat == "denim":
                # Diagonal denim twill weave + mud/dust specks
                adraw.line([px, py, min(x1 - 2, px + 14), min(size - 2, py + 14)], fill=(*c_light, 255), width=1)
                hdraw.line([px, py, min(x1 - 2, px + 14), min(size - 2, py + 14)], fill=148, width=1)
                if rng.random() < 0.40:
                    mud = (122, 96, 68)
                    r = rng.randint(3, 9)
                    adraw.ellipse([px - r, py - r, px + r, py + r], fill=(*mud, 255))
            elif pat == "stone":
                # Cracked orange sandstone facets
                w = rng.randint(10, 28)
                h = rng.randint(10, 28)
                facet = c_light if rng.random() > 0.5 else c_dark
                adraw.rectangle([px, py, min(x1 - 3, px + w), min(size - 3, py + h)], fill=(*facet, 255), outline=(*c_dark, 255))
                hdraw.rectangle([px, py, min(x1 - 3, px + w), min(size - 3, py + h)], fill=rng.randint(90, 175), outline=60)
            elif pat == "scrap":
                # Weathered yellow/blue scrap metal with scratches & rivets
                w = rng.randint(12, 30)
                h = rng.randint(12, 30)
                plate = lerp_color(c_base, (70, 110, 135) if rng.random() < 0.28 else c_dark, rng.uniform(0.15, 0.45))
                adraw.rectangle([px, py, min(x1 - 3, px + w), min(size - 3, py + h)], fill=(*plate, 255))
                adraw.line([px, py, min(x1 - 2, px + 18), min(size - 2, py + 6)], fill=(*c_light, 255), width=2)
                hdraw.rectangle([px, py, min(x1 - 3, px + w), min(size - 3, py + h)], fill=165, outline=80)
            elif pat == "hair":
                # Hair strands; for Volt, singed dark tips!
                h = rng.randint(20, 60)
                strand = (35, 28, 24) if (fighter_id == "volt" and rng.random() < 0.38) else c_dark
                adraw.line([px, py, px + rng.randint(-4, 4), min(size - 1, py + h)], fill=(*strand, 255), width=3)
                hdraw.line([px, py, px + rng.randint(-4, 4), min(size - 1, py + h)], fill=160, width=2)
            elif pat in ("leather", "metal", "glow"):
                r = rng.randint(4, 14)
                col = c_light if pat == "glow" else c_dark
                adraw.ellipse([px - r, py - r, px + r, py + r], fill=(*col, 255))
                hdraw.ellipse([px - r, py - r, px + r, py + r], fill=160 if pat == "glow" else 110)

    # Convert height_map to tangent-space normal map (RGB)
    h_pixels = height_map.load()
    normal_img = Image.new("RGB", (size, size), (128, 128, 255))
    n_pixels = normal_img.load()
    strength = 2.5
    for y in range(size):
        ym = max(0, y - 1)
        yp = min(size - 1, y + 1)
        for x in range(size):
            xm = max(0, x - 1)
            xp = min(size - 1, x + 1)
            dx = (h_pixels[xp, y] - h_pixels[xm, y]) / 255.0 * strength
            dy = (h_pixels[x, yp] - h_pixels[x, ym]) / 255.0 * strength
            dz = 1.0
            inv_len = 1.0 / math.sqrt(dx * dx + dy * dy + dz * dz)
            nx = int(((-dx * inv_len) * 0.5 + 0.5) * 255)
            ny = int(((-dy * inv_len) * 0.5 + 0.5) * 255)
            nz = int(((dz * inv_len) * 0.5 + 0.5) * 255)
            n_pixels[x, y] = (max(0, min(255, nx)), max(0, min(255, ny)), max(0, min(255, nz)))

    albedo.save(out_dir / "albedo.png")
    mask.save(out_dir / "mask.png")
    normal_img.save(out_dir / "normal.png")
    print(f"Generated textures for {fighter_id} in {out_dir}")


FIGHTER_TEX_CONFIGS = {
    "kaze": {
        "skin_base": "#d89c74",
        "skin_sunburn": "#c68860",
        "primary": "#28654F",
        "primary_pattern": "robe",
        "secondary": "#84A98C",
        "secondary_pattern": "robe",
        "accent": "#4AD69D",
        "hair": "#22201E",
        "leather": "#26463B",
        "dark": "#1B2823",
    },
    "ignis": {
        "skin_base": "#EDD3BE",      # Pale tone kept for eye whites only
        "skin_sunburn": "#D8776A",   # Sunburnt pink-red over the whole upper body (menu-pausa-v2)
        "primary": "#5B7088",        # Worn blue jeans (recolorable by palette)
        "primary_pattern": "denim",
        "secondary": "#5C4028",      # Cowboy hat & boots brown leather
        "secondary_pattern": "leather",
        "accent": "#F97316",         # Solar fire / brass buckle
        "hair": "#4A3221",           # Brown beard
        "leather": "#47311E",        # Belt & boots
        "dark": "#A68246",           # Brass buckle
    },
    "tophia": {
        "skin_base": "#E0A482",      # Exposed head skin
        "skin_sunburn": "#CF906E",
        "primary": "#C86428",        # Orange sandstone knight armor
        "primary_pattern": "stone",
        "secondary": "#8C421A",      # Darker sandstone bevels
        "secondary_pattern": "stone",
        "accent": "#FFA834",         # Glowing tectonic cracks
        "hair": "#1C1B20",           # Short straight black hair
        "leather": "#4E3529",        # Inner stone joints
        "dark": "#292320",
    },
    "volt": {
        "skin_base": "#E5AF8A",
        "skin_sunburn": "#D19A75",
        "primary": "#D49B38",        # Salvaged yellow/ochre scrap armor
        "primary_pattern": "scrap",
        "secondary": "#435C6E",      # Salvaged blue-grey metal & dark patched pants
        "secondary_pattern": "scrap",
        "accent": "#22E4FF",         # Bright cyan battery & cannon core
        "hair": "#E5C158",           # Blond hair with singed dark tips
        "leather": "#332E2A",        # Cables, straps & heavy boots
        "dark": "#8F2D26",           # Red waist rag & rust details
    },
}


def generate_portraits():
    out_dir = GODOT / "assets" / "ui" / "portraits"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Extract high-res V2/V5 portraits from concept art and apply clean alpha vignette/cutout
    v2_sheet = Image.open(CONCEPT / "personagens-v2.png").convert("RGBA")
    sw, sh = v2_sheet.size

    sources = {
        "kaze": (v2_sheet, (int(sw * 0.04), int(sh * 0.01), int(sw * 0.21), int(sh * 0.28)), "#28654F"),
        "ignis": (v2_sheet, (int(sw * 0.29), int(sh * 0.01), int(sw * 0.47), int(sh * 0.28)), "#A54332"),
        "tophia": (Image.open(CONCEPT / "tophia-retrato-gdd-v1.png").convert("RGBA"), None, "#98531F"),
        "volt": (Image.open(CONCEPT / "volt-retrato-gdd-v1.png").convert("RGBA"), None, "#206A7C"),
    }

    for fid, (img, crop_box, border_hex) in sources.items():
        if crop_box:
            cropped = img.crop(crop_box)
        else:
            iw, ih = img.size
            side = min(iw, ih)
            left = (iw - side) // 2
            cropped = img.crop((left, 0, left + side, side))

        portrait = cropped.resize((256, 256), Image.Resampling.LANCZOS)
        # Key out near-white/ivory background at edges into smooth alpha + stylized frame
        px = portrait.load()
        for y in range(256):
            for x in range(256):
                r, g, b, a = px[x, y]
                # Ivory paper background in concepts is around (244, 240, 232)
                dist_bg = math.sqrt((r - 245) ** 2 + (g - 241) ** 2 + (b - 234) ** 2)
                # Keep interior face skin intact; only fade background outside head silhouette
                cx, cy = (x - 128) / 128.0, (y - 136) / 128.0
                radial = math.sqrt(cx * cx + cy * cy)
                if dist_bg < 26 and (radial > 0.42 or y < 30):
                    alpha = int(max(0.0, min(1.0, (dist_bg - 8) / 18.0)) * 255)
                    px[x, y] = (r, g, b, alpha)

        portrait.save(out_dir / f"{fid}.png")
        print(f"Saved V2/V5 portrait: {out_dir / f'{fid}.png'}")


if __name__ == "__main__":
    import sys
    only = sys.argv[sys.argv.index("--fighter") + 1] if "--fighter" in sys.argv else None
    for fid, cfg in FIGHTER_TEX_CONFIGS.items():
        if only is None or fid == only:
            generate_fighter_textures(fid, cfg)
    if only is None:
        generate_portraits()
