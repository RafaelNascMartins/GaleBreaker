"""Per-fighter animation timing (60 fps frames), shared by the Blender builder and Godot.

Attack clips use markers: wind (anticipation peak), contact, hold (end of the
impact hold), follow (end of follow-through), recover (back near stance), end.
Godot maps combat startup -> [0, contact], active -> [contact, follow] and
recovery -> [follow, end], so the gameplay frame data never changes.

Fighters without an entry keep the original 24-frame layout.
"""
import json
from pathlib import Path

LEGACY_ATTACK = {"wind": 4, "contact": 6, "hold": 10, "follow": 12, "recover": 18, "end": 24}
LEGACY_STATES = {"idle": 40, "walk": 24, "dash": 10, "guard_high": 10, "parry": 16, "hit": 16,
                 "knockdown": 24, "ko": 30, "victory": 40}

# World units travelled per walk cycle (two steps). Chosen so each walk clip
# plays at most ~1.3x its authored speed at full walk speed.
STRIDE = {"kaze": 1.8, "ignis": 1.8, "tophia": 1.55, "volt": 1.9}

ATTACK_CLIPS = ["light_1", "light_2", "light_3", "heavy", "heavy_2", "heavy_3", "elemental", "ultimate", "down_punch", "air_punch", "sweep",
                "rock_spike"]


def _attack(wind, contact, hold, follow, recover, end):
    return {"wind": wind, "contact": contact, "hold": hold, "follow": follow, "recover": recover, "end": end}


TIMING = {
    # Kaze: quick, whipping and fluid. Short wind-ups, long cloth follow-through.
    "kaze": {
        "attacks": {
            "light_1": _attack(5, 7, 9, 12, 17, 22),
            "light_2": _attack(5, 7, 9, 12, 17, 22),
            "light_3": _attack(7, 10, 13, 16, 22, 28),
            # K chain (Legends Babuin): K1 low shin kick, K2 front push kick, K3 jumping side kick.
            "heavy": _attack(6, 9, 12, 15, 21, 26),
            "heavy_2": _attack(8, 11, 14, 18, 25, 32),
            "heavy_3": _attack(10, 13, 16, 20, 28, 36),
            "elemental": _attack(11, 14, 18, 22, 29, 36),
            "ultimate": _attack(18, 24, 30, 35, 44, 54),
        },
        "states": {"idle": 64, "walk": 26, "dash": 12, "guard_high": 12, "parry": 18, "hit": 20,
                   "knockdown": 30, "ko": 40, "victory": 48},
    },
    # Ignis: slow, heavy, committed. Long wind-ups, big holds on impact, heavy recovery.
    "ignis": {
        "attacks": {
            "light_1": _attack(8, 11, 14, 17, 24, 30),
            "light_2": _attack(8, 11, 14, 17, 24, 30),
            "light_3": _attack(13, 17, 21, 25, 33, 40),
            # K chain (Legends Dale): K1 big boot, K2 Marreta Caipira.
            "heavy": _attack(6, 9, 12, 15, 21, 26),
            "heavy_2": _attack(17, 21, 26, 30, 40, 48),
            "elemental": _attack(15, 19, 24, 28, 37, 44),
            "ultimate": _attack(22, 28, 34, 40, 50, 58),
            "down_punch": _attack(6, 9, 13, 16, 22, 28),
            "air_punch": _attack(5, 8, 12, 15, 20, 26),
            "sweep": _attack(7, 10, 14, 17, 24, 30),
        },
        "states": {"idle": 52, "walk": 34, "dash": 14, "guard_high": 14, "parry": 18, "hit": 22,
                   "knockdown": 32, "ko": 44, "victory": 56},
    },
    # X12 (legends_x12_anim.py), boxer: the jab with no wind-up (smear at 2, hit 3-8), the cross
    # with a short load and pull (3-5), smear 7, hit 8-12. Clips not listed keep the legacy layout.
    "tophia": {
        "attacks": {
            "light_1": _attack(1, 3, 8, 10, 16, 22),
            "light_2": _attack(5, 8, 12, 14, 20, 26),
            "light_3": _attack(4, 7, 11, 13, 19, 24),
            "heavy": _attack(8, 12, 17, 20, 28, 34),
            "down_punch": _attack(3, 6, 10, 12, 18, 24),
            "sweep": _attack(5, 8, 12, 15, 22, 28),
            "air_punch": _attack(4, 6, 12, 14, 19, 24),
            "elemental": _attack(3, 6, 10, 12, 18, 22),
            "ultimate": _attack(26, 30, 36, 40, 50, 58),
            "rock_spike": _attack(6, 10, 13, 16, 24, 30),
        },
    },
    # Orsted (legends_orsted_anim.py), calm zoner: J1-J3 point-blank shots (J3 a 360 spin into
    # the shot), K the projectile (a long aim, a big kick), down+J the bomb toss.
    "volt": {
        "attacks": {
            "light_1": _attack(8, 12, 22, 26, 34, 42),   # the user's J1: a visible wind-up, a 10-frame held shot
            "light_2": _attack(6, 10, 19, 23, 30, 38),   # 2026-11-08 frame budget (study section 11)
            "light_3": _attack(12, 16, 26, 31, 40, 50),
            "heavy": _attack(18, 26, 34, 38, 48, 60),       # charged shot: 26-frame charge (move_rules)
            "down_punch": _attack(8, 14, 22, 24, 34, 44),
            "sweep": _attack(6, 10, 18, 20, 30, 40),
            "air_punch": _attack(3, 5, 9, 11, 17, 24),
            "elemental": _attack(12, 18, 24, 26, 38, 50),    # pulse 18/8/24 (move_rules)
            "ultimate": _attack(32, 42, 50, 54, 72, 90),     # beam 42/12/36 (move_rules)
        },
        "states": {"idle": 64, "walk": 22, "dash": 12, "guard_high": 10, "parry": 18, "hit": 20,
                   "knockdown": 30, "ko": 40, "victory": 48},
    },
}


def attack(fid, clip):
    return TIMING.get(fid, {}).get("attacks", {}).get(clip, LEGACY_ATTACK)


def state(fid, name):
    return TIMING.get(fid, {}).get("states", {}).get(name, LEGACY_STATES[name])


def export_json(path: Path):
    out = {}
    for fid in ["kaze", "ignis", "tophia", "volt"]:
        out[fid] = {
            "attacks": {c: attack(fid, c) for c in ATTACK_CLIPS},
            "states": {s: state(fid, s) for s in LEGACY_STATES},
            "stride": STRIDE[fid],
        }
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    export_json(Path(__file__).resolve().parents[2] / "godot" / "data" / "anim_timing.json")
