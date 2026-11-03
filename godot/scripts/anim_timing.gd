class_name GaleAnimTiming
extends RefCounted
## Per-fighter clip markers (60 fps frames) written by art-source/tools/anim_timing.py.
## Combat frame data never changes; only how its phases map onto each clip.

const PATH := "res://data/anim_timing.json"
const LEGACY_ATTACK := {"wind": 4, "contact": 6, "hold": 10, "follow": 12, "recover": 18, "end": 24}
const LEGACY_STATES := {"idle": 40, "walk": 24, "dash": 10, "guard_high": 10, "parry": 16, "hit": 16, "knockdown": 24, "ko": 30, "victory": 40}

static var _data: Dictionary = {}

static func _table() -> Dictionary:
	if _data.is_empty():
		var file := FileAccess.open(PATH, FileAccess.READ)
		if file != null:
			var parsed: Variant = JSON.parse_string(file.get_as_text())
			if parsed is Dictionary:
				_data = parsed
	return _data

static func attack(id: String, clip: String) -> Dictionary:
	var marks: Variant = _table().get(id, {}).get("attacks", {}).get(clip)
	return marks if marks is Dictionary else LEGACY_ATTACK

static func state_frames(id: String, state: String) -> int:
	return int(_table().get(id, {}).get("states", {}).get(state, LEGACY_STATES.get(state, 24)))

static func state_sec(id: String, state: String) -> float:
	return float(state_frames(id, state)) / 60.0

## Distance covered by one walk cycle; drives walk playback speed and footsteps.
static func stride(id: String) -> float:
	return float(_table().get(id, {}).get("stride", 1.6))

static func contact_sec(id: String, clip: String) -> float:
	return float(attack(id, clip).contact) / 60.0

## Maps a combat phase and its progress (0..1) to a clip time in seconds.
static func attack_seek(id: String, clip: String, phase: String, progress: float) -> float:
	var m := attack(id, clip)
	match phase:
		"startup":
			return lerpf(0.0, float(m.contact), progress) / 60.0
		"active":
			return lerpf(float(m.contact), float(m.follow), progress) / 60.0
		_:
			return lerpf(float(m.follow), float(m.end), progress) / 60.0
