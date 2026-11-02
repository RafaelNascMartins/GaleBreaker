extends SceneTree

func _initialize() -> void:
	call_deferred("capture")

func settle() -> void:
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw

func capture() -> void:
	var output := ProjectSettings.globalize_path("res://../art-source/previews")
	DirAccess.make_dir_recursive_absolute(output)
	var app: Node = load("res://scenes/main.tscn").instantiate()
	root.add_child(app)
	await settle()
	app.set_process(false)
	app.set_physics_process(false)
	for id: String in ["kaze", "ignis", "tophia", "volt"]:
		app.fighter1 = id
		app.fighter2 = "ignis" if id == "kaze" else "kaze"
		app.mode = "versus"
		app.start_match()
		app.sim.countdown = 0
		app.sim.p1.x = -1.15
		app.sim.p2.x = 1.15
		app.sim.hazards.clear()
		app.sim.banner_frames = 0
		app.update_hud()
		for frame in 90:
			app.arena.render(app.sim, 1.0 / 60.0)
		await settle()
		root.get_texture().get_image().save_png(output + "/combat-" + id + ".png")
		for kind: String in ["elemental", "ultimate"]:
			app.sim.p1.action = "active"
			app.sim.p1.move = app.data.move(id, kind, [])
			app.sim.p1.frames = 3
			app.sim.p1.phase_total = 8
			for frame in 8:
				app.arena.render(app.sim, 1.0 / 60.0)
			await settle()
			root.get_texture().get_image().save_png(output + "/" + id + "-" + kind + ".png")
	print("COMBAT POLISH CAPTURE COMPLETE")
	quit()
