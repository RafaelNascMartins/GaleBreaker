extends SceneTree
## Renders for the GDD (docs/gdd/build_gdd.py), from the real game renderer on a transparent
## background: every outfit of the Legends fighters at rest, and each one's signature moves
## frozen on the contact frame with the matching face.
## godot --path godot --script res://tests/capture_gdd.gd -- <out_dir>

const FIGHTERS := ["kaze", "ignis", "tophia", "volt"]
# clip, frame (60 fps, the contact / pose key), face
const POSES := {
	"kaze": [["light_3", 10, 6], ["heavy_2", 11, 2], ["elemental", 14, 7], ["ultimate", 24, 10], ["victory", 32, 5]],
	"ignis": [["light_3", 17, 2], ["heavy", 9, 6], ["elemental", 19, 2], ["ultimate", 28, 10], ["victory", 12, 5]],
	"tophia": [["light_2", 9, 6], ["heavy", 13, 10], ["elemental", 7, 7], ["ultimate", 31, 2], ["victory", 30, 5]],
	"volt": [["light_2", 14, 7], ["heavy", 22, 7], ["down_punch", 15, 11], ["ultimate", 46, 2], ["victory", 30, 11]],
}

var vp: SubViewport

func _initialize() -> void:
	call_deferred("capture")

func settle() -> void:
	for i in 3:
		await process_frame
	await RenderingServer.frame_post_draw

func shot(view: Node3D, path: String) -> void:
	await settle()
	var img := vp.get_texture().get_image()
	# crop to the figure (alpha) with a margin, so the page can lay it out freely
	var used := img.get_used_rect()
	if used.size.x > 0:
		used = used.grow(12).intersection(Rect2i(Vector2i.ZERO, img.get_size()))
		img = img.get_region(used)
	img.save_png(path)

func capture() -> void:
	var args := OS.get_cmdline_user_args()
	var out_dir := args[0] if args.size() > 0 else ProjectSettings.globalize_path("res://").path_join("../docs/gdd/assets/renders").simplify_path()
	DirAccess.make_dir_recursive_absolute(out_dir)
	vp = SubViewport.new()
	vp.size = Vector2i(1400, 1700)
	vp.transparent_bg = true
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	vp.own_world_3d = true
	root.add_child(vp)
	var data := GaleData.new()
	var world := Node3D.new()
	vp.add_child(world)
	var env := WorldEnvironment.new()
	env.environment = Environment.new()
	env.environment.background_mode = Environment.BG_CLEAR_COLOR
	env.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.environment.ambient_light_color = Color.WHITE
	env.environment.ambient_light_energy = 0.8
	world.add_child(env)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-40, 30, 0)
	world.add_child(sun)
	var camera := Camera3D.new()
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	world.add_child(camera)
	for id: String in FIGHTERS:
		var catalog := GaleVisualCatalog.load_for(id)
		for p in catalog.palettes.size():
			var view := GaleFighterView.new()
			world.add_child(view)
			view.build(data, id, p)
			view.aura.visible = false
			view.rotation.y = 0.0
			var looks := [["idle", 0, 0, 205.0]]
			if p == 0:
				looks.append(["frente", 0, 0, 180.0])
				for pose: Array in POSES[id]:
					looks.append([pose[0], pose[1], pose[2], 240.0])
			for l: Array in looks:
				view.play_clip("idle" if l[0] == "frente" else String(l[0]), float(l[1]) / 60.0)
				view.set_face(int(l[2]))
				var yaw := deg_to_rad(float(l[3]))
				camera.size = 2.9
				camera.position = Vector3(sin(yaw) * 6.0, 1.7, cos(yaw) * 6.0)
				camera.look_at(Vector3(0, 1.15, 0))
				var name := "%s_%d" % [id, p] if l[0] == "idle" else "%s_%s" % [id, l[0]]
				await shot(view, out_dir.path_join(name + ".png"))
			view.queue_free()
			await settle()
	print("gdd renders done")
	quit()
