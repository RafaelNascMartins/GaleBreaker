extends Node3D
## Bounded visual effects only. Hitboxes, travel and damage remain in GaleCombat.

var fighter_id := ""
var tint := Color.WHITE
var material: StandardMaterial3D
var pieces: Array[MeshInstance3D] = []
var rings: Array[MeshInstance3D] = []
var shards: Array[MeshInstance3D] = []
var fist: Array[MeshInstance3D] = []
var beam: MeshInstance3D
var glow: MeshInstance3D

func set_tint(color: Color) -> void:
	tint = color
	if material != null:
		material.albedo_color = Color(color, 1.0 if fighter_id == "tophia" else 0.72)
		material.emission = color * 0.35

func add_mesh(mesh: Mesh) -> MeshInstance3D:
	var node := MeshInstance3D.new()
	node.mesh = mesh
	node.material_override = material
	node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(node)
	pieces.append(node)
	return node

func configure(id: String, color: Color) -> void:
	fighter_id = id
	material = StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.transparency = BaseMaterial3D.TRANSPARENCY_DISABLED if id == "tophia" else BaseMaterial3D.TRANSPARENCY_ALPHA
	material.emission_enabled = id != "tophia"
	set_tint(color)
	for i in 7:
		var mesh := TorusMesh.new()
		mesh.inner_radius = 0.86
		mesh.outer_radius = 1.0
		mesh.rings = 28
		mesh.ring_segments = 6
		rings.append(add_mesh(mesh))
	for i in 12:
		var mesh := CylinderMesh.new()
		mesh.top_radius = 0.0
		mesh.bottom_radius = 0.15
		mesh.height = 0.35
		mesh.radial_segments = 5
		shards.append(add_mesh(mesh))
	if id == "tophia":
		for i in 5:
			var knuckle := BoxMesh.new()
			knuckle.size = Vector3(0.18, 0.23, 0.25)
			fist.append(add_mesh(knuckle))
	var cylinder := CylinderMesh.new()
	cylinder.top_radius = 0.14
	cylinder.bottom_radius = 0.09
	cylinder.height = 1.0
	cylinder.radial_segments = 12
	beam = add_mesh(cylinder)
	beam.rotation.x = PI / 2.0
	var sphere := SphereMesh.new()
	sphere.radius = 0.18
	sphere.height = 0.36
	glow = add_mesh(sphere)
	visible = false

func present(f: Dictionary, progress: float, muzzle: Vector3, hand: Vector3, foot: Vector3) -> void:
	for piece in pieces:
		piece.visible = false
	var kind := String(f.move.get("type", "light"))
	var active: bool = f.action == "active"
	var charging: bool = f.action == "startup" and kind in ["heavy", "ultimate"]
	visible = active or (fighter_id == "volt" and charging)
	if not visible:
		return
	var phase := clampf(progress, 0.0, 1.0)
	match fighter_id:
		"kaze":
			if kind == "ultimate":
				for i in rings.size():
					var ring := rings[i]
					ring.visible = true
					ring.position = Vector3(0, 0.18 + i * 0.35, -1.65)
					ring.scale = Vector3.ONE * (0.22 + i * 0.105 + sin(phase * TAU + i) * 0.025)
					ring.rotation = Vector3(sin(phase * TAU + i) * 0.12, phase * TAU + i, 0)
			elif kind in ["elemental", "heavy"]:
				for i in 3:
					var ring := rings[i]
					ring.visible = true
					ring.rotation.z = PI / 2.0
					ring.scale = Vector3.ONE * (0.30 + i * 0.10)
					ring.position = (foot if kind == "heavy" else Vector3(0, 1.20, -0.75 - phase * 1.6)) + Vector3(0, 0, -i * 0.13)
		"ignis":
			if kind == "light" and int(f.move.get("chain_step", 1)) < 3:
				return
			for i in 10:
				var shard := shards[i]
				shard.visible = true
				var angle := TAU * i / 10.0
				var radius := 0.22 + phase * 0.7
				shard.position = Vector3(cos(angle) * radius, 0.14 + sin(phase * PI) * 0.3, -0.7 + sin(angle) * radius)
				shard.scale = Vector3(0.8, (1.8 if kind == "ultimate" else 0.7) * (1.0 - phase * 0.7), 0.8)
				shard.rotation = Vector3(phase * 3.0, angle, 0.5)
			rings[0].visible = true
			rings[0].position = Vector3(0, 0.04, -0.75)
			rings[0].scale = Vector3.ONE * (0.22 + phase * 1.0)
		"tophia":
			if kind == "elemental":
				for i in 3:
					var stone := shards[i]
					var height := clampf(phase * 4.0 - i * 0.55, 0.0, 1.0) * (0.8 + i * 0.25)
					stone.visible = height > 0.01
					stone.position = Vector3(0, height * 0.5, -0.8 - i * 0.6)
					stone.scale = Vector3(2.5, height / 0.35, 2.5)
			elif kind == "ultimate":
				for i in 5:
					fist[i].visible = true
					fist[i].position = hand + Vector3((i % 3 - 1) * 0.20, floorf(i / 3.0) * 0.15, -0.65 - phase * 0.6)
					fist[i].scale = Vector3.ONE * 2.6
		"volt":
			glow.visible = true
			glow.position = muzzle
			glow.scale = Vector3.ONE * (0.3 + phase * 1.6 if charging else 0.6)
			if not active:
				return
			if kind == "elemental":
				glow.visible = false
				for i in 3:
					rings[i].visible = true
					rings[i].position = Vector3(0, 0.55 + i * 0.25, 0)
					rings[i].scale = Vector3.ONE * (0.25 + phase * 0.8)
			elif kind == "ultimate":
				beam.visible = true
				beam.position = muzzle + Vector3(0, 0, -1.3)
				beam.scale = Vector3(1.5, 2.6, 1.5)
			else:
				glow.position = muzzle + Vector3(0, 0, -phase * 1.5)
				glow.scale = Vector3.ONE * (1.5 if kind == "heavy" else 0.6)
