extends SceneTree

func _initialize() -> void:
	call_deferred("capture")

func settle(frames: int = 5) -> void:
	for i in frames:
		await process_frame
	await RenderingServer.frame_post_draw

func capture() -> void:
	var app: Node = load("res://scenes/main.tscn").instantiate()
	root.add_child(app)
	await settle()
	root.get_texture().get_image().save_png("res://tests/menu.png")
	app.show_settings()
	await settle()
	root.get_texture().get_image().save_png("res://tests/settings.png")
	app.close_modal()
	app.mode = "training"
	app.start_match()
	app.sim.countdown = 0
	app.sim.p1.x = -1.2
	app.sim.p2.x = 1.2
	app.sim.announce("GALE BREAKER — GODOT", 600)
	await settle(30)
	root.get_texture().get_image().save_png("res://tests/combat.png")
	app.pause_match()
	await settle()
	root.get_texture().get_image().save_png("res://tests/pause.png")
	app.show_menu()
	app.show_skills()
	await settle()
	root.get_texture().get_image().save_png("res://tests/skills.png")
	print("CAPTURE COMPLETE")
	quit()
