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
# Set when a foot lands during the walk cycle; main.gd plays the step and clears it.
var footfall_pending := false
const IDLE_SPEED := 0.5
var flashes_enabled := true
var shake_strength := 0.65
var contact_shadow: MeshInstance3D
# Presentation-only motion layer (squash/stretch, lean, hit shake, limb trails).
# It never touches combat hitboxes, which live in combat.gd.
var pivot_base := Transform3D.IDENTITY
var fx_squash := 0.0
var fx_lean := 0.0
var fx_shake := 0.0
var land_timer := 0.0
var was_grounded := true
var trail: MeshInstance3D
var trail_mesh: ImmediateMesh
var trail_points: Array = []
const TRAIL_LIFE := 0.14
const MOVE_WEIGHT := {"light": 0.6, "heavy": 1.0, "elemental": 0.9, "ultimate": 1.3}
const TRAIL_LIMBS := {
	"kaze": {"light_2": "socket_hand_l", "light_3": "socket_foot_r", "heavy": "socket_foot_r"},
	"ignis": {"light_2": "socket_hand_l", "elemental": "socket_foot_r", "ultimate": "socket_chest"},
}
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
	if model_pivot!=null:model_pivot.position.y=0.025
	if model_pivot != null:
		pivot_base = model_pivot.transform

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
	aura.position.y = 0.04
	add_child(aura)
	var shadow_plane:=PlaneMesh.new()
	shadow_plane.size=Vector2(0.9,0.55)
	contact_shadow=MeshInstance3D.new()
	contact_shadow.mesh=shadow_plane
	var shadow_mat:=ShaderMaterial.new()
	shadow_mat.shader=preload("res://scripts/contact_shadow.gdshader")
	contact_shadow.material_override=shadow_mat
	contact_shadow.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(contact_shadow)
	trail_mesh = ImmediateMesh.new()
	trail = MeshInstance3D.new()
	trail.mesh = trail_mesh
	trail.top_level = true
	trail.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var trail_mat := StandardMaterial3D.new()
	trail_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	trail_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	trail_mat.vertex_color_use_as_albedo = true
	trail_mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	trail.material_override = trail_mat
	add_child(trail)

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

	var attack_clip := ""
	if state_key == "victory":
		play_clip("victory", minf(state_elapsed, GaleAnimTiming.state_sec(fighter_id, "victory")))
	elif state_key == "ko":
		play_clip("ko", minf(state_elapsed, GaleAnimTiming.state_sec(fighter_id, "ko")))
	elif f.action in ["startup", "active", "recovery"] and not f.move.is_empty():
		var mtype: String = String(f.move.get("type", "light"))
		var clip := mtype
		if mtype == "light":
			clip = "light_%d" % clampi(int(f.move.get("chain_step", 1)), 1, 3)
		elif mtype == "heavy" and String(f.move.get("animStyle", "")) == "low_sweep":
			clip = "sweep"

		var total_frames := maxi(1, int(f.get("phase_total", f.frames)))
		var progress := clampf(1.0 - float(maxi(0, int(f.frames))) / float(total_frames), 0.0, 1.0)
		play_clip(clip, GaleAnimTiming.attack_seek(fighter_id, clip, String(f.action), progress))
		attack_clip = clip
		if f.move.get("delivery","melee") == "melee" or (f.id == "volt" and f.action == "startup"):
			move_effects.present(f, progress, socket_position("socket_muzzle"), socket_position("socket_hand_r"), socket_position("socket_foot_r"))
	elif f.action == "knockdown":
		play_clip("knockdown", minf(state_elapsed, GaleAnimTiming.state_sec(fighter_id, "knockdown")))
	elif f.action == "hitstun":
		play_clip("hit", minf(state_elapsed, GaleAnimTiming.state_sec(fighter_id, "hit")))
	elif f.action == "parry":
		play_clip("parry", minf(state_elapsed, GaleAnimTiming.state_sec(fighter_id, "parry")))
	elif f.action in ["guard", "blockstun"]:
		if f.crouch:
			play_clip("guard_low", 0.08)
		else:
			# Each block replays the brace-and-rebound before holding the guard.
			play_clip("guard_high", minf(state_elapsed, GaleAnimTiming.state_sec(fighter_id, "guard_high")))
	elif f.action == "dash":
		play_clip("dash", minf(state_elapsed, GaleAnimTiming.state_sec(fighter_id, "dash")))
	elif not f.grounded:
		play_clip("jump_start" if float(f.vy) > 4.0 else "jump_air", 0.08)
	elif f.crouch:
		play_clip("crouch", 0.12)
	elif f.action == "walk":
		var forward: bool = float(f.vx) * float(f.facing) >= 0.0
		var w_clip := "walk_forward" if forward else "walk_back"
		var cycle := GaleAnimTiming.state_sec(fighter_id, "walk")
		var previous := locomotion_phase
		locomotion_phase = fmod(locomotion_phase + absf(float(f.vx)) * presentation_delta * cycle / GaleAnimTiming.stride(fighter_id), cycle)
		# Two footfalls per cycle: when the phase wraps and when it crosses the middle.
		if locomotion_phase < previous or (previous < cycle * 0.5 and locomotion_phase >= cycle * 0.5):
			footfall_pending = true
		play_clip(w_clip, locomotion_phase)
	else:
		play_clip("idle", fmod(time * IDLE_SPEED, GaleAnimTiming.state_sec(fighter_id, "idle")))
	_update_motion_fx(f, attack_clip)

	aura.scale = Vector3.ONE * (1.2 + sin(time * 6.0) * 0.1 if f.boss else 1.0)
	aura.visible=bool(f.boss)
	contact_shadow.position.y=-float(f.y)+0.04
	contact_shadow.scale=Vector3.ONE/(1.0+float(f.y)*0.15)
	if material != null:
		material.set_shader_parameter("flash_amount", 1.0 if flashes_enabled and int(f.flash) > 0 else 0.0)
		material.set_shader_parameter("base_color", Color.WHITE if flashes_enabled and int(f.flash) > 0 else primary)
	syncing = false


func _update_motion_fx(f: Dictionary, attack_clip: String) -> void:
	var squash := 0.0
	var lean := 0.0
	var shake := 0.0
	var grounded := bool(f.get("grounded", true))
	if grounded and not was_grounded:
		land_timer = 0.12
	was_grounded = grounded
	land_timer = maxf(0.0, land_timer - presentation_delta)
	var action := String(f.action)
	if attack_clip != "":
		var weight: float = MOVE_WEIGHT.get(String(f.move.get("type", "light")), 0.6)
		var heavy_body := 1.3 if fighter_id == "ignis" else 1.0
		var progress := clampf(1.0 - float(maxi(0, int(f.frames))) / float(maxi(1, int(f.get("phase_total", f.frames)))), 0.0, 1.0)
		match action:
			"startup":
				# Load: crouch into the wind-up and lean away from the target.
				squash = 0.07 * weight * heavy_body * progress
				lean = -0.07 * weight * progress
			"active":
				# Release: stretch through the strike and throw the body forward.
				squash = -0.08 * weight * (1.0 - progress * 0.5) * (1.2 if fighter_id == "kaze" else 1.0)
				lean = 0.13 * weight
			_:
				squash = 0.03 * weight * heavy_body * (1.0 - progress)
				lean = 0.05 * weight * (1.0 - progress)
	elif action == "hitstun" or action == "knockdown":
		var decay := clampf(1.0 - state_elapsed / GaleAnimTiming.state_sec(fighter_id, "hit"), 0.0, 1.0)
		squash = 0.06 * decay
		lean = -0.2 * decay
		shake = sin(state_elapsed * 95.0) * 0.035 * decay * shake_strength / 0.65
	elif action == "dash":
		squash = -0.04
		lean = 0.14
	elif not grounded:
		squash = -0.05 if float(f.vy) > 0.0 else 0.0
	if land_timer > 0.0:
		squash += 0.12 * land_timer / 0.12
	# Follow the target at presentation speed; hitstop (zero delta) freezes the pose.
	var blend := 1.0 - exp(-presentation_delta * 28.0)
	fx_squash = lerpf(fx_squash, squash, blend)
	fx_lean = lerpf(fx_lean, lean, blend)
	fx_shake = shake if presentation_delta > 0.0 else fx_shake
	if model_pivot != null:
		var stretch := Basis.from_scale(Vector3(1.0 + fx_squash * 0.6, 1.0 - fx_squash, 1.0 + fx_squash * 0.6))
		# Forward is -Z in view space, so a forward lean tips the top toward -Z.
		model_pivot.transform = Transform3D(Basis(Vector3.RIGHT, -fx_lean) * stretch, Vector3(fx_shake, 0, 0)) * pivot_base
		# Sockets drive VFX origins, so they must match the pose actually drawn.
		_update_sockets()
	_update_trail(f, attack_clip)

func _update_trail(f: Dictionary, attack_clip: String) -> void:
	if trail == null:
		return
	var limbs: Dictionary = TRAIL_LIMBS.get(fighter_id, {})
	if presentation_delta > 0.0:
		for point: Dictionary in trail_points:
			point.age += presentation_delta
		trail_points = trail_points.filter(func(point: Dictionary) -> bool: return point.age < TRAIL_LIFE)
		if attack_clip != "" and String(f.action) == "active" and fighter_id in TRAIL_LIMBS:
			var socket_name: String = limbs.get(attack_clip, "socket_hand_r")
			if sockets.has(socket_name):
				trail_points.append({"pos": (sockets[socket_name] as Node3D).global_position, "age": 0.0,
					"width": 0.11 if String(f.move.get("type", "light")) in ["heavy", "ultimate"] else 0.06})
	trail_mesh.clear_surfaces()
	if trail_points.size() < 2:
		return
	var tint := Color(catalog.palettes[palette_index].accent) if catalog != null else Color.WHITE
	trail_mesh.surface_begin(Mesh.PRIMITIVE_TRIANGLE_STRIP)
	for point: Dictionary in trail_points:
		var life: float = 1.0 - float(point.age) / TRAIL_LIFE
		var half: float = float(point.width) * life
		trail_mesh.surface_set_color(Color(tint, 0.55 * life))
		trail_mesh.surface_add_vertex(point.pos + Vector3.UP * half)
		trail_mesh.surface_set_color(Color(tint, 0.55 * life))
		trail_mesh.surface_add_vertex(point.pos - Vector3.UP * half)
	trail_mesh.surface_end()
