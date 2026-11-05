extends SceneTree
## Screenshots for the repository README, from the real game (1280x720):
## menu, garage (Treino), patio (Arcade), options board and a fight on each arena.
## godot --path godot --script res://tests/capture_readme.gd -- <out_dir>

var out_dir := "res://../docs/readme"

func _initialize() -> void:
	call_deferred("capture")

func frame() -> void:
	await process_frame
	await RenderingServer.frame_post_draw

func frames(n: int) -> void:
	for i in n:
		await frame()

func shot(name: String) -> void:
	root.get_texture().get_image().save_png(out_dir.path_join(name + ".png"))

func capture() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() > 0:
		out_dir = args[0]
	DirAccess.make_dir_recursive_absolute(out_dir)
	root.size = Vector2i(1280, 720)
	var app: Node = load("res://scenes/main.tscn").instantiate()
	root.add_child(app)
	await frames(40)
	shot("menu")
	app.open_garage()
	var guard := 0
	while not app.arena.garage_open() and guard < 600:
		await frame()
		guard += 1
	await frames(20)
	shot("treino")
	app.close_garage()
	await frames(160)
	app.open_arcade_select()
	guard = 0
	while (app.patio_ui == null or not app.patio_ui.interactive) and guard < 900:
		await frame()
		guard += 1
	await frames(20)
	shot("arcade")
	app.leave_arcade_select()
	await frames(60)
	app.open_board_settings()
	await frames(200)
	shot("opcoes")
	app.close_settings()
	await frames(120)
	for stage: String in ["zephyr_dojo", "molten_forge", "storm_market"]:
		app.close_modal()
		app.mode = "versus"
		app.fighter1 = "kaze"
		app.fighter2 = "ignis"
		app.stage = stage
		app.start_match()
		app.sim.countdown = 0
		app.sim.p1.x = -0.9
		app.sim.p2.x = 0.9
		await frames(40)
		app.sim.banner = ""
		app.sim.banner_frames = 0
		# Dale throws the hammer (J3) at Babuin; the shot lands near the impact.
		var p2: Dictionary = app.sim.p2
		p2.chain = 3
		p2.chain_frames = 30
		app.sim.attack(p2, "light", false)
		await frames(17)
		shot("luta_" + stage)
	quit()
