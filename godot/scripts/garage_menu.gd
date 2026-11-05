class_name GaleGarageMenu
extends Node3D
## The training menu painted on the garage's closed gate leaf
## (concept-art/ui/atlas-treino-garagem-v1/treino-garagem-portao-integrado-v3.png).
## Fixed words are the paint inscriptions of the atlas; values that change (fighters,
## behaviour) are written with a stencil font in the same cream paint.
## Local frame: origin at the gate centre, +X screen right, +Y up, +Z toward the camera.

const INK := "res://assets/ui/garage/%s.png"
const PAINT := Color("EDE3CB")
const PAINT_DIM := Color("B9AE95")
const STENCIL := "res://assets/ui/fonts/PortaoStencil-Desgastado.fnt"
const BEHAVIOURS := ["PASSIVO", "DEFENDE ALTO", "DEFENDE BAIXO", "PULA", "IA"]
const LABEL_X := -0.98
const VALUE_X := 0.62

var main: Node
var widgets: Array = []
var focus := 0
var hover := -1
var interactive := false
var pointer: MeshInstance3D
var stencil: Font
var textures := {}

func setup(main_node: Node, panel: MeshInstance3D) -> void:
	main = main_node
	stencil = load(STENCIL)
	# The gate faces the camera (-Z in Godot); screen right is -X.
	var centre: Vector3 = panel.global_transform * panel.get_aabb().get_center()
	var out := Vector3(0, 0, -1)
	global_transform = Transform3D(Basis(Vector3(-1, 0, 0), Vector3.UP, out), centre + out * 0.035)
	var lamp := OmniLight3D.new()
	lamp.light_color = Color("ffd9a0")
	lamp.light_energy = 1.2
	lamp.omni_range = 4.5
	get_parent().add_child(lamp)
	lamp.global_position = global_transform * Vector3(0.3, 0.8, 1.6)

func clear() -> void:
	for child in get_children():
		child.queue_free()
	widgets.clear()
	hover = -1

func rebuild() -> void:
	var keep := focus
	clear()
	ink("treino", 1.55, Vector2(0, 1.3))
	ink("sublinhado", 1.5, Vector2(0.02, 1.02))
	var ids: Array = GaleData.IDS
	choice_row("lutador", 0.56, Vector2(LABEL_X, 0.62), fighter_name(main.fighter1), func(step: int) -> void:
		main.fighter1 = ids[posmod(ids.find(main.fighter1) + step, ids.size())]
		main.palette1 = 0)
	choice_row("adversario", 0.66, Vector2(LABEL_X, 0.3), fighter_name(main.fighter2), func(step: int) -> void:
		main.fighter2 = ids[posmod(ids.find(main.fighter2) + step, ids.size())]
		main.palette2 = 0)
	choice_row("comportamento", 0.86, Vector2(LABEL_X, -0.02), BEHAVIOURS[main.training_behavior], func(step: int) -> void:
		main.training_behavior = posmod(main.training_behavior + step, BEHAVIOURS.size()))
	hitbox_row(Vector2(LABEL_X, -0.34))
	ink("sublinhado", 1.75, Vector2(-0.05, -0.56), Color(0.85, 0.82, 0.7, 0.55))
	button("iniciar-treino", 1.4, Vector2(0.08, -0.82), func() -> void: main.start_training_from_garage())
	ink("sublinhado", 1.3, Vector2(0.1, -1.02), Color(1, 1, 1, 0.85))
	button("esc-voltar", 0.62, Vector2(-0.1, -1.32), func() -> void: main.close_garage())
	pointer = ink("indicador-selecao", 0.26, Vector2.ZERO)
	focus = clampi(keep, 0, widgets.size() - 1)
	refresh_focus()

func fighter_name(id: String) -> String:
	return GaleVisualCatalog.load_for(id).display_name.to_upper()

# --- pieces -------------------------------------------------------------------------
func texture(id: String) -> Texture2D:
	if not textures.has(id):
		textures[id] = load(INK % id)
	return textures[id]

## A paint inscription from the atlas, `width` metres wide, centred on pos.
func ink(id: String, width: float, pos: Vector2, tint := Color.WHITE, parent: Node3D = self) -> MeshInstance3D:
	var tex := texture(id)
	var quad := QuadMesh.new()
	quad.size = Vector2(width, width * tex.get_height() / tex.get_width())
	var node := MeshInstance3D.new()
	node.mesh = quad
	node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var material := StandardMaterial3D.new()
	material.albedo_texture = tex
	material.albedo_color = tint
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	material.roughness = 0.9
	node.material_override = material
	node.position = Vector3(pos.x, pos.y, 0.004)
	parent.add_child(node)
	return node

func paint_text(value: String, pos: Vector2, size: int, parent: Node3D = self) -> Label3D:
	var label := Label3D.new()
	label.text = value
	label.font = stencil
	label.font_size = size
	label.pixel_size = 0.0026
	label.modulate = PAINT
	label.outline_size = 0
	label.shaded = true
	label.double_sided = false
	label.position = Vector3(pos.x, pos.y, 0.006)
	parent.add_child(label)
	return label

## Left-aligned label inscription; `width` is its painted width.
func label_ink(id: String, width: float, pos: Vector2) -> void:
	ink(id, width, Vector2(pos.x + width * 0.5, pos.y))

func choice_row(id: String, width: float, pos: Vector2, value: String, step: Callable) -> void:
	label_ink(id, width, pos)
	var root := Node3D.new()
	root.position = Vector3(VALUE_X, pos.y, 0)
	add_child(root)
	ink("seta-esquerda", 0.07, Vector2(-0.4, 0), Color.WHITE, root)
	ink("seta-direita", 0.07, Vector2(0.4, 0), Color.WHITE, root)
	var caption := paint_text(value, Vector2(0, 0.005), 46 if value.length() < 9 else 34, root)
	widgets.append({"kind": "choice", "row": pos.y, "root": root, "caption": caption, "step": step,
		"rect": Rect2(Vector2(LABEL_X - 0.05, pos.y - 0.13), Vector2(VALUE_X - LABEL_X + 0.5, 0.26))})

func hitbox_row(pos: Vector2) -> void:
	label_ink("exibir-hitboxes", 0.86, pos)
	var root := Node3D.new()
	root.position = Vector3(VALUE_X, pos.y, 0)
	add_child(root)
	var on: bool = main.arena.show_boxes
	var answer := ink("sim" if on else "nao", 0.4, Vector2.ZERO, Color.WHITE, root)
	widgets.append({"kind": "toggle", "row": pos.y, "root": root, "answer": answer,
		"rect": Rect2(Vector2(LABEL_X - 0.05, pos.y - 0.13), Vector2(VALUE_X - LABEL_X + 0.5, 0.26))})

func button(id: String, width: float, pos: Vector2, action: Callable) -> void:
	var node := ink(id, width, pos)
	widgets.append({"kind": "button", "row": pos.y, "root": node, "action": action,
		"rect": Rect2(pos - Vector2(width * 0.5 + 0.1, 0.13), Vector2(width + 0.2, 0.26))})

# --- behaviour ----------------------------------------------------------------------
func activate(index: int) -> void:
	if index < 0 or index >= widgets.size():
		return
	var w: Dictionary = widgets[index]
	main.audio.play("click")
	match String(w.kind):
		"button":
			(w.action as Callable).call()
		"choice":
			change(index, 1)
		"toggle":
			change(index, 1)

func change(index: int, step: int) -> void:
	var w: Dictionary = widgets[index]
	match String(w.kind):
		"choice":
			(w.step as Callable).call(step)
			rebuild()
		"toggle":
			main.arena.show_boxes = not main.arena.show_boxes
			rebuild()
		_:
			return
	main.audio.play("hover")

func refresh_focus() -> void:
	for i in widgets.size():
		var w: Dictionary = widgets[i]
		var root: Node3D = w.root
		if not is_instance_valid(root):
			continue
		var lit := interactive and (i == focus or i == hover)
		root.create_tween().tween_property(root, "scale", Vector3.ONE * (1.06 if lit else 1.0), 0.1)
	if is_instance_valid(pointer) and not widgets.is_empty():
		# The green painted arrow sits left of the focused line.
		var row := float(widgets[focus].row)
		var x := LABEL_X - 0.02 if String(widgets[focus].kind) != "button" else -0.85
		pointer.position = Vector3(x - 0.13, row, 0.004)
		pointer.visible = interactive

func local_point(screen: Vector2) -> Vector2:
	var camera: Camera3D = main.arena.camera
	var inverse := global_transform.affine_inverse()
	var origin := inverse * camera.project_ray_origin(screen)
	var direction := inverse.basis * camera.project_ray_normal(screen)
	if absf(direction.z) < 0.0001:
		return Vector2(INF, INF)
	var hit := origin + direction * ((0.01 - origin.z) / direction.z)
	return Vector2(hit.x, hit.y)

func widget_at(point: Vector2) -> int:
	for i in widgets.size():
		if (widgets[i].rect as Rect2).has_point(point):
			return i
	return -1

func handle_input(event: InputEvent) -> bool:
	if not interactive:
		return false
	if event is InputEventMouseMotion:
		var over := widget_at(local_point(event.position))
		if over != hover:
			hover = over
			if over >= 0:
				focus = over
				main.audio.play("hover")
			refresh_focus()
		return over >= 0
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
		var point := local_point(event.position)
		var index := widget_at(point)
		if index < 0:
			return false
		focus = index
		var w: Dictionary = widgets[index]
		# Clicking the left arrow side of a value steps back.
		if String(w.kind) == "choice" and point.x < VALUE_X:
			change(index, -1 if point.x > VALUE_X - 0.5 else 1)
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
		change(focus, -1 if event.is_action_pressed("ui_left") else 1)
	elif event.is_action_pressed("ui_accept"):
		activate(focus)
	else:
		return false
	return true

func move_focus(step: int) -> void:
	focus = posmod(focus + step, widgets.size())
	main.audio.play("hover")
	refresh_focus()
