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
	sim.p1.x=-4;sim.p2.x=5
	sim.arena_cycle.clock=809
	advance(sim,1)
	check(sim.arena_cycle.visible_now() and sim.p1.hp==sim.p1.max_hp,"arena danger is announced before it can damage players")
	sim.arena_cycle.clock=899
	advance(sim,1)
	check(sim.p1.hp<sim.p1.max_hp,"forge eruption damages inside the announced footprint")
	sim=fresh("ignis");sim.mode="training";advance(sim,950)
	check(sim.arena_cycle.clock==0,"training disables disruptive arena events")
	sim=fresh("kaze");sim.stage_id="molten_forge";sim.arena_cycle.reset(sim.stage_id)
	sim.p1.x=-4;sim.p1.y=2;sim.p1.grounded=false;sim.arena_cycle.clock=899
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
	print("GDD TESTS: %d checks, %d failures"%[checks,failures])
	quit(1 if failures>0 else 0)
