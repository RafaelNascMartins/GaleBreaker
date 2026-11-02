extends Node3D
## Every visible attack is positioned from the combat simulation's entity.

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
