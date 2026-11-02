extends SceneTree

func _initialize() -> void:
	call_deferred("build_all")

func set_owner_recursive(node: Node, root_owner: Node) -> void:
	for child in node.get_children():
		child.owner = root_owner
		set_owner_recursive(child, root_owner)

func find_typed(node: Node, type_name: String) -> Node:
	if node.get_class() == type_name:
		return node
	for child in node.get_children():
		var found := find_typed(child, type_name)
		if found != null:
			return found
	return null

func build_all() -> void:
	var shader: Shader = load("res://scripts/toon.gdshader")

	# 1. Build visual catalog .tres, character materials .tres, and fighter scenes .tscn
	for id: String in GaleData.IDS:
		var cat := GaleVisualCatalog.build_default(id)
		var cat_err := ResourceSaver.save(cat, "res://resources/visuals/%s.tres" % id)
		assert(cat_err == OK, "Failed to save catalog for " + id)

		var mat := ShaderMaterial.new()
		mat.shader = shader
		mat.set_shader_parameter("use_textures", true)
		mat.set_shader_parameter("albedo_tex", load(cat.albedo_path))
		mat.set_shader_parameter("mask_tex", load(cat.mask_path))
		mat.set_shader_parameter("normal_tex", load(cat.normal_path))
		var p0: Dictionary = cat.palettes[0]
		mat.set_shader_parameter("palette_primary", Color(p0.primary))
		mat.set_shader_parameter("palette_secondary", Color(p0.secondary))
		mat.set_shader_parameter("palette_accent", Color(p0.accent))
		var mat_path := "res://materials/characters/%s.tres" % id
		var mat_err := ResourceSaver.save(mat, mat_path)
		assert(mat_err == OK, "Failed to save material for " + id)

		# Create fighter wrapper scene that instances <id>.glb and attaches sockets
		var fighter_root := Node3D.new()
		fighter_root.name = id.capitalize() + "Fighter"
		var pivot := Node3D.new()
		pivot.name = "ModelPivot"
		# glTF front is +Z; rotate pivot by PI so local -Z matches fighter_view adapter without rotating combat state
		pivot.rotation.y = PI
		fighter_root.add_child(pivot)
		pivot.owner = fighter_root

		var glb_scene: PackedScene = load(cat.glb_path)
		var model := glb_scene.instantiate()
		model.name = "Model"
		pivot.add_child(model)
		model.owner = fighter_root

		# Add persistent sockets on Fighter root so reimporting GLB preserves socket nodes
		var sockets := {
			"socket_root": Vector3(0, 0.05, 0),
			"socket_chest": Vector3(0, 1.35, -0.25),
			"socket_hand_l": Vector3(0.32, 1.15, -0.45),
			"socket_hand_r": Vector3(-0.32, 1.15, -0.45),
			"socket_foot_r": Vector3(-0.18, 0.25, -0.45),
			"socket_muzzle": Vector3(-0.32, 1.10, -0.85),
		}
		for sname: String in sockets.keys():
			var marker := Marker3D.new()
			marker.name = sname
			marker.position = sockets[sname]
			fighter_root.add_child(marker)
			marker.owner = fighter_root

		var packed_fighter := PackedScene.new()
		packed_fighter.pack(fighter_root)
		var f_err := ResourceSaver.save(packed_fighter, cat.scene_path)
		assert(f_err == OK, "Failed to save fighter scene for " + id)
		fighter_root.free()

	# 2. Build environment materials .tres and stage scenes .tscn
	var stage_colors := {
		"zephyr_dojo": Color("e2e8f0"),
		"molten_forge": Color("1c1917"),
		"storm_market": Color("b45309"),
	}
	for stage_id: String in GaleData.STAGES:
		var smat := ShaderMaterial.new()
		smat.shader = shader
		smat.set_shader_parameter("base_color", stage_colors[stage_id])
		ResourceSaver.save(smat, "res://materials/environments/%s.tres" % stage_id)

		var stage_root := Node3D.new()
		stage_root.name = stage_id.to_pascal_case() + "Stage"
		var glb_stage: PackedScene = load("res://assets/environments/%s/stage.glb" % stage_id)
		var env_instance := glb_stage.instantiate()
		env_instance.name = "Environment"
		stage_root.add_child(env_instance)
		env_instance.owner = stage_root

		var props_holder := Node3D.new()
		props_holder.name = "Props"
		stage_root.add_child(props_holder)
		props_holder.owner = stage_root

		var packed_stage := PackedScene.new()
		packed_stage.pack(stage_root)
		var s_err := ResourceSaver.save(packed_stage, "res://scenes/stages/%s.tscn" % stage_id)
		assert(s_err == OK, "Failed to save stage scene for " + stage_id)
		stage_root.free()

	# 3. Build UI scenes: main_menu.tscn, pause_menu.tscn, combat_hud.tscn
	for ui_name: String in ["main_menu", "pause_menu", "combat_hud"]:
		var ui_root := Control.new()
		ui_root.name = ui_name.to_pascal_case()
		ui_root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		ui_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var packed_ui := PackedScene.new()
		packed_ui.pack(ui_root)
		var u_err := ResourceSaver.save(packed_ui, "res://scenes/ui/%s.tscn" % ui_name)
		assert(u_err == OK, "Failed to save UI scene " + ui_name)
		ui_root.free()

	print("GENERATED ALL SCENES AND VISUAL RESOURCES SUCCESSFULLY.")
	quit(0)
