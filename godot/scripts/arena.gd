class_name GaleArena
extends Node3D

var camera: Camera3D
var world_env: WorldEnvironment
var sun: DirectionalLight3D
var fill: DirectionalLight3D
var scenery: Node3D
var stage_instance: Node3D
var fighters: Array[GaleFighterView] = []
var props: Array[Node3D] = []
var broken_props: Array[Node3D] = []
var effects: Array = []
var boxes: Array[MeshInstance3D] = []
var show_boxes := false
var menu_mode := false
var shake := 0.0
var clock := 0.0
var focused_x := 0.0
var shake_strength := 0.65
var attack_renderer: Node3D
const AttackRenderer = preload("res://scripts/attack_renderer.gd")
var danger: MeshInstance3D
var stage_effect: MeshInstance3D
var warning_label: Label3D
var sky_material: ProceduralSkyMaterial
# Living stage pieces exported by art-source/tools/stage_builder.py.
var crowd: Array = []
var banners: Array = []
var barriers: Array = []
var crowd_excitement := 0.0
var water_materials: Array[StandardMaterial3D] = []
# Main menu beach (concept-art/ui/menu-principal-praia-v1.png), built by stage_builder.build_beach.
const MENU_SCENE := "res://assets/environments/beach/stage.glb"
var menu_scene_active := false

func _ready() -> void:
	attack_renderer = AttackRenderer.new()
	add_child(attack_renderer)
	var warning_mat := StandardMaterial3D.new()
	warning_mat.albedo_color=Color(1.0,0.58,0.16,0.38)
	warning_mat.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
	warning_mat.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA
	danger=GaleFighterView.box(self,Vector3.ONE,Vector3.ZERO,warning_mat)
	stage_effect=GaleFighterView.box(self,Vector3.ONE,Vector3.ZERO,GaleFighterView.mat(Color("dc8b38")))
	warning_label=Label3D.new()
	warning_label.billboard=BaseMaterial3D.BILLBOARD_ENABLED
	warning_label.font_size=40
	warning_label.pixel_size=0.009
	add_child(warning_label)
	world_env = WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_SKY
	sky_material=ProceduralSkyMaterial.new()
	sky_material.sky_top_color=Color("26475d")
	sky_material.sky_horizon_color=Color("d6b6a5")
	sky_material.ground_bottom_color=Color("253c43")
	sky_material.ground_horizon_color=Color("d6b6a5")
	var sky:=Sky.new()
	sky.sky_material=sky_material
	env.sky=sky
	env.background_color = Color("102235")
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color("c6e7ff")
	env.ambient_light_energy = 0.42
	env.tonemap_mode = Environment.TONE_MAPPER_ACES
	world_env.environment = env
	add_child(world_env)

	sun = DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-46, -28, 0)
	sun.light_energy = 0.85
	sun.shadow_enabled = true
	add_child(sun)

	fill = DirectionalLight3D.new()
	fill.rotation_degrees = Vector3(-20, 140, 0)
	fill.light_color = Color("6bcaff")
	fill.light_energy = 0.22
	add_child(fill)

	camera = Camera3D.new()
	camera.position = Vector3(0, 5.2, 16.5)
	camera.fov = 42
	add_child(camera)
	camera.look_at(Vector3(0, 1.2, 0))
	camera.current = true

func build(data: GaleData, sim: GaleCombat) -> void:
	attack_renderer.reset()
	if menu_scene_active:
		# Restore the fight lighting after the lit menu beach.
		sun.rotation_degrees = Vector3(-46, -28, 0)
		sun.light_energy = 0.85
		sun.light_color = Color.WHITE
		fill.light_energy = 0.22
		world_env.environment.ambient_light_color = Color("c6e7ff")
		world_env.environment.ambient_light_energy = 0.42
	menu_scene_active = false
	water_materials.clear()
	if is_instance_valid(scenery):
		remove_child(scenery)
		scenery.queue_free()
	scenery = Node3D.new()
	scenery.name = "Scenery"
	add_child(scenery)
	fighters.clear()
	props.clear()
	broken_props.clear()
	boxes.clear()
	for effect: Dictionary in effects:
		if is_instance_valid(effect.node):
			effect.node.queue_free()
	effects.clear()

	var stage := data.stage(sim.stage_id)
	if world_env != null and world_env.environment != null:
		world_env.environment.background_color = Color(stage.skyColor).darkened(0.35)
		world_env.environment.ambient_light_color = Color(stage.fogColor)
		sky_material.sky_top_color=Color(stage.skyColor).darkened(0.22)
		sky_material.sky_horizon_color=Color(stage.fogColor).lightened(0.10)
		sky_material.ground_horizon_color=Color(stage.fogColor)

	var stage_scene_path := "res://scenes/stages/%s.tscn" % sim.stage_id
	if ResourceLoader.exists(stage_scene_path):
		var packed_stage: PackedScene = load(stage_scene_path) as PackedScene
		stage_instance = packed_stage.instantiate() as Node3D
		scenery.add_child(stage_instance)
		_style_environment(stage_instance, {})
		_collect_living_pieces(stage_instance)
	else:
		var stone := GaleFighterView.mat(Color(stage.groundColor))
		GaleFighterView.box(scenery, Vector3(22, 0.5, 9), Vector3(0, -0.28, 0), stone)

	# Floor fight-line markings at Z=0, Y=0, X in [-EDGE, +EDGE]
	var trim := GaleFighterView.mat(Color(stage.accentColor), sim.stage_id == "molten_forge")
	var dark := GaleFighterView.mat(Color("182536"))
	GaleFighterView.box(scenery, Vector3(GaleCombat.EDGE * 2.0, 0.018, 0.025), Vector3(0, 0.01, -1.7), trim)

	for f: Dictionary in [sim.p1, sim.p2]:
		var view := GaleFighterView.new()
		scenery.add_child(view)
		view.build(data, f.id, f.palette)
		fighters.append(view)
		for color: Color in [Color(0.1, 0.8, 1, 0.2), Color(1, 0.3, 0.1, 0.3)]:
			var material := StandardMaterial3D.new()
			material.albedo_color = color
			material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			var debug_box := GaleFighterView.box(scenery, Vector3.ONE, Vector3.ZERO, material)
			debug_box.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			boxes.append(debug_box)

	var intact_path := "res://assets/environments/%s/prop_intact.glb" % sim.stage_id
	var broken_path := "res://assets/environments/%s/prop_broken.glb" % sim.stage_id
	var intact_packed: PackedScene = load(intact_path) as PackedScene if ResourceLoader.exists(intact_path) else null
	var broken_packed: PackedScene = load(broken_path) as PackedScene if ResourceLoader.exists(broken_path) else null

	for hazard: Dictionary in sim.hazards:
		var prop_node: Node3D
		if intact_packed != null:
			prop_node = intact_packed.instantiate() as Node3D
			prop_node.position = Vector3(hazard.x, 0.0, -0.55)
			scenery.add_child(prop_node)
		else:
			prop_node = GaleFighterView.box(scenery, Vector3(0.6, 0.8, 0.6), Vector3(hazard.x, 0.4, 0), trim)
		props.append(prop_node)
		_style_environment(prop_node, {})

		var broken_node: Node3D
		if broken_packed != null:
			broken_node = broken_packed.instantiate() as Node3D
			broken_node.position = Vector3(hazard.x, 0.0, -0.55)
			broken_node.visible = false
			scenery.add_child(broken_node)
		else:
			broken_node = GaleFighterView.box(scenery, Vector3(0.5, 0.12, 0.5), Vector3(hazard.x, 0.06, 0), dark)
			broken_node.visible = false
		broken_props.append(broken_node)
		_style_environment(broken_node, {})

	focused_x = 0

func _style_environment(node: Node, cache: Dictionary, lit: bool = false) -> void:
	# The imported PBR stage was clipping to white on Compatibility. Use the
	# same bounded toon lighting as the fighters so their silhouettes stay clear.
	if node is MeshInstance3D:
		var mesh_node := node as MeshInstance3D
		for surface in mesh_node.mesh.get_surface_count():
			var source := mesh_node.get_active_material(surface) as StandardMaterial3D
			if source == null:
				continue
			if String(mesh_node.name).begins_with("Backdrop"):
				# The painted far background keeps its own colours, unlit, and casts no shadow.
				var painting := StandardMaterial3D.new()
				painting.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
				painting.albedo_texture = source.albedo_texture
				mesh_node.set_surface_override_material(surface, painting)
				mesh_node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
				continue
			if source.resource_name.begins_with("glint_"):
				# Sunlight sparkling on the water: additive, drifting with the waves.
				var glint := StandardMaterial3D.new()
				glint.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
				glint.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
				glint.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
				glint.albedo_texture = source.albedo_texture
				glint.texture_repeat = true
				mesh_node.set_surface_override_material(surface, glint)
				mesh_node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
				water_materials.append(glint)
				continue
			if lit and not source.resource_name.begins_with("glow_"):
				# Lit scene (menu beach): real sun light and shadows, including leaf shadows on the sand.
				var key_lit := source.get_instance_id()
				if not cache.has(key_lit):
					var surface_mat := StandardMaterial3D.new()
					surface_mat.albedo_color = source.albedo_color
					surface_mat.albedo_texture = source.albedo_texture
					surface_mat.texture_repeat = true
					surface_mat.roughness = 0.35 if source.resource_name.begins_with("water_") else 1.0
					surface_mat.metallic_specular = 0.3 if source.resource_name.begins_with("water_") else 0.0
					if source.resource_name.begins_with("cutout_"):
						surface_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
						surface_mat.alpha_scissor_threshold = 0.5
						surface_mat.cull_mode = BaseMaterial3D.CULL_DISABLED
					if source.resource_name.begins_with("water_"):
						water_materials.append(surface_mat)
					cache[key_lit] = surface_mat
				mesh_node.set_surface_override_material(surface, cache[key_lit])
				continue
			if source.resource_name.begins_with("cutout_"):
				# Foliage, flowers and corals: hard alpha edge, visible from both sides.
				var leaf := StandardMaterial3D.new()
				leaf.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
				leaf.albedo_texture = source.albedo_texture
				leaf.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
				leaf.alpha_scissor_threshold = 0.5
				leaf.cull_mode = BaseMaterial3D.CULL_DISABLED
				mesh_node.set_surface_override_material(surface, leaf)
				continue
			if source.resource_name.begins_with("water_"):
				# Painted water drifts slowly (see _animate_living_pieces).
				var water := StandardMaterial3D.new()
				water.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
				water.albedo_texture = source.albedo_texture
				water.texture_repeat = true
				mesh_node.set_surface_override_material(surface, water)
				water_materials.append(water)
				continue
			if String(mesh_node.name).begins_with("Barrier"):
				# Heat curtain: invisible until a fighter nears the precipice.
				var curtain := StandardMaterial3D.new()
				curtain.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
				curtain.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
				curtain.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
				curtain.cull_mode = BaseMaterial3D.CULL_DISABLED
				curtain.albedo_color = Color(1.0, 0.45, 0.12, 0.0)
				mesh_node.set_surface_override_material(surface, curtain)
				continue
			var key := source.get_instance_id()
			if not cache.has(key) and source.resource_name.begins_with("glow_"):
				# Lava, fire, lamps and stained glass keep their full brightness.
				var glow := StandardMaterial3D.new()
				glow.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
				glow.albedo_color = source.albedo_color
				glow.albedo_texture = source.albedo_texture
				glow.texture_repeat = true
				cache[key] = glow
			if not cache.has(key):
				var toon := GaleFighterView.mat(source.albedo_color.darkened(0.12), source.emission_enabled)
				if source.albedo_texture != null:
					toon.set_shader_parameter("use_textures", true)
					toon.set_shader_parameter("albedo_tex", source.albedo_texture)
				cache[key] = toon
			mesh_node.set_surface_override_material(surface, cache[key])
	for child in node.get_children():
		_style_environment(child, cache, lit)

func _collect_living_pieces(root_node: Node) -> void:
	crowd.clear()
	banners.clear()
	barriers.clear()
	crowd_excitement = 0.0
	var rng := RandomNumberGenerator.new()
	rng.seed = 4242
	for node: Node in root_node.find_children("*", "Node3D", true, false):
		var piece := node as Node3D
		var label := String(piece.name)
		if label.begins_with("Crowd_"):
			crowd.append({"node": piece, "base": piece.position, "phase": rng.randf() * TAU, "rate": rng.randf_range(2.2, 3.4)})
		elif label.begins_with("Banner_"):
			banners.append({"node": piece, "base": piece.rotation, "phase": rng.randf() * TAU})
		elif label.begins_with("Barrier_") and piece is MeshInstance3D:
			barriers.append(piece)

func show_menu_scene() -> void:
	if menu_scene_active:
		return
	attack_renderer.reset()
	if is_instance_valid(scenery):
		remove_child(scenery)
		scenery.queue_free()
	scenery = Node3D.new()
	scenery.name = "Scenery"
	add_child(scenery)
	fighters.clear()
	props.clear()
	broken_props.clear()
	boxes.clear()
	water_materials.clear()
	stage_instance = (load(MENU_SCENE) as PackedScene).instantiate() as Node3D
	scenery.add_child(stage_instance)
	_style_environment(stage_instance, {}, true)
	# Afternoon sun from behind the bay: the canopy shadow falls on the foreground sand.
	sun.rotation_degrees = Vector3(-50, 150, 0)
	# Compatibility renderer: a little sun goes a long way on the pale sand.
	sun.light_energy = 0.13
	sun.light_color = Color("fff3dd")
	sun.directional_shadow_max_distance = 70.0
	fill.light_energy = 0.12
	world_env.environment.ambient_light_color = Color("cfe9ff")
	world_env.environment.ambient_light_energy = 0.32
	_collect_living_pieces(stage_instance)
	sky_material.sky_top_color = Color("1f6fe0")
	sky_material.sky_horizon_color = Color("bfe8fb")
	sky_material.ground_horizon_color = Color("bfe8fb")
	sky_material.ground_bottom_color = Color("2a7fb8")
	menu_scene_active = true
	set_menu_mode(true, true)

func _animate_living_pieces(delta: float, sim: GaleCombat) -> void:
	for water: StandardMaterial3D in water_materials:
		water.uv1_offset = Vector3(sin(clock * 0.21) * 0.012, clock * 0.006, 0)
	crowd_excitement = maxf(0.0, crowd_excitement - delta * 0.55)
	for person: Dictionary in crowd:
		var t: float = clock * float(person.rate) + float(person.phase)
		var hop := absf(sin(t)) * (0.02 + crowd_excitement * 0.24)
		var node: Node3D = person.node
		node.position = person.base + Vector3(0, hop, 0)
		node.rotation.z = sin(t * 0.5) * 0.04 * (1.0 + crowd_excitement * 2.0)
	for cloth: Dictionary in banners:
		var node: Node3D = cloth.node
		node.rotation = cloth.base + Vector3(sin(clock * 1.4 + float(cloth.phase)) * 0.07, 0, sin(clock * 0.9 + float(cloth.phase)) * 0.04)
	for barrier: MeshInstance3D in barriers:
		var side := signf(barrier.global_position.x)
		var nearest := 99.0
		if not sim.p1.is_empty() and not menu_scene_active:
			for f: Dictionary in [sim.p1, sim.p2]:
				nearest = minf(nearest, GaleCombat.EDGE - float(f.x) * side)
		var glow := clampf(1.0 - nearest / 1.4, 0.0, 1.0) * (0.75 + 0.25 * sin(clock * 9.0))
		var curtain := barrier.get_surface_override_material(0) as StandardMaterial3D
		if curtain != null:
			curtain.albedo_color.a = glow * 0.45

func set_menu_mode(enabled: bool, hide_fighters: bool = true) -> void:
	menu_mode = enabled
	for f_view: GaleFighterView in fighters:
		if is_instance_valid(f_view):
			f_view.visible = not (enabled and hide_fighters)
	for p_node: Node3D in props:
		if is_instance_valid(p_node):
			p_node.visible = not (enabled and hide_fighters)
	for b_node: Node3D in broken_props:
		if is_instance_valid(b_node):
			b_node.visible = false

func render(sim: GaleCombat, delta: float) -> void:
	attack_renderer.render(sim.attacks.items)
	var cycle:=sim.arena_cycle
	var stage_visible:bool=not menu_mode and sim.mode!="training" and cycle.visible_now()
	danger.visible=stage_visible
	warning_label.visible=stage_visible
	stage_effect.visible=stage_visible and (cycle.active_now() or sim.stage_id=="storm_market")
	if stage_visible:
		danger.position=Vector3(cycle.x,0.02,0)
		danger.scale=Vector3(cycle.width,0.025,1.1)
		warning_label.position=Vector3(cycle.x,2.8,0)
		warning_label.text="%s · %.1fs" % [cycle.label,maxf(0.0,float(900-cycle.clock)/60.0)]
		stage_effect.position=Vector3(cycle.x,0.5,0)
		stage_effect.scale=Vector3(cycle.width,1.0,0.7)
		if sim.stage_id=="storm_market":
			stage_effect.scale=Vector3(0.7,0.7,0.7)
			stage_effect.position.y=0.4+maxf(0.0,float(900-cycle.clock)/90.0)*5.0
	var step_delta := 0.0 if sim.freeze > 0 else delta
	clock += step_delta
	_animate_living_pieces(step_delta, sim)
	for i in fighters.size():
		var state: Dictionary = sim.p1 if i == 0 else sim.p2
		var visual_state := state.duplicate()
		visual_state.presentation_victory = sim.winner == i + 1
		fighters[i].sync(visual_state, clock)
		var hurt := GaleCombat.hurt_rect(state)
		var hit := GaleCombat.hit_rect(state)
		for j in 2:
			var rect: Rect2 = hurt if j == 0 else hit
			var mesh := boxes[i * 2 + j]
			mesh.visible = show_boxes and (j == 0 or (state.action == "active" and state.move.get("delivery","melee") == "melee"))
			mesh.position = Vector3(rect.get_center().x, rect.get_center().y, 0.02)
			mesh.scale = Vector3(maxf(0.01, rect.size.x), maxf(0.01, rect.size.y), 0.4)
	if not menu_mode:
		for i in mini(props.size(), sim.hazards.size()):
			var hazard: Dictionary = sim.hazards[i]
			props[i].visible = hazard.hp > 0
			props[i].position.x = hazard.x
			props[i].rotation.z += hazard.vx * step_delta
			if i < broken_props.size():
				broken_props[i].visible = hazard.hp <= 0
				broken_props[i].position.x = hazard.x
	for i in range(effects.size() - 1, -1, -1):
		var effect: Dictionary = effects[i]
		effect.life -= delta
		if effect.life <= 0:
			effect.node.queue_free()
			effects.remove_at(i)
		else:
			effect.node.scale += Vector3.ONE * delta * 5.0

	if menu_mode:
		# Sanctuary overview camera matching menu-principal-v3.png
		var menu_cam_pos := Vector3(1.2 + sin(clock * 0.25) * 0.25, 2.8, 12.2)
		camera.position = camera.position.lerp(menu_cam_pos, 1.0 - exp(-5.0 * delta))
		camera.look_at(Vector3(0.4, 2.3, -4.0))
		camera.h_offset = 0.0
	else:
		# Close camera; it stops short of the walls so the corner blockers stay framed.
		var limit := GaleCombat.EDGE - 2.2
		focused_x = lerpf(focused_x, clampf((sim.p1.x + sim.p2.x) * 0.5, -limit, limit), 1 - exp(-6 * delta))
		var distance: float = absf(sim.p1.x - sim.p2.x)
		var z := clampf(5.0 + distance * 0.5, 6.0, 10.5)
		if sim.winner>0:z+=1.0
		shake = maxf(0, shake - delta * 2)
		camera.position = camera.position.lerp(Vector3(focused_x, 2.4 + maxf(sim.p1.y, sim.p2.y) * 0.4, z), 1 - exp(-8 * delta))
		camera.look_at(Vector3(focused_x, 1.05 + maxf(sim.p1.y, sim.p2.y) * 0.4, 0))
		camera.h_offset = sin(clock * 65.0) * shake * 0.12 * shake_strength

func impact(event: Dictionary) -> void:
	# The bazaar crowd reacts to big moments.
	if event.kind in ["heavy", "ultimate", "ko", "clash"]:
		crowd_excitement = 1.0
	elif event.kind == "hit":
		crowd_excitement = maxf(crowd_excitement, 0.35)
	var node := Node3D.new()
	add_child(node)
	node.position = event.position
	var color: Color = event.color
	var material := GaleFighterView.mat(color, true)
	for i in 6:
		var beam := GaleFighterView.box(node, Vector3(0.06, 0.7, 0.06), Vector3.ZERO, material)
		beam.rotation.z = float(i) * PI / 3.0
	effects.append({"node": node, "life": 0.16})
	shake = 0.5 if event.kind in ["heavy", "ultimate", "clash", "ko"] else 0.2
