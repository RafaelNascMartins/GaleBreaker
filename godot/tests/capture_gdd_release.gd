extends SceneTree

var app: Node
var output := ""

func _initialize() -> void: call_deferred("capture")

func settle() -> void:
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw

func save(name: String) -> void:
	await settle()
	root.get_texture().get_image().save_png(output+"/"+name+".png")

func capture() -> void:
	output=ProjectSettings.globalize_path("res://../art-source/previews/gdd-build")
	DirAccess.make_dir_recursive_absolute(output)
	app=load("res://scenes/main.tscn").instantiate()
	root.add_child(app)
	await settle()
	app.prefs.file_path="user://capture-gdd.cfg"
	app.set_process(false);app.set_physics_process(false)
	app.show_menu()
	for i in 90: app.arena.render(app.sim,GaleCombat.DT)
	await save("menu")
	app.show_menu(true)
	await save("selection")
	app.show_settings()
	await save("settings")
	app.close_modal();app.show_menu()
	app.skill_target_player=1;app.skill_target_fighter="volt";app.show_skills()
	await save("skills-p2")
	app.close_modal()
	for stage:String in GaleData.STAGES:
		app.mode="versus";app.stage=stage
		app.fighter1="kaze" if stage=="zephyr_dojo" else "ignis" if stage=="molten_forge" else "volt"
		app.fighter2="tophia"
		app.start_match();app.sim.countdown=0;app.sim.banner_frames=0
		app.sim.p1.x=-1.5;app.sim.p2.x=1.5;app.update_hud()
		for i in 90:app.arena.render(app.sim,GaleCombat.DT)
		await save(stage)
		if stage=="zephyr_dojo":
			app.pause_match();await save("pause");app.resume_match()
		app.sim.arena_cycle.clock=850;app.arena.render(app.sim,GaleCombat.DT)
		await save(stage+"-warning")
	app.stage="zephyr_dojo";app.fighter1="kaze";app.start_tutorial()
	for i in 45:app.arena.render(app.sim,GaleCombat.DT)
	await save("tutorial")
	app.show_training_tools()
	await save("training")
	app.close_modal();app.show_menu();app.mode="arcade";app.arcade_index=4;app.show_arcade_intro()
	await save("arcade-intro")
	app.close_modal();app.screen="playing";app.sim.winner=1;app.sim.wins=[2,0];app.sim.countdown=0;app.sim.banner_frames=0;app.update_hud();app.show_outcome()
	for i in 45:app.arena.render(app.sim,GaleCombat.DT)
	await save("arcade-ending")
	DirAccess.remove_absolute(ProjectSettings.globalize_path(app.prefs.file_path))
	print("GDD CAPTURE COMPLETE")
	print("DRAW CALLS: ",Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME))
	print("OBJECTS: ",Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME))
	quit()
