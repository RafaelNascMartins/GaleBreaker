extends SceneTree

var failures := 0
var checks := 0
var database := GaleData.new()

func check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures += 1
		push_error("FAIL: " + message)
	else:
		print("PASS: " + message)

func fresh(game_mode: String = "versus") -> GaleCombat:
	var sim := GaleCombat.new(database)
	sim.start("kaze", "ignis", "zephyr_dojo", game_mode)
	sim.countdown = 0
	sim.hazards.clear()
	sim.p1.x = -0.5
	sim.p2.x = 0.5
	return sim

func advance(sim: GaleCombat, frames: int, a: Dictionary = {}, b: Dictionary = {}) -> void:
	for i in frames:
		sim.step(GaleCombat.idle_input() if a.is_empty() else a, GaleCombat.idle_input() if b.is_empty() else b)

func attack_input(kind: String, crouch: bool = false) -> Dictionary:
	var inp := GaleCombat.idle_input()
	inp.attack = kind
	inp.crouch = crouch
	return inp

## One frame of a direction in numpad notation (relative to P1 facing right) plus a button.
func dir_input(d: int, button: String = "") -> Dictionary:
	var inp := GaleCombat.idle_input()
	inp.axis = float(((d - 1) % 3) - 1)
	inp.crouch = d in [1, 2, 3]
	inp.attack = button
	return inp

func command_sim() -> GaleCombat:
	var sim := GaleCombat.new(database)
	sim.start("tophia", "kaze", "zephyr_dojo", "versus")
	sim.countdown = 0
	sim.p1.meter = 100.0
	sim.p1.x = -3.5
	sim.p2.x = 3.0
	return sim

func play_motion(sim: GaleCombat, dirs: Array, button: String, frames_each: int = 2) -> void:
	for i in dirs.size():
		for k in frames_each:
			var last: bool = i == dirs.size() - 1 and k == frames_each - 1
			sim.step(dir_input(int(dirs[i]), button if last else ""), GaleCombat.idle_input())

func command_input_checks() -> void:
	var sim := command_sim()
	play_motion(sim, [4, 1, 2, 3, 6], "elemental")
	check(String(sim.p1.move.get("type", "")) == "rock_spike", "half circle forward + elemental throws X12's rock spike")
	sim = command_sim()
	play_motion(sim, [4, 2, 6], "elemental", 3)
	check(String(sim.p1.move.get("type", "")) == "rock_spike", "the short half circle (4-2-6) also counts")
	sim = command_sim()
	play_motion(sim, [5], "elemental")
	check(String(sim.p1.move.get("type", "")) == "elemental", "elemental alone stays the straight stone jab")
	sim = command_sim()
	play_motion(sim, [4, 4, 5, 6, 6], "elemental", 3)
	check(String(sim.p1.move.get("type", "")) == "elemental", "walking back then forward does not throw the rock")
	sim = command_sim()
	play_motion(sim, [2, 3, 6], "elemental", 3)
	check(String(sim.p1.move.get("type", "")) == "elemental", "a quarter circle (2-3-6) is not the half circle")
	sim = command_sim()
	play_motion(sim, [4, 1, 2, 3, 6], "")
	for i in 20:
		sim.step(GaleCombat.idle_input(), GaleCombat.idle_input())
	sim.step(dir_input(5, "elemental"), GaleCombat.idle_input())
	check(String(sim.p1.move.get("type", "")) == "elemental", "an old motion expires (no rock long after it)")
	var kaze := GaleCombat.new(database)
	kaze.start("kaze", "tophia", "zephyr_dojo", "versus")
	kaze.countdown = 0
	play_motion(kaze, [4, 1, 2, 3, 6], "elemental")
	check(String(kaze.p1.move.get("type", "")) == "elemental", "fighters without the command keep their elemental")
	# the stone flies, lands where it was aimed and the spike launches the opponent
	sim = command_sim()
	sim.p2.x = sim.p1.x + 3.9
	play_motion(sim, [4, 1, 2, 3, 6], "elemental")
	var landed := false
	for i in 90:
		sim.step(GaleCombat.idle_input(), GaleCombat.idle_input())
		if sim.p2.hp < sim.p2.max_hp:
			landed = true
			break
	check(landed and not sim.p2.grounded, "the falling stone raises a spike that hits and launches")
	sim = command_sim()
	sim.p2.x = sim.p1.x + 1.0
	play_motion(sim, [4, 1, 2, 3, 6], "elemental")
	for i in 90:
		sim.step(GaleCombat.idle_input(), GaleCombat.idle_input())
	check(sim.p2.hp == sim.p2.max_hp, "the spike rises where the stone lands, not at point blank")

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	check(database.content.fighters.size() == 4 and database.content.stages.size() == 3, "all source fighters and arenas imported")
	for id: String in GaleData.IDS:
		check(database.fighter(id).moves.size() == 6, id + " has six source moves")
		check(database.content.arcade[id].size() == 4, id + " has four arcade stages")
	var base := database.move("kaze", "light", [])
	var upgraded := database.move("kaze", "light", ["kaze_combo_1", "kaze_combo_2"])
	check(upgraded.startupFrames == 3 and upgraded.damage > base.damage, "skill modifiers affect startup and damage")
	check(database.max_hp("volt", ["volt_def_1"]) > database.max_hp("volt", []), "defense skill increases HP")
	check(database.toggle_skill("kaze", [], "kaze_combo_2") == ["kaze_combo_2"], "skills can be chosen freely without tier locks")
	check(database.toggle_skill("kaze", ["kaze_combo_1", "kaze_combo_2"], "kaze_combo_1") == ["kaze_combo_2"], "removing a skill preserves independent choices")
	var full := ["kaze_combo_1", "kaze_combo_2", "kaze_elem_1"]
	check(database.toggle_skill("kaze", full, "kaze_def_1") == full, "skill budget cannot be exceeded")
	check(GaleCombat.blocks(true, "low") and not GaleCombat.blocks(false, "low"), "low guard rule")
	check(GaleCombat.blocks(false, "overhead") and not GaleCombat.blocks(true, "overhead"), "overhead guard rule")
	command_input_checks()
	var sim := fresh()
	sim.step(attack_input("light"), GaleCombat.idle_input())
	advance(sim, 12)
	check(sim.p2.hp < sim.p2.max_hp, "jab damages a nearby opponent")
	check(sim.p1.combo == 1 and sim.p1.chain == 2, "jab advances punch chain")
	check(sim.p1.meter > 25, "connected jab gains meter")
	sim = fresh()
	sim.p1.x = -GaleCombat.EDGE + 0.5
	sim.p2.x = GaleCombat.EDGE - 0.5
	sim.step(attack_input("light"), GaleCombat.idle_input())
	advance(sim, 30)
	check(sim.p2.hp == sim.p2.max_hp, "out of range attacks do not teleport or damage")
	sim = fresh()
	var guard := GaleCombat.idle_input()
	guard.axis = 1.0
	sim.step(attack_input("light"), guard)
	advance(sim, 12, {}, guard)
	check(sim.p2.hp >= sim.p2.max_hp - base.chipDamage, "holding back applies chip damage only")
	sim = fresh()
	sim.step(attack_input("down_punch", true), GaleCombat.idle_input())
	advance(sim, 10)
	check(not sim.p2.grounded and sim.p2.vy > 0, "low launcher lifts defender")
	sim = fresh()
	sim.p1.meter = 10
	check(not sim.attack(sim.p1, "ultimate", false), "ultimate requires meter")
	sim.p1.meter = 75
	check(sim.attack(sim.p1, "ultimate", false) and sim.p1.meter == 25 and sim.freeze == 21, "ultimate consumes 50 meter and freezes")
	sim = fresh()
	sim.p1.action = "hitstun"
	sim.p1.frames = 30
	var breaker := GaleCombat.idle_input()
	breaker.breaker = true
	sim.step(breaker, GaleCombat.idle_input())
	check(sim.p1.breaker_cd == 360 and sim.p1.immunity == 120, "combo breaker applies cooldown and immunity")
	sim = fresh()
	var parry := GaleCombat.idle_input()
	parry.parry = true
	sim.step(attack_input("light"), parry)
	advance(sim, 6)
	check(sim.p2.hp == sim.p2.max_hp and sim.p2.meter > 25, "perfect parry prevents damage and gains meter")
	sim = fresh()
	sim.p2.hp = 1
	sim.step(attack_input("light"), GaleCombat.idle_input())
	advance(sim, 15)
	check(sim.wins[0] == 1 and sim.winner == 0 and sim.round_wait > 0, "first round does not finish best of three")
	advance(sim, 116 + GaleCombat.COUNTDOWN_FRAMES)
	check(sim.round_number == 2 and sim.p2.hp == sim.p2.max_hp and sim.countdown == 0, "round resets HP and runs the next countdown")
	sim.p2.hp = 0
	sim.step(GaleCombat.idle_input(), GaleCombat.idle_input())
	check(sim.winner == 1 and sim.wins[0] == 2, "second round victory finishes match")
	sim = fresh()
	sim.remaining = 0
	sim.p1.hp = sim.p1.max_hp
	sim.p2.hp = sim.p2.max_hp
	sim.step(GaleCombat.idle_input(), GaleCombat.idle_input())
	check(sim.wins == [0, 0] and sim.round_wait > 0, "equal health time over replays round without favoring P1")
	sim = fresh("training")
	sim.p2.hp = 0
	advance(sim, 1)
	check(sim.p2.hp >= 1 and sim.winner == 0 and sim.remaining == 99, "training prevents KO and disables timer")
	sim = fresh()
	sim.start("kaze", "kaze", "zephyr_dojo", "versus")
	check(sim.p1.palette != sim.p2.palette, "mirror palettes are distinct")
	sim.start("kaze", "ignis", "molten_forge", "arcade", [], [], 4)
	check(sim.p2.boss and sim.p2.hp > database.max_hp("ignis", []), "arcade final boss receives overcharge")
	var prefs := GalePreferences.new()
	check(not prefs.remap(0, 4, KEY_R).is_empty(), "reserved key cannot be bound")
	check(not prefs.remap(0, 4, KEY_KP_1).is_empty(), "P2 bindings cannot conflict with P1")
	prefs.file_path = "user://regression-preferences.cfg"
	prefs.volume = 0.35
	prefs.skills.kaze = ["kaze_combo_1", "kaze_combo_2"]
	check(prefs.remap(0, 4, KEY_H).is_empty(), "free key can be rebound")
	var restored := GalePreferences.new()
	restored.file_path = prefs.file_path
	restored.load_from_disk(database)
	check(restored.keys[0][4] == KEY_H and is_equal_approx(restored.volume, 0.35), "native controls and volume persist")
	check(restored.skills.kaze == prefs.skills.kaze, "native skill choices persist")
	var invalid := ConfigFile.new()
	invalid.set_value("save", "version", 1)
	invalid.set_value("controls", "0", [KEY_R])
	invalid.set_value("skills", "kaze", ["kaze_combo_2", "fake"])
	invalid.set_value("audio", "volume", 999)
	invalid.save(prefs.file_path)
	restored = GalePreferences.new()
	restored.file_path = prefs.file_path
	restored.load_from_disk(database)
	check(restored.volume == 1 and restored.keys[0][4] == KEY_J, "invalid saved settings use safe limits and defaults")
	check(restored.skills.kaze == ["kaze_combo_2"], "invalid saved IDs are rejected while valid independent choices survive")
	DirAccess.remove_absolute(ProjectSettings.globalize_path(prefs.file_path))
	sim = fresh()
	sim.p1.move = database.move("kaze", "air_punch", [])
	for i in 3:
		sim.p2.grounded = false
		sim.p2.y = 1
		sim.resolve_hit(sim.p1, sim.p2, GaleCombat.idle_input())
	check(sim.p1.dribbles == 3 and sim.p2.action == "knockdown" and sim.p2.vy < 0, "third air dribble forces a finisher slam")
	sim = fresh()
	sim.start("kaze", "kaze", "zephyr_dojo", "versus")
	sim.countdown = 0
	sim.hazards.clear()
	sim.p1.x = -0.5
	sim.p2.x = 0.5
	sim.step(attack_input("light"), attack_input("light"))
	advance(sim, 5)
	check(sim.p1.hp == sim.p1.max_hp and sim.p2.hp == sim.p2.max_hp and sim.p1.meter >= 50, "simultaneous overlapping attacks clash without HP loss")
	for stage: String in GaleData.STAGES:
		sim = fresh()
		sim.stage_id = stage
		sim.reset_hazards()
		check(sim.hazards.is_empty(), stage + " has no throwable props")
	sim = fresh("arcade")
	for i in 20000:
		var ai := sim.ai_input()
		sim.step(GaleCombat.idle_input(), ai)
		if sim.winner != 0:
			break
	check(sim.winner == 2, "AI can complete a full match against an idle player")
	sim = fresh()
	sim.p1.x = -3.0
	var x0: float = sim.p1.x
	sim.attack(sim.p1, "light", false)
	sim.step(GaleCombat.idle_input(), GaleCombat.idle_input())
	var stepped_back: bool = sim.p1.x < x0
	advance(sim, 20)
	check(stepped_back and sim.p1.x > x0 + 0.1, "Babuin J1 hesitates back, then advances with the punch")
	sim = fresh()
	sim.attack(sim.p1, "light", false)
	var froze := 0
	for i in 30:
		sim.step(GaleCombat.idle_input(), GaleCombat.idle_input())
		froze = maxi(froze, sim.freeze)
	check(froze >= 3, "Babuin J1 holds a visible hitstop on connect")
	# Counter hit: the same J1 landing while the opponent is starting an attack freezes longer
	# and adds a moment of slow motion.
	sim = fresh()
	sim.attack(sim.p1, "light", false)
	var counter_freeze := 0
	var counter_slow := 0
	for i in 30:
		if sim.freeze == 0:
			if sim.p2.action != "startup":
				sim.p2.action = "idle"
				sim.attack(sim.p2, "light", false)   # (his heavy has armour)
			sim.p2.frames = 30
		sim.step(GaleCombat.idle_input(), GaleCombat.idle_input())
		counter_freeze = maxi(counter_freeze, sim.freeze)
		counter_slow = maxi(counter_slow, sim.slow)
	check(counter_freeze >= froze + 3 and counter_slow > 0, "a counter hit freezes longer than a normal hit and slows the action")
	check(int(sim.p2.flash) <= 3, "the hit flash is short, so the hurt pose reads during the freeze")
	sim = fresh()
	var kick_steps: Array = []
	for press in 3:
		sim.p1.action = "idle"
		sim.p1.frames = 0
		sim.attack(sim.p1, "heavy", false)
		kick_steps.append(int(sim.p1.move.chain_step))
	check(kick_steps == [1, 2, 3] and String(sim.p1.move.name) == "Chute Giratório", "Babuin K presses chain K1 low kick, K2 front kick, K3 spinning back kick")
	# Instantiate the actual scene and exercise menus and all arena/model combinations.
	var app: Node = load("res://scenes/main.tscn").instantiate()
	root.add_child(app)
	await process_frame
	check(app.screen == "menu", "main scene initializes menu")
	app.show_skills()
	check(is_instance_valid(app.modal), "skills modal opens")
	check(not app.menu.visible, "modal hides selection controls and releases their keyboard focus")
	app.show_settings()
	check(is_instance_valid(app.rebind_label), "settings and remapping initialize")
	app.close_modal()
	check(app.menu.visible, "closing modal restores selection")
	for arena_id: String in GaleData.STAGES:
		app.stage = arena_id
		for id: String in GaleData.IDS:
			app.fighter1 = id
			app.preview()
			app.arena.render(app.sim, 1.0 / 60.0)
			check(app.arena.fighters[0].is_valid_asset(), id + " GLB scene has Skeleton3D, 27 required clips, textures, masks, sockets and valid scale")
	check(app.arena.fighters.size() == 2, "all arenas and fighter models build and render")
	# Validate palette swaps and Ignis sunburn mask preservation
	app.fighter1 = "ignis"
	app.palette1 = 2
	app.preview()
	var ignis_view: GaleFighterView = app.arena.fighters[0]
	# Dale (Legends): one hand-painted 256 page, no recolour mask; the face comes from the atlas.
	var page: Texture2D = ignis_view.material.get_shader_parameter("albedo_px")
	check(ignis_view.material.get_shader_parameter("pixelated") == true and page != null and page.get_width() == 256, "Dale uses his hand-painted 256 Legends page")
	check(ignis_view.material.get_shader_parameter("face_px") != null, "Dale shows expressions from his face atlas")
	# Validate animation sync with startup/active/recovery, freeze, cancel, side switch and round reset
	app.fighter1 = "kaze"
	app.fighter2 = "volt"
	app.mode = "versus"
	app.start_match()
	check(app.screen == "playing", "match starts from selection")
	app.sim.countdown = 0
	app.sim.p1.x = -0.5
	app.sim.p2.x = 0.5
	app.sim.step(attack_input("light"), GaleCombat.idle_input())
	app.arena.render(app.sim, 1.0 / 60.0)
	var kaze_view: GaleFighterView = app.arena.fighters[0]
	var t_startup := kaze_view.current_anim_time
	check(kaze_view.current_clip == "light_1" and t_startup >= 0.0, "attack startup selects light_1 clip")
	app.sim.freeze = 5
	var clock_before: float = app.arena.clock
	app.arena.render(app.sim, 1.0 / 60.0)
	check(is_equal_approx(app.arena.clock, clock_before) and is_equal_approx(kaze_view.current_anim_time, t_startup), "hitstop/super freeze pauses animation progression")
	app.sim.freeze = 0
	advance(app.sim, 5)
	app.arena.render(app.sim, 1.0 / 60.0)
	check(app.sim.p1.connected, "attack connects for cancel test")
	app.sim.step(attack_input("heavy"), GaleCombat.idle_input())
	# Hitstop buffers the cancel; animation must stay frozen until simulation resumes.
	advance(app.sim, app.sim.freeze + 1)
	app.arena.render(app.sim, 1.0 / 60.0)
	check(kaze_view.current_clip == "heavy" and kaze_view.current_anim_time < 0.05, "buffered cancel starts heavy immediately after hitstop")
	# Side switch facing test
	app.sim.p1.action = "idle"
	app.sim.p1.x = 2.0
	app.sim.p2.x = -2.0
	app.sim.step(GaleCombat.idle_input(), GaleCombat.idle_input())
	app.arena.render(app.sim, 1.0 / 60.0)
	check(app.sim.p1.facing < 0 and kaze_view.basis.determinant() < 0.0, "side switch mirrors the Legends fighter like a 2.5D fighter")
	# Round reset animation test
	app.sim.next_round()
	app.arena.render(app.sim, 1.0 / 60.0)
	check(kaze_view.current_clip == "idle" and app.sim.p1.facing > 0, "round reset restores idle clip and default facing")
	# Move list modal test from pause
	app.pause_match()
	var frozen_timer: float = app.sim.remaining
	await physics_frame
	check(app.screen == "paused" and app.sim.remaining == frozen_timer, "pause stops combat")
	app.show_moves()
	check(is_instance_valid(app.modal), "move list modal opens with GDD v0.9 attack sheets")
	app.close_modal()
	app.resume_match()
	app.sim.winner = 1
	app.show_outcome()
	app.start_match()
	check(app.sim.winner == 0 and app.screen == "playing", "restart discards previous outcome")
	app.show_menu()
	await process_frame
	app.queue_free()
	await process_frame
	print("GODOT TESTS: %d checks, %d failures" % [checks, failures])
	quit(1 if failures > 0 else 0)
