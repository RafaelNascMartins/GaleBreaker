extends SceneTree

var failures := 0
var checks := 0
var data := GaleData.new()

func _initialize() -> void: call_deferred("run")

func check(ok: bool, text: String) -> void:
	checks += 1
	if ok: print("PASS: "+text)
	else:
		failures += 1
		push_error("FAIL: "+text)

func fresh(id: String, opponent: String = "kaze") -> GaleCombat:
	var sim := GaleCombat.new(data)
	sim.start(id,opponent,"zephyr_dojo","versus")
	sim.countdown = 0
	sim.hazards.clear()
	sim.p1.meter = 100
	sim.p2.meter = 100
	return sim

func advance(sim: GaleCombat, count: int, a: Dictionary = {}, b: Dictionary = {}) -> void:
	for i in count:
		sim.step(GaleCombat.idle_input() if a.is_empty() else a,GaleCombat.idle_input() if b.is_empty() else b)

func run() -> void:
	var sim := fresh("volt")
	sim.p1.x=-3.0;sim.p2.x=3.0
	sim.attack(sim.p1,"light",false)
	advance(sim,10)
	check(sim.p2.hp==sim.p2.max_hp and sim.attacks.items.size()==1,"Volt bolt travels before hitting a distant target")
	advance(sim,28)
	check(sim.p2.hp<sim.p2.max_hp,"projectile can hit after its owner leaves active animation")
	sim=fresh("volt")
	sim.p1.x=-3;sim.p2.x=3
	sim.attack(sim.p1,"light",false)
	var guard:=GaleCombat.idle_input();guard.guard=true
	advance(sim,55,{},guard)
	check(sim.p2.blocks==1 and sim.p2.hp>sim.p2.max_hp-20,"blocking a traveling projectile applies chip once")
	sim=fresh("volt")
	sim.attack(sim.p1,"light",false)
	var jump:=GaleCombat.idle_input();jump.jump=true
	advance(sim,1,{},jump)
	advance(sim,34)
	check(sim.p2.hp==sim.p2.max_hp,"a jumped projectile does not damage through its visual trail")
	sim=fresh("volt")
	sim.p1.x=-3;sim.p2.x=3
	sim.attack(sim.p1,"light",false)
	for i in 60:
		var input:=GaleCombat.idle_input()
		for e:Dictionary in sim.attacks.items:
			if e.delay<=0 and absf(float(e.x)-float(sim.p2.x))<1.1: input.parry=true
		sim.step(GaleCombat.idle_input(),input)
	check(sim.p2.parries==1 and sim.p2.hp==sim.p2.max_hp,"a correctly timed parry consumes the projectile")
	sim=fresh("volt","volt")
	sim.p1.x=-3;sim.p2.x=3
	sim.attack(sim.p1,"light",false);sim.attack(sim.p2,"light",false)
	advance(sim,55)
	check(sim.p1.hp==sim.p1.max_hp and sim.p2.hp==sim.p2.max_hp and sim.attacks.items.is_empty(),"opposed projectiles clash and disappear before hitting players")
	sim=fresh("volt")
	sim.attack(sim.p1,"light",false)
	var original:int=sim.attacks.items[0].move.damage
	sim.p1.move.damage=9999
	check(sim.attacks.items[0].move.damage==original,"fired attacks retain an independent move snapshot")
	sim.next_round()
	check(sim.attacks.items.is_empty(),"round reset removes all pending and traveling attacks")
	sim=fresh("kaze")
	sim.attack(sim.p1,"ultimate",false)
	sim.p1.action="hitstun";sim.p1.frames=30
	sim.freeze=0
	advance(sim,2)
	check(sim.attacks.items.is_empty(),"interrupting startup cancels the telegraphed ultimate")
	sim=fresh("kaze")
	sim.p1.x=0;sim.p2.x=1.9
	sim.attack(sim.p1,"ultimate",false)
	advance(sim,170)
	check(sim.p1.combo>=3 and sim.p2.hp<sim.p2.max_hp-180,"fixed tornado produces successive real impacts and a finisher")
	sim=fresh("kaze")
	sim.p1.x=0;sim.p2.x=1.9
	sim.attack(sim.p1,"ultimate",false)
	var flee:=GaleCombat.idle_input();flee.axis=1.0
	advance(sim,150,{},flee)
	check(sim.p2.hp==sim.p2.max_hp,"leaving the tornado warning avoids its damage")
	sim=fresh("tophia")
	sim.attack(sim.p1,"elemental",false)
	check(sim.attacks.items.size()==3 and sim.attacks.items[0].delay<sim.attacks.items[1].delay and sim.attacks.items[1].delay<sim.attacks.items[2].delay,"stone spires have separate positions and announced impact times")
	check(data.move("tophia","heavy",[]).armorHits==0,"Tophia armor is visual and does not grant automatic super armor")
	sim=fresh("ignis")
	sim.stage_id="molten_forge";sim.arena_cycle.reset(sim.stage_id)
	sim.p1.x=-3;sim.p2.x=5
	sim.arena_cycle.clock=809
	advance(sim,1)
	check(sim.arena_cycle.visible_now() and sim.p1.hp==sim.p1.max_hp,"arena danger is announced before it can damage players")
	sim.arena_cycle.clock=899
	advance(sim,1)
	check(sim.p1.hp<sim.p1.max_hp,"forge eruption damages inside the announced footprint")
	sim=fresh("ignis");sim.mode="training";advance(sim,950)
	check(sim.arena_cycle.clock==0,"training disables disruptive arena events")
	sim=fresh("kaze");sim.stage_id="molten_forge";sim.arena_cycle.reset(sim.stage_id)
	sim.p1.x=-3;sim.p1.y=2;sim.p1.grounded=false;sim.arena_cycle.clock=899
	advance(sim,1)
	check(sim.p1.hp==sim.p1.max_hp,"jumping above a warned floor eruption avoids damage")
	sim=fresh("volt")
	sim.p1.x=0;sim.p2.x=4
	sim.attack(sim.p1,"ultimate",false)
	check(sim.attacks.items[0].kind=="beam" and sim.attacks.items[0].delay>=40,"Volt beam announces its fixed line before firing")
	advance(sim,100)
	check(sim.p2.hp<sim.p2.max_hp-250,"charged beam hits across its actual fixed line")
	for id:String in GaleData.IDS:
		sim=fresh(id,"ignis" if id!="ignis" else "kaze")
		sim.mode="training"
		var tutorial:=GaleTutorial.new();tutorial.prepare(sim)
		for frame in 2400:
			var input:=GaleCombat.idle_input()
			match tutorial.step:
				0: input.axis=-1.0
				1: input.jump=true
				2: input.crouch=true
				3: input.guard=true
				4: if frame%12==0: input.attack="light"
				5: if frame%30==0: input.attack="heavy"
				6: if frame%60==0: input.attack="elemental"
				7: if frame%90==0: input.attack="ultimate"
			sim.step(input,tutorial.dummy_input(sim))
			tutorial.update(sim,input)
			if tutorial.complete: break
		check(tutorial.complete,id+" can complete all eight tutorial objectives through simulation")
	var prefs:=GalePreferences.new()
	for action:String in GalePreferences.ACTIONS:
		var events:=GalePreferences.pad_events(action,7)
		check(not events.is_empty() and events[0].device==7,"gamepad "+action+" binds only its assigned device")
	prefs.file_path="user://gdd-regression.cfg"
	prefs.skills.kaze=["kaze_combo_2"]
	prefs.skills2.kaze=["kaze_def_1"]
	prefs.shake_strength=0.0;prefs.flashes=false
	prefs.arcade_run={"fighter":"kaze","index":3,"palette":1,"skills":["kaze_combo_2"]}
	prefs.save_to_disk()
	var restored:=GalePreferences.new();restored.file_path=prefs.file_path;restored.load_from_disk(data)
	check(restored.skills.kaze!=restored.skills2.kaze,"mirror-match loadouts persist independently for P1 and P2")
	check(restored.arcade_run.index==3 and not restored.flashes and restored.shake_strength==0.0,"Arcade progress and accessibility settings persist")
	DirAccess.remove_absolute(ProjectSettings.globalize_path(prefs.file_path))
	var app:Node=load("res://scenes/main.tscn").instantiate();root.add_child(app)
	await process_frame
	app.prefs.file_path="user://gdd-app-regression.cfg"
	app.start_tutorial()
	check(app.tutorial!=null and is_instance_valid(app.tutorial_label),"guided tutorial starts from a real menu scene")
	app.show_training_tools()
	check(app.screen=="paused" and is_instance_valid(app.modal),"training laboratory pauses and exposes dummy configuration")
	app.show_menu();app.show_settings()
	check(app.modal.find_children("*","ScrollContainer",true,false).size()>0,"settings fit inside a scrollable panel")
	app.close_modal()
	app.mode="versus";app.fighter1="kaze";app.fighter2="kaze"
	app.prefs.skills.kaze=["kaze_combo_2"]
	app.prefs.skills2.kaze=["kaze_def_1"]
	app.start_match()
	check(app.sim.p1.skills!=app.sim.p2.skills,"a real mirror match uses separate player loadouts")
	app.mode="arcade";app.arcade_index=2;app.show_arcade_intro()
	check(app.screen=="intro" and app.sim.countdown>0,"Arcade introduction holds the match before countdown")
	app.show_menu();app.resume_arcade()
	check(app.arcade_index==2 and app.screen=="intro","continue restores the recorded Arcade stage")
	app.close_modal();app.sim.winner=1;app.arcade_index=4;app.show_outcome()
	check(app.prefs.arcade_run.is_empty(),"finishing the tower clears its continue checkpoint")
	app.close_modal();app.queue_free();await process_frame
	DirAccess.remove_absolute(ProjectSettings.globalize_path("user://gdd-app-regression.cfg"))
	var sound := GaleAudio.new()
	root.add_child(sound)
	check(sound.samples.size() == GaleAudio.SAMPLE_PATHS.size(), "every recorded sound effect and voice line loads")
	check(sound.menu_music is AudioStreamMP3 and (sound.menu_music as AudioStreamMP3).loop, "menu music loads and loops")
	check(sound.fight_music.size() == GaleAudio.FIGHT_MUSIC_PATHS.size(), "all fight tracks load")
	sound.set_music("zephyr_dojo", true)
	var first_track: AudioStream = sound.music.stream
	sound.set_music("zephyr_dojo", false)
	sound.set_music("zephyr_dojo", true)
	check(first_track in sound.fight_music and sound.music.stream == first_track, "a match keeps its fight track through pause and resume")
	sound.play_menu_music()
	sound.set_music("zephyr_dojo", true)
	check(sound.music.stream in sound.fight_music and sound.music.stream != first_track, "the next match draws a different fight track")
	sound.music.stop()
	sound.play("", "kaze", "light_2")
	var last := sound.players[(sound.cursor - 1 + sound.players.size()) % sound.players.size()]
	check(last.stream == sound.samples["kaze_light_2"], "Kaze J2 hit uses its recorded punch")
	check(float(GaleCombat.COUNTDOWN_FRAMES) / 60.0 >= 3.4, "countdown leaves room for the full announcer line")
	var crouch_sim := fresh("kaze")
	var crouch_walk := GaleCombat.idle_input()
	crouch_walk.crouch = true
	crouch_walk.axis = 1.0
	var crouch_x := float(crouch_sim.p1.x)
	advance(crouch_sim, 30, crouch_walk)
	check(is_equal_approx(float(crouch_sim.p1.x), crouch_x) and crouch_sim.p1.crouch, "crouching fighters cannot walk")
	for id: String in GaleData.IDS:
		var walk_rate := float(data.fighter(id).walkSpeed) * GaleAnimTiming.state_sec(id, "walk") / GaleAnimTiming.stride(id)
		check(walk_rate <= 1.35, id + " walk clip plays near its authored speed (%.2fx)" % walk_rate)
	for stage: String in GaleData.STAGES:
		var stage_scene: Node3D = (load("res://scenes/stages/%s.tscn" % stage) as PackedScene).instantiate()
		var left := stage_scene.find_children("Blocker_L*", "MeshInstance3D", true, false)
		var right := stage_scene.find_children("Blocker_R*", "MeshInstance3D", true, false)
		check(left.size() == 1 and right.size() == 1, stage + " has an obstacle in each corner")
		if left.size() == 1 and right.size() == 1:
			var l_box: AABB = (left[0] as MeshInstance3D).get_aabb()
			var r_box: AABB = (right[0] as MeshInstance3D).get_aabb()
			check(l_box.end.x <= -GaleCombat.EDGE - 0.2 and r_box.position.x >= GaleCombat.EDGE + 0.2, stage + " corner obstacles sit just beyond the walls")
		if stage == "storm_market":
			check(stage_scene.find_children("Crowd_*", "MeshInstance3D", true, false).size() >= 20, "bazaar corridor has a watching crowd")
		if stage == "molten_forge":
			check(stage_scene.find_children("Barrier_*", "MeshInstance3D", true, false).size() == 2, "forge precipice has a barrier on both sides")
		stage_scene.free()
	var menu_app: Node = load("res://scenes/main.tscn").instantiate()
	root.add_child(menu_app)
	await process_frame
	menu_app.prefs.file_path = "user://gdd-pause-regression.cfg"
	menu_app.mode = "versus"; menu_app.stage = "zephyr_dojo"
	menu_app.start_match()
	menu_app.pause_match()
	var pause_items: Array[String] = []
	for item: Node in menu_app.modal.find_children("*", "Button", true, false):
		pause_items.append(String((item as Button).text))
	check(pause_items == ["CONTINUAR", "REINICIAR PARTIDA", "OPÇÕES", "VOLTAR AO MENU"], "pause menu follows the concept without the move list (%s)" % [pause_items])
	menu_app.resume_match()
	menu_app.settings_tab = "controles"
	menu_app.listening = [1, 6]
	menu_app.show_settings()
	check(menu_app.listening == [1, 6], "redrawing the options keeps the key waiting to be remapped")
	menu_app.prefs.keys[0][0] = KEY_Z
	menu_app.restore_default_keys()
	check(menu_app.prefs.keys == GalePreferences.DEFAULT_KEYS and menu_app.listening.is_empty(), "restore defaults brings back the original keys")
	menu_app.close_settings()
	menu_app.settings_tab = "geral"
	menu_app.prefs.arcade_run = {}
	menu_app.show_menu()
	var menu_items: Array[String] = []
	for item: Node in menu_app.menu.find_children("*", "Button", true, false):
		menu_items.append(String((item as Button).text))
	check(menu_app.arena.menu_scene_active and menu_app.arena.stage_instance != null, "main menu shows the 3D beach scene")
	check(menu_items == ["ARCADE", "VERSUS LOCAL", "TREINO", "HABILIDADES", "OPÇÕES", "TUTORIAL", "SAIR"], "main menu follows the beach concept list (%s)" % [menu_items])
	menu_app.open_mode("versus")
	check(not menu_app.arena.menu_scene_active and menu_app.arena.fighters.size() == 2, "choosing a mode leaves the beach for the fighter preview")
	for strike: String in ["light_1", "light_2", "light_3", "heavy"]:
		check(sound.has_sample("kaze_" + strike), "Babuin " + strike + " has a recorded strike sound")
	check(menu_app.strike_sound({"type": "light", "chain_step": 3}) == "light_3" and menu_app.strike_sound({"type": "heavy"}) == "heavy" and menu_app.strike_sound({"type": "ultimate"}) == "", "strike sounds map J1-J3 and K only")
	check(GaleVisualCatalog.load_for("kaze").display_name == "Babuin" and String(data.fighter("kaze").name) == "Babuin", "Kaze is presented as Babuin while keeping its internal id")
	var face_view := GaleFighterView.new()
	root.add_child(face_view)
	face_view.build(data, "kaze", 0)
	check(bool(face_view.material.get_shader_parameter("use_face")) and face_view.material.get_shader_parameter("face_tex") != null, "Babuin's flat face draws the expression atlas")
	var face_state := {"move": {"type": "light"}}
	check(face_view._face_for(face_state, "active", 1.0) == GaleFighterView.Face.SHOUT and face_view._face_for({"move": {"type": "ultimate"}}, "startup", 1.0) == GaleFighterView.Face.FOCUS, "attacks shout and specials focus")
	check(face_view._face_for({}, "hitstun", 1.0) == GaleFighterView.Face.HURT and face_view._face_for({}, "ko", 1.0) == GaleFighterView.Face.KO and face_view._face_for({}, "victory", 1.0) == GaleFighterView.Face.VICTORY and face_view._face_for({}, "guard", 1.0) == GaleFighterView.Face.EFFORT, "hurt, KO, victory and guard have their own faces")
	face_view.set_face(GaleFighterView.Face.HURT)
	check(is_equal_approx(float(face_view.material.get_shader_parameter("face_cell")), float(GaleFighterView.Face.HURT)), "changing expression picks the atlas cell")
	face_view.queue_free()
	# Options on the forest quest board.
	menu_app.set_process(false)
	menu_app.show_menu()
	var beach: Node = menu_app.arena.stage_instance
	check(beach.find_child("QuestBoardPanel", true, false) != null and beach.find_child("CamPath_0", true, false) != null and beach.find_child("BoardLook", true, false) != null, "beach scene has the forest quest board and the camera path")
	menu_app.open_board_settings()
	for i in 140:
		menu_app.arena.render(menu_app.sim, 1.0 / 60.0)
	await process_frame
	check(menu_app.arena.board_open() and menu_app.board_ui.interactive and menu_app.board_ui.widgets.size() >= 12, "choosing Opções flies into the clearing and the options are paper notes and ink drawings on the board")
	var muted_before: bool = menu_app.prefs.muted
	for i in menu_app.board_ui.widgets.size():
		if String(menu_app.board_ui.widgets[i].kind) == "toggle":
			menu_app.board_ui.activate(i)
			break
	check(menu_app.prefs.muted != muted_before, "circling the other answer on the board changes the option")
	menu_app.board_ui.switch_tab("controles")
	var keycaps := 0
	for w: Dictionary in menu_app.board_ui.widgets:
		if String(w.kind) == "button" and (w.rect as Rect2).size.y < 0.07:
			keycaps += 1
	check(keycaps == 22, "the controls tab circles a key per action and player")
	menu_app.board_ui.switch_tab("geral")
	menu_app.close_settings()
	for i in 140:
		menu_app.arena.render(menu_app.sim, 1.0 / 60.0)
	await process_frame
	check(not menu_app.arena.board_open() and menu_app.menu.visible and not is_instance_valid(menu_app.modal), "leaving the board flies back and restores the beach menu")
	# Arcade select on the beach.
	menu_app.open_arcade_select()
	check(menu_app.modal.has_meta("arcade_select") and menu_app.arena.select_view != null and menu_app.arena.select_view.fighter_id == menu_app.fighter1, "Arcade opens the beach fighter select")
	menu_app.choose_arcade_fighter("ignis")
	menu_app.choose_arcade_outfit(2)
	check(menu_app.fighter1 == "ignis" and menu_app.palette1 == 2 and menu_app.arena.select_view.fighter_id == "ignis", "choosing a fighter and outfit updates the beach model")
	menu_app.leave_arcade_select()
	check(menu_app.arena.select_view == null and menu_app.menu.visible and not menu_app.in_arcade_select, "leaving the select returns to the beach menu")
	menu_app.queue_free()
	await process_frame
	sound.queue_free()

	print("GDD TESTS: %d checks, %d failures"%[checks,failures])
	quit(1 if failures>0 else 0)
