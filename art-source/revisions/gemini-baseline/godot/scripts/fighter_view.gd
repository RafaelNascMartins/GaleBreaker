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
var move_vfx: MeshInstance3D
var vfx_secondary: MeshInstance3D
var material: ShaderMaterial
var accent: ShaderMaterial
var primary := Color.GREEN
var current_clip: String = ""
var current_anim_time: float = 0.0

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

	for m: MeshInstance3D in meshes:
		m.material_override = material

	sockets.clear()
	for sname: String in ["socket_root", "socket_chest", "socket_hand_l", "socket_hand_r", "socket_foot_r", "socket_muzzle"]:
		var marker := scene_instance.get_node_or_null(sname) as Node3D
		if marker != null:
			sockets[sname] = marker

	var torus := TorusMesh.new()
	torus.inner_radius = 0.63
	torus.outer_radius = 0.72
	torus.rings = 20
	torus.ring_segments = 8
	aura = MeshInstance3D.new()
	aura.mesh = torus
	aura.material_override = accent
	aura.position.y = 0.03
	add_child(aura)

	move_vfx = orb(self, 0.48, Vector3(0, 1.15, -1.1), accent)
	move_vfx.visible = false
	vfx_secondary = box(self, Vector3(0.45, 0.45, 0.45), Vector3(0, 0.4, -1.4), accent)
	vfx_secondary.visible = false

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
	current_clip = clip_name
	current_anim_time = seek_sec
	anim_player.play(clip_name, 0.0, 0.0)
	anim_player.seek(seek_sec, true)
	anim_player.advance(0.0)

func sync(f: Dictionary, time: float) -> void:
	position = Vector3(f.x, f.y, 0)
	rotation.y = -PI / 2.0 if f.facing > 0 else PI / 2.0
	scale = Vector3.ONE

	move_vfx.visible = false
	vfx_secondary.visible = false

	if f.action in ["startup", "active", "recovery"] and not f.move.is_empty():
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
		_update_attack_vfx(f, mtype, progress)
	elif int(f.get("hp", 1)) <= 0:
		play_clip("ko", 0.35)
	elif f.action == "knockdown":
		var kd_sec := 0.20 if f.grounded else 0.08
		play_clip("knockdown", kd_sec)
	elif f.action == "hitstun":
		play_clip("hit", 0.06)
	elif f.action == "parry":
		play_clip("parry", 0.08)
	elif f.action in ["guard", "blockstun"]:
		play_clip("guard_low" if f.crouch else "guard_high", 0.08)
	elif f.action == "dash":
		play_clip("dash", 0.08)
	elif not f.grounded:
		play_clip("jump_start" if float(f.vy) > 4.0 else "jump_air", 0.08)
	elif f.crouch:
		play_clip("crouch", 0.12)
	elif f.action == "walk":
		var forward: bool = float(f.vx) * float(f.facing) >= 0.0
		var w_clip := "walk_forward" if forward else "walk_back"
		play_clip(w_clip, fmod(time * 1.1, 24.0 / 60.0))
	else:
		play_clip("idle", fmod(time * 0.65, 40.0 / 60.0))

	aura.scale = Vector3.ONE * (1.2 + sin(time * 6.0) * 0.1 if f.boss else 1.0)
	if material != null:
		material.set_shader_parameter("flash_amount", 1.0 if int(f.flash) > 0 else 0.0)
		material.set_shader_parameter("base_color", Color.WHITE if int(f.flash) > 0 else primary)

func _update_attack_vfx(f: Dictionary, mtype: String, progress: float) -> void:
	if f.action != "active":
		return
	var chain_step := int(f.move.get("chain_step", 1))
	match fighter_id:
		"kaze":
			if mtype == "heavy":
				# Chute do Vendaval: Jade wind crescent at foot
				move_vfx.visible = true
				move_vfx.position = sockets["socket_foot_r"].position + Vector3(0, 0.75, -0.9)
				move_vfx.scale = Vector3(1.1, 0.35, 1.8)
			elif mtype == "elemental":
				# Rajada de Vento: Traveling horizontal jade wind wave
				move_vfx.visible = true
				move_vfx.position = Vector3(0, 1.25, -1.4 - progress * 2.8)
				move_vfx.scale = Vector3(1.1, 1.2, 2.4)
			elif mtype == "ultimate":
				# Tufão Celestial: Towering vertical jade tornado ahead of Kaze
				move_vfx.visible = true
				move_vfx.position = Vector3(0, 1.6, -2.5)
				move_vfx.scale = Vector3(1.6, 3.2, 1.6)
		"ignis":
			if (mtype == "light" and chain_step == 3) or mtype == "heavy":
				# Soco de Roça J3 / Marreta Caipira: Ground slam shockwave
				vfx_secondary.visible = true
				vfx_secondary.position = Vector3(0, 0.15, -1.25)
				vfx_secondary.scale = Vector3(1.8, 0.25, 1.8)
			elif mtype == "elemental":
				# Pisada da Fornalha: Low radial fire & dust burst at boot
				move_vfx.visible = true
				move_vfx.position = Vector3(0, 0.32, -1.1)
				move_vfx.scale = Vector3(2.1, 0.45, 2.1)
			elif mtype == "ultimate":
				# Fúria do Meio-Dia: Huge solar sunburst around shoulder charge
				move_vfx.visible = true
				move_vfx.position = Vector3(0, 1.35, -1.6)
				move_vfx.scale = Vector3(2.2, 2.0, 2.8)
		"tophia":
			if (mtype == "light" and chain_step == 3) or mtype == "heavy":
				# Punho de Arenito J3 / Martelo de Pedra: Rock fragments & dust splash
				vfx_secondary.visible = true
				vfx_secondary.position = Vector3(0, 0.25, -1.3)
				vfx_secondary.scale = Vector3(1.6, 0.55, 1.6)
			elif mtype == "elemental":
				# Erupção Rochosa: Sequential rising orange sandstone spires
				vfx_secondary.visible = true
				vfx_secondary.position = Vector3(0, 0.75, -1.5 - progress * 2.4)
				vfx_secondary.scale = Vector3(0.9, 2.4, 1.4)
			elif mtype == "ultimate":
				# Colosso de Terra: Colossal projected orange stone fist
				move_vfx.visible = true
				move_vfx.position = Vector3(0, 1.45, -2.6)
				move_vfx.scale = Vector3(2.0, 1.9, 3.2)
		"volt":
			if mtype == "light":
				# Tiro de Sucata: J1 standing bolt, J2 crouched low bolt, J3 two-handed burst
				move_vfx.visible = true
				var h_y := 0.68 if chain_step == 2 else 1.18
				var reach := 1.8 if chain_step < 3 else 2.4
				move_vfx.position = Vector3(-0.15, h_y, -0.95 - progress * reach)
				move_vfx.scale = Vector3(0.42, 0.42, 1.2 if chain_step == 3 else 0.75)
			elif mtype == "heavy":
				# Disparo Carregado: Large slow cyan plasma orb
				move_vfx.visible = true
				move_vfx.position = Vector3(0, 1.18, -1.2 - progress * 2.2)
				move_vfx.scale = Vector3(1.15, 1.15, 1.35)
			elif mtype == "elemental":
				# Curto-Circuito: Circular cyan electric pulse around Volt
				move_vfx.visible = true
				move_vfx.position = Vector3(0, 1.05, -0.2)
				move_vfx.scale = Vector3(2.3, 1.5, 2.3)
			elif mtype == "ultimate":
				# Sobrecarga Total: Massive horizontal cyan beam
				move_vfx.visible = true
				move_vfx.position = Vector3(0, 1.20, -2.8)
				move_vfx.scale = Vector3(1.1, 1.1, 4.6)
