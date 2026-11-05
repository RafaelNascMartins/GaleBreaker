extends SceneTree
## Frames of the training garage from the real game: the camera turn from the beach menu and
## the gate menu once it has stopped. Writes garage_turn.png (strip) and garage_menu.png.
## godot --path godot --script res://tests/capture_garage.gd -- <out_dir>

var out_dir := "res://tests/visual-polish"

func _initialize() -> void:
	call_deferred("capture")

func frame() -> void:
	await process_frame
	await RenderingServer.frame_post_draw

func capture() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() > 0:
		out_dir = args[0]
	DirAccess.make_dir_recursive_absolute(out_dir)
	root.size = Vector2i(1280, 720)
	var app: Node = load("res://scenes/main.tscn").instantiate()
	root.add_child(app)
	for i in 30:
		await frame()
	root.get_texture().get_image().save_png(out_dir.path_join("menu.png"))
	app.open_garage()
	var strip := Image.create(320 * 5, 180, false, Image.FORMAT_RGBA8)
	var shot := 0
	for i in 110:
		await frame()
		if i % 20 == 0 and shot < 5:
			var img := root.get_texture().get_image()
			img.convert(Image.FORMAT_RGBA8)
			img.resize(320, 180)
			strip.blit_rect(img, Rect2i(0, 0, 320, 180), Vector2i(shot * 320, 0))
			shot += 1
	strip.save_png(out_dir.path_join("garage_turn.png"))
	var guard := 0
	while not app.arena.garage_open() and guard < 600:
		await frame()
		guard += 1
	for i in 20:
		await frame()
	root.get_texture().get_image().save_png(out_dir.path_join("garage_menu.png"))
	print("garage open: ", app.arena.garage_open(), " widgets: ", app.garage_ui.widgets.size())
	quit()
