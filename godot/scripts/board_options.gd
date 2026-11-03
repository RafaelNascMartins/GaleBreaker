class_name GaleBoardOptions
extends Node3D
## The options as paper and pen on the forest quest board (concept-art/ui/opcoes-papel-caneta-psx-v4.png):
## torn paper notes pinned on the parchment for the buttons (they lift when pressed), and ink
## drawings for the values: a rail with a dot, answers circled in an oval, arrows around a choice.
## Local frame: origin at the parchment centre, +X screen right, +Y up, +Z toward the camera.

const PANEL := Vector2(3.1, 1.72)
const INK := Color("1F3D2B")
const INK_FADED := Color("6B6A55")
const CREAM := Color("F3E9CF")
const FONT_PATH := "res://assets/ui/fonts/Cinzel-Variable.ttf"
const BODY_FONT_PATH := "res://assets/ui/fonts/EBGaramond-Variable.ttf"
# Paper and ink pieces cut from concept-art/ui/atlas-opcoes-psx-v1 (generate_ui_frames.py).
const PAPER := "res://assets/ui/board/paper/%s.png"
const ACTION_LABELS := ["Pular", "Agachar", "Esquerda", "Direita", "Básico", "Forte", "Elemental", "Ultimate", "Defesa", "Dash", "Breaker"]
const PAD_LABELS := ["A", "D-pad ↓", "D-pad ←", "D-pad →", "X", "Y", "B", "RB", "LB", "R3", "L3"]
const FOOTER_Y := -0.68

var main: Node
var widgets: Array = []
var focus := 0
var hover := -1
var dragging := -1
var interactive := false
var status_label: Label3D
var serif: FontVariation
var body: FontVariation
var board_lamp: OmniLight3D
var textures := {}
var tilt_seed := 0

func setup(main_node: Node, panel: MeshInstance3D) -> void:
	main = main_node
	serif = FontVariation.new()
	serif.base_font = load(FONT_PATH)
	serif.variation_opentype = {TextServerManager.get_primary_interface().name_to_tag("wght"): 700}
	body = FontVariation.new()
	body.base_font = load(BODY_FONT_PATH)
	body.variation_opentype = {TextServerManager.get_primary_interface().name_to_tag("wght"): 600}
	# The parchment faces +X in the world; build a frame whose +Z points out of it.
	var centre: Vector3 = panel.global_transform * panel.get_aabb().get_center()
	global_transform = Transform3D(Basis(Vector3(0, 0, -1), Vector3.UP, Vector3(1, 0, 0)), centre + Vector3(0.03, 0, 0))
	# Warm lantern light in front of the board (the sun is behind it).
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
	tilt_seed = 0

func rebuild() -> void:
	var keep := focus
	clear()
	text("OPÇÕES", Vector2(0, 0.7), 50, INK, true)
	note("GERAL", Vector2(-0.42, 0.5), Vector2(0.8, 0.2), main.settings_tab == "geral", 27, func() -> void: switch_tab("geral"))
	note("CONTROLES", Vector2(0.42, 0.5), Vector2(0.8, 0.2), main.settings_tab == "controles", 27, func() -> void: switch_tab("controles"))
	if main.settings_tab == "geral":
		build_general()
	else:
		build_controls()
	note("ESC  VOLTAR", Vector2(-0.55, FOOTER_Y), Vector2(0.68, 0.2), false, 24, func() -> void: main.close_settings(), "papel-botao-normal")
	note("SALVAR E VOLTAR", Vector2(0.4, FOOTER_Y), Vector2(1.04, 0.22), true, 25, func() -> void: main.close_settings(), "papel-acao-largo")
	status_label = text("", Vector2(0, -0.52), 17, INK_FADED, false)
	focus = clampi(keep, 0, widgets.size() - 1)
	refresh_focus()

func build_general() -> void:
	var p: GalePreferences = main.prefs
	var left := -1.29
	var right := 0.03
	heading("ÁUDIO", Vector2(left, 0.33))
	heading("JOGO E CONFORTO", Vector2(right, 0.33))
	slider_row("Volume geral", Vector2(left, 0.15), Vector2(-0.52, -0.12), p.volume, func(v: float) -> void: p.volume = v)
	slider_row("Música", Vector2(left, 0.01), Vector2(-0.52, -0.12), p.music_volume, func(v: float) -> void: p.music_volume = v)
	slider_row("Efeitos sonoros", Vector2(left, -0.13), Vector2(-0.52, -0.12), p.sfx_volume, func(v: float) -> void: p.sfx_volume = v)
	toggle_row("Áudio ativo", Vector2(left, -0.27), -0.45, not p.muted, func(on: bool) -> void: p.muted = not on)
	slider_row("Intensidade da câmera", Vector2(right, 0.15), Vector2(1.04, 1.4), p.shake_strength, func(v: float) -> void: p.shake_strength = v)
	cycle_row("Dificuldade Arcade", Vector2(right, 0.03), 1.04, ["Tranquilo", "Normal", "Intenso"], p.difficulty, func(i: int) -> void: p.difficulty = i)
	toggle_row("Flashes de impacto", Vector2(right, -0.1), 1.04, p.flashes, func(on: bool) -> void: p.flashes = on)
	toggle_row("Vibração do gamepad", Vector2(right, -0.22), 1.04, p.vibration, func(on: bool) -> void: p.vibration = on)
	toggle_row("Mostrar áreas de colisão", Vector2(right, -0.34), 1.04, main.arena.show_boxes, func(on: bool) -> void: main.arena.show_boxes = on)
	sprite("divisor-vertical", 0.02, Vector3(-0.05, -0.04, 0.004), self, 0.76)

func build_controls() -> void:
	note("TECLADO", Vector2(-0.98, 0.33), Vector2(0.5, 0.13), main.settings_input == "teclado", 17, func() -> void: switch_input("teclado"))
	note("GAMEPAD", Vector2(-0.44, 0.33), Vector2(0.5, 0.13), main.settings_input == "gamepad", 17, func() -> void: switch_input("gamepad"))
	if main.settings_input == "teclado":
		note("RESTAURAR PADRÕES", Vector2(1.0, 0.33), Vector2(0.62, 0.13), false, 13, func() -> void: main.restore_default_keys(), "papel-acao-largo")
	sprite("divisor-vertical", 0.02, Vector3(-0.03, -0.12, 0.004), self, 0.62)
	# Each player gets two short columns of actions, every key circled in ink.
	for player in 2:
		var x0 := -1.29 if player == 0 else 0.03
		heading("JOGADOR %d" % (player + 1), Vector2(x0, 0.2))
		for action in GalePreferences.ACTIONS.size():
			var x := x0 + 0.64 * (action / 6)
			var y := 0.07 - (action % 6) * 0.098
			text(ACTION_LABELS[action], Vector2(x, y), 22, INK, false, HORIZONTAL_ALIGNMENT_LEFT)
			if main.settings_input == "teclado":
				var active: bool = main.listening == [player, action]
				key_oval(main.key_label(main.prefs.keys[player][action]), Vector2(x + 0.45, y), active, func() -> void:
					main.listening = [player, action]
					main.show_settings()
					main.rebind_label.text = "Pressione a nova tecla para %s do Jogador %d. Esc cancela." % [ACTION_LABELS[action], player + 1])
			else:
				key_oval(PAD_LABELS[action], Vector2(x + 0.45, y), false, Callable())

# --- pieces -------------------------------------------------------------------------
func texture(id: String) -> Texture2D:
	if not textures.has(id):
		textures[id] = load(PAPER % id)
	return textures[id]

func sprite(id: String, width: float, pos: Vector3, parent: Node3D = self, height: float = -1.0, shadow := false) -> MeshInstance3D:
	var tex := texture(id)
	var quad := QuadMesh.new()
	quad.size = Vector2(width, height if height > 0.0 else width * tex.get_height() / tex.get_width())
	var node := MeshInstance3D.new()
	node.mesh = quad
	node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var material := StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.albedo_texture = tex
	if shadow:
		# A soft dark copy under a note: it reads as paper lifted off the parchment.
		material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		material.albedo_color = Color(0.12, 0.07, 0.02, 0.32)
	elif id.begins_with("papel") or id.begins_with("pino"):
		# Paper and brass keep the hard PSX pixels and torn edges.
		material.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
		material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
		material.alpha_scissor_threshold = 0.5
	else:
		# Ink strokes are thin: blend them so they never break up when small.
		material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	node.material_override = material
	node.position = pos
	parent.add_child(node)
	return node

func set_sprite(node: MeshInstance3D, id: String) -> void:
	(node.material_override as StandardMaterial3D).albedo_texture = texture(id)

func text(value: String, pos: Vector2, size: int, color: Color, heading_font: bool = false, align := HORIZONTAL_ALIGNMENT_CENTER, parent: Node3D = self, z: float = 0.008) -> Label3D:
	var label := Label3D.new()
	label.text = value
	label.font_size = size
	label.pixel_size = 0.003
	label.modulate = color
	label.outline_size = 0
	label.horizontal_alignment = align
	label.position = Vector3(pos.x, pos.y, z)
	label.double_sided = false
	label.font = serif if heading_font else body
	parent.add_child(label)
	return label

func text_width(value: String, size: int, heading_font: bool) -> float:
	var font: Font = serif if heading_font else body
	return font.get_string_size(value, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x * 0.003

func heading(value: String, pos: Vector2) -> void:
	text(value, pos, 31, INK, true, HORIZONTAL_ALIGNMENT_LEFT)
	var width := text_width(value, 31, true) + 0.06
	sprite("sublinhado-duplo", width, Vector3(pos.x + width * 0.5 - 0.03, pos.y - 0.065, 0.005), self, 0.03)

func add_widget(widget: Dictionary) -> int:
	widgets.append(widget)
	return widgets.size() - 1

func next_tilt() -> float:
	# Each note is pinned a little crooked, always the same way for the same layout.
	tilt_seed += 1
	return deg_to_rad(sin(tilt_seed * 12.9898) * 1.6)

func note(label: String, pos: Vector2, size: Vector2, active: bool, font: int, action: Callable, paper := "") -> void:
	var root := Node3D.new()
	root.position = Vector3(pos.x, pos.y, 0.0)
	root.rotation.z = next_tilt()
	add_child(root)
	var base := paper if paper != "" else ("papel-botao-selecionado" if active else "papel-botao-normal")
	sprite(base, size.x, Vector3(0.016, -0.02, 0.003), root, size.y, true)
	var sheet := sprite(base, size.x, Vector3(0, 0, 0.006), root, size.y)
	var lift := 0.012 if active else 0.0
	var caption := text(label, Vector2(0.03 if active else 0.0, lift), font, INK if active else INK_FADED.darkened(0.25), true, HORIZONTAL_ALIGNMENT_CENTER, root, 0.012)
	if active:
		var mark := text_width(label, font, true) * 0.5 + 0.06
		sprite("confirmar", 0.085, Vector3(-mark + 0.01, lift + 0.01, 0.011), root)
		if paper != "":
			sprite("sublinhado-duplo", size.x * 0.62, Vector3(0.03, lift - 0.06, 0.011), root, 0.028)
	add_widget({"kind": "button", "root": root, "sheet": sheet, "paper": base, "active": active, "caption": caption,
		"rect": Rect2(pos - size * 0.5, size), "action": action, "rest": 0.0})

func slider_row(label: String, pos: Vector2, rail: Vector2, value: float, setter: Callable) -> void:
	# rail: x of the rail centre and the right edge of the percentage.
	text(label, pos, 26, INK, false, HORIZONTAL_ALIGNMENT_LEFT)
	var width := 0.42
	sprite("slider-trilho", width, Vector3(rail.x, pos.y, 0.005), self, 0.058)
	var dot := sprite("slider-marcador", 0.052, Vector3(rail.x, pos.y, 0.009))
	var percent := text("", Vector2(rail.y, pos.y), 25, INK, false, HORIZONTAL_ALIGNMENT_RIGHT)
	# The ink rail has end ticks; the dot travels between them.
	var travel := width * 0.9
	var index := add_widget({"kind": "slider", "root": dot, "rect": Rect2(Vector2(rail.x - width * 0.5 - 0.04, pos.y - 0.05), Vector2(width + 0.08, 0.1)),
		"value": value, "set": setter, "percent": percent, "x0": rail.x - travel * 0.5, "width": travel, "rest": 0.009})
	set_slider(index, value, false)

func set_slider(index: int, value: float, save: bool = true) -> void:
	var w: Dictionary = widgets[index]
	value = clampf(snappedf(value, 0.05), 0.0, 1.0)
	w.value = value
	var dot: Node3D = w.root
	dot.position.x = float(w.x0) + float(w.width) * value
	(w.percent as Label3D).text = "%d%%" % roundi(value * 100)
	if save:
		(w.set as Callable).call(value)
		main.persist()

func toggle_row(label: String, pos: Vector2, x: float, on: bool, setter: Callable) -> void:
	text(label, pos, 26, INK, false, HORIZONTAL_ALIGNMENT_LEFT)
	var root := Node3D.new()
	root.position = Vector3(x, pos.y, 0)
	add_child(root)
	# The answer is written on the paper and circled in ink.
	var oval := sprite("oval-contorno", 0.25, Vector3(0, -0.004, 0.005), root, 0.1)
	var answer := text("Sim" if on else "Não", Vector2.ZERO, 25, INK, false, HORIZONTAL_ALIGNMENT_CENTER, root, 0.009)
	add_widget({"kind": "toggle", "root": root, "rect": Rect2(Vector2(x - 0.13, pos.y - 0.055), Vector2(0.26, 0.11)), "on": on,
		"set": setter, "oval": oval, "caption": answer, "active": false, "rest": 0.0})

func cycle_row(label: String, pos: Vector2, x: float, names: Array, index: int, setter: Callable) -> void:
	text(label, pos, 26, INK, false, HORIZONTAL_ALIGNMENT_LEFT)
	var root := Node3D.new()
	root.position = Vector3(x, pos.y, 0)
	add_child(root)
	sprite("seta-esquerda", 0.034, Vector3(-0.2, 0, 0.006), root)
	sprite("seta-direita", 0.034, Vector3(0.2, 0, 0.006), root)
	sprite("sublinhado-duplo", 0.26, Vector3(0, -0.045, 0.005), root, 0.022)
	var value := text(names[index], Vector2(0, 0.006), 25, INK, false, HORIZONTAL_ALIGNMENT_CENTER, root, 0.009)
	add_widget({"kind": "cycle", "root": root, "rect": Rect2(Vector2(x - 0.24, pos.y - 0.06), Vector2(0.48, 0.12)), "names": names,
		"index": index, "set": setter, "label": value, "rest": 0.0})

func key_oval(label: String, pos: Vector2, active: bool, action: Callable) -> void:
	var root := Node3D.new()
	root.position = Vector3(pos.x, pos.y, 0)
	add_child(root)
	var oval := sprite("oval-preenchido" if active else "oval-contorno", 0.27, Vector3(0, -0.003, 0.005), root, 0.078)
	var caption := text(label, Vector2.ZERO, 16, CREAM if active else INK, false, HORIZONTAL_ALIGNMENT_CENTER, root, 0.009)
	if action.is_valid():
		add_widget({"kind": "button", "root": root, "oval": oval, "caption": caption, "active": active,
			"rect": Rect2(pos - Vector2(0.135, 0.033), Vector2(0.27, 0.066)), "action": action, "rest": 0.0})

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
	# The note lifts off the parchment and settles back on its pin.
	var root: Node3D = w.root
	if not is_instance_valid(root):
		return
	var rest := float(w.rest)
	var tween := root.create_tween()
	tween.tween_property(root, "position:z", rest + 0.035, 0.06).set_trans(Tween.TRANS_QUAD)
	tween.tween_property(root, "position:z", rest, 0.18).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)

func set_toggle(index: int, on: bool) -> void:
	var w: Dictionary = widgets[index]
	w.on = on
	(w.caption as Label3D).text = "Sim" if on else "Não"
	(w.set as Callable).call(on)
	main.persist()

func step_cycle(index: int, step: int) -> void:
	var w: Dictionary = widgets[index]
	w.index = posmod(int(w.index) + step, (w.names as Array).size())
	(w.label as Label3D).text = w.names[w.index]
	(w.set as Callable).call(int(w.index))
	main.persist()

func refresh_focus() -> void:
	for i in widgets.size():
		var w: Dictionary = widgets[i]
		var root: Node3D = w.root
		if not is_instance_valid(root):
			continue
		var lit := interactive and (i == focus or i == hover)
		# Hover: a note gets the green-edged paper, an ink oval gets filled in.
		if w.has("sheet") and not bool(w.active):
			set_sprite(w.sheet, "papel-botao-hover" if lit else String(w.paper))
		if w.has("oval") and not bool(w.active):
			set_sprite(w.oval, "oval-preenchido" if lit else "oval-contorno")
			(w.caption as Label3D).modulate = CREAM if lit else INK
		var target := Vector3.ONE * (1.06 if lit else 1.0)
		root.create_tween().tween_property(root, "scale", target, 0.1)

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
