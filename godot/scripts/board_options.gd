class_name GaleBoardOptions
extends Node3D
## The options as physical pieces on the forest quest board (concept-art/ui/quest-board-opcoes-floresta-v2.png):
## raised wooden/jade plaques that sink when pressed, brass slider knobs on rails,
## sliding switches and key caps, with the text written on the parchment.
## Local frame: origin at the parchment centre, +X screen right, +Y up, +Z toward the camera.

const PANEL := Vector2(3.1, 1.72)
const INK := Color("23382D")
const JADE := Color("2F7A57")
const CREAM := Color("EFE4CB")
const BRASS := Color("C9A24E")
const GREY := Color("8D8C86")
const FONT_PATH := "res://assets/ui/fonts/Cinzel-Variable.ttf"
const ACTION_LABELS := ["Pular", "Agachar", "Esquerda", "Direita", "Básico", "Forte", "Elemental", "Ultimate", "Defesa", "Dash", "Breaker"]
const PAD_LABELS := ["A", "D-pad ↓", "D-pad ←", "D-pad →", "X", "Y", "B", "RB", "LB", "R3", "L3"]

var main: Node
var widgets: Array = []
var focus := 0
var hover := -1
var dragging := -1
var interactive := false
var status_label: Label3D
var serif: FontVariation
var board_lamp: OmniLight3D

func setup(main_node: Node, panel: MeshInstance3D) -> void:
	main = main_node
	serif = FontVariation.new()
	serif.base_font = load(FONT_PATH)
	serif.variation_opentype = {TextServerManager.get_primary_interface().name_to_tag("wght"): 700}
	# The parchment faces +X in the world; build a frame whose +Z points out of it.
	var centre: Vector3 = panel.global_transform * panel.get_aabb().get_center()
	global_transform = Transform3D(Basis(Vector3(0, 0, -1), Vector3.UP, Vector3(1, 0, 0)), centre + Vector3(0.03, 0, 0))
	# Warm lantern light in front of the board, so the pieces show their relief
	# (the sun is behind the board). The parchment itself is unshaded.
	var lamp := OmniLight3D.new()
	lamp.light_color = Color("ffe2b0")
	lamp.light_energy = 1.6
	lamp.omni_range = 5.0
	lamp.shadow_enabled = false
	get_parent().add_child(lamp)
	lamp.global_position = global_transform * Vector3(-0.6, 1.1, 1.5)
	board_lamp = lamp

# --- building -----------------------------------------------------------------------
func clear() -> void:
	for child in get_children():
		child.queue_free()
	widgets.clear()
	hover = -1
	dragging = -1

func rebuild() -> void:
	var keep := focus
	clear()
	text("OPÇÕES", Vector2(0, 0.69), 44, INK, true)
	plaque_row([["GERAL", main.settings_tab == "geral", func() -> void: switch_tab("geral")],
		["CONTROLES", main.settings_tab == "controles", func() -> void: switch_tab("controles")]], 0.47, Vector2(0.8, 0.16), 22)
	if main.settings_tab == "geral":
		build_general()
	else:
		build_controls()
	plaque("ESC  VOLTAR", Vector2(-1.16, -0.76), Vector2(0.66, 0.14), false, 18, func() -> void: main.close_settings())
	plaque("SALVAR E VOLTAR", Vector2(1.02, -0.76), Vector2(0.96, 0.16), true, 19, func() -> void: main.close_settings())
	status_label = text("", Vector2(0, -0.76), 13, Color("4C5A52"))
	focus = clampi(keep, 0, widgets.size() - 1)
	refresh_focus()

func build_general() -> void:
	var p: GalePreferences = main.prefs
	heading("ÁUDIO", Vector2(-1.5, 0.27))
	heading("JOGO E CONFORTO", Vector2(0.06, 0.27))
	var left := -1.5
	var right := 0.06
	slider_row("Volume geral", Vector2(left, 0.1), p.volume, func(v: float) -> void: p.volume = v)
	slider_row("Música", Vector2(left, -0.06), p.music_volume, func(v: float) -> void: p.music_volume = v)
	slider_row("Efeitos sonoros", Vector2(left, -0.22), p.sfx_volume, func(v: float) -> void: p.sfx_volume = v)
	toggle_row("Áudio ativo", Vector2(left, -0.38), not p.muted, func(on: bool) -> void: p.muted = not on)
	slider_row("Intensidade da câmera", Vector2(right, 0.1), p.shake_strength, func(v: float) -> void: p.shake_strength = v)
	cycle_row("Dificuldade Arcade", Vector2(right, -0.06), ["Tranquilo", "Normal", "Intenso"], p.difficulty, func(i: int) -> void: p.difficulty = i)
	toggle_row("Flashes de impacto", Vector2(right, -0.22), p.flashes, func(on: bool) -> void: p.flashes = on)
	toggle_row("Vibração do gamepad", Vector2(right, -0.38), p.vibration, func(on: bool) -> void: p.vibration = on)
	toggle_row("Mostrar áreas de colisão", Vector2(right, -0.54), main.arena.show_boxes, func(on: bool) -> void: main.arena.show_boxes = on)
	divider(Vector2(0, -0.13), 0.78)

func build_controls() -> void:
	plaque_row([["TECLADO", main.settings_input == "teclado", func() -> void: switch_input("teclado")],
		["GAMEPAD", main.settings_input == "gamepad", func() -> void: switch_input("gamepad")]], 0.31, Vector2(0.52, 0.11), 15)
	if main.settings_input == "teclado":
		plaque("RESTAURAR PADRÕES", Vector2(1.2, 0.31), Vector2(0.62, 0.1), false, 11, func() -> void: main.restore_default_keys())
	for player in 2:
		var x0 := -1.5 if player == 0 else 0.08
		heading("JOGADOR %d" % (player + 1), Vector2(x0, 0.19))
		for action in GalePreferences.ACTIONS.size():
			var y := 0.08 - action * 0.068
			text(ACTION_LABELS[action], Vector2(x0 + 0.05, y), 16, INK, false, HORIZONTAL_ALIGNMENT_LEFT)
			if main.settings_input == "teclado":
				var active: bool = main.listening == [player, action]
				key_cap(main.key_label(main.prefs.keys[player][action]), Vector2(x0 + 1.18, y), active, func() -> void:
					main.listening = [player, action]
					main.show_settings()
					main.rebind_label.text = "Pressione a nova tecla para %s do Jogador %d. Esc cancela." % [ACTION_LABELS[action], player + 1])
			else:
				key_cap(PAD_LABELS[action], Vector2(x0 + 1.18, y), false, Callable())

# --- pieces -------------------------------------------------------------------------
func cel(color: Color) -> ShaderMaterial:
	var material := ShaderMaterial.new()
	material.shader = GaleArena.CelSurface
	material.set_shader_parameter("color", color)
	return material

func box(size: Vector3, pos: Vector3, color: Color, parent: Node3D = self) -> MeshInstance3D:
	var mesh := BoxMesh.new()
	mesh.size = size
	var node := MeshInstance3D.new()
	node.mesh = mesh
	node.material_override = cel(color)
	node.position = pos
	parent.add_child(node)
	return node

func text(value: String, pos: Vector2, size: int, color: Color, heading_font: bool = false, align := HORIZONTAL_ALIGNMENT_CENTER, parent: Node3D = self, z: float = 0.004) -> Label3D:
	var label := Label3D.new()
	label.text = value
	label.font_size = size
	label.pixel_size = 0.003
	label.modulate = color
	label.outline_size = 0
	label.horizontal_alignment = align
	label.position = Vector3(pos.x, pos.y, z)
	label.double_sided = false
	if heading_font:
		label.font = serif
	parent.add_child(label)
	return label

func heading(value: String, pos: Vector2) -> void:
	text(value, pos, 26, INK, true, HORIZONTAL_ALIGNMENT_LEFT)

func divider(pos: Vector2, height: float) -> void:
	box(Vector3(0.006, height, 0.004), Vector3(pos.x, pos.y, 0.003), BRASS)

func add_widget(widget: Dictionary) -> int:
	widgets.append(widget)
	return widgets.size() - 1

func plaque(label: String, pos: Vector2, size: Vector2, active: bool, font: int, action: Callable) -> void:
	var root := Node3D.new()
	root.position = Vector3(pos.x, pos.y, 0.0)
	add_child(root)
	var face := JADE if active else CREAM
	# Darker body under a lighter face: reads as a thick raised board.
	box(Vector3(size.x + 0.02, size.y + 0.02, 0.05), Vector3(0, 0, 0.025), face.darkened(0.45), root)
	var top := box(Vector3(size.x, size.y, 0.03), Vector3(0, 0, 0.06), face, root)
	for sx in [-1, 1]:
		box(Vector3(0.03, 0.03, 0.02), Vector3(sx * (size.x * 0.5 - 0.04), 0, 0.08), BRASS, root)
	text(label, Vector2.ZERO, font, Color("F4EFE4") if active else JADE, true, HORIZONTAL_ALIGNMENT_CENTER, root, 0.077)
	add_widget({"kind": "button", "root": root, "face": top, "rect": Rect2(pos - size * 0.5, size), "action": action, "rest": 0.0})

func plaque_row(items: Array, y: float, size: Vector2, font: int) -> void:
	var gap := 0.04
	var x := -(size.x + gap) * 0.5 * (items.size() - 1)
	for item: Array in items:
		plaque(String(item[0]), Vector2(x, y), size, bool(item[1]), font, item[2])
		x += size.x + gap

func slider_row(label: String, pos: Vector2, value: float, setter: Callable) -> void:
	text(label, pos, 21, INK, false, HORIZONTAL_ALIGNMENT_LEFT)
	var rail_x := pos.x + 0.98
	var width := 0.4
	box(Vector3(width, 0.022, 0.02), Vector3(rail_x, pos.y, 0.01), Color("B9B9A9"))
	var fill := box(Vector3(width, 0.026, 0.024), Vector3(rail_x, pos.y, 0.012), JADE)
	var knob := box(Vector3(0.06, 0.06, 0.05), Vector3(rail_x, pos.y, 0.03), Color("E8C877"))
	knob.rotation.z = PI / 4
	var percent := text("", Vector2(pos.x + 1.4, pos.y), 19, INK, false, HORIZONTAL_ALIGNMENT_RIGHT)
	var index := add_widget({"kind": "slider", "root": knob, "rect": Rect2(Vector2(rail_x - width * 0.5 - 0.04, pos.y - 0.05), Vector2(width + 0.08, 0.1)),
		"value": value, "set": setter, "fill": fill, "percent": percent, "x0": rail_x - width * 0.5, "width": width, "rest": 0.03})
	set_slider(index, value, false)

func set_slider(index: int, value: float, save: bool = true) -> void:
	var w: Dictionary = widgets[index]
	value = clampf(snappedf(value, 0.05), 0.0, 1.0)
	w.value = value
	var knob: Node3D = w.root
	knob.position.x = float(w.x0) + float(w.width) * value
	var fill: MeshInstance3D = w.fill
	fill.scale.x = maxf(value, 0.001)
	fill.position.x = float(w.x0) + float(w.width) * value * 0.5
	(w.percent as Label3D).text = "%d%%" % roundi(value * 100)
	if save:
		(w.set as Callable).call(value)
		main.persist()

func toggle_row(label: String, pos: Vector2, on: bool, setter: Callable) -> void:
	text(label, pos, 21, INK, false, HORIZONTAL_ALIGNMENT_LEFT)
	var root := Node3D.new()
	root.position = Vector3(pos.x + 1.24, pos.y, 0)
	add_child(root)
	var track := box(Vector3(0.18, 0.08, 0.04), Vector3(0, 0, 0.02), JADE if on else GREY, root)
	var lever := box(Vector3(0.075, 0.075, 0.05), Vector3(0.045 if on else -0.045, 0, 0.055), Color("F6F0E2"), root)
	add_widget({"kind": "toggle", "root": root, "rect": Rect2(pos + Vector2(1.13, -0.05), Vector2(0.22, 0.1)), "on": on,
		"set": setter, "track": track, "lever": lever, "rest": 0.0})

func cycle_row(label: String, pos: Vector2, names: Array, index: int, setter: Callable) -> void:
	text(label, pos, 21, INK, false, HORIZONTAL_ALIGNMENT_LEFT)
	var root := Node3D.new()
	root.position = Vector3(pos.x + 1.12, pos.y, 0)
	add_child(root)
	box(Vector3(0.56, 0.1, 0.04), Vector3(0, 0, 0.02), Color("FBF7EE"), root)
	box(Vector3(0.58, 0.12, 0.03), Vector3(0, 0, 0.012), JADE, root)
	var value := text("‹  %s  ›" % names[index], Vector2.ZERO, 17, INK, false, HORIZONTAL_ALIGNMENT_CENTER, root, 0.045)
	add_widget({"kind": "cycle", "root": root, "rect": Rect2(pos + Vector2(0.83, -0.06), Vector2(0.58, 0.12)), "names": names,
		"index": index, "set": setter, "label": value, "rest": 0.0})

func key_cap(label: String, pos: Vector2, active: bool, action: Callable) -> void:
	var root := Node3D.new()
	root.position = Vector3(pos.x, pos.y, 0)
	add_child(root)
	var face := JADE if active else Color("FBF7EE")
	box(Vector3(0.3, 0.058, 0.03), Vector3(0, 0, 0.015), face.darkened(0.4) if active else JADE, root)
	var top := box(Vector3(0.28, 0.05, 0.022), Vector3(0, 0, 0.038), face, root)
	text(label, Vector2.ZERO, 13, Color("F4EFE4") if active else INK, false, HORIZONTAL_ALIGNMENT_CENTER, root, 0.051)
	if action.is_valid():
		add_widget({"kind": "button", "root": root, "face": top, "rect": Rect2(pos - Vector2(0.15, 0.03), Vector2(0.3, 0.06)), "action": action, "rest": 0.0})

# --- behaviour ----------------------------------------------------------------------
func switch_tab(tab: String) -> void:
	main.settings_tab = tab
	focus = 0
	rebuild()

func switch_input(kind: String) -> void:
	main.settings_input = kind
	rebuild()

func activate(index: int) -> void:
	if index < 0 or index >= widgets.size():
		return
	var w: Dictionary = widgets[index]
	main.audio.play("click")
	press(w)
	match String(w.kind):
		"button":
			(w.action as Callable).call()
		"toggle":
			set_toggle(index, not bool(w.on))
		"cycle":
			step_cycle(index, 1)

func press(w: Dictionary) -> void:
	# The piece sinks into the board and springs back.
	var root: Node3D = w.root
	if not is_instance_valid(root):
		return
	var rest := float(w.rest)
	var tween := root.create_tween()
	tween.tween_property(root, "position:z", rest - 0.035, 0.06).set_trans(Tween.TRANS_QUAD)
	tween.tween_property(root, "position:z", rest, 0.16).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)

func set_toggle(index: int, on: bool) -> void:
	var w: Dictionary = widgets[index]
	w.on = on
	var lever: Node3D = w.lever
	lever.create_tween().tween_property(lever, "position:x", 0.045 if on else -0.045, 0.14).set_trans(Tween.TRANS_CUBIC)
	((w.track as MeshInstance3D).material_override as ShaderMaterial).set_shader_parameter("color", JADE if on else GREY)
	(w.set as Callable).call(on)
	main.persist()

func step_cycle(index: int, step: int) -> void:
	var w: Dictionary = widgets[index]
	w.index = posmod(int(w.index) + step, (w.names as Array).size())
	(w.label as Label3D).text = "‹  %s  ›" % w.names[w.index]
	(w.set as Callable).call(int(w.index))
	main.persist()

func refresh_focus() -> void:
	for i in widgets.size():
		var w: Dictionary = widgets[i]
		var root: Node3D = w.root
		if not is_instance_valid(root):
			continue
		var lit := interactive and (i == focus or i == hover)
		var target := Vector3.ONE * (1.06 if lit else 1.0)
		root.create_tween().tween_property(root, "scale", target, 0.1)

func local_point(screen: Vector2) -> Vector2:
	var camera: Camera3D = main.arena.camera
	var inverse := global_transform.affine_inverse()
	var origin := inverse * camera.project_ray_origin(screen)
	var direction := inverse.basis * camera.project_ray_normal(screen)
	if absf(direction.z) < 0.0001:
		return Vector2(INF, INF)
	var hit := origin + direction * ((0.05 - origin.z) / direction.z)
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
		var point := local_point(event.position)
		if dragging >= 0:
			var w: Dictionary = widgets[dragging]
			set_slider(dragging, (point.x - float(w.x0)) / float(w.width))
			return true
		var over := widget_at(point)
		if over != hover:
			hover = over
			if over >= 0:
				focus = over
				main.audio.play("hover")
			refresh_focus()
		return over >= 0
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		var point := local_point(event.position)
		var index := widget_at(point)
		if not event.pressed:
			dragging = -1
			return index >= 0
		if index < 0:
			return false
		focus = index
		if String(widgets[index].kind) == "slider":
			dragging = index
			var w: Dictionary = widgets[index]
			set_slider(index, (point.x - float(w.x0)) / float(w.width))
		else:
			activate(index)
		return true
	if not event.is_pressed() or event.is_echo():
		return false
	if event.is_action_pressed("ui_down") or event.is_action_pressed("ui_focus_next"):
		move_focus(1)
	elif event.is_action_pressed("ui_up") or event.is_action_pressed("ui_focus_prev"):
		move_focus(-1)
	elif event.is_action_pressed("ui_left") or event.is_action_pressed("ui_right"):
		var step := -1 if event.is_action_pressed("ui_left") else 1
		var w: Dictionary = widgets[focus]
		match String(w.kind):
			"slider":
				set_slider(focus, float(w.value) + 0.05 * step)
			"cycle":
				step_cycle(focus, step)
			"toggle":
				set_toggle(focus, step > 0)
			_:
				move_focus(step)
	elif event.is_action_pressed("ui_accept"):
		activate(focus)
	else:
		return false
	return true

func move_focus(step: int) -> void:
	focus = posmod(focus + step, widgets.size())
	main.audio.play("hover")
	refresh_focus()

func _process(_delta: float) -> void:
	if is_instance_valid(status_label) and main != null and is_instance_valid(main.rebind_label):
		var message := String(main.rebind_label.text)
		status_label.text = "" if message.begins_with("Ajuste") else message
