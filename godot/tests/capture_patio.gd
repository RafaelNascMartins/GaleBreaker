extends SceneTree
## The Arcade select on the village patio, from the real game: patio.png after the fade.
## godot --path godot --script res://tests/capture_patio.gd -- <out_dir>

func _initialize() -> void:
	call_deferred("capture")

func frame() -> void:
	await process_frame
	await RenderingServer.frame_post_draw

func capture() -> void:
	var args := OS.get_cmdline_user_args()
	var out_dir := args[0] if args.size() > 0 else "res://tests/visual-polish"
	DirAccess.make_dir_recursive_absolute(out_dir)
	root.size = Vector2i(1280, 720)
	var app: Node = load("res://scenes/main.tscn").instantiate()
	root.add_child(app)
	for i in 30:
		await frame()
	app.open_arcade_select()
	var guard := 0
	while (app.patio_ui == null or not app.patio_ui.interactive) and guard < 900:
		await frame()
		guard += 1
	for i in 20:
		await frame()
	root.get_texture().get_image().save_png(out_dir.path_join("patio.png"))
	print("patio interactive: ", app.patio_ui != null and app.patio_ui.interactive)
	quit()
