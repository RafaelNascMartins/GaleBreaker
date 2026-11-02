class_name GalePreferences
extends RefCounted

const PATH := "user://preferences.cfg"
const ACTIONS := ["jump", "crouch", "left", "right", "light", "heavy", "elemental", "ultimate", "guard", "dash", "breaker"]
const RESERVED := [KEY_ESCAPE, KEY_P, KEY_R, KEY_M, KEY_TAB, KEY_F5, KEY_F11, KEY_F12]
var volume := 0.8
var muted := false
var file_path := PATH
var skills := {"kaze": ["kaze_combo_1", "kaze_elem_1"], "ignis": ["ignis_combo_1"], "tophia": ["tophia_def_1"], "volt": ["volt_combo_1"]}
var keys: Array = [
	[KEY_W, KEY_S, KEY_A, KEY_D, KEY_J, KEY_K, KEY_L, KEY_U, KEY_SPACE, KEY_SHIFT, KEY_B],
	[KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT, KEY_KP_1, KEY_KP_2, KEY_KP_3, KEY_KP_4, KEY_KP_0, KEY_ENTER, KEY_KP_5]]

func load_from_disk(data: GaleData) -> void:
	var config := ConfigFile.new()
	if config.load(file_path) != OK or config.get_value("save", "version", 0) != 1:
		install_input()
		return
	var saved_volume: Variant = config.get_value("audio", "volume", 0.8)
	if (saved_volume is float or saved_volume is int) and is_finite(float(saved_volume)):
		volume = clampf(float(saved_volume), 0, 1)
	var saved_mute: Variant = config.get_value("audio", "muted", false)
	if saved_mute is bool:
		muted = saved_mute
	for id: String in GaleData.IDS:
		var values: Variant = config.get_value("skills", id, skills[id])
		if values is Array:
			skills[id] = data.normalize_skills(id, values)
	var candidates: Array = []
	var used: Array = []
	var valid := true
	for player in 2:
		var values: Variant = config.get_value("controls", str(player), keys[player])
		if not values is Array or values.size() != ACTIONS.size():
			valid = false
			break
		for code: Variant in values:
			if not code is int or int(code) <= 0 or int(code) in RESERVED or code in used or OS.get_keycode_string(int(code)).is_empty():
				valid = false
			used.append(code)
		candidates.append(values)
	if valid:
		keys = candidates
	install_input()

func save_to_disk() -> Error:
	var config := ConfigFile.new()
	config.set_value("save", "version", 1)
	config.set_value("audio", "volume", volume)
	config.set_value("audio", "muted", muted)
	for id: String in GaleData.IDS:
		config.set_value("skills", id, skills[id])
	for player in 2:
		config.set_value("controls", str(player), keys[player])
	return config.save(file_path)

func remap(player: int, action: int, code: int) -> String:
	if code <= 0 or code in RESERVED:
		return "Tecla reservada. Escolha outra."
	for p in 2:
		for a in ACTIONS.size():
			if keys[p][a] == code and (p != player or a != action):
				return "Tecla já atribuída a outro comando."
	keys[player][action] = code
	install_input()
	save_to_disk()
	return ""

func install_input() -> void:
	for player in 2:
		for i in ACTIONS.size():
			var name := "p%d_%s" % [player + 1, ACTIONS[i]]
			if not InputMap.has_action(name):
				InputMap.add_action(name)
			InputMap.action_erase_events(name)
			var event := InputEventKey.new()
			event.physical_keycode = keys[player][i]
			InputMap.action_add_event(name, event)

static func input_for(player: int) -> Dictionary:
	var prefix := "p%d_" % player
	var result := GaleCombat.idle_input()
	result.axis = Input.get_axis(prefix + "left", prefix + "right")
	result.jump = Input.is_action_just_pressed(prefix + "jump")
	result.crouch = Input.is_action_pressed(prefix + "crouch")
	result.guard = Input.is_action_pressed(prefix + "guard")
	result.parry = Input.is_action_just_pressed(prefix + "guard")
	result.dash = Input.is_action_just_pressed(prefix + "dash")
	result.breaker = Input.is_action_just_pressed(prefix + "breaker")
	for kind: String in ["ultimate", "elemental", "heavy", "light"]:
		if Input.is_action_just_pressed(prefix + kind):
			result.attack = kind
			break
	return result
