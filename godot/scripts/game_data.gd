class_name GaleData
extends RefCounted

const IDS := ["kaze", "ignis", "tophia", "volt"]
const STAGES := ["zephyr_dojo", "molten_forge", "storm_market"]
const MAX_POINTS := 4
var content: Dictionary

func _init() -> void:
	content = JSON.parse_string(FileAccess.get_file_as_string("res://data/game_data.json"))

func fighter(id: String) -> Dictionary:
	return content.fighters[id]

func stage(id: String) -> Dictionary:
	return content.stages[id]

func arcade(id: String, index: int) -> Dictionary:
	return content.arcade[id][clampi(index - 1, 0, 3)]

func palette(id: String, index: int) -> Dictionary:
	return content.palettes[id][posmod(index, 4)]

func normalize_skills(id: String, values: Array) -> Array:
	var result: Array = []
	var spent := 0
	var nodes: Array = fighter(id).skillTree.duplicate()
	for node: Dictionary in nodes:
		if node.id in values and spent + int(node.cost) <= MAX_POINTS:
			result.append(node.id)
			spent += int(node.cost)
	return result

func toggle_skill(id: String, current: Array, key: String) -> Array:
	var node: Dictionary = {}
	for item: Dictionary in fighter(id).skillTree:
		if item.id == key:
			node = item
	if node.is_empty():
		return current
	var desired := current.duplicate()
	if key in current:
		desired.erase(key)
		return desired
	desired.append(key)
	var normalized := normalize_skills(id, desired)
	return normalized if normalized.size() == desired.size() else current

func move(id: String, kind: String, skills: Array) -> Dictionary:
	var result: Dictionary = fighter(id).moves[kind].duplicate(true)
	GaleMoveRules.apply(id,kind,result)
	var damage := 1.0
	var meter := 1.0
	var gust := 0.0
	var startup := 0
	var chip := 0
	for node: Dictionary in fighter(id).skillTree:
		if node.id not in skills:
			continue
		var effect: Dictionary = node.effect
		damage *= float(effect.get("damageMultiplier", 1.0))
		meter *= float(effect.get("meterGainMultiplier", 1.0))
		gust += float(effect.get("gustForceBonus", 0.0))
		startup += int(effect.get("startupReductionFrames", 0))
		chip += int(effect.get("chipDamageBonus", 0))
	result.damage = roundi(float(result.damage) * damage)
	result.meterGain = roundi(float(result.meterGain) * meter)
	result.gustForce = float(result.gustForce) * (1.0 + gust)
	result.startupFrames = maxi(3, int(result.startupFrames) - startup)
	result.chipDamage = int(result.chipDamage) + chip
	return result

func max_hp(id: String, skills: Array) -> int:
	var hp := int(fighter(id).baseHp)
	for node: Dictionary in fighter(id).skillTree:
		if node.id in skills:
			hp += int(node.effect.get("maxHpBonus", 0))
	return hp
