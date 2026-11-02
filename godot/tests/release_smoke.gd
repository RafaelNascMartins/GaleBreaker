extends SceneTree

func _initialize() -> void: call_deferred("run")

func run() -> void:
	var app:Node=load("res://scenes/main.tscn").instantiate()
	root.add_child(app)
	await process_frame
	app.set_process(false);app.set_physics_process(false)
	app.prefs.file_path="user://release-smoke.cfg"
	for stage:String in GaleData.STAGES:
		for id:String in GaleData.IDS:
			app.stage=stage;app.fighter1=id;app.fighter2="ignis" if id!="ignis" else "kaze";app.mode="versus"
			app.start_match();app.sim.countdown=0
			for kind:String in ["light","heavy","elemental","ultimate"]:
				app.sim.freeze=0;app.sim.p1.action="idle";app.sim.p1.meter=100
				app.sim.attack(app.sim.p1,kind,false)
				for frame in 90:
					app.sim.step(GaleCombat.idle_input(),GaleCombat.idle_input())
					app.arena.render(app.sim,GaleCombat.DT)
			await process_frame
			print("RELEASE SMOKE: ",stage," / ",id)
	app.start_tutorial();app.show_training_tools();app.close_modal();app.show_menu();app.show_settings()
	await process_frame
	app.close_modal();app.show_menu()
	DirAccess.remove_absolute(ProjectSettings.globalize_path(app.prefs.file_path))
	print("RELEASE SMOKE COMPLETE: 12 arena/fighter combinations, 48 attacks and native menus")
	quit()
