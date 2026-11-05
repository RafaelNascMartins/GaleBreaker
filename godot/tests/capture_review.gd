extends SceneTree
## Player-eye review sheets of the Legends Babuin, captured from the real game (training mode,
## Babuin vs Babuin, the fight camera as the player sees it at 1280x720). The sim is stepped here
## one frame at a time so every captured frame is a real gameplay frame. Writes to <out_dir>:
##   review_screen.png  one full game frame (true on-screen size)
##   review_idle.png    the idle loop (P1 on top, P2 below), a tile every 4 frames
##   review_chain.png   P1 plays J1 -> J2 -> J3 into P2, every 2 frames
##   review_faces.png   each combat expression on P1 and P2, at screen size and zoomed
## godot --path godot --script res://tests/capture_review.gd -- <out_dir>

const TILE := Vector2i(200, 260)
var out_dir := "res://tests/visual-polish"
var app: Node

func _initialize() -> void:
	call_deferred("capture")

func frame() -> void:
	await process_frame
	await RenderingServer.frame_post_draw

func step(input1: Dictionary = GaleCombat.idle_input()) -> void:
	app.sim.step(input1, GaleCombat.idle_input())
	await frame()

func crop(img: Image, view: GaleFighterView) -> Image:
	var cam: Camera3D = root.get_viewport().get_camera_3d()
	var top := cam.unproject_position(view.global_position + Vector3(0, 2.2, 0))
	var feet := cam.unproject_position(view.global_position + Vector3(0, -0.05, 0))
	var h := maxi(8, int(feet.y - top.y))
	var w := int(h * TILE.x / float(TILE.y))  # about 1.7 m wide around the fighter
	var region := img.get_region(Rect2i(Vector2i(int(feet.x) - w / 2, int(top.y)), Vector2i(w, h)))
	region.resize(TILE.x, TILE.y, Image.INTERPOLATE_NEAREST)
	return region

func sheet(tiles: Array, cols: int, path: String) -> void:
	var rows := int(ceil(tiles.size() / float(cols)))
	var out := Image.create(TILE.x * cols, TILE.y * rows, false, Image.FORMAT_RGBA8)
	out.fill(Color("1b1b1b"))
	for i in tiles.size():
		out.blit_rect(tiles[i], Rect2i(Vector2i.ZERO, TILE), Vector2i((i % cols) * TILE.x, (i / cols) * TILE.y))
	out.save_png(path)

func capture() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() > 0:
		out_dir = args[0]
	DirAccess.make_dir_recursive_absolute(out_dir)
	root.size = Vector2i(1280, 720)
	app = load("res://scenes/main.tscn").instantiate()
	root.add_child(app)
	for i in 5:
		await frame()
	app.mode = "training"
	app.fighter1 = "kaze"
	app.fighter2 = "kaze"
	app.start_match()
	if "--outfit" in args:
		var outfit := int(args[args.find("--outfit") + 1])
		for view: GaleFighterView in app.arena.fighters:
			view.apply_palette(outfit)
	app.sim.countdown = 0
	app.sim.p1.x = -1.8
	app.sim.p2.x = 1.8
	app.screen = "review"  # main stops stepping the sim; it still renders every frame
	for i in 30:
		await step()
	var p1: GaleFighterView = app.arena.fighters[0]
	var p2: GaleFighterView = app.arena.fighters[1]
	root.get_texture().get_image().save_png(out_dir + "/review_screen.png")

	var top: Array = []
	var bottom: Array = []
	var idle_frames := int(GaleAnimTiming.state_sec("kaze", "idle") * 60.0)
	for f in idle_frames:
		await step()
		if f % 4 == 0:
			var img := root.get_texture().get_image()
			top.append(crop(img, p1))
			bottom.append(crop(img, p2))
	sheet(top + bottom, top.size(), out_dir + "/review_idle.png")

	app.sim.p1.x = -0.9
	app.sim.p2.x = 0.9
	for i in 10:
		await step()
	var tiles: Array = []
	for f in 90:
		var input := GaleCombat.idle_input()
		if f % 5 == 0 and f < 60:
			input.attack = "light"
		await step(input)
		if f % 2 == 0:
			tiles.append(crop(root.get_texture().get_image(), p1))
	sheet(tiles, 15, out_dir + "/review_chain.png")

	app.sim.p1.x = -1.8
	app.sim.p2.x = 1.8
	for i in 40:
		await step()
	tiles = []
	var zoom: Array = []
	for expression in GaleFighterView.Face.values():
		for view: GaleFighterView in [p1, p2]:
			view.set_face(expression)
		await frame()
		var img := root.get_texture().get_image()
		for view: GaleFighterView in [p1, p2]:
			var t := crop(img, view)
			tiles.append(t)
			var head := t.get_region(Rect2i(Vector2i(50, 0), Vector2i(100, 130)))
			head.resize(TILE.x, TILE.y, Image.INTERPOLATE_NEAREST)
			zoom.append(head)
	sheet(tiles + zoom, 16, out_dir + "/review_faces.png")
	print("REVIEW CAPTURE COMPLETE")
	quit()
