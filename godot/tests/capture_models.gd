extends SceneTree

var views: Array[GaleFighterView] = []
var output := "res://tests/visual-polish"

func _initialize() -> void:
	call_deferred("capture")

func settle() -> void:
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw

func capture() -> void:
	DirAccess.make_dir_recursive_absolute(output)
	root.size = Vector2i(1280, 720)
	var data := GaleData.new()
	var ids := ["kaze", "ignis", "tophia", "volt"]
	var canvas := Control.new()
	root.add_child(canvas)
	for i in 4:
		var container := SubViewportContainer.new()
		container.position = Vector2((i % 2) * 640, (i / 2) * 360 + 34)
		container.size = Vector2(640, 320)
		container.stretch = true
		canvas.add_child(container)
		var viewport := SubViewport.new()
		viewport.size = Vector2i(640, 320)
		viewport.own_world_3d = true
		viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		container.add_child(viewport)
		var world := Node3D.new()
		viewport.add_child(world)
		var env := WorldEnvironment.new()
		env.environment = Environment.new()
		env.environment.background_mode = Environment.BG_COLOR
		env.environment.background_color = Color("e6e4dc")
		env.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
		env.environment.ambient_light_color = Color.WHITE
		env.environment.ambient_light_energy = 0.7
		world.add_child(env)
		var camera := Camera3D.new()
		world.add_child(camera)
		camera.projection = Camera3D.PROJECTION_ORTHOGONAL
		camera.size = 2.6
		camera.position = Vector3(0.8, 1.9, 5)
		camera.look_at(Vector3(0, 1.0, 0))
		var view := GaleFighterView.new()
		world.add_child(view)
		view.build(data, ids[i], 0)
		view.rotation.y = -PI / 2.0
		view.aura.visible = false
		views.append(view)
		var label := Label.new()
		label.position = Vector2((i % 2) * 640 + 18, (i / 2) * 360 + 6)
		label.text = ids[i].to_upper()
		label.add_theme_font_size_override("font_size", 22)
		canvas.add_child(label)
	await settle()
	for clip: String in ["idle", "light_1", "light_2", "light_3", "heavy", "elemental", "ultimate", "guard_high","victory","ko"]:
		for view in views:
			var camera:Camera3D=view.get_viewport().get_camera_3d()
			camera.size=3.4 if clip in ["victory","ko"] else 2.6
			var seek := 0.0
			if clip in ["victory","ko"]:
				seek = GaleAnimTiming.state_sec(view.fighter_id, clip)
			elif clip.begins_with("light") or clip in ["heavy","elemental","ultimate"]:
				seek = GaleAnimTiming.contact_sec(view.fighter_id, clip)
			elif clip == "guard_high":
				seek = 0.1
			view.play_clip(clip, seek)
		await settle()
		root.get_texture().get_image().save_png(output + "/" + clip + ".png")
	if "--animate" in OS.get_cmdline_user_args():
		# Each fighter plays light_1..3 back to back at its own clip lengths.
		for frame in 96:
			for view in views:
				view.get_viewport().get_camera_3d().size=2.6
				var local := frame
				var step := 1
				while step < 3 and local >= int(GaleAnimTiming.attack(view.fighter_id, "light_%d" % step).end):
					local -= int(GaleAnimTiming.attack(view.fighter_id, "light_%d" % step).end)
					step += 1
				view.play_clip("light_%d" % step, minf(float(local), float(GaleAnimTiming.attack(view.fighter_id, "light_%d" % step).end)) / 60.0)
			await settle()
			root.get_texture().get_image().save_png(output + "/frame-%03d.png" % frame)
	print("MODEL CAPTURE COMPLETE")
	quit()
