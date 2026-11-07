extends SceneTree
## Side-view silhouettes of every attack on its contact frame (anim_timing.json), white on
## black, to compare pose shapes with references (docs/estudos/poses-de-ataque-e-game-feel.md).
## Each pixel is coloured by its depth from the side camera (heat map: near the camera red/yellow,
## far blue), so the near and far arm or leg read apart even when they overlap in the silhouette.
## godot --path godot --script res://tests/capture_silhouettes.gd -- <out_dir> [clip]

const CLIPS := ["light_1", "light_2", "light_3", "heavy", "heavy_2", "heavy_3", "elemental", "ultimate", "sweep", "down_punch", "air_punch"]

var vp: SubViewport

# Unshaded depth heat in each view, measured around the fighter's hips (the fighter steps toward
# the front camera in a lunge; a fixed range would paint everything red).
const HEAT := """
shader_type spatial;
render_mode unshaded, cull_disabled;
varying float depth;
uniform float centre = 6.0;   // camera-space depth of the fighter's hips this frame
void vertex() { depth = -(MODELVIEW_MATRIX * vec4(VERTEX, 1.0)).z; }
void fragment() {
	float t = clamp((centre + 0.55 - depth) / 1.1, 0.0, 1.0);   // 0 far, 1 near, around the hips
	vec3 c = mix(vec3(0.10, 0.20, 0.85), vec3(0.20, 0.85, 0.75), smoothstep(0.0, 0.4, t));
	c = mix(c, vec3(1.0, 0.85, 0.15), smoothstep(0.35, 0.7, t));
	c = mix(c, vec3(0.95, 0.15, 0.10), smoothstep(0.65, 1.0, t));
	ALBEDO = c;
}
"""

func _initialize() -> void:
	call_deferred("capture")

func settle() -> void:
	for i in 3:
		await process_frame
	await RenderingServer.frame_post_draw

func capture() -> void:
	var args := OS.get_cmdline_user_args()
	var out_dir: String = args[0]
	DirAccess.make_dir_recursive_absolute(out_dir)
	var timing: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/anim_timing.json"))
	vp = SubViewport.new()
	vp.size = Vector2i(700, 700)
	vp.transparent_bg = true
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	vp.own_world_3d = true
	root.add_child(vp)
	var world := Node3D.new()
	vp.add_child(world)
	var env := WorldEnvironment.new()
	env.environment = Environment.new()
	env.environment.background_mode = Environment.BG_CLEAR_COLOR
	world.add_child(env)
	var camera := Camera3D.new()
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.size = 3.0
	world.add_child(camera)
	# The game is 3D and fighters turn: every pose is checked from the side (the game camera),
	# three-quarter and front.
	var views := {"perfil": 270.0, "tres_quartos": 225.0, "frente": 180.0}
	var data := GaleData.new()
	for id: String in ["kaze", "ignis"]:
		var view := GaleFighterView.new()
		world.add_child(view)
		view.build(data, id, 0)
		view.aura.visible = false
		view.rotation.y = 0.0
		var heat := ShaderMaterial.new()
		heat.shader = Shader.new()
		heat.shader.code = HEAT
		for m: Node in view.find_children("*", "MeshInstance3D", true, false):
			(m as MeshInstance3D).material_override = heat
		# Optional: args[1] = one clip, every 3rd frame of it (to check a whole clip).
		var shots: Array = []
		if args.size() > 1:
			for f in range(0, 61, 3):
				shots.append([args[1], f])
		else:
			for clip: String in CLIPS:
				shots.append([clip, int(timing[id]["attacks"].get(clip, {}).get("contact", 6))])
		for shot: Array in shots:
			var clip: String = shot[0]
			if view.anim_player == null or not view.anim_player.has_animation(clip):
				continue
			view.play_clip(clip, float(shot[1]) / 60.0)
			for vname: String in views:
				var yaw := deg_to_rad(float(views[vname]))
				camera.position = Vector3(sin(yaw) * 6.0, 1.2, cos(yaw) * 6.0)
				camera.look_at(Vector3(0, 1.2, 0))
				var hips := view.skeleton.get_bone_global_pose(view.skeleton.find_bone("hips")).origin
				hips = view.skeleton.global_transform * hips
				heat.set_shader_parameter("centre", -(camera.global_transform.affine_inverse() * hips).z)
				await settle()
				_save(vp.get_texture().get_image(), out_dir.path_join(("%s_%s_%s.png" % [id, clip, vname]) if args.size() < 2 else ("%s_%s_%02d_%s.png" % [id, clip, int(shot[1]), vname])))
		view.queue_free()
		await settle()
	print("silhouettes done")
	quit()

func _save(img: Image, path: String) -> void:
	img.convert(Image.FORMAT_RGBA8)
	for y in img.get_height():
		for x in img.get_width():
			var c := img.get_pixel(x, y)
			img.set_pixel(x, y, Color(c.r, c.g, c.b) if c.a > 0.5 else Color.BLACK)
	img.save_png(path)
