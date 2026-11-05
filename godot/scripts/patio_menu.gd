class_name GalePatioMenu
extends Node3D
## Arcade select on the village patio (concept-art/ui/atlas-patio-casas-v1/concept-patio-babuin-v6.png).
## The stall is real geometry from stage.glb; this node writes the texts on its boards (Patio*
## anchors), pins the fighter's portrait on the poster, and hangs the outfits on the rack: each
## outfit is the fighter model in that palette, in its rest pose, with head, hands and feet
## folded away so only the clothes show.
## Rows: 0 fighter (poster), 1 outfit (rack), 2 HABILIDADES, 3 INICIAR ARCADE.

const CREAM := Color("F4E9CF")
const INK := Color("2B2118")
const JADE := Color("3E8A5C")
const SERIF := "res://assets/ui/fonts/Cinzel-Variable.ttf"
const BODY := "res://assets/ui/fonts/EBGaramond-Variable.ttf"
# Hand-brushed lettering like the concept's painted signs (until a painted lettering atlas exists).
const BRUSH := "res://assets/ui/fonts/CaveatBrush-Regular.ttf"
const HIDDEN_BONES := ["head", "neck", "hand", "foot", "ear"]
const PAGE := 4
const OUTFIT_SCALE := 0.7

var main: Node
var anchors := {}
var focus := 1
var hover := -1
var interactive := false
var serif: FontVariation
var body: FontVariation
var brush: Font
var rows: Array = []        # {"root": Node3D, "rect": Rect2 in screen space (computed live)}
var hangers: Array = []     # GaleFighterView per visible outfit
var tags: Array = []
var poster: MeshInstance3D

func setup(main_node: Node, patio_anchors: Dictionary) -> void:
	main = main_node
	anchors = patio_anchors
	brush = load(BRUSH)
	serif = FontVariation.new()
	serif.base_font = load(SERIF)
	serif.variation_opentype = {TextServerManager.get_primary_interface().name_to_tag("wght"): 700}
	body = FontVariation.new()
	body.base_font = load(BODY)
	body.variation_opentype = {TextServerManager.get_primary_interface().name_to_tag("wght"): 600}
	body.variation_transform = Transform2D(Vector2(1, 0), Vector2(-0.18, 1), Vector2.ZERO)

func anchor(name: String) -> Vector3:
	return anchors.get(name, Vector3.ZERO)

# --- building ---------------------------------------------------------------------
func rebuild() -> void:
	for child in get_children():
		child.queue_free()
	rows.clear()
	hangers.clear()
	tags.clear()
	var cat := GaleVisualCatalog.load_for(main.fighter1)
	# Top sign and the ROUPAS plank, painted in cream.
	paint("ARCADE", anchor("PatioArcadeSign"), 150, CREAM, brush, 8)
	paint("ROUPAS", anchor("PatioRoupas"), 72, CREAM, brush, 6)
	# Name board on the easel: big name, the title below in italic.
	# (the easel board leans back: write a little in front of it)
	# The easel is turned toward the stall: write in its own frame.
	var board := Node3D.new()
	add_child(board)
	board.position = anchor("PatioNameBoard")
	board.basis = anchors.get("PatioNameBoard:basis", Basis())
	paint(cat.display_name.to_upper(), Vector3(0, 0.15, 0.1), 104, CREAM, brush, 6, board)
	paint(cat.subtitle, Vector3(0, -0.06, 0.12), 54, CREAM, brush, 5, board)
	var swirl := quad(load("res://assets/environments/beach/textures/patio/emblema-vento-marfim.png"), Vector2(0.34, 0.22), Vector3.ZERO)
	remove_child(swirl)
	board.add_child(swirl)
	swirl.position = Vector3(0, -0.25, 0.12)
	# Poster: the portrait pinned on the paper, the name written under it.
	var poster_path := "res://assets/ui/posters/%s.png" % main.fighter1
	var portrait_path := "res://assets/ui/portraits/%s.png" % main.fighter1
	var poster_at := anchor("PatioPoster")
	if ResourceLoader.exists(poster_path):
		# Painted poster (with the name already on it) covering the paper.
		poster = quad(load(poster_path), Vector2(0.6, 0.76), poster_at + Vector3(0, -0.02, 0.004))
	else:
		if ResourceLoader.exists(portrait_path):
			poster = quad(load(portrait_path), Vector2(0.5, 0.5), poster_at + Vector3(0, 0.07, 0.004))
		paint(cat.display_name.to_upper(), poster_at + Vector3(0, -0.26, 0.006), 34, INK, serif, 0)
	var poster_row := Node3D.new()
	add_child(poster_row)
	poster_row.position = poster_at
	paint("‹", poster_at + Vector3(-0.48, 0.0, 0.01), 90, CREAM, serif, 6)
	paint("›", poster_at + Vector3(0.48, 0.0, 0.01), 90, CREAM, serif, 6)
	rows.append({"root": poster_row, "area": [poster_at + Vector3(-0.6, -0.5, 0), poster_at + Vector3(0.6, 0.6, 0)]})
	# Rack: three outfits from the current page, a tag with the name under each.
	var count: int = cat.palettes.size()
	# When every outfit fits on the rack they stay in catalog order; otherwise the rack pages.
	var page: int = main.arcade_outfit_page if count > PAGE else 0
	var rack_row := Node3D.new()
	add_child(rack_row)
	for slot in mini(PAGE, count):
		var palette := posmod(page + slot, count)
		var hang := anchor("PatioHanger_%d" % slot)
		hangers.append(hanger(palette, hang))
		var tag_at := anchor("PatioTag_%d" % slot)
		var label := paint(String(cat.palettes[palette].name), tag_at, 50, INK, brush, 0)
		tags.append({"label": label, "palette": palette, "area": [hang + Vector3(-0.45, -1.45, 0), hang + Vector3(0.45, 0.2, 0)]})
	rows.append({"root": rack_row, "area": [anchor("PatioArrow_L") + Vector3(-0.2, -0.8, 0), anchor("PatioArrow_R") + Vector3(0.2, 0.7, 0)]})
	# The two wooden buttons.
	for pair: Array in [["PatioSkills", "HABILIDADES", 70, 1.3], ["PatioStart", "INICIAR ARCADE", 104, 2.4]]:
		var at := anchor(String(pair[0]))
		var root := Node3D.new()
		add_child(root)
		root.position = at
		paint(String(pair[1]), Vector3(0, 0.03, 0), int(pair[2]), CREAM, brush, 7, root)
		var stroke := ColorRectish(Vector2(float(pair[3]) * 0.6, 0.035), JADE, Vector3(0, -0.15, 0.004), root)
		rows.append({"root": root, "area": [at + Vector3(-float(pair[3]) * 0.5, -0.3, 0), at + Vector3(float(pair[3]) * 0.5, 0.3, 0)], "stroke": stroke})
	refresh()

func paint(text: String, at: Vector3, size: int, color: Color, font: Font, outline: int, parent: Node3D = self) -> Label3D:
	var label := Label3D.new()
	label.text = text
	label.font = font
	label.font_size = size
	label.pixel_size = 0.0022
	label.modulate = color
	label.outline_size = outline
	label.outline_modulate = Color(0.12, 0.07, 0.03, 0.9)
	label.double_sided = false
	label.shaded = false
	parent.add_child(label)
	label.position = at if parent == self else at
	return label

func quad(tex: Texture2D, size: Vector2, at: Vector3) -> MeshInstance3D:
	var mesh := QuadMesh.new()
	mesh.size = size
	var node := MeshInstance3D.new()
	node.mesh = mesh
	var material := StandardMaterial3D.new()
	material.albedo_texture = tex
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
	material.roughness = 1.0
	node.material_override = material
	add_child(node)
	node.position = at
	return node

## A thin painted stroke (the jade underline of the focused board).
func ColorRectish(size: Vector2, color: Color, at: Vector3, parent: Node3D) -> MeshInstance3D:
	var mesh := QuadMesh.new()
	mesh.size = size
	var node := MeshInstance3D.new()
	node.mesh = mesh
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	node.material_override = material
	parent.add_child(node)
	node.position = at
	return node

## The fighter model in one palette hung from a hanger: rest pose, head/hands/feet folded away.
func hanger(palette: int, at: Vector3) -> GaleFighterView:
	var view := GaleFighterView.new()
	add_child(view)
	view.build(main.data, main.fighter1, palette)
	view.aura.visible = false
	if view.anim_player != null:
		view.anim_player.stop()
	view.set_process(false)
	if view.skeleton != null:
		view.skeleton.reset_bone_poses()
		for bone in view.skeleton.get_bone_count():
			var bone_name := view.skeleton.get_bone_name(bone).to_lower()
			for hidden: String in HIDDEN_BONES:
				if bone_name.contains(hidden):
					view.skeleton.set_bone_pose_scale(bone, Vector3.ONE * 0.001)
	# The shoulders rest on the hanger bar (shoulder height ~1.5 m in the model); the clothes face
	# the camera and nearly reach the counter.
	view.scale = Vector3.ONE * OUTFIT_SCALE
	view.position = at + Vector3(0, -1.5 * OUTFIT_SCALE + 0.03, 0.02)
	view.rotation.y = PI
	return view

# --- behaviour --------------------------------------------------------------------
func refresh() -> void:
	for i in rows.size():
		var root: Node3D = rows[i].root
		if not is_instance_valid(root):
			continue
		var lit := interactive and (i == focus or i == hover)
		if i >= 2:
			root.create_tween().tween_property(root, "scale", Vector3.ONE * (1.08 if lit else 1.0), 0.12)
			(rows[i].stroke as MeshInstance3D).visible = lit
	for t: Dictionary in tags:
		var chosen: bool = int(t.palette) == int(main.palette1)
		(t.label as Label3D).modulate = JADE.darkened(0.25) if chosen else INK
		(t.label as Label3D).text = ("✓ " if chosen else "") + (t.label as Label3D).text.trim_prefix("✓ ")
	for i in hangers.size():
		var view: GaleFighterView = hangers[i]
		var chosen: bool = i < tags.size() and int(tags[i].palette) == int(main.palette1)
		view.create_tween().tween_property(view, "scale", Vector3.ONE * OUTFIT_SCALE * (1.06 if chosen else 1.0), 0.15)
	if is_instance_valid(poster):
		poster.scale = Vector3.ONE * (1.05 if interactive and (focus == 0 or hover == 0) else 1.0)

func _process(_delta: float) -> void:
	# Each hanger swings very gently, out of step with the others.
	var t := Time.get_ticks_msec() / 1000.0
	for i in hangers.size():
		var view: GaleFighterView = hangers[i]
		if is_instance_valid(view):
			view.rotation.z = sin(t * 1.1 + i * 1.7) * 0.03

func step_outfit(step: int) -> void:
	var count: int = GaleVisualCatalog.load_for(main.fighter1).palettes.size()
	var palette := posmod(int(main.palette1) + step, count)
	# Page so the chosen outfit is always on the rack.
	var page: int = main.arcade_outfit_page
	if posmod(palette - page, count) >= PAGE:
		main.arcade_outfit_page = posmod(palette - (PAGE - 1 if step > 0 else 0), count)
	main.choose_arcade_outfit(palette)

func step_fighter(step: int) -> void:
	var ids: Array = GaleData.IDS
	main.choose_arcade_fighter(ids[posmod(ids.find(main.fighter1) + step, ids.size())])

func activate(index: int) -> void:
	main.audio.play("click")
	match index:
		0: step_fighter(1)
		1: step_outfit(1)
		2: main.open_arcade_skills()
		3: main.start_arcade_from_select()

func change(step: int) -> void:
	match focus:
		0: step_fighter(step)
		1: step_outfit(step)
		_: move_focus(step)

func move_focus(step: int) -> void:
	focus = posmod(focus + step, rows.size())
	main.audio.play("hover")
	refresh()

func screen_rect(area: Array) -> Rect2:
	var camera: Camera3D = main.arena.camera
	var a := camera.unproject_position(area[0])
	var b := camera.unproject_position(area[1])
	return Rect2(Vector2(minf(a.x, b.x), minf(a.y, b.y)), (a - b).abs())

func row_at(point: Vector2) -> int:
	for i in rows.size():
		if screen_rect(rows[i].area).has_point(point):
			return i
	return -1

func handle_input(event: InputEvent) -> bool:
	if not interactive:
		return false
	if event is InputEventMouseMotion:
		var over := row_at(event.position)
		if over != hover:
			hover = over
			if over >= 0:
				focus = over
				main.audio.play("hover")
			refresh()
		return over >= 0
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		# A click on an outfit picks it; on the stall arrows it pages; on the poster sides, fighter.
		for t: Dictionary in tags:
			if screen_rect(t.area).has_point(event.position):
				focus = 1
				main.audio.play("click")
				main.choose_arcade_outfit(int(t.palette))
				return true
		var index := row_at(event.position)
		if index < 0:
			return false
		focus = index
		if index <= 1:
			var centre := screen_rect(rows[index].area).get_center()
			change(-1 if event.position.x < centre.x else 1)
		else:
			activate(index)
		return true
	if not event.is_pressed() or event.is_echo():
		return false
	if event.is_action_pressed("ui_down"):
		move_focus(1)
	elif event.is_action_pressed("ui_up"):
		move_focus(-1)
	elif event.is_action_pressed("ui_left") or event.is_action_pressed("ui_right"):
		change(-1 if event.is_action_pressed("ui_left") else 1)
	elif event.is_action_pressed("ui_accept"):
		activate(focus)
	elif event is InputEventKey and (event.keycode == KEY_Q or event.keycode == KEY_E):
		main.turn_select_fighter(-0.4 if event.keycode == KEY_Q else 0.4)
	else:
		return false
	return true
