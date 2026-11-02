class_name GaleFighterView
extends Node3D

var fighter_id: String = "kaze"
var palette_index: int = 0
var catalog: GaleVisualCatalog
var scene_instance: Node3D
var model_pivot: Node3D
var skeleton: Skeleton3D
var anim_player: AnimationPlayer
var meshes: Array[MeshInstance3D] = []
var sockets: Dictionary = {}
var aura: MeshInstance3D
var material: ShaderMaterial
var accent: ShaderMaterial
var primary := Color.GREEN
var current_clip: String = ""
var current_anim_time: float = 0.0
var presentation_delta: float = 0.0
var last_sync_time: float = -1.0
var syncing := false
var move_effects: Node3D
var socket_bones := {}
var state_elapsed := 0.0
var last_state := ""
var locomotion_phase := 0.0
const MoveEffects = preload("res://scripts/move_effects.gd")

static func mat(color: Color, glow: bool = false) -> ShaderMaterial:
	var result := ShaderMaterial.new()
	result.shader = preload("res://scripts/toon.gdshader")
	result.set_shader_parameter("base_color", color)
	result.set_shader_parameter("glow", glow)
	result.set_shader_parameter("use_textures", false)
	return result

static func box(parent: Node3D, size: Vector3, pos: Vector3, color_material: Material) -> MeshInstance3D:
	var mesh := BoxMesh.new()
	mesh.size = size
	var instance := MeshInstance3D.new()
	instance.mesh = mesh
	instance.material_override = color_material
	instance.position = pos
	parent.add_child(instance)
	return instance

static func orb(parent: Node3D, radius: float, pos: Vector3, color_material: Material) -> MeshInstance3D:
	var mesh := SphereMesh.new()
	mesh.radius = radius
	mesh.height = radius * 2.0
	mesh.radial_segments = 12
	mesh.rings = 6
	var instance := MeshInstance3D.new()
	instance.mesh = mesh
	instance.material_override = color_material
	instance.position = pos
	parent.add_child(instance)
	return instance

static func _collect_nodes(node: Node, out_meshes: Array[MeshInstance3D], out_state: Dictionary) -> void:
	if node is MeshInstance3D:
		out_meshes.append(node as MeshInstance3D)
	elif node is Skeleton3D and out_state.get("skeleton") == null:
		out_state["skeleton"] = node
	elif node is AnimationPlayer and out_state.get("anim_player") == null:
		out_state["anim_player"] = node
	for child in node.get_children():
		_collect_nodes(child, out_meshes, out_state)

func build(data: GaleData, id: String, palette: int) -> void:
	fighter_id = id
	palette_index = posmod(palette, 4)
	catalog = GaleVisualCatalog.load_for(id)
	var swatch: Array = data.palette(id, palette_index).swatch
	var v2_pal: Dictionary = catalog.palettes[palette_index] if catalog.palettes.size() > palette_index else {
		"primary": swatch[0], "secondary": swatch[1], "accent": swatch[2]
	}
	primary = Color(v2_pal.primary)
	accent = mat(Color(v2_pal.accent), true)

	var base_mat: ShaderMaterial = load(catalog.material_path) as ShaderMaterial
	if base_mat != null:
		material = base_mat.duplicate() as ShaderMaterial
	else:
		material = mat(primary)
		material.set_shader_parameter("use_textures", true)
		material.set_shader_parameter("albedo_tex", load(catalog.albedo_path))
		material.set_shader_parameter("mask_tex", load(catalog.mask_path))
		material.set_shader_parameter("normal_tex", load(catalog.normal_path))

	apply_palette(palette_index, data)

	var packed: PackedScene = load(catalog.scene_path) as PackedScene
	scene_instance = packed.instantiate() as Node3D
	add_child(scene_instance)
	model_pivot = scene_instance.get_node_or_null("ModelPivot") as Node3D

	meshes.clear()
	var found := {}
	_collect_nodes(scene_instance, meshes, found)
	skeleton = found.get("skeleton") as Skeleton3D
	anim_player = found.get("anim_player") as AnimationPlayer
	if anim_player != null:
		anim_player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL

	for m: MeshInstance3D in meshes:
		m.material_override = material

	sockets.clear()
	for sname: String in ["socket_root", "socket_chest", "socket_hand_l", "socket_hand_r", "socket_foot_r", "socket_muzzle"]:
		var marker := scene_instance.get_node_or_null(sname) as Node3D
		if marker != null:
			sockets[sname] = marker
	var bindings := {"socket_root":"root", "socket_chest":"chest", "socket_hand_l":"hand_l", "socket_hand_r":"hand_r", "socket_foot_r":"foot_r", "socket_muzzle":"cannon"}
	for sname: String in bindings:
		socket_bones[sname] = skeleton.find_bone(bindings[sname])

	var torus := TorusMesh.new()
	torus.inner_radius = 0.44
	torus.outer_radius = 0.47
	torus.rings = 20
	torus.ring_segments = 8
	aura = MeshInstance3D.new()
	aura.mesh = torus
	aura.material_override = accent
	aura.position.y = 0.03
	add_child(aura)

	move_effects = MoveEffects.new()
	add_child(move_effects)
	move_effects.configure(fighter_id, primary if fighter_id == "tophia" else Color(v2_pal.accent))

	play_clip("idle", 0.0)

func apply_palette(palette: int, data: GaleData = null) -> void:
	palette_index = posmod(palette, 4)
	if catalog == null:
		catalog = GaleVisualCatalog.load_for(fighter_id)
	var v2_pal: Dictionary = catalog.palettes[palette_index]
	primary = Color(v2_pal.primary)
	var sec := Color(v2_pal.secondary)
	var acc := Color(v2_pal.accent)
	if material != null:
		material.set_shader_parameter("base_color", primary)
		material.set_shader_parameter("palette_primary", primary)
		material.set_shader_parameter("palette_secondary", sec)
		material.set_shader_parameter("palette_accent", acc)
	if accent != null:
		accent.set_shader_parameter("base_color", acc)
	if is_instance_valid(move_effects):
		move_effects.set_tint(primary if fighter_id == "tophia" else acc)
	if data != null and false:
		pass

func is_valid_asset() -> bool:
	if skeleton == null or skeleton.get_bone_count() < 15:
		return false
	if anim_player == null:
		return false
	var list := anim_player.get_animation_list()
	for req: String in GaleVisualCatalog.REQUIRED_CLIPS:
		var mapped: String = catalog.clips.get(req, req)
		if mapped not in list:
			return false
	if material == null or not bool(material.get_shader_parameter("use_textures")):
		return false
	if material.get_shader_parameter("albedo_tex") == null or material.get_shader_parameter("mask_tex") == null:
		return false
	for sname: String in ["socket_root", "socket_chest", "socket_hand_l", "socket_hand_r", "socket_foot_r", "socket_muzzle"]:
		if not sockets.has(sname):
			return false
	return scale.x > 0.0 and scale.y > 0.0 and meshes.size() > 0

func play_clip(logical_name: String, seek_sec: float = 0.0) -> void:
	if anim_player == null:
		return
	var clip_name: String = catalog.clips.get(logical_name, logical_name) if catalog != null else logical_name
	if not anim_player.has_animation(clip_name):
		return
	var changed := current_clip != clip_name
	# Re-sampling an in-progress crossfade at zero delta can change the pose even
	# though its clock is frozen. Keep the last evaluated pose through hitstop.
	if not changed and is_equal_approx(current_anim_time, seek_sec) and (not syncing or presentation_delta <= 0.0):
		_update_sockets()
		return
	current_clip = clip_name
	current_anim_time = seek_sec
	if changed:
		var blend := 0.045 if logical_name.begins_with("light") or logical_name in ["heavy", "hit", "parry"] else 0.09
		anim_player.play(clip_name, blend if syncing else 0.0, 0.0)
	anim_player.seek(seek_sec, false)
	anim_player.advance(presentation_delta if syncing else 0.0)
	_update_sockets()

func _update_sockets() -> void:
	if skeleton == null:
		return
	for sname: String in socket_bones:
		var index: int = socket_bones[sname]
		if index < 0:
			continue
		var pose := skeleton.get_bone_global_pose(index)
		if sname == "socket_muzzle":
			pose.origin += pose.basis * Vector3(0, 0.55, -0.055)
		sockets[sname].global_transform = skeleton.global_transform * pose

func socket_position(sname: String) -> Vector3:
	return to_local(sockets[sname].global_position) if sockets.has(sname) else Vector3.ZERO

func sync(f: Dictionary, time: float) -> void:
	presentation_delta = clampf(time - last_sync_time, 0.0, 1.0 / 15.0) if last_sync_time >= 0.0 else 0.0
	last_sync_time = time
	var state_key: String = "victory" if bool(f.get("presentation_victory", false)) else ("ko" if int(f.hp) <= 0 else String(f.action))
	state_elapsed = state_elapsed + presentation_delta if state_key == last_state else 0.0
	last_state = state_key
	syncing = true
	position = Vector3(f.x, f.y, 0)
	rotation.y = -PI / 2.0 if f.facing > 0 else PI / 2.0
	scale = Vector3.ONE

	move_effects.visible = false

	if state_key == "victory":
		play_clip("victory", minf(state_elapsed, 40.0 / 60.0))
	elif state_key == "ko":
		play_clip("ko", minf(state_elapsed, 30.0 / 60.0))
	elif f.action in ["startup", "active", "recovery"] and not f.move.is_empty():
		var mtype: String = String(f.move.get("type", "light"))
		var clip := mtype
		if mtype == "light":
			clip = "light_%d" % clampi(int(f.move.get("chain_step", 1)), 1, 3)
		elif mtype == "heavy" and String(f.move.get("animStyle", "")) == "low_sweep":
			clip = "sweep"

		var total_frames := maxi(1, int(f.get("phase_total", f.frames)))
		var progress := clampf(1.0 - float(maxi(0, int(f.frames))) / float(total_frames), 0.0, 1.0)
		var seek_sec := 0.0
		match String(f.action):
			"startup":
				seek_sec = lerpf(0.0, 6.0 / 60.0, progress)
			"active":
				seek_sec = lerpf(6.0 / 60.0, 12.0 / 60.0, progress)
			"recovery":
				seek_sec = lerpf(12.0 / 60.0, 24.0 / 60.0, progress)
		play_clip(clip, seek_sec)
		move_effects.present(f, progress, socket_position("socket_muzzle"), socket_position("socket_hand_r"), socket_position("socket_foot_r"))
	elif f.action == "knockdown":
		play_clip("knockdown", minf(state_elapsed, 24.0 / 60.0))
	elif f.action == "hitstun":
		play_clip("hit", minf(state_elapsed, 16.0 / 60.0))
	elif f.action == "parry":
		play_clip("parry", minf(state_elapsed, 16.0 / 60.0))
	elif f.action in ["guard", "blockstun"]:
		play_clip("guard_low" if f.crouch else "guard_high", 0.08)
	elif f.action == "dash":
		play_clip("dash", minf(state_elapsed, 10.0 / 60.0))
	elif not f.grounded:
		play_clip("jump_start" if float(f.vy) > 4.0 else "jump_air", 0.08)
	elif f.crouch:
		play_clip("crouch", 0.12)
	elif f.action == "walk":
		var forward: bool = float(f.vx) * float(f.facing) >= 0.0
		var w_clip := "walk_forward" if forward else "walk_back"
		locomotion_phase = fmod(locomotion_phase + absf(float(f.vx)) * presentation_delta * 0.4 / 0.85, 0.4)
		play_clip(w_clip, locomotion_phase)
	else:
		play_clip("idle", fmod(time * 0.65, 40.0 / 60.0))

	aura.scale = Vector3.ONE * (1.2 + sin(time * 6.0) * 0.1 if f.boss else 1.0)
	if material != null:
		material.set_shader_parameter("flash_amount", 1.0 if int(f.flash) > 0 else 0.0)
		material.set_shader_parameter("base_color", Color.WHITE if int(f.flash) > 0 else primary)
	syncing = false

