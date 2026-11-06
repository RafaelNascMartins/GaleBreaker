extends SceneTree
## Every outfit of one fighter from several sides and a head close-up, from the real game
## renderer (toon shader, face atlas, outfit pages and bodies), in the idle pose at rest.
## godot --path godot --script res://tests/capture_outfits.gd -- <out_dir> [fighter]

func _initialize() -> void:
	call_deferred("capture")

func settle() -> void:
	for i in 3:
		await process_frame
	await RenderingServer.frame_post_draw

func capture() -> void:
	var args := OS.get_cmdline_user_args()
	var out_dir := args[0] if args.size() > 0 else "res://tests/visual-polish/outfits"
	var id := args[1] if args.size() > 1 else "ignis"
	DirAccess.make_dir_recursive_absolute(out_dir)
	root.size = Vector2i(640, 800)
	var data := GaleData.new()
	var world := Node3D.new()
	root.add_child(world)
	var env := WorldEnvironment.new()
	env.environment = Environment.new()
	env.environment.background_mode = Environment.BG_COLOR
	env.environment.background_color = Color("8c8c8c")
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
	var catalog := GaleVisualCatalog.load_for(id)
	# yaw of the camera around the fighter (the model faces +Z after the view's turn), height, look-at height, ortho size
	var shots := {"frente": [180.0, 1.3, 1.2, 2.8], "costas": [0.0, 1.3, 1.2, 2.8], "lado_esq": [90.0, 1.3, 1.2, 2.8],
		"lado_dir": [270.0, 1.3, 1.2, 2.8], "tres_quartos": [215.0, 1.8, 1.2, 2.8], "baixo_entre_pernas": [195.0, 0.15, 0.85, 1.9],
		"baixo_gluteos": [15.0, 0.15, 0.85, 1.9], "ombros_cima": [200.0, 4.0, 1.6, 1.6],
		"cabeca": [200.0, 2.1, 2.05, 0.8], "cabeca_lado": [270.0, 2.1, 2.05, 0.8], "cabeca_costas": [20.0, 2.1, 2.05, 0.8],
		"quadril": [180.0, 1.1, 1.05, 0.7]}
	for p in catalog.palettes.size():
		var view := GaleFighterView.new()
		world.add_child(view)
		view.build(data, id, p)
		view.aura.visible = false
		view.rotation.y = 0.0
		view.play_clip("idle", 0.0)
		for shot: String in shots:
			var s: Array = shots[shot]
			var yaw := deg_to_rad(float(s[0]))
			camera.size = float(s[3])
			camera.position = Vector3(sin(yaw) * 6.0, float(s[1]), cos(yaw) * 6.0)
			camera.look_at(Vector3(0, float(s[2]), 0))
			await settle()
			root.get_texture().get_image().save_png(out_dir.path_join("%s_%d_%s.png" % [id, p, shot]))
		view.queue_free()
		await settle()
	print("outfits: ", catalog.palettes.size())
	quit()
