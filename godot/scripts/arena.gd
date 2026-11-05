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
# Beach menu: cartoon sky shader (arenas keep the procedural sky).
var sky: Sky
var toon_sky: ShaderMaterial
# Living stage pieces exported by art-source/tools/stage_builder.py.
var crowd: Array = []
var banners: Array = []
var barriers: Array = []
var crowd_excitement := 0.0
var water_materials: Array[Material] = []
# Main menu beach (concept-art/ui/menu-principal-praia-v1.png), built by stage_builder.build_beach.
const MENU_SCENE := "res://assets/environments/beach/stage.glb"
var menu_scene_active := false
# Flight from the beach menu into the forest clearing with the options board.
signal board_ready
signal board_closed
const BOARD_FLIGHT_TIME := 1.7
# The board faces +X; the camera stops this far in front of the parchment centre.
const BOARD_VIEW_OFFSET := Vector3(4.1, 0.2, 0.0)
const MENU_LOOK := Vector3(0.4, 2.3, -4.0)
var board_path: Curve3D
var board_look := Vector3.ZERO
var board_panel: MeshInstance3D
var board_flight := 0.0
var board_target := 0.0
# Training garage behind the menu camera: the camera turns 180 degrees to its gate.
signal garage_ready
signal garage_closed
const GARAGE_TURN_TIME := 1.8
var garage_cam := Vector3.ZERO
var garage_look := Vector3.ZERO
var garage_panel: MeshInstance3D
var garage_flight := 0.0
var garage_target := 0.0
# The heavy bag hangs from this pivot (top of its chain) and sways gently.
var bag_pivot: Node3D
const BAG_TOP := Vector3(-0.75, 3.64, 21.6)
# Arcade select in the village patio (reached by a fade to black): camera, fighter spot and the
# stall anchors where the menu texts and the outfits on hangers go.
var patio_cam := Vector3.ZERO
var patio_look := Vector3.ZERO
var patio_spot := Vector3.ZERO
var patio_anchors := {}
var patio_shot := false
# Arcade select: camera and fighter spot on the beach.
var select_shot := false
var select_view: GaleFighterView
var select_turn := 0.0
# Open sand near the water, clear of the foliage wall on the left.
const SELECT_SPOT := Vector3(2.62, 0.0, -2.09)
const SELECT_CAM := Vector3(0.05, 1.25, 2.25)
const SELECT_LOOK := Vector3(3.69, 1.0, -2.18)
# Model forward is -Z: this yaw turns the fighter toward the camera, slightly to the panel.
const SELECT_FACING := 2.95
# Cel-shaded scenery: shadow side = ambient, lit side = ambient + sun.
const FIGHT_SUN := 0.55
const FIGHT_AMBIENT := 0.5

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
	sky=Sky.new()
	sky.sky_material=sky_material
	env.sky=sky
	env.background_color = Color("102235")
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color("c6e7ff")
	env.ambient_light_energy = FIGHT_AMBIENT
	env.tonemap_mode = Environment.TONE_MAPPER_ACES
	world_env.environment = env
	add_child(world_env)

	sun = DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-46, -28, 0)
	sun.light_energy = FIGHT_SUN
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
	select_shot = false
	select_view = null
	board_path = null
	if menu_scene_active:
		# Restore the fight lighting after the lit menu beach.
		sun.rotation_degrees = Vector3(-46, -28, 0)
		sun.light_energy = FIGHT_SUN
		sun.light_color = Color.WHITE
		fill.light_energy = 0.22
		world_env.environment.ambient_light_color = Color("c6e7ff")
		world_env.environment.ambient_light_energy = FIGHT_AMBIENT
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
		# Only a hint of the stage tint: the cel shadow side is lit by ambient alone.
		world_env.environment.ambient_light_color = Color(stage.fogColor).lerp(Color("f2ece2"), 0.8)
		sky.sky_material = sky_material
		_apply_menu_lighting(false)
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

const CelSurface = preload("res://shaders/cel/cel_surface.gdshader")
const CelCutout = preload("res://shaders/cel/cel_cutout.gdshader")
const ToonWater = preload("res://shaders/water/toon_water.gdshader")
const InkOutline = preload("res://shaders/cel/outline.tres")
const WATER_DETAIL := "res://assets/environments/beach/textures/agua.png"

static func toon_water_material() -> ShaderMaterial:
	var water := ShaderMaterial.new()
	water.shader = ToonWater
	for pair: Array in [["surface_noise", 0.06], ["distort_noise", 0.03]]:
		var noise := FastNoiseLite.new()
		noise.frequency = pair[1]
		noise.seed = 11 if pair[0] == "surface_noise" else 29
		var tex := NoiseTexture2D.new()
		tex.noise = noise
		tex.seamless = true
		tex.width = 256
		tex.height = 256
		water.set_shader_parameter(pair[0], tex)
	if ResourceLoader.exists(WATER_DETAIL):
		water.set_shader_parameter("detail_tex", load(WATER_DETAIL))
	return water

static func cel_material(source: StandardMaterial3D, cutout: bool = false) -> ShaderMaterial:
	var cel := ShaderMaterial.new()
	cel.shader = CelCutout if cutout else CelSurface
	cel.set_shader_parameter("color", source.albedo_color)
	if source.albedo_texture != null:
		cel.set_shader_parameter("base_texture", source.albedo_texture)
	return cel

func _style_environment(node: Node, cache: Dictionary) -> void:
	# Scenery uses the lit cel shader (shaders/cel): banded light, real shadows and a
	# soft rim. Paintings, glows, glints and the heat curtain stay unshaded.
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
			if source.resource_name.begins_with("water_toon"):
				mesh_node.set_surface_override_material(surface, toon_water_material())
				mesh_node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
				continue
			if String(mesh_node.name).begins_with("QuestBoardPanel"):
				# The options are read on this parchment: keep it bright and unshaded.
				var parchment := StandardMaterial3D.new()
				parchment.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
				parchment.albedo_texture = source.albedo_texture
				parchment.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
				parchment.alpha_scissor_threshold = 0.5
				parchment.albedo_color = Color(0.97, 0.95, 0.9)
				mesh_node.set_surface_override_material(surface, parchment)
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
			if not cache.has(key):
				if source.resource_name.begins_with("glow_"):
					# Lava, fire, lamps and stained glass keep their full brightness.
					var glow := StandardMaterial3D.new()
					glow.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
					glow.albedo_color = source.albedo_color
					glow.albedo_texture = source.albedo_texture
					glow.texture_repeat = true
					cache[key] = glow
				else:
					var cel := cel_material(source, source.resource_name.begins_with("cutout_"))
					if not source.resource_name.begins_with("cutout_"):
						# Ink line around solid scenery (cards would outline as squares).
						cel.next_pass = InkOutline
					if source.resource_name.begins_with("water_"):
						# Painted water drifts slowly and catches a sharp sun highlight.
						cel.set_shader_parameter("specular", Color(1, 1, 1, 0.55))
						water_materials.append(cel)
					cache[key] = cel
			mesh_node.set_surface_override_material(surface, cache[key])
	for child in node.get_children():
		_style_environment(child, cache)

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
	_style_environment(stage_instance, {})
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
	_collect_board_markers(stage_instance)
	if toon_sky == null:
		toon_sky = ShaderMaterial.new()
		toon_sky.shader = load("res://shaders/sky/toon_sky.gdshader")
		toon_sky.set_shader_parameter("sky_color", Color("1f6fe0"))
		toon_sky.set_shader_parameter("horizon_color", Color("bfe8fb"))
		toon_sky.set_shader_parameter("sun_color", Color("fff3dd"))
		# Smaller, more numerous clouds (closer to the beach concept).
		toon_sky.set_shader_parameter("cloud_scale", 4.5)
		toon_sky.set_shader_parameter("cloud_threshold", 0.56)
	sky.sky_material = toon_sky
	sky_material.sky_top_color = Color("1f6fe0")
	sky_material.sky_horizon_color = Color("bfe8fb")
	sky_material.ground_horizon_color = Color("bfe8fb")
	sky_material.ground_bottom_color = Color("2a7fb8")
	menu_scene_active = true
	set_menu_mode(true, true)

func _collect_board_markers(root_node: Node) -> void:
	board_path = Curve3D.new()
	board_flight = 0.0
	board_target = 0.0
	var index := 0
	while root_node.find_child("CamPath_%d" % index, true, false) != null:
		var mark := root_node.find_child("CamPath_%d" % index, true, false) as Node3D
		board_path.add_point(mark.global_position)
		index += 1
	# Smooth the corners of the flight.
	for i in range(1, board_path.point_count - 1):
		var tangent := (board_path.get_point_position(i + 1) - board_path.get_point_position(i - 1)) * 0.22
		board_path.set_point_in(i, -tangent)
		board_path.set_point_out(i, tangent)
	var look := root_node.find_child("BoardLook", true, false) as Node3D
	if look != null:
		board_look = look.global_position
		# Final stop is set here (not in Blender) so the parchment fills the frame for reading.
		if board_path.point_count > 1:
			board_path.set_point_position(board_path.point_count - 1, board_look + BOARD_VIEW_OFFSET)
	board_panel = root_node.find_child("QuestBoardPanel", true, false) as MeshInstance3D
	garage_flight = 0.0
	garage_target = 0.0
	garage_panel = root_node.find_child("GaragePanel", true, false) as MeshInstance3D
	var cam_mark := root_node.find_child("CamGarage", true, false) as Node3D
	var look_mark := root_node.find_child("GarageLook", true, false) as Node3D
	if cam_mark != null and look_mark != null:
		garage_cam = cam_mark.global_position
		garage_look = look_mark.global_position
	_light_garage()
	patio_anchors.clear()
	patio_cam = Vector3.ZERO
	for node in root_node.find_children("Patio*", "Node3D", true, false):
		patio_anchors[String(node.name)] = (node as Node3D).global_position
		patio_anchors[String(node.name) + ":basis"] = (node as Node3D).global_basis
	var cam_patio := root_node.find_child("CamPatio", true, false) as Node3D
	if cam_patio != null and patio_anchors.has("PatioLook") and patio_anchors.has("PatioSpot"):
		patio_cam = cam_patio.global_position
		patio_look = patio_anchors.PatioLook
		patio_spot = patio_anchors.PatioSpot

## Fly into the clearing (on = true) or back to the beach menu view.
## Forward+ lighting for the menu scene: ambient occlusion, bounced light, glow, and inside the
## garage late sun through the windows (volumetric shafts) plus the pendant lamp.
func _apply_menu_lighting(on: bool) -> void:
	var env := world_env.environment
	env.ssao_enabled = on
	env.ssao_radius = 1.2
	env.ssao_intensity = 2.2
	env.ssil_enabled = on
	env.ssil_intensity = 1.2
	env.glow_enabled = on
	env.glow_intensity = 0.7
	env.glow_bloom = 0.05
	env.glow_hdr_threshold = 1.1
	env.volumetric_fog_enabled = on
	env.volumetric_fog_density = 0.0
	env.volumetric_fog_albedo = Color("ffe4b8")
	env.volumetric_fog_length = 16.0
	env.volumetric_fog_detail_spread = 1.5
	env.volumetric_fog_temporal_reprojection_enabled = true

func _light_garage() -> void:
	_apply_menu_lighting(true)
	if garage_cam == Vector3.ZERO:
		return
	var lights := Node3D.new()
	lights.name = "GarageLights"
	scenery.add_child(lights)
	# Soft late sun through the two windows left of the gate: wide, gentle cones slanting
	# down across the room toward the right, with blurred shadows; the dust shows the rays.
	for x: float in [-0.1, 0.9]:
		var sun_in := SpotLight3D.new()
		sun_in.light_color = Color("ffcf8a")
		sun_in.light_energy = 4.0
		sun_in.spot_range = 11.0
		sun_in.spot_angle = 11.0
		sun_in.spot_angle_attenuation = 2.0
		sun_in.spot_attenuation = 0.6
		sun_in.light_size = 0.6
		sun_in.shadow_enabled = true
		sun_in.shadow_blur = 2.5
		sun_in.light_volumetric_fog_energy = 12.0
		sun_in.light_specular = 0.2
		lights.add_child(sun_in)
		sun_in.position = Vector3(x, 3.25, 26.3)
		sun_in.look_at(Vector3(x - 2.6, 0.0, 22.0))
	_garage_rays(lights)
	_hang_bag()
	# Warm bounce filling the whole room (the concept garage is bright, not a dark cave).
	var fill := OmniLight3D.new()
	fill.light_color = Color("ffe2b8")
	fill.light_energy = 1.6
	fill.omni_range = 9.0
	fill.omni_attenuation = 0.4
	lights.add_child(fill)
	fill.position = Vector3(-0.8, 2.6, 21.5)
	var lamp := OmniLight3D.new()
	lamp.light_color = Color("ffd29a")
	lamp.light_energy = 1.4
	lamp.omni_range = 5.5
	lamp.shadow_enabled = true
	lamp.light_volumetric_fog_energy = 0.4
	lights.add_child(lamp)
	lamp.position = Vector3(-2.2, 2.6, 22.4)
	var lantern := OmniLight3D.new()
	lantern.light_color = Color("ffb35c")
	lantern.light_energy = 1.2
	lantern.omni_range = 2.0
	lights.add_child(lantern)
	lantern.position = Vector3(0.75, 1.1, 26.1)
	# Dusty air only inside the garage, so the window light reads as shafts.
	var dust := FogVolume.new()
	dust.size = Vector3(8.0, 4.2, 7.5)
	var fog := FogMaterial.new()
	fog.density = 0.012
	fog.albedo = Color("fff0d8")
	dust.material = fog
	lights.add_child(dust)
	dust.position = Vector3(-0.6, 2.1, 22.75)
	# Dim the garage's own ambient: the sky light floods an indoor room otherwise.
	var shade := ReflectionProbe.new()
	shade.size = Vector3(8.0, 4.4, 7.5)
	shade.interior = true
	shade.ambient_mode = ReflectionProbe.AMBIENT_COLOR
	shade.ambient_color = Color("6a5040")
	shade.ambient_color_energy = 0.6
	lights.add_child(shade)
	shade.position = Vector3(-0.6, 2.2, 22.75)

## Reparent the bag, its straps and chain under a pivot at the beam so it can swing.
func _hang_bag() -> void:
	bag_pivot = Node3D.new()
	bag_pivot.name = "BagPivot"
	scenery.add_child(bag_pivot)
	bag_pivot.position = BAG_TOP
	var parts: Array[Node3D] = []
	for node in stage_instance.find_children("Bag*", "Node3D", true, false):
		parts.append(node as Node3D)
	for part in parts:
		var keep := part.global_transform
		part.get_parent().remove_child(part)
		bag_pivot.add_child(part)
		part.global_transform = keep

## God rays as in the concept: soft additive beams from each window slanting down to the floor.
## Each beam is a quad turned about its own axis to face the garage camera.
func _garage_rays(parent: Node3D) -> void:
	var material := ShaderMaterial.new()
	material.shader = preload("res://shaders/sky/god_ray.gdshader")
	var view := garage_cam
	var beams := [[-0.1, 0.0, 0.09], [0.9, 0.0, 0.09], [0.15, 0.3, 0.045], [0.65, -0.25, 0.055], [0.4, 0.1, 0.035]]
	for beam: Array in beams:
		var x: float = beam[0]
		var start := Vector3(x, 3.25, 26.35)
		var end := Vector3(x - 2.6 + float(beam[1]), 0.0, 22.2)
		var axis := end - start
		var quad := MeshInstance3D.new()
		var mesh := QuadMesh.new()
		mesh.size = Vector2(1.1, axis.length())
		quad.mesh = mesh
		quad.material_override = material.duplicate()
		quad.material_override.set_shader_parameter("strength", float(beam[2]))
		quad.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		parent.add_child(quad)
		var up := axis.normalized()
		var to_view := (view - (start + end) * 0.5)
		var normal := (to_view - up * to_view.dot(up)).normalized()
		var side := up.cross(normal)
		quad.global_transform = Transform3D(Basis(side, up, normal), (start + end) * 0.5)

## Turn around to the training garage (on = true) or back to the beach menu view.
func focus_garage(on: bool) -> void:
	garage_target = 1.0 if on else 0.0

func garage_open() -> bool:
	return garage_target > 0.0 and garage_flight >= 1.0

func focus_board(on: bool) -> void:
	board_target = 1.0 if on else 0.0

func board_open() -> bool:
	return board_target > 0.0 and board_flight >= 1.0

## Screen rectangle of the parchment, valid once the camera has stopped at the board.
func board_screen_rect() -> Rect2:
	if board_panel == null:
		return Rect2()
	var aabb := board_panel.get_aabb()
	var points := PackedVector2Array()
	for i in 8:
		points.append(camera.unproject_position(board_panel.global_transform * aabb.get_endpoint(i)))
	var rect := Rect2(points[0], Vector2.ZERO)
	for point in points:
		rect = rect.expand(point)
	return rect

func _update_menu_camera(delta: float) -> bool:
	"""Board flight and arcade select shot; returns true while one of them drives the camera."""
	if board_path != null and board_path.point_count > 1 and (board_flight > 0.0 or board_target > 0.0):
		var was := board_flight
		board_flight = move_toward(board_flight, board_target, delta / BOARD_FLIGHT_TIME)
		var t := board_flight * board_flight * (3.0 - 2.0 * board_flight)
		var length := board_path.get_baked_length()
		camera.position = board_path.sample_baked(t * length, true)
		var ahead := board_path.sample_baked(minf(length, t * length + 3.0), true) + Vector3(0, -0.15, 0)
		var look := MENU_LOOK.lerp(ahead, smoothstep(0.0, 0.25, t))
		look = look.lerp(board_look, smoothstep(0.55, 1.0, t))
		camera.look_at(look)
		camera.h_offset = 0.0
		if was < 1.0 and board_flight >= 1.0:
			board_ready.emit()
		elif was > 0.0 and board_flight <= 0.0:
			board_closed.emit()
		return true
	if garage_cam != Vector3.ZERO and (garage_flight > 0.0 or garage_target > 0.0):
		var was := garage_flight
		garage_flight = move_toward(garage_flight, garage_target, delta / GARAGE_TURN_TIME)
		# One ease-in-out over the whole move (quintic: no jolt at start or stop); the turn
		# leads and the walk to the gate trails, sharing that single eased timeline.
		var f := garage_flight
		var eased := f * f * f * (f * (f * 6.0 - 15.0) + 10.0)
		var turn := clampf(eased / 0.8, 0.0, 1.0)
		var walk := clampf((eased - 0.2) / 0.8, 0.0, 1.0)
		var start := Vector3(1.2, 2.8, 12.2)
		camera.position = start.lerp(garage_cam, walk)
		# Indoors: less sky ambient so the window light and the lamp model the room.
		world_env.environment.ambient_light_energy = lerpf(0.32, 0.36, walk)
		var from_dir := (MENU_LOOK - start).normalized()
		var to_dir := (garage_look - garage_cam).normalized()
		# Turn through the sea side (the right), not across the foliage wall on the left.
		var yaw0 := atan2(from_dir.x, from_dir.z)
		var yaw1 := atan2(to_dir.x, to_dir.z)
		if yaw1 > yaw0:
			yaw1 -= TAU
		var yaw := lerpf(yaw0, yaw1, turn)
		var pitch := lerpf(asin(from_dir.y), asin(to_dir.y), turn)
		var dir := Vector3(sin(yaw) * cos(pitch), sin(pitch), cos(yaw) * cos(pitch))
		camera.look_at(camera.position + dir)
		camera.h_offset = 0.0
		if was < 1.0 and garage_flight >= 1.0:
			garage_ready.emit()
		elif was > 0.0 and garage_flight <= 0.0:
			garage_closed.emit()
		return true
	if patio_shot and patio_cam != Vector3.ZERO:
		# Still camera with a barely-there drift (the stall texts must not swim).
		camera.position = patio_cam + Vector3(sin(clock * 0.2) * 0.03, sin(clock * 0.27) * 0.015, 0)
		camera.look_at(patio_look)
		camera.h_offset = 0.0
		if is_instance_valid(select_view):
			select_view.rotation.y = lerp_angle(select_view.rotation.y, _patio_facing() + select_turn, 1.0 - exp(-8.0 * delta))
		return true
	if select_shot:
		camera.position = camera.position.lerp(SELECT_CAM, 1.0 - exp(-4.0 * delta))
		camera.look_at(SELECT_LOOK)
		camera.h_offset = 0.0
		if is_instance_valid(select_view):
			select_view.rotation.y = lerp_angle(select_view.rotation.y, SELECT_FACING + select_turn, 1.0 - exp(-8.0 * delta))
		return true
	return false

## Arcade select: show (or replace) the chosen fighter standing on the beach.
func show_select_fighter(data: GaleData, id: String, palette: int) -> void:
	select_shot = true
	if is_instance_valid(select_view) and select_view.fighter_id == id:
		select_view.apply_palette(palette, data)
		return
	if is_instance_valid(select_view):
		select_view.queue_free()
	select_view = GaleFighterView.new()
	scenery.add_child(select_view)
	select_view.build(data, id, palette)
	select_view.position = patio_spot if patio_shot else SELECT_SPOT
	select_view.rotation.y = (_patio_facing() if patio_shot else SELECT_FACING) + select_turn
	select_view.scale = Vector3.ONE
	select_view.aura.visible = false
	select_view.play_clip("select", 0.0)

## Cut to the village patio (the caller hides the cut behind a fade to black).
func show_patio(on: bool) -> void:
	patio_shot = on and patio_cam != Vector3.ZERO
	_light_patio(patio_shot)
	if patio_shot:
		camera.position = patio_cam
		camera.look_at(patio_look)
		if is_instance_valid(select_view):
			select_view.position = patio_spot
			select_view.rotation.y = _patio_facing() + select_turn
	else:
		camera.position = Vector3(1.2, 2.8, 12.2)
		camera.look_at(MENU_LOOK)

## Late-afternoon light of the patio concept: a warm sun low from the upper left behind the big
## tree, its leaves dappling the cobbles (an unseen canopy that only casts shadows), warmer
## ambient. The beach light is put back when leaving.
var patio_saved := {}
var patio_gobo: Node3D

func _light_patio(on: bool) -> void:
	var env := world_env.environment
	if on:
		if patio_saved.is_empty():
			patio_saved = {"basis": sun.global_transform.basis, "energy": sun.light_energy, "color": sun.light_color,
				"ambient": env.ambient_light_color, "ambient_energy": env.ambient_light_energy, "fill": fill.light_energy}
		# Light travels toward the camera's right and a little toward it, from high on the left.
		var travel := Vector3(0.55, -0.62, 0.55).normalized()
		sun.global_transform = Transform3D(Basis.looking_at(travel, Vector3.UP), Vector3.ZERO)
		sun.light_energy = 0.95
		sun.light_color = Color("ffd9a6")
		sun.shadow_blur = 1.6
		env.ambient_light_color = Color("ffe7cc")
		env.ambient_light_energy = 0.4
		fill.light_energy = 0.06
		if not is_instance_valid(patio_gobo):
			patio_gobo = _leaf_gobo()
		patio_gobo.visible = true
	elif not patio_saved.is_empty():
		sun.global_transform = Transform3D(patio_saved.basis, Vector3.ZERO)
		sun.light_energy = patio_saved.energy
		sun.light_color = patio_saved.color
		env.ambient_light_color = patio_saved.ambient
		env.ambient_light_energy = patio_saved.ambient_energy
		fill.light_energy = patio_saved.fill
		patio_saved.clear()
		if is_instance_valid(patio_gobo):
			patio_gobo.visible = false

## Leaf cards high over the patio that are invisible but cast the dappled shadows.
func _leaf_gobo() -> Node3D:
	var root := Node3D.new()
	root.name = "PatioLeafShadows"
	scenery.add_child(root)
	var material := StandardMaterial3D.new()
	material.albedo_texture = load("res://assets/environments/beach/textures/folhas.png")
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
	material.alpha_scissor_threshold = 0.5
	material.cull_mode = BaseMaterial3D.CULL_DISABLED
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	var centre := patio_spot + Vector3(1.6, 0, -0.5)
	for i in 46:
		if rng.randf() < 0.5:
			continue  # gaps between the leaf clusters let the sun through
		var quad := MeshInstance3D.new()
		var mesh := QuadMesh.new()
		mesh.size = Vector2.ONE * rng.randf_range(1.1, 2.0)
		quad.mesh = mesh
		quad.material_override = material
		quad.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY
		root.add_child(quad)
		# Spread over the front half of the patio, then lifted up the light path so the
		# shadows land on the cobbles, the fighter and the stall front.
		var ground := centre + Vector3(rng.randf_range(-6.0, 5.0), 0, rng.randf_range(-3.0, 4.5))
		quad.position = ground + Vector3(-0.55, 0.62, -0.55).normalized() * rng.randf_range(6.0, 8.0)
		quad.rotation = Vector3(deg_to_rad(-90 + rng.randf_range(-25, 25)), rng.randf_range(0, TAU), 0)
	return root

## Yaw that turns the fighter (model forward -Z) toward the patio camera, a touch toward the stall.
func _patio_facing() -> float:
	var to_cam := patio_cam - patio_spot
	return atan2(-to_cam.x, -to_cam.z) + 0.25

func hide_select_fighter() -> void:
	select_shot = false
	select_turn = 0.0
	if is_instance_valid(select_view):
		select_view.queue_free()
	select_view = null

func _animate_living_pieces(delta: float, sim: GaleCombat) -> void:
	if is_instance_valid(bag_pivot):
		# A slow pendulum: two out-of-step sways (about 1.5 degrees) and a faint twist.
		bag_pivot.rotation = Vector3(
			deg_to_rad(sin(clock * 0.9) * 1.4 + sin(clock * 0.37) * 0.5),
			deg_to_rad(sin(clock * 0.21) * 3.0),
			deg_to_rad(sin(clock * 0.71 + 1.3) * 1.0))
	var drift := Vector2(sin(clock * 0.21) * 0.012, clock * 0.006)
	for water: Material in water_materials:
		if water is ShaderMaterial:
			(water as ShaderMaterial).set_shader_parameter("uv_offset", drift)
		else:
			(water as StandardMaterial3D).uv1_offset = Vector3(drift.x, drift.y, 0)
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

	if menu_mode and menu_scene_active and _update_menu_camera(delta):
		if is_instance_valid(select_view):
			select_view.present("select", clock)
	elif menu_mode:
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
	shake = 0.5 if event.kind in ["heavy", "ultimate", "clash", "ko"] else (0.32 if int(event.get("chain_step", 1)) == 3 else 0.2)
