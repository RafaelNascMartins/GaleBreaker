class_name GalePreferences
extends RefCounted

const PATH := "user://preferences.cfg"
const ACTIONS := ["jump", "crouch", "left", "right", "light", "heavy", "elemental", "ultimate", "guard", "dash", "breaker"]
const RESERVED := [KEY_ESCAPE, KEY_P, KEY_R, KEY_M, KEY_TAB, KEY_F2, KEY_F5, KEY_F11, KEY_F12]
var volume := 0.8
var muted := false
var music_volume := 0.7
var sfx_volume := 0.85
var shake_strength := 0.65
var flashes := true
var vibration := true
var difficulty := 1
var skills2 := {"kaze":[],"ignis":[],"tophia":[],"volt":[]}
var arcade_run := {}
var file_path := PATH
var skills := {"kaze": ["kaze_combo_1", "kaze_elem_1"], "ignis": ["ignis_combo_1"], "tophia": ["tophia_def_1"], "volt": ["volt_combo_1"]}
const DEFAULT_KEYS := [
	[KEY_W, KEY_S, KEY_A, KEY_D, KEY_J, KEY_K, KEY_L, KEY_U, KEY_SPACE, KEY_SHIFT, KEY_B],
	[KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT, KEY_KP_1, KEY_KP_2, KEY_KP_3, KEY_KP_4, KEY_KP_0, KEY_ENTER, KEY_KP_5]]
var keys: Array = DEFAULT_KEYS.duplicate(true)

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
	for field: String in ["music_volume","sfx_volume","shake_strength"]:
		var value: Variant = config.get_value("options",field,get(field))
		if (value is float or value is int) and is_finite(float(value)):
			set(field,clampf(float(value),0,1))
	for field: String in ["flashes","vibration"]:
		var value: Variant = config.get_value("options",field,get(field))
		if value is bool:
			set(field,value)
	var saved_difficulty:Variant=config.get_value("options","difficulty",1)
	difficulty=clampi(saved_difficulty,0,2) if saved_difficulty is int else 1
	var run: Variant = config.get_value("arcade","run",{})
	if run is Dictionary and run.get("fighter","") in GaleData.IDS and int(run.get("index",0)) in range(1,5):
		arcade_run = run
	for id: String in GaleData.IDS:
		var values: Variant = config.get_value("skills", id, skills[id])
		if values is Array:
			skills[id] = data.normalize_skills(id, values)
		var values2: Variant = config.get_value("skills_p2",id,[])
		if values2 is Array:
			skills2[id] = data.normalize_skills(id,values2)
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
	for field: String in ["music_volume","sfx_volume","shake_strength","flashes","vibration","difficulty"]:
		config.set_value("options",field,get(field))
	config.set_value("arcade","run",arcade_run)
	for id: String in GaleData.IDS:
		config.set_value("skills", id, skills[id])
		config.set_value("skills_p2",id,skills2[id])
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

func restore_default_keys() -> void:
	keys = DEFAULT_KEYS.duplicate(true)
	install_input()
	save_to_disk()

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
	install_gamepads()

static func pad_events(action: String, device: int) -> Array[InputEvent]:
	var result: Array[InputEvent] = []
	var buttons := {"jump":JOY_BUTTON_A,"crouch":JOY_BUTTON_DPAD_DOWN,"left":JOY_BUTTON_DPAD_LEFT,"right":JOY_BUTTON_DPAD_RIGHT,"light":JOY_BUTTON_X,"heavy":JOY_BUTTON_Y,"elemental":JOY_BUTTON_B,"ultimate":JOY_BUTTON_RIGHT_SHOULDER,"guard":JOY_BUTTON_LEFT_SHOULDER,"dash":JOY_BUTTON_RIGHT_STICK,"breaker":JOY_BUTTON_LEFT_STICK}
	var button := InputEventJoypadButton.new()
	button.device = device
	button.button_index = buttons[action]
	result.append(button)
	if action in ["left","right","crouch"]:
		var axis := InputEventJoypadMotion.new()
		axis.device = device
		axis.axis = JOY_AXIS_LEFT_Y if action == "crouch" else JOY_AXIS_LEFT_X
		axis.axis_value = -1.0 if action == "left" else 1.0
		result.append(axis)
	return result

func install_gamepads() -> void:
	var devices := Input.get_connected_joypads()
	for player in 2:
		for action: String in ACTIONS:
			var name := "p%d_%s" % [player+1,action]
			for old in InputMap.action_get_events(name):
				if old is InputEventJoypadButton or old is InputEventJoypadMotion:
					InputMap.action_erase_event(name,old)
			InputMap.action_set_deadzone(name,0.3)
			if devices.size() > player:
				for event in pad_events(action,devices[player]):
					InputMap.action_add_event(name,event)
	for action:String in ["ui_up","ui_down","ui_left","ui_right","ui_accept","ui_cancel"]:
		if not InputMap.has_action(action):InputMap.add_action(action)
		var button:=InputEventJoypadButton.new()
		button.device=-1
		button.button_index={"ui_up":JOY_BUTTON_DPAD_UP,"ui_down":JOY_BUTTON_DPAD_DOWN,"ui_left":JOY_BUTTON_DPAD_LEFT,"ui_right":JOY_BUTTON_DPAD_RIGHT,"ui_accept":JOY_BUTTON_A,"ui_cancel":JOY_BUTTON_B}[action]
		if not InputMap.action_has_event(action,button):InputMap.action_add_event(action,button)
		if action in ["ui_up","ui_down","ui_left","ui_right"]:
			var axis:=InputEventJoypadMotion.new()
			axis.device=-1
			axis.axis=JOY_AXIS_LEFT_Y if action in ["ui_up","ui_down"] else JOY_AXIS_LEFT_X
			axis.axis_value=-1.0 if action in ["ui_up","ui_left"] else 1.0
			if not InputMap.action_has_event(action,axis):InputMap.action_add_event(action,axis)

func hint(player: int, action: int) -> String:
	if Input.get_connected_joypads().size()>player:
		return ["A","↓","←","→","X","Y","B","RB","LB","R3","L3"][action]
	return OS.get_keycode_string(keys[player][action])

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
