extends Node3D
## Every visible attack is positioned from the combat simulation's entity.

# palettes whose thrown bomb is the dynamite stick (visual_catalog "prop": "Dinamite"): Orsted's
# gunslinger outfit
const DYNAMITE_PALETTES := {"volt": [2]}

var views := {}

func reset() -> void:
	for node: Node3D in views.values():
		node.queue_free()
	views.clear()

func material(color: Color, alpha: float = 1.0) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(color,alpha)
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA if alpha < 1.0 else BaseMaterial3D.TRANSPARENCY_DISABLED
	return mat

func mesh_node(parent: Node3D, mesh: Mesh, mat: Material, pos: Vector3 = Vector3.ZERO) -> MeshInstance3D:
	var node := MeshInstance3D.new()
	node.mesh = mesh
	node.material_override = mat
	node.position = pos
	node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(node)
	return node

func ring(parent: Node3D, mat: Material, radius: float) -> MeshInstance3D:
	var torus := TorusMesh.new()
	torus.inner_radius = radius * 0.89
	torus.outer_radius = radius
	torus.rings = 28
	torus.ring_segments = 5
	return mesh_node(parent,torus,mat)

func build(e: Dictionary) -> Node3D:
	var node := Node3D.new()
	add_child(node)
	var color := Color("50caa0") if e.fighter=="kaze" else Color("f78a37") if e.fighter=="ignis" else Color("ce6d2d") if e.fighter=="tophia" else Color("2ee0f5")
	var solid := material(color)
	var soft := material(color,0.5)
	var warning := BoxMesh.new()
	warning.size = Vector3(e.width,0.025,0.65)
	var telegraph := mesh_node(node,warning,material(color,0.45))
	telegraph.name = "Warning"
	var body := Node3D.new()
	body.name = "Body"
	node.add_child(body)
	match String(e.kind):
		"bolt","charged_bolt":
			var sphere := SphereMesh.new()
			sphere.radius = float(e.width)*0.5
			sphere.height = float(e.height)
			mesh_node(body,sphere,solid)
			var trail := BoxMesh.new()
			trail.size = Vector3(e.width*1.5,e.height*0.35,0.08)
			mesh_node(body,trail,soft,Vector3(-e.facing*e.width*0.6,0,0))
		"wave":
			for i in 3:
				var swirl := ring(body,soft,0.42+i*0.07)
				swirl.rotation.x = PI/2.0
				swirl.position.x = i*0.12
		"vortex":
			for i in 8:
				var swirl := ring(body,soft,0.2+i*0.08)
				swirl.position.y = -1.4+i*0.37
		"stone":
			var chunk := BoxMesh.new()
			chunk.size = Vector3(e.width, e.height, 0.42)
			mesh_node(body,chunk,solid)
			var trail := BoxMesh.new()
			trail.size = Vector3(e.width*1.2,e.height*0.3,0.08)
			mesh_node(body,trail,soft,Vector3(-e.facing*e.width*0.7,0,0))
		"rock_spike":
			var spike := CylinderMesh.new()
			spike.top_radius = 0
			spike.bottom_radius = float(e.width)*0.5
			spike.height = e.height
			spike.radial_segments = 5
			mesh_node(body,spike,solid)
			var rock := BoxMesh.new()
			rock.size = Vector3(0.32,0.28,0.3)
			var flying := mesh_node(node,rock,solid)
			flying.name = "Rock"
		"bomb":
			# the blast: a hot core and expanding rings; the flying bomb (slate body, blue gem, copper
			# collar, like the prop in his hand) is the "Rock" node
			var core := SphereMesh.new()
			core.radius = 0.55
			core.height = 1.1
			mesh_node(body,core,material(Color("e3fcff"),0.85))
			var glow := SphereMesh.new()
			glow.radius = 0.85
			glow.height = 1.5
			mesh_node(body,glow,soft)
			for i in 2:
				var blast := ring(body,soft,0.75-i*0.2)
				blast.position.y = -float(e.y)+0.05+i*0.06
			var bomb := Node3D.new()
			bomb.name = "Rock"
			node.add_child(bomb)
			if int(e.get("palette", 0)) in DYNAMITE_PALETTES.get(String(e.fighter), []):
				# the gunslinger's dynamite: a red stick, a grey cap, the lit fuse's spark
				var stick := CylinderMesh.new()
				stick.top_radius = 0.026
				stick.bottom_radius = 0.026
				stick.height = 0.17
				stick.radial_segments = 8
				mesh_node(bomb,stick,material(Color("c62f28")))
				var cap := CylinderMesh.new()
				cap.top_radius = 0.028
				cap.bottom_radius = 0.028
				cap.height = 0.025
				cap.radial_segments = 8
				mesh_node(bomb,cap,material(Color("8a7a72")),Vector3(0,0.095,0))
				var spark := SphereMesh.new()
				spark.radius = 0.022
				spark.height = 0.044
				spark.radial_segments = 5
				spark.rings = 2
				mesh_node(bomb,spark,material(Color("ffc23a")),Vector3(0.012,0.13,0))
				return node
			var shell := SphereMesh.new()
			shell.radius = 0.085
			shell.height = 0.19
			shell.radial_segments = 8
			shell.rings = 4
			mesh_node(bomb,shell,material(Color("3b4250")))
			var gem := SphereMesh.new()
			gem.radius = 0.045
			gem.height = 0.09
			gem.radial_segments = 6
			gem.rings = 3
			mesh_node(bomb,gem,material(Color("2ee0f5")),Vector3(0,0,0.07))
			var collar := CylinderMesh.new()
			collar.top_radius = 0.05
			collar.bottom_radius = 0.05
			collar.height = 0.03
			collar.radial_segments = 8
			mesh_node(bomb,collar,material(Color("b8733a")),Vector3(0,0.09,0))
		"spikes":
			var stone := CylinderMesh.new()
			stone.top_radius = 0
			stone.bottom_radius = float(e.width)*0.5
			stone.height = e.height
			stone.radial_segments = 6
			mesh_node(body,stone,solid)
		"fist":
			var palm := BoxMesh.new()
			palm.size = Vector3(e.width*0.65,e.height*0.75,0.55)
			mesh_node(body,palm,solid)
			for i in 4:
				var knuckle := BoxMesh.new()
				knuckle.size = Vector3(0.23,e.height*0.23,0.6)
				mesh_node(body,knuckle,solid,Vector3(e.facing*0.3,-0.36+i*0.24,0))
		"beam":
			var beam := BoxMesh.new()
			beam.size = Vector3(e.width,e.height,0.25)
			mesh_node(body,beam,soft)
			var core := BoxMesh.new()
			core.size = Vector3(e.width,e.height*0.24,0.28)
			mesh_node(body,core,material(Color("e3fcff")))
		"pulse","stomp":
			for i in 3:
				var pulse := ring(body,soft,float(e.width)*0.5-i*0.15)
				pulse.position.y = -e.y+0.04+i*0.07
	return node

func render(entities: Array) -> void:
	var alive := {}
	for e: Dictionary in entities:
		alive[e.id] = true
		if not views.has(e.id):
			views[e.id] = build(e)
		var node: Node3D = views[e.id]
		node.position = Vector3(e.x,e.y,0)
		var warning: MeshInstance3D = node.get_node("Warning")
		warning.position.y = -e.y+0.015
		warning.visible = e.delay > 0 and e.speed == 0
		var body: Node3D = node.get_node("Body")
		body.visible = e.delay <= 0
		if e.kind == "vortex":
			body.rotation.y = float(e.age)*0.17
		elif e.kind == "stone":
			body.rotation.z = -float(e.facing) * float(e.age) * 0.35
		elif e.kind == "bomb":
			# dropped from his hand to the ground in front of him, spinning, then the blast swells
			var bomb: Node3D = node.get_node("Rock")
			var flight := maxi(1, int(e.get("flight", 1)))
			bomb.visible = e.delay > 0 and e.delay <= flight
			if bomb.visible:
				var t := 1.0 - float(e.delay) / float(flight)
				var bx := lerpf(float(e.x0), float(e.x), t)
				var by := lerpf(0.85, 0.12, t) + 0.2 * 4.0 * t * (1.0 - t)
				bomb.position = Vector3(bx - float(e.x), by - float(e.y), 0)
				bomb.rotation.z = -float(e.facing) * t * TAU
			var swell := clampf(float(e.age+1)/4.0,0.2,1.0)
			body.scale = Vector3.ONE * swell
			body.position.y = -float(e.y)*0.4*(1.0-swell)
		elif e.kind == "rock_spike":
			# the stone flies in a half-moon arc from her hand to the landing point, then the spike rises
			var rock: MeshInstance3D = node.get_node("Rock")
			var flight := maxi(1, int(e.get("flight", 1)))
			rock.visible = e.delay > 0 and e.delay <= flight
			if rock.visible:
				var t := 1.0 - float(e.delay) / float(flight)
				var rx := lerpf(float(e.x0), float(e.x), t)
				var ry := lerpf(1.6, 0.15, t) + 1.8 * 4.0 * t * (1.0 - t)    # peak ~2.7 m, stays on screen
				rock.position = Vector3(rx - float(e.x), ry - float(e.y), 0)
				rock.rotation.z = t * TAU * 1.5
			var rise := clampf(float(e.age+1)/3.0,0.1,1.0)
			body.scale.y = rise
			body.position.y = -float(e.height)*0.5*(1.0-rise)
		elif e.kind == "spikes":
			var growth := clampf(float(e.age+1)/3.0,0.1,1.0)
			body.scale.y = growth
			body.position.y = -float(e.height)*0.5*(1.0-growth)
		elif e.kind in ["pulse","stomp"]:
			body.scale = Vector3.ONE*(0.4+minf(float(e.age)/6.0,0.6))
	for id: int in views.keys():
		if not alive.has(id):
			views[id].queue_free()
			views.erase(id)
