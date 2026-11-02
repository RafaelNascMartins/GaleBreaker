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
	else:
		var stone := GaleFighterView.mat(Color(stage.groundColor))
		GaleFighterView.box(scenery, Vector3(22, 0.5, 9), Vector3(0, -0.28, 0), stone)

	# Floor fight-line markings at Z=0, Y=0, X in [-9.5, +9.5]
	var trim := GaleFighterView.mat(Color(stage.accentColor), sim.stage_id == "molten_forge")
	var dark := GaleFighterView.mat(Color("182536"))
	GaleFighterView.box(scenery, Vector3(19.0, 0.018, 0.025), Vector3(0, 0.01, -1.7), trim)

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

func _style_environment(node: Node, cache: Dictionary) -> void:
	# The imported PBR stage was clipping to white on Compatibility. Use the
	# same bounded toon lighting as the fighters so their silhouettes stay clear.
	if node is MeshInstance3D:
		var mesh_node := node as MeshInstance3D
		for surface in mesh_node.mesh.get_surface_count():
			var source := mesh_node.get_active_material(surface) as StandardMaterial3D
			if source == null:
				continue
			var key := source.get_instance_id()
			if not cache.has(key):
				cache[key] = GaleFighterView.mat(source.albedo_color.darkened(0.12), source.emission_enabled)
			mesh_node.set_surface_override_material(surface, cache[key])
	for child in node.get_children():
		_style_environment(child, cache)

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
		focused_x = lerpf(focused_x, (sim.p1.x + sim.p2.x) * 0.5, 1 - exp(-6 * delta))
		var distance: float = absf(sim.p1.x - sim.p2.x)
		var z := clampf(6.4 + distance * 0.55, 7.0, 18.0)
		if sim.winner>0:z+=1.0
		shake = maxf(0, shake - delta * 2)
		camera.position = camera.position.lerp(Vector3(focused_x, 2.65 + maxf(sim.p1.y, sim.p2.y) * 0.4, z), 1 - exp(-8 * delta))
		camera.look_at(Vector3(focused_x, 1.05 + maxf(sim.p1.y, sim.p2.y) * 0.4, 0))
		camera.h_offset = sin(clock * 65.0) * shake * 0.12 * shake_strength

func impact(event: Dictionary) -> void:
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
