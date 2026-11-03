extends Node

var data := GaleData.new()
var prefs := GalePreferences.new()
var sim := GaleCombat.new(data)
var arena: GaleArena
var audio: GaleAudio
var ui: Control
var screen := "menu"
var mode := "arcade"
var fighter1 := "kaze"
var fighter2 := "ignis"
var stage := "zephyr_dojo"
var palette1 := 0
var palette2 := 0
var arcade_index := 1
var skill_target_fighter := "kaze"
var modal: Control
var menu: Control
var hud: Control
var health_bars: Array[ProgressBar] = []
var meter_bars: Array[ProgressBar] = []
var name_labels: Array[Label] = []
var combo_labels: Array[Label] = []
var portrait_rects: Array[TextureRect] = []
var timer_label: Label
var banner_label: Label
var round_label: Label
var status_label: Label
var rebind_label: Label
var listening: Array = []
var ticks := 0
var skill_target_player := 0
var tutorial: GaleTutorial
var tutorial_label: Label
var training_behavior := 0
var command_labels: Array = []
var in_selection := false
var editorial_font: Font
var hover_quiet_until := 0
var attack_serials := [0, 0]
var early_sound_serials := [-1, -1]
# Recorded strike sounds start this many frames before the active window so
# their transient lands on the contact frame.
const STRIKE_SOUND_LEAD_FRAMES := 4

func _ready() -> void:
	DisplayServer.window_set_title("Gale Breaker")
	# Cinzel, the roman serif of the UI concepts (assets/ui/fonts, SIL OFL).
	editorial_font=cinzel(600)
	get_window().min_size = Vector2i(1000, 650)
	prefs.load_from_disk(data)
	Input.joy_connection_changed.connect(func(_device: int, _connected: bool) -> void: prefs.install_gamepads())
	arena = GaleArena.new()
	add_child(arena)
	audio = GaleAudio.new()
	add_child(audio)
	audio.apply_settings(prefs)
	var layer := CanvasLayer.new()
	add_child(layer)
	ui = Control.new()
	ui.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	ui.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer.add_child(ui)
	ui.theme = make_theme()
	sim.start(fighter1, fighter2, stage, "training", prefs.skills[fighter1])
	arena.build(data, sim)
	show_menu()

func make_theme() -> Theme:
	var theme := Theme.new()
	theme.default_font_size = 16
	var panel := StyleBoxFlat.new()
	panel.bg_color = Color(0.07, 0.12, 0.11, 0.90)
	panel.border_color = Color("28654F")
	panel.set_border_width_all(2)
	panel.set_corner_radius_all(6)
	panel.content_margin_left = 20
	panel.content_margin_right = 20
	panel.content_margin_top = 16
	panel.content_margin_bottom = 16
	theme.set_stylebox("panel", "PanelContainer", panel)
	var normal := StyleBoxFlat.new()
	normal.bg_color = Color(0.11, 0.20, 0.17, 0.92)
	normal.border_color = Color("28654F")
	normal.set_border_width_all(1)
	normal.set_corner_radius_all(4)
	normal.content_margin_top = 8
	normal.content_margin_bottom = 8
	normal.content_margin_left = 14
	normal.content_margin_right = 14
	theme.set_stylebox("normal", "Button", normal)
	var hover: StyleBoxFlat = normal.duplicate()
	hover.bg_color = Color("28654F")
	hover.border_color = Color("84A98C")
	theme.set_stylebox("hover", "Button", hover)
	theme.set_stylebox("pressed", "Button", hover)
	theme.set_color("font_color", "Label", Color("F8F5EE"))
	theme.set_color("font_color", "Button", Color("F8F5EE"))
	return theme

func label(parent: Node, text: String, size: int = 16, color: Color = Color("F8F5EE")) -> Label:
	var node := Label.new()
	node.text = text
	node.add_theme_font_size_override("font_size", size)
	node.add_theme_color_override("font_color", color)
	if size>=26 and editorial_font!=null:node.add_theme_font_override("font",editorial_font)
	parent.add_child(node)
	return node

func nav_button(parent: Node, text: String, callback: Callable, active: bool = false) -> Button:
	var node:=button(parent,text,callback,active)
	var normal:=StyleBoxFlat.new()
	normal.bg_color=Color(0,0,0,0)
	normal.content_margin_left=14;normal.content_margin_right=14
	normal.content_margin_top=8;normal.content_margin_bottom=8
	node.add_theme_stylebox_override("normal",normal)
	var hover:StyleBoxFlat=normal.duplicate()
	hover.bg_color=Color(0.15,0.32,0.25,0.25)
	node.add_theme_stylebox_override("hover",hover)
	var focus:StyleBoxFlat=normal.duplicate()
	focus.border_color=Color("84A98C");focus.set_border_width_all(1)
	node.add_theme_stylebox_override("focus",focus)
	node.add_theme_color_override("font_color",Color("A3C9A8") if active else Color("F8F5EE"))
	node.alignment=HORIZONTAL_ALIGNMENT_LEFT
	return node

func button(parent: Node, text: String, callback: Callable, primary_style: bool = false) -> Button:
	var node := Button.new()
	node.text = text
	node.focus_mode = Control.FOCUS_ALL
	if primary_style:
		var jade_box := StyleBoxFlat.new()
		jade_box.bg_color = Color("28654F")
		jade_box.border_color = Color("A3C9A8")
		jade_box.set_border_width_all(1)
		jade_box.set_corner_radius_all(4)
		jade_box.content_margin_top = 10
		jade_box.content_margin_bottom = 10
		jade_box.content_margin_left = 16
		jade_box.content_margin_right = 16
		node.add_theme_stylebox_override("normal", jade_box)
	node.pressed.connect(func() -> void:
		audio.play("click")
		callback.call())
	node.mouse_entered.connect(func() -> void: audio.play("hover"))
	# Keyboard/gamepad navigation; skip clicks (already hovered) and automatic focus on screen open.
	node.focus_entered.connect(func() -> void:
		if not node.is_hovered() and Time.get_ticks_msec() >= hover_quiet_until:
			audio.play("hover"))
	# Soft glow while hovered or focused.
	var glow := func(on: bool) -> void:
		var lit := on or node.has_focus() or node.is_hovered()
		ease_to(node, "modulate", Color(1.1, 1.1, 1.1) if lit else Color.WHITE, 0.14)
	node.mouse_entered.connect(glow.bind(true))
	node.focus_entered.connect(glow.bind(true))
	node.mouse_exited.connect(glow.bind(false))
	node.focus_exited.connect(glow.bind(false))
	parent.add_child(node)
	return node

## Smooth UI motion helpers (all short ease-out tweens bound to the node).
func ease_to(node: Node, property: String, value: Variant, duration: float) -> void:
	if not is_instance_valid(node) or not node.is_inside_tree():
		return
	var tween := node.create_tween()
	tween.set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	tween.tween_property(node, property, value, duration)

func fade_in(node: CanvasItem, duration: float = 0.2, slide: Vector2 = Vector2.ZERO) -> void:
	node.modulate.a = 0.0
	var tween := node.create_tween().set_parallel(true)
	tween.set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	tween.tween_property(node, "modulate:a", 1.0, duration)
	if slide != Vector2.ZERO and node is Control:
		var control := node as Control
		var target := control.position
		control.position = target + slide
		tween.tween_property(control, "position", target, duration)

func instantiate_ui_scene(scene_path: String, fallback_alpha: float = 0.65) -> Control:
	var root_ctrl: Control
	if ResourceLoader.exists(scene_path):
		var packed: PackedScene = load(scene_path) as PackedScene
		root_ctrl = packed.instantiate() as Control
	else:
		root_ctrl = Control.new()
	root_ctrl.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	ui.add_child(root_ctrl)
	var bg := ColorRect.new()
	bg.color = Color(0.02, 0.04, 0.05, fallback_alpha)
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root_ctrl.add_child(bg)
	return root_ctrl

func overlay(alpha: float = 0.72) -> Control:
	var background := ColorRect.new()
	background.color = Color(0.02, 0.04, 0.05, alpha)
	background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	ui.add_child(background)
	return background

func centered(parent: Control, width: float = 1020, ivory_card: bool = false, scroll_height: float = 0.0) -> VBoxContainer:
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	parent.add_child(center)
	var panel := PanelContainer.new()
	panel.custom_minimum_size.x = width
	if ivory_card:
		var card := StyleBoxFlat.new()
		card.bg_color = Color("F4EFE4")
		card.border_color = Color("28654F")
		card.set_border_width_all(2)
		card.set_corner_radius_all(4)
		card.content_margin_left = 28
		card.content_margin_right = 28
		card.content_margin_top = 24
		card.content_margin_bottom = 24
		panel.add_theme_stylebox_override("panel", card)
	center.add_child(panel)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 12)
	if scroll_height > 0.0:
		var scroll := ScrollContainer.new()
		scroll.custom_minimum_size.y = minf(scroll_height,float(get_viewport().get_visible_rect().size.y)-100.0)
		scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
		panel.add_child(scroll)
		scroll.add_child(column)
		column.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	else:
		panel.add_child(column)
	return column

func make_portrait_box(parent: Node, id: String, size_px: int = 68) -> TextureRect:
	var frame := PanelContainer.new()
	var fstyle := StyleBoxFlat.new()
	var cat := GaleVisualCatalog.load_for(id)
	fstyle.bg_color = Color("1A2421")
	fstyle.border_color = cat.accent_color
	fstyle.set_border_width_all(2)
	fstyle.set_corner_radius_all(4)
	fstyle.content_margin_left = 2
	fstyle.content_margin_right = 2
	fstyle.content_margin_top = 2
	fstyle.content_margin_bottom = 2
	frame.add_theme_stylebox_override("panel", fstyle)
	parent.add_child(frame)
	var rect := TextureRect.new()
	rect.custom_minimum_size = Vector2(size_px, size_px)
	rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	rect.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	if ResourceLoader.exists(cat.portrait_path):
		rect.texture = load(cat.portrait_path)
	frame.add_child(rect)
	return rect

func close_modal() -> void:
	listening.clear()
	if is_instance_valid(modal):
		ui.remove_child(modal)
		modal.queue_free()
	modal = null
	if is_instance_valid(menu):
		menu.show()

func clear_menu() -> void:
	if is_instance_valid(menu):
		ui.remove_child(menu)
		menu.queue_free()
	menu = null

func show_menu(selection: bool = false) -> void:
	tutorial = null
	in_selection = selection
	close_modal()
	clear_menu()
	if is_instance_valid(hud):
		ui.remove_child(hud)
		hud.queue_free()
		hud = null
	screen = "selection" if selection else "menu"
	audio.stop_voice()
	audio.play_menu_music()
	if not selection:
		# Beach scene from concept-art/ui/menu-principal-praia-v1.png.
		arena.show_menu_scene()
		menu = instantiate_ui_scene("res://scenes/ui/main_menu.tscn", 0.0)
		build_beach_menu()
		return
	if arena.menu_scene_active:
		preview()
	arena.set_menu_mode(false, false)

	menu = instantiate_ui_scene("res://scenes/ui/main_menu.tscn", 0.38)
	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	margin.add_theme_constant_override("margin_left", 56)
	margin.add_theme_constant_override("margin_right", 56)
	margin.add_theme_constant_override("margin_top", 42)
	margin.add_theme_constant_override("margin_bottom", 32)
	menu.add_child(margin)

	var main_vbox := VBoxContainer.new()
	main_vbox.add_theme_constant_override("separation", 18)
	margin.add_child(main_vbox)

	# Title ONLY "GALE BREAKER" (no Elemental Clash subtitle per GDD & Implementation Plan)
	var title_lbl := label(main_vbox, "G A L E   B R E A K E R", 44, Color("F8F5EE"))
	title_lbl.add_theme_constant_override("outline_size", 2)
	var gold_line := ColorRect.new()
	gold_line.custom_minimum_size = Vector2(420, 2)
	gold_line.color = Color("C5A059")
	main_vbox.add_child(gold_line)

	var body_hbox := HBoxContainer.new()
	body_hbox.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body_hbox.add_theme_constant_override("separation", 48)
	main_vbox.add_child(body_hbox)

	# Left Minimalist Navigation List (matching menu-principal-v3.png)
	var nav_col := VBoxContainer.new()
	nav_col.custom_minimum_size.x = 300
	nav_col.add_theme_constant_override("separation", 10)
	body_hbox.add_child(nav_col)

	var mode_titles := {"arcade": "ARCADE", "versus": "VERSUS LOCAL", "training": "TREINO"}
	for m_key: String in ["arcade", "versus", "training"]:
		var is_active: bool = (mode == m_key)
		var prefix := "—   " if is_active else "      "
		var btn := nav_button(nav_col, prefix + String(mode_titles[m_key]), func() -> void:
			mode = m_key
			show_menu(true), is_active)
		btn.alignment = HORIZONTAL_ALIGNMENT_LEFT
		if is_active:
			call_deferred("focus_control",btn)

	var sk_btn := nav_button(nav_col, "      HABILIDADES", func() -> void:
		skill_target_player = 0
		skill_target_fighter = fighter1
		show_skills())
	sk_btn.alignment = HORIZONTAL_ALIGNMENT_LEFT

	var mv_btn := nav_button(nav_col, "      LISTA DE GOLPES", show_moves)
	mv_btn.alignment = HORIZONTAL_ALIGNMENT_LEFT
	mv_btn.visible=selection

	var op_btn := nav_button(nav_col, "      OPÇÕES", show_settings)
	op_btn.alignment = HORIZONTAL_ALIGNMENT_LEFT

	var start_btn := nav_button(nav_col, "—   INICIAR COMBATE", func() -> void:
		arcade_index = 1
		begin_fight(), true)
	start_btn.alignment = HORIZONTAL_ALIGNMENT_LEFT
	start_btn.visible=selection
	if selection: call_deferred("focus_control",start_btn)
	nav_button(nav_col,"      TUTORIAL",start_tutorial)
	if not prefs.arcade_run.is_empty():
		nav_button(nav_col,"      CONTINUAR ARCADE",resume_arcade)
	nav_button(nav_col,"      VOLTAR" if selection else "      SAIR",func() -> void:
		if selection: show_menu()
		else: get_tree().quit())
	if not selection:
		label(main_vbox,"↑ ↓  NAVEGAR     ENTER / A  CONFIRMAR     START  PREPARAR COMBATE",13,Color("D7D0C2"))
		return

	# Right Compact Match Configuration & V2 Roster Preview Card
	var setup_panel := PanelContainer.new()
	setup_panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	body_hbox.add_child(setup_panel)
	var setup := VBoxContainer.new()
	setup.add_theme_constant_override("separation", 10)
	setup_panel.add_child(setup)

	var header_row := HBoxContainer.new()
	header_row.add_theme_constant_override("separation", 18)
	setup.add_child(header_row)
	make_portrait_box(header_row, fighter1, 64)
	var cat1 := GaleVisualCatalog.load_for(fighter1)
	var cat2 := GaleVisualCatalog.load_for(fighter2)
	var vs_info := VBoxContainer.new()
	vs_info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header_row.add_child(vs_info)
	label(vs_info, "%s (%s)  ×  %s (%s)" % [cat1.display_name.to_upper(), cat1.element_label, cat2.display_name.to_upper(), cat2.element_label], 20, Color("F8F5EE"))
	label(vs_info, "%s  •  Orçamento livre de 4 pontos de habilidade" % cat1.subtitle, 13, Color("A3C9A8"))
	make_portrait_box(header_row, fighter2, 64)

	var names: Array = []
	for id: String in GaleData.IDS:
		var c := GaleVisualCatalog.load_for(id)
		names.append("%s — %s" % [c.display_name, c.subtitle])

	option(setup, "Lutador 1", names, GaleData.IDS.find(fighter1), func(index: int) -> void:
		fighter1 = GaleData.IDS[index]
		preview()
		show_menu(true))

	var p1_pal_names: Array = []
	for p: Dictionary in cat1.palettes:
		p1_pal_names.append(p.name)
	option(setup, "Paleta P1", p1_pal_names, palette1, func(index: int) -> void:
		palette1 = index
		preview())

	option(setup, "Adversário (Treino / Versus)", names, GaleData.IDS.find(fighter2), func(index: int) -> void:
		fighter2 = GaleData.IDS[index]
		preview()
		show_menu(true))

	var p2_pal_names: Array = []
	for p: Dictionary in cat2.palettes:
		p2_pal_names.append(p.name)
	option(setup, "Paleta P2", p2_pal_names, palette2, func(index: int) -> void:
		palette2 = index
		preview())

	var stages: Array = []
	for id: String in GaleData.STAGES:
		stages.append(data.stage(id).name)
	option(setup, "Arena (Treino / Versus)", stages, GaleData.STAGES.find(stage), func(index: int) -> void:
		stage = GaleData.STAGES[index]
		preview())

	var quick_row := HBoxContainer.new()
	quick_row.add_theme_constant_override("separation", 12)
	setup.add_child(quick_row)
	button(quick_row, "Habilidades P1 (%s)" % cat1.display_name, func() -> void:
		skill_target_player = 0
		skill_target_fighter = fighter1
		show_skills())
	button(quick_row, "Habilidades P2 (%s)" % cat2.display_name, func() -> void:
		skill_target_player = 1
		skill_target_fighter = fighter2
		show_skills())
	button(quick_row, "Inspecionar Modelos 3D", preview)

	# Bottom Minimalist Prompt Bar (matching menu-principal-v3.png)
	var footer_row := HBoxContainer.new()
	main_vbox.add_child(footer_row)
	label(footer_row, "↑ ↓  NAVEGAR        ENTER  CONFIRMAR        P / ESC  PAUSA        R  REINICIAR        M  ÁUDIO", 13, Color("D7D0C2"))

func build_beach_menu() -> void:
	# Soft shade on the left keeps the list readable over the bright beach.
	var gradient := Gradient.new()
	gradient.set_color(0, Color(0.02, 0.06, 0.06, 0.58))
	gradient.set_color(1, Color(0.02, 0.06, 0.06, 0.0))
	var shade_tex := GradientTexture2D.new()
	shade_tex.gradient = gradient
	shade_tex.fill_to = Vector2(1, 0)
	var shade := TextureRect.new()
	shade.texture = shade_tex
	shade.stretch_mode = TextureRect.STRETCH_SCALE
	shade.position = Vector2.ZERO
	shade.size = Vector2(640, 720)
	shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	menu.add_child(shade)
	var column := VBoxContainer.new()
	column.position = Vector2(64, 62)
	column.add_theme_constant_override("separation", 0)
	menu.add_child(column)
	# Title set in the golden alphabet (art-source/tools/generate_title.py).
	var title := TextureRect.new()
	title.texture = load("res://assets/ui/title/title.png")
	title.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	title.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT
	title.custom_minimum_size = Vector2(400, 119)
	column.add_child(title)
	var title_gap := Control.new()
	title_gap.custom_minimum_size.y = 6
	column.add_child(title_gap)
	var rule := ColorRect.new()
	rule.color = Color("C5A059")
	rule.custom_minimum_size = Vector2(300, 2)
	column.add_child(rule)
	var gap := Control.new()
	gap.custom_minimum_size.y = 24
	column.add_child(gap)
	var items: Array = [
		["ARCADE", open_arcade_select],
		["VERSUS LOCAL", open_mode.bind("versus")],
		["TREINO", open_mode.bind("training")],
		["HABILIDADES", open_player_skills],
		["OPÇÕES", open_board_settings],
	]
	if not prefs.arcade_run.is_empty():
		items.insert(1, ["CONTINUAR ARCADE", resume_arcade])
	items.append(["TUTORIAL", start_tutorial])
	items.append(["SAIR", quit_game])
	var mode_titles := {"arcade": "ARCADE", "versus": "VERSUS LOCAL", "training": "TREINO"}
	for entry: Array in items:
		var item := beach_item(column, String(entry[0]), entry[1])
		if String(entry[0]) == mode_titles.get(mode, "ARCADE"):
			call_deferred("focus_control", item)
	fade_in(column, 0.35, Vector2(-16, 0))
	var footer := label(menu, "↑↓  NAVEGAR        ENTER  CONFIRMAR", 13, Color("EFE8DA"))
	footer.position = Vector2(46, 684)
	footer.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.4))
	footer.add_theme_constant_override("outline_size", 4)

func open_mode(selected_mode: String) -> void:
	mode = selected_mode
	show_menu(true)

func open_player_skills() -> void:
	skill_target_player = 0
	skill_target_fighter = fighter1
	show_skills()

func quit_game() -> void:
	get_tree().quit()

## Concept menu entry: letter-spaced serif text; a jade dash marks the focused item.
func beach_item(parent: Control, text: String, callback: Callable) -> Button:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 16)
	parent.add_child(row)
	# The jade dash grows out from the left on focus; its slot keeps the text aligned.
	var slot := Control.new()
	slot.custom_minimum_size = Vector2(30, 4)
	slot.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(slot)
	var dash := ColorRect.new()
	dash.color = Color("A3C9A8")
	dash.size = Vector2(0, 4)
	dash.modulate.a = 0.0
	slot.add_child(dash)
	var item := button(row, text, callback)
	item.alignment = HORIZONTAL_ALIGNMENT_LEFT
	item.custom_minimum_size = Vector2(380, 46)
	item.add_theme_font_override("font", spaced_font(5))
	item.add_theme_font_size_override("font_size", 23)
	for state: String in ["normal", "hover", "focus", "pressed", "hover_pressed"]:
		item.add_theme_stylebox_override(state, StyleBoxEmpty.new())
	item.add_theme_color_override("font_color", Color("EFE8DA"))
	for state: String in ["font_hover_color", "font_focus_color", "font_pressed_color"]:
		item.add_theme_color_override(state, Color.WHITE)
	item.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.35))
	item.add_theme_constant_override("outline_size", 5)
	item.focus_entered.connect(func() -> void:
		ease_to(dash, "size:x", 30.0, 0.18)
		ease_to(dash, "modulate:a", 1.0, 0.18))
	item.focus_exited.connect(func() -> void:
		ease_to(dash, "size:x", 0.0, 0.18)
		ease_to(dash, "modulate:a", 0.0, 0.18))
	# Hovering moves the focus, so mouse and keyboard share one marker.
	item.mouse_entered.connect(func() -> void: item.grab_focus())
	return item

func spaced_font(spacing: int) -> FontVariation:
	var font := FontVariation.new()
	font.base_font = editorial_font
	font.spacing_glyph = spacing
	return font

func option(parent: Node, title: String, values: Array, selected: int, callback: Callable) -> void:
	var row := HBoxContainer.new()
	parent.add_child(row)
	var heading := label(row, title, 14, Color("D7D0C2"))
	heading.custom_minimum_size.x = 200
	var choice := OptionButton.new()
	choice.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	for text: String in values:
		choice.add_item(text)
	choice.select(clampi(selected, 0, values.size() - 1))
	choice.item_selected.connect(callback)
	row.add_child(choice)

func preview() -> void:
	sim.start(fighter1, fighter2, stage, "training", prefs.skills[fighter1], prefs.skills[fighter2], 1, palette1, palette2)
	arena.build(data, sim)
	arena.set_menu_mode(false, false)

func start_match() -> void:
	close_modal()
	clear_menu()
	var opponent := fighter2
	var arena_id := stage
	var opponent_skills: Array = prefs.skills2.get(fighter2, []) if mode == "versus" else []
	var opponent_palette := palette2
	if mode == "arcade":
		var spec := data.arcade(fighter1, arcade_index)
		opponent = spec.opponentId
		arena_id = spec.stageId
		opponent_skills = spec.unlockedSkills
		opponent_palette = int(spec.opponentPalette)
	sim.start(fighter1, opponent, arena_id, mode, prefs.skills[fighter1], opponent_skills, arcade_index, palette1, opponent_palette)
	sim.difficulty = prefs.difficulty
	if mode == "arcade":
		prefs.arcade_run = {"fighter":fighter1,"index":arcade_index,"palette":palette1,"skills":prefs.skills[fighter1].duplicate()}
		persist()
	arena.build(data, sim)
	arena.set_menu_mode(false, false)
	screen = "playing"
	build_hud()
	apply_presentation_options()
	audio.set_music(sim.stage_id, true)

func build_hud() -> void:
	command_labels.clear()
	if is_instance_valid(hud):
		ui.remove_child(hud)
		hud.queue_free()
	health_bars.clear()
	meter_bars.clear()
	name_labels.clear()
	combo_labels.clear()
	portrait_rects.clear()

	if ResourceLoader.exists("res://scenes/ui/combat_hud.tscn"):
		var packed_hud: PackedScene = load("res://scenes/ui/combat_hud.tscn")
		hud = packed_hud.instantiate() as Control
	else:
		hud = Control.new()
	hud.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	hud.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ui.add_child(hud)

	# Top Bar matching hud-combate-v2.png: Portrait P1 | Name & HP Bar | 99 / ROUND 1 | Name & HP Bar | Portrait P2
	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_TOP_WIDE)
	for side: String in ["left", "right", "top"]:
		margin.add_theme_constant_override("margin_" + side, 22)
	hud.add_child(margin)

	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 16)
	margin.add_child(row)

	var p1_id: String = sim.p1.id
	var p2_id: String = sim.p2.id
	portrait_rects.append(make_portrait_box(row, p1_id, 66))

	for i in 2:
		if i == 1:
			var center := VBoxContainer.new()
			center.custom_minimum_size.x = 150
			row.add_child(center)
			timer_label = label(center, "99", 38, Color("F8F5EE"))
			timer_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			round_label = label(center, "— ROUND 1 —", 13, Color("D7D0C2"))
			round_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			var pause_button:=button(center, "PAUSA", pause_match)
			pause_button.focus_mode=Control.FOCUS_NONE
		var column := VBoxContainer.new()
		column.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(column)
		var nl := label(column, "", 20, Color("F8F5EE"))
		if i == 1:
			nl.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		name_labels.append(nl)

		var health := ProgressBar.new()
		health.custom_minimum_size.y = 24
		health.show_percentage = false
		var bg_box := StyleBoxFlat.new()
		bg_box.bg_color = Color(0.08, 0.11, 0.11, 0.88)
		bg_box.border_color = Color("C5A059")
		bg_box.set_border_width_all(2)
		bg_box.set_corner_radius_all(3)
		health.add_theme_stylebox_override("background", bg_box)
		var fill := StyleBoxFlat.new()
		fill.bg_color = Color("28654F") if i == 0 else Color("A54332")
		fill.set_corner_radius_all(2)
		health.add_theme_stylebox_override("fill", fill)
		column.add_child(health)
		health_bars.append(health)

		var cl := label(column, "", 16, Color("F4CE75"))
		if i == 1:
			cl.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		combo_labels.append(cl)

	portrait_rects.append(make_portrait_box(row, p2_id, 66))

	banner_label = label(hud, "", 30, Color("F4CE75"))
	banner_label.set_anchors_and_offsets_preset(Control.PRESET_CENTER_TOP)
	banner_label.offset_left = -450
	banner_label.offset_right = 450
	banner_label.offset_top = 152
	banner_label.offset_bottom = 212
	banner_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER

	# Bottom Bar matching hud-combate-v2.png + GDD v0.9 16 Attack Icons & Elemental Meters
	var footer := PanelContainer.new()
	footer.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	footer.offset_top = -98
	var fstyle := StyleBoxFlat.new()
	fstyle.bg_color = Color(0.04, 0.07, 0.07, 0.84)
	fstyle.border_color = Color("28654F")
	fstyle.border_width_top = 1
	fstyle.content_margin_left = 22
	fstyle.content_margin_right = 22
	fstyle.content_margin_top = 8
	fstyle.content_margin_bottom = 8
	footer.add_theme_stylebox_override("panel", fstyle)
	hud.add_child(footer)

	var bottom_hbox := HBoxContainer.new()
	bottom_hbox.add_theme_constant_override("separation", 20)
	footer.add_child(bottom_hbox)

	for i in 2:
		var fid: String = p1_id if i == 0 else p2_id
		var cat := GaleVisualCatalog.load_for(fid)
		var side_col := VBoxContainer.new()
		side_col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		side_col.add_theme_constant_override("separation", 4)
		bottom_hbox.add_child(side_col)

		var elem_row := HBoxContainer.new()
		elem_row.add_theme_constant_override("separation", 10)
		side_col.add_child(elem_row)
		label(elem_row, "◆ " + cat.element_label, 14, cat.accent_color.lightened(0.25))

		var meter := ProgressBar.new()
		meter.custom_minimum_size = Vector2(180, 12)
		meter.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		meter.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		meter.show_percentage = false
		var mfill := StyleBoxFlat.new()
		mfill.bg_color = cat.accent_color.lightened(0.15)
		mfill.set_corner_radius_all(2)
		meter.add_theme_stylebox_override("fill", mfill)
		elem_row.add_child(meter)
		meter_bars.append(meter)

		# 4 GDD v0.9 Attack Icons with move names and current keybinds
		var icons_row := GridContainer.new()
		icons_row.columns=2
		icons_row.add_theme_constant_override("h_separation",10)
		icons_row.add_theme_constant_override("v_separation",2)
		side_col.add_child(icons_row)
		var action_defs := [
			{"act": "light", "key_idx": 4},
			{"act": "heavy", "key_idx": 5},
			{"act": "elemental", "key_idx": 6},
			{"act": "ultimate", "key_idx": 7},
		]
		for adef: Dictionary in action_defs:
			var cell:=HBoxContainer.new()
			cell.size_flags_horizontal=Control.SIZE_EXPAND_FILL
			icons_row.add_child(cell)
			var act_name: String = adef.act
			var icon_path: String = cat.attack_icons.get(act_name, "")
			if ResourceLoader.exists(icon_path):
				var irec := TextureRect.new()
				irec.custom_minimum_size = Vector2(22, 22)
				irec.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
				irec.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
				irec.texture = load(icon_path)
				cell.add_child(irec)
			var key_str := prefs.hint(i,int(adef.key_idx))
			var gdd_mname: String = cat.gdd_moves.get(act_name, {}).get("name", act_name)
			var command:=label(cell, "[%s] %s" % [key_str, gdd_mname], 10, Color("D7D0C2"))
			command.clip_text=true
			command.custom_minimum_size.x=125
			command.size_flags_horizontal=Control.SIZE_EXPAND_FILL
			command.tooltip_text=gdd_mname
			command_labels.append({"label":command,"player":i,"action":int(adef.key_idx),"name":gdd_mname})

		if i == 0:
			var center_status := VBoxContainer.new()
			center_status.alignment = BoxContainer.ALIGNMENT_CENTER
			bottom_hbox.add_child(center_status)
			status_label = label(center_status, "", 12, Color("A3C9A8"))
			status_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			var aux_help := "%s Defesa   %s Dash   %s Breaker" % [
				OS.get_keycode_string(prefs.keys[0][8]),
				OS.get_keycode_string(prefs.keys[0][9]),
				OS.get_keycode_string(prefs.keys[0][10])
			]
			var aux_lbl := label(center_status, aux_help, 11, Color("D7D0C2"))
			aux_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER

	update_hud()

func update_hud() -> void:
	if not is_instance_valid(hud) or not is_instance_valid(timer_label):
		return
	for entry:Dictionary in command_labels:
		if is_instance_valid(entry.label): entry.label.text="[%s] %s" % [prefs.hint(entry.player,entry.action),entry.name]
	for i in 2:
		var f: Dictionary = sim.p1 if i == 0 else sim.p2
		var cat := GaleVisualCatalog.load_for(f.id)
		var pips := "●".repeat(sim.wins[i]) + "○".repeat(2 - sim.wins[i])
		name_labels[i].text = "%s   %s" % [cat.display_name.to_upper(), pips]
		health_bars[i].max_value = f.max_hp
		health_bars[i].value = f.hp
		meter_bars[i].value = f.meter
		combo_labels[i].text = "%d ACERTOS • %d DMG" % [f.combo, f.combo_damage] if f.combo > 1 else "HP %d / %d   •   %s %d%%" % [f.hp, f.max_hp, cat.element_label, f.meter]
	timer_label.text = "∞" if mode == "training" else str(ceili(sim.remaining))
	round_label.text = "— ROUND %d —" % sim.round_number
	banner_label.text = str(ceili(sim.countdown * 3.0 / GaleCombat.COUNTDOWN_FRAMES)) if sim.countdown > 0 else (sim.banner if sim.banner_frames > 0 else "")
	status_label.text = "%s  /  %s%s" % [mode.to_upper(), data.stage(sim.stage_id).name, "  /  ETAPA %d/4" % arcade_index if mode == "arcade" else ""]

func pause_match() -> void:
	if screen != "playing":
		return
	screen = "paused"
	audio.set_music(sim.stage_id, false)
	audio.pause_voice(true)
	# Tall ivory card from concept-art/menu-pausa-v2.png, drawn with the pause atlas.
	modal = instantiate_ui_scene("res://scenes/ui/pause_menu.tscn", 0.45)
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	modal.add_child(center)
	fade_in(modal, 0.18)
	fade_in(center, 0.22, Vector2(0, 18))
	var card := PanelContainer.new()
	card.custom_minimum_size = Vector2(420, 560)
	var card_style := atlas_style("panel_pause", 30)
	card_style.content_margin_left = 46
	card_style.content_margin_right = 46
	card_style.content_margin_top = 54
	card_style.content_margin_bottom = 40
	card.add_theme_stylebox_override("panel", card_style)
	center.add_child(card)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 8)
	card.add_child(column)
	var title := label(column, "P A U S A", 34, Color("27372F"))
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	atlas_rule(column, 260)
	var gap := Control.new()
	gap.custom_minimum_size.y = 18
	column.add_child(gap)
	pause_item(column, "CONTINUAR", resume_match)
	pause_item(column, "REINICIAR PARTIDA", start_match)
	pause_item(column, "OPÇÕES", show_settings)
	atlas_rule(column, 200)
	pause_item(column, "VOLTAR AO MENU", show_menu)
	var filler := Control.new()
	filler.size_flags_vertical = Control.SIZE_EXPAND_FILL
	column.add_child(filler)
	var hint := label(column, "ESC  •  CONTINUAR", 12, Color("62695F"))
	hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	focus_first(column)

## Pieces of concept-art/ui/pausa-atlas-v1.png (regions from pausa-atlas-v1.json).
const PAUSE_ATLAS_PATH := "res://assets/ui/pause/pausa-atlas-v1.png"
const PAUSE_ATLAS := {"button_normal": Rect2(35, 149, 302, 76), "button_focus": Rect2(394, 149, 302, 76), "button_pressed": Rect2(753, 149, 302, 76), "panel_pause": Rect2(46, 389, 281, 298), "separator": Rect2(397, 529, 297, 26)}

func atlas_piece(piece: String) -> AtlasTexture:
	var texture := AtlasTexture.new()
	texture.atlas = load(PAUSE_ATLAS_PATH)
	texture.region = PAUSE_ATLAS[piece]
	return texture

func atlas_style(piece: String, margin: float) -> StyleBoxTexture:
	var style := StyleBoxTexture.new()
	style.texture = atlas_piece(piece)
	style.texture_margin_left = margin
	style.texture_margin_right = margin
	style.texture_margin_top = margin
	style.texture_margin_bottom = margin
	return style

func atlas_rule(parent: Control, width: float) -> void:
	var rule := TextureRect.new()
	rule.texture = atlas_piece("separator")
	rule.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	rule.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	rule.custom_minimum_size = Vector2(width, 22)
	rule.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	parent.add_child(rule)

## Concept style: plain text items; the focused one becomes the jade plate.
func pause_item(parent: Control, text: String, callback: Callable) -> Button:
	var item := button(parent, text, callback)
	item.custom_minimum_size.y = 56
	item.add_theme_font_size_override("font_size", 17)
	item.add_theme_stylebox_override("normal", StyleBoxEmpty.new())
	item.add_theme_stylebox_override("disabled", StyleBoxEmpty.new())
	for state: String in ["hover", "focus"]:
		var plate := atlas_style("button_focus", 18)
		plate.content_margin_left = 16
		plate.content_margin_right = 16
		item.add_theme_stylebox_override(state, plate)
	item.add_theme_stylebox_override("pressed", atlas_style("button_pressed", 18))
	item.add_theme_color_override("font_color", Color("27372F"))
	for state: String in ["font_hover_color", "font_focus_color", "font_pressed_color", "font_hover_pressed_color"]:
		item.add_theme_color_override(state, Color("F4EFE4"))
	return item

func resume_match() -> void:
	if tutorial!=null and tutorial.complete:
		tutorial=null
		if is_instance_valid(tutorial_label): tutorial_label.get_parent().queue_free()
	close_modal()
	screen = "playing"
	audio.set_music(sim.stage_id, true)
	audio.pause_voice(false)

func show_moves() -> void:
	var return_to_pause := (screen == "paused")
	close_modal()
	if is_instance_valid(menu):
		menu.hide()
	modal = overlay(0.82)
	var column := centered(modal, 980)
	var active_id: String = sim.p1.id if screen in ["playing", "paused"] and not sim.p1.is_empty() else fighter1
	var cat := GaleVisualCatalog.load_for(active_id)
	label(column, "LISTA DE GOLPES  /  %s (%s)" % [cat.display_name.to_upper(), cat.element_label], 24, Color("A3C9A8"))

	var switcher := HBoxContainer.new()
	switcher.add_theme_constant_override("separation", 10)
	column.add_child(switcher)
	for fid: String in GaleData.IDS:
		var fc := GaleVisualCatalog.load_for(fid)
		button(switcher, fc.display_name, func() -> void:
			fighter1 = fid
			if not sim.p1.is_empty():
				sim.p1.id = fid
			if return_to_pause:
				screen = "paused"
			show_moves(), fid == active_id)

	var action_map := [
		{"key": "light", "label": "BÁSICO", "bind": 4},
		{"key": "heavy", "label": "FORTE", "bind": 5},
		{"key": "elemental", "label": "ELEMENTAL", "bind": 6},
		{"key": "ultimate", "label": "ULTIMATE", "bind": 7},
	]
	for item: Dictionary in action_map:
		var akey: String = item.key
		var mdata: Dictionary = data.move(active_id, akey, prefs.skills.get(active_id, []))
		var gdd_info: Dictionary = cat.gdd_moves.get(akey, {})
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 14)
		column.add_child(row)

		var icon_path: String = cat.attack_icons.get(akey, "")
		if ResourceLoader.exists(icon_path):
			var irec := TextureRect.new()
			irec.custom_minimum_size = Vector2(54, 54)
			irec.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
			irec.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
			irec.texture = load(icon_path)
			row.add_child(irec)

		var text_col := VBoxContainer.new()
		text_col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(text_col)
		var bind_key := OS.get_keycode_string(prefs.keys[0][int(item.bind)])
		label(text_col, "[%s] %s — %s  (Dano %d • Startup %df • Alcance %.1fm)" % [
			bind_key, item.label, gdd_info.get("name", mdata.name), int(mdata.damage), int(mdata.startupFrames), float(mdata.range)
		], 15, Color("F4CE75"))
		label(text_col, "Movimento: %s   |   Função: %s   |   Resposta: %s" % [
			gdd_info.get("sequence", ""), gdd_info.get("behavior", ""), gdd_info.get("counter", "")
		], 13, Color("D7D0C2"))

	var dp_key := OS.get_keycode_string(prefs.keys[0][3]) + " + " + OS.get_keycode_string(prefs.keys[0][4])
	var sw_key := OS.get_keycode_string(prefs.keys[0][3]) + " + " + OS.get_keycode_string(prefs.keys[0][5])
	label(column, "Variantes contextuais:  [%s] Lançador Baixo  •  [Pulo + %s] Ataque Aéreo  •  [%s] Rasteira" % [
		dp_key, OS.get_keycode_string(prefs.keys[0][4]), sw_key
	], 13, Color("A3C9A8"))

	button(column, "Voltar", func() -> void:
		close_modal()
		if return_to_pause:
			screen = "playing"
			pause_match())

func show_outcome() -> void:
	screen = "outcome"
	audio.set_music(sim.stage_id, false)
	# Versus always celebrates the winner; against the CPU the line follows player 1.
	audio.play_voice("victory" if mode == "versus" or sim.winner == 1 else "lose")
	modal = overlay()
	var column := centered(modal, 560)
	var completed := mode == "arcade" and arcade_index == 4 and sim.winner == 1
	if completed:
		prefs.arcade_run = {}
		persist()
	label(column, "TORRE CONCLUÍDA!" if completed else ("VITÓRIA!" if sim.winner == 1 else "FIM DE COMBATE"), 34, Color("A3C9A8"))
	var c1 := GaleVisualCatalog.load_for(sim.p1.id)
	var c2 := GaleVisualCatalog.load_for(sim.p2.id)
	label(column, "%s  %d × %d  %s" % [c1.display_name, sim.wins[0], sim.wins[1], c2.display_name], 18)
	if completed:
		label(column,"Quatro confrontos vencidos com %s.\nSeu conjunto de habilidades levou você até o fim da torre." % c1.display_name,17)
		label(column,"Obrigado por jogar Gale Breaker.",20,Color("F4CE75"))
	if mode == "arcade" and arcade_index < 4 and sim.winner == 1:
		button(column, "Próximo adversário", func() -> void:
			arcade_index += 1
			show_arcade_intro(), true)
	button(column, "Nova torre" if completed else "Tentar novamente / Continue", func() -> void:
		if completed:
			arcade_index = 1
		begin_fight())
	button(column, "Voltar à seleção", show_menu)
	focus_first(column)

func show_skills() -> void:
	close_modal()
	if is_instance_valid(menu):
		menu.hide()
	modal = overlay()
	var column := centered(modal, 920, false, 540)
	var target := skill_target_fighter if skill_target_fighter in GaleData.IDS else fighter1
	var cat := GaleVisualCatalog.load_for(target)
	var loadouts: Dictionary = prefs.skills if skill_target_player == 0 else prefs.skills2
	label(column, "HABILIDADES P%d  /  " % (skill_target_player+1) + cat.display_name.to_upper(), 26, Color("A3C9A8"))

	var switcher := HBoxContainer.new()
	switcher.add_theme_constant_override("separation", 10)
	column.add_child(switcher)
	for fid: String in GaleData.IDS:
		var fc := GaleVisualCatalog.load_for(fid)
		button(switcher, fc.display_name, func() -> void:
			skill_target_fighter = fid
			if skill_target_player == 0:
				fighter1 = fid
			else:
				fighter2 = fid
			show_skills(), fid == target)

	var spent := 0
	for node: Dictionary in data.fighter(target).skillTree:
		if node.id in loadouts[target]:
			spent += int(node.cost)
	label(column, "Pontos disponíveis: %d / 4" % (4 - spent), 20, Color("F4CE75"))
	for node: Dictionary in data.fighter(target).skillTree:
		var chosen: bool = node.id in loadouts[target]
		var row := HBoxContainer.new()
		column.add_child(row)
		var action := button(row, ("✓ " if chosen else "+ ") + String(node.name), func() -> void:
			loadouts[target] = data.toggle_skill(target, loadouts[target], node.id)
			persist()
			show_skills(), chosen)
		action.custom_minimum_size.x = 270
		var description := label(row, "%d PT • %s — %s" % [node.cost, node.statTag, node.description], 14)
		description.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		description.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		description.tooltip_text = node.description
	label(column, "Escolhas independentes, até quatro pontos. Sem XP, travas de nível ou grind.", 14, Color("D7D0C2"))
	button(column, "Zerar habilidades", func() -> void:
		loadouts[target] = []
		persist()
		show_skills())
	button(column, "Fechar", func() -> void:
		close_modal()
		if in_arcade_select: show_arcade_select()
		elif in_selection: show_menu(true))
	focus_first(column)

## Options screen from concept-art/ui/opcoes-geral-praia-v2.png and opcoes-controles-praia-v2.png.
const OPTIONS_DIR := "res://assets/ui/options/"
const CINZEL_PATH := "res://assets/ui/fonts/Cinzel-Variable.ttf"
const INK := Color("23382D")
const INK_SOFT := Color("4C5A52")
const JADE := Color("1F5C42")
const GOLD := Color("C6A052")
const ACTION_LABELS := ["Pular", "Agachar", "Esquerda", "Direita", "Básico", "Forte", "Elemental", "Ultimate", "Defesa", "Dash", "Breaker"]
const PAD_LABELS := ["A", "D-pad ↓", "D-pad ←", "D-pad →", "X", "Y", "B", "RB", "LB", "R3", "L3"]
var settings_tab := "geral"
# Options opened from the beach menu live on the forest quest board (see arena.focus_board).
var settings_on_board := false
var menu_fade: Tween
var board_ui: GaleBoardOptions
const SETTINGS_DESIGN := Vector2(1145, 680)
# Tighter canvas on the board, so it is scaled down less and reads larger.
const BOARD_DESIGN := Vector2(840, 540)
var in_arcade_select := false
var arcade_outfit_page := 0
var settings_input := "teclado"

func cinzel(weight: int = 700, spacing: int = 0) -> FontVariation:
	var font := FontVariation.new()
	font.base_font = load(CINZEL_PATH)
	font.variation_opentype = {TextServerManager.get_primary_interface().name_to_tag("wght"): weight}
	font.spacing_glyph = spacing
	return font

func ink_label(parent: Node, text: String, size: int, color: Color = INK, font: Font = null) -> Label:
	var node := Label.new()
	node.text = text
	node.add_theme_font_size_override("font_size", size)
	node.add_theme_color_override("font_color", color)
	if font != null:
		node.add_theme_font_override("font", font)
	parent.add_child(node)
	return node

func gold_rule(parent: Node, width: float = 0.0) -> ColorRect:
	var rule := ColorRect.new()
	rule.color = GOLD
	rule.custom_minimum_size = Vector2(width, 1)
	rule.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	if width <= 0.0:
		rule.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	parent.add_child(rule)
	return rule

func plate_button(parent: Node, text: String, active: bool, size: Vector2, font_size: int, callback: Callable) -> Button:
	var plate := button(parent, text, callback)
	plate.custom_minimum_size = size
	plate.add_theme_font_override("font", cinzel(700, 2))
	plate.add_theme_font_size_override("font_size", font_size)
	var face := JADE if active else Color("F3EBD8")
	plate.add_theme_stylebox_override("normal", raised_style(face, false, false))
	plate.add_theme_stylebox_override("hover", raised_style(face.lightened(0.08), false, false))
	plate.add_theme_stylebox_override("focus", raised_style(face.lightened(0.08), false, true))
	plate.add_theme_stylebox_override("pressed", raised_style(face.darkened(0.06), true, false))
	var text_color := Color("F4EFE4") if active else JADE
	plate.add_theme_color_override("font_color", text_color)
	plate.add_theme_color_override("font_hover_color", text_color)
	plate.add_theme_color_override("font_focus_color", Color("F4EFE4"))
	plate.add_theme_color_override("font_pressed_color", Color("F4EFE4"))
	plate.add_theme_constant_override("outline_size", 0)
	return plate

## Raised "3D" plate: a darker bottom edge gives it thickness, a light top rim catches the
## light and a soft shadow lifts it off the parchment; pressed, it sinks onto the surface.
func raised_style(face: Color, pressed: bool, focused: bool) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = face
	style.border_color = face.darkened(0.42)
	style.border_width_left = 2
	style.border_width_right = 2
	style.border_width_top = 3 if pressed else 2
	style.border_width_bottom = 2 if pressed else 6
	style.set_corner_radius_all(8)
	style.shadow_color = Color(0.1, 0.07, 0.03, 0.18 if pressed else 0.32)
	style.shadow_size = 2 if pressed else 5
	style.shadow_offset = Vector2(0, 1 if pressed else 3)
	style.content_margin_left = 12
	style.content_margin_right = 12
	style.content_margin_top = 4 + (3 if pressed else 0)
	style.content_margin_bottom = 4
	if focused:
		style.border_color = GOLD
		style.set_border_width_all(3)
		style.border_width_bottom = 6
	return style

func section_header(parent: Node, text: String) -> void:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 16)
	parent.add_child(row)
	ink_label(row, text, 25, INK, cinzel(700, 1))
	gold_rule(row)

func option_row(parent: Node, text: String) -> HBoxContainer:
	var row := HBoxContainer.new()
	row.custom_minimum_size.y = 44
	row.add_theme_constant_override("separation", 14)
	parent.add_child(row)
	var title := ink_label(row, text, 18)
	title.custom_minimum_size.x = 140 if settings_on_board else 170
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	return row

func jade_slider(row: HBoxContainer, value: float, on_change: Callable) -> void:
	var slider := HSlider.new()
	slider.min_value = 0; slider.max_value = 1; slider.step = 0.05
	slider.value = value
	slider.custom_minimum_size = Vector2(120 if settings_on_board else 190, 30)
	slider.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	var track := StyleBoxFlat.new()
	track.bg_color = Color("BFC9BC")
	track.set_corner_radius_all(4)
	track.content_margin_top = 4; track.content_margin_bottom = 4
	var fill := track.duplicate() as StyleBoxFlat
	fill.bg_color = JADE
	slider.add_theme_stylebox_override("slider", track)
	slider.add_theme_stylebox_override("grabber_area", fill)
	slider.add_theme_stylebox_override("grabber_area_highlight", fill)
	var diamond := load(OPTIONS_DIR + "grabber.png")
	slider.add_theme_icon_override("grabber", diamond)
	slider.add_theme_icon_override("grabber_highlight", diamond)
	row.add_child(slider)
	var percent := ink_label(row, "%d%%" % roundi(value * 100), 18)
	percent.custom_minimum_size.x = 48
	percent.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	slider.value_changed.connect(func(v: float) -> void:
		percent.text = "%d%%" % roundi(v * 100)
		on_change.call(v))

func jade_toggle(row: HBoxContainer, enabled: bool, on_change: Callable) -> void:
	var toggle := CheckButton.new()
	toggle.button_pressed = enabled
	toggle.focus_mode = Control.FOCUS_ALL
	toggle.add_theme_icon_override("checked", load(OPTIONS_DIR + "toggle_on.png"))
	toggle.add_theme_icon_override("unchecked", load(OPTIONS_DIR + "toggle_off.png"))
	for state: String in ["normal", "hover", "pressed", "focus", "hover_pressed"]:
		toggle.add_theme_stylebox_override(state, StyleBoxEmpty.new())
	toggle.toggled.connect(func(value: bool) -> void:
		audio.play("click")
		on_change.call(value))
	row.add_child(toggle)

func key_label(code: int) -> String:
	var names := {KEY_UP: "↑", KEY_DOWN: "↓", KEY_LEFT: "←", KEY_RIGHT: "→", KEY_SPACE: "ESPAÇO", KEY_ENTER: "ENTER", KEY_KP_ENTER: "NUM ENTER", KEY_SHIFT: "SHIFT", KEY_CTRL: "CTRL", KEY_ALT: "ALT"}
	if names.has(code):
		return names[code]
	if code >= KEY_KP_0 and code <= KEY_KP_9:
		return "NUM %d" % (code - KEY_KP_0)
	return OS.get_keycode_string(code).to_upper()

func key_pill(parent: Node, text: String, active: bool, callback: Callable) -> Button:
	var pill := button(parent, text, callback)
	pill.custom_minimum_size = Vector2(96 if settings_on_board else 124, 22)
	pill.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	pill.add_theme_font_size_override("font_size", 15)
	# Keycaps: same raised look, smaller.
	var face := JADE if active else Color("FBF7EE")
	for state: String in ["normal", "disabled"]:
		pill.add_theme_stylebox_override(state, keycap_style(face, false, false))
	pill.add_theme_stylebox_override("hover", keycap_style(face.lightened(0.06), false, false))
	pill.add_theme_stylebox_override("pressed", keycap_style(face.darkened(0.06), true, false))
	pill.add_theme_stylebox_override("focus", keycap_style(face, false, true))
	var text_color := Color("F4EFE4") if active else INK
	for state: String in ["font_color", "font_hover_color", "font_focus_color", "font_pressed_color", "font_disabled_color"]:
		pill.add_theme_color_override(state, text_color)
	pill.add_theme_constant_override("outline_size", 0)
	return pill

func keycap_style(face: Color, pressed: bool, focused: bool) -> StyleBoxFlat:
	var style := raised_style(face, pressed, focused)
	style.border_width_bottom = 1 if pressed else 4
	style.shadow_size = 1 if pressed else 3
	style.shadow_offset = Vector2(0, 1 if pressed else 2)
	style.set_corner_radius_all(6)
	style.content_margin_top = 2 if pressed else 0
	style.content_margin_bottom = 0
	style.content_margin_left = 6
	style.content_margin_right = 6
	if not focused:
		style.border_color = JADE if face.v > 0.5 else face.darkened(0.45)
	return style

func show_settings() -> void:
	if settings_on_board and is_instance_valid(board_ui):
		board_ui.rebuild()
		return
	var was_paused := (screen == "paused")
	var redraw := is_instance_valid(modal) and modal.has_meta("settings")
	# Redrawing must not cancel a key that is waiting to be remapped.
	var pending := listening.duplicate()
	close_modal()
	listening = pending
	if is_instance_valid(menu):
		menu.hide()
	if was_paused:
		screen = "paused"
	# Over the beach (main menu) the shade stays light; over a paused fight it is a bit darker.
	modal = overlay(0.0 if settings_on_board else (0.45 if was_paused else 0.18))
	modal.set_meta("settings", true)
	var frame := TextureRect.new()
	frame.texture = load(OPTIONS_DIR + "frame.png")
	frame.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	frame.stretch_mode = TextureRect.STRETCH_SCALE
	frame.size = SETTINGS_DESIGN
	frame.position = Vector2(67, 20)
	modal.add_child(frame)
	if not redraw:
		fade_in(modal, 0.18)
		fade_in(frame, 0.24, Vector2(0, 16))
	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	for side: String in ["left", "right"]:
		margin.add_theme_constant_override("margin_" + side, 18 if settings_on_board else 62)
	# The brand line sits inside the raised tab, below its gold inner rule.
	margin.add_theme_constant_override("margin_top", 6 if settings_on_board else 31)
	margin.add_theme_constant_override("margin_bottom", 18 if settings_on_board else 42)
	frame.add_child(margin)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 3)
	margin.add_child(column)

	if not settings_on_board:
		var brand := ink_label(column, "GALE BREAKER", 15, INK, cinzel(600, 7))
		brand.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	var title := ink_label(column, "OPÇÕES", 42, INK, cinzel(700, 6))
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	atlas_rule(column, 420)

	var tabs := HBoxContainer.new()
	tabs.add_theme_constant_override("separation", 0)
	column.add_child(tabs)
	gold_rule(tabs)
	for tab: Array in [["geral", "GERAL"], ["controles", "CONTROLES"]]:
		plate_button(tabs, String(tab[1]), settings_tab == tab[0], Vector2(230 if settings_on_board else 290, 40), 20, func() -> void:
			settings_tab = tab[0]
			show_settings())
	gold_rule(tabs)

	var body := VBoxContainer.new()
	body.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_theme_constant_override("separation", 2)
	column.add_child(body)
	if settings_tab == "geral":
		build_general_options(body)
	else:
		build_control_options(body)
	if redraw:
		fade_in(body, 0.14)

	gold_rule(column)
	var footer := HBoxContainer.new()
	footer.add_theme_constant_override("separation", 12)
	column.add_child(footer)
	var esc := key_pill(footer, "ESC", false, close_settings)
	esc.custom_minimum_size = Vector2(56, 30)
	var back := button(footer, "VOLTAR", close_settings)
	back.add_theme_font_override("font", cinzel(700, 2))
	back.add_theme_font_size_override("font_size", 19)
	for state: String in ["normal", "hover", "pressed", "focus"]:
		back.add_theme_stylebox_override(state, StyleBoxEmpty.new())
	for state: String in ["font_color", "font_hover_color", "font_focus_color", "font_pressed_color"]:
		back.add_theme_color_override(state, INK)
	back.add_theme_constant_override("outline_size", 0)
	var middle := CenterContainer.new()
	middle.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	footer.add_child(middle)
	if settings_tab == "geral":
		var italic := FontVariation.new()
		italic.base_font = ThemeDB.fallback_font
		italic.variation_transform = Transform2D(Vector2(1, 0), Vector2(0.2, 1), Vector2.ZERO)
		# The hint doubles as the status line on this tab.
		rebind_label = ink_label(middle, "Ajuste o som e o conforto da partida.", 15, INK_SOFT, italic)
	else:
		gamepad_legend(middle)
	plate_button(footer, "SALVAR E VOLTAR", true, Vector2(280, 44), 18, close_settings)
	focus_first(body)

func build_general_options(body: VBoxContainer) -> void:
	var columns := HBoxContainer.new()
	columns.add_theme_constant_override("separation", 18 if settings_on_board else 28)
	columns.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_child(columns)
	var left := VBoxContainer.new()
	left.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	columns.add_child(left)
	var divider := ColorRect.new()
	divider.color = GOLD
	divider.custom_minimum_size = Vector2(1, 0)
	columns.add_child(divider)
	var right := VBoxContainer.new()
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	columns.add_child(right)
	for side: VBoxContainer in [left, right]:
		var gap := Control.new()
		gap.custom_minimum_size.y = 22
		side.add_child(gap)

	section_header(left, "ÁUDIO")
	jade_slider(option_row(left, "Volume geral"), prefs.volume, func(v: float) -> void: prefs.volume = v; persist())
	jade_slider(option_row(left, "Música"), prefs.music_volume, func(v: float) -> void: prefs.music_volume = v; persist())
	jade_slider(option_row(left, "Efeitos sonoros"), prefs.sfx_volume, func(v: float) -> void: prefs.sfx_volume = v; persist())
	jade_toggle(option_row(left, "Áudio ativo"), not prefs.muted, func(on: bool) -> void: prefs.muted = not on; persist())

	section_header(right, "JOGO E CONFORTO")
	jade_slider(option_row(right, "Intensidade da câmera"), prefs.shake_strength, func(v: float) -> void: prefs.shake_strength = v; persist())
	var difficulty_row := option_row(right, "Dificuldade Arcade")
	var picker := OptionButton.new()
	for name: String in ["Tranquilo", "Normal", "Intenso"]:
		picker.add_item(name)
	picker.selected = prefs.difficulty
	picker.custom_minimum_size = Vector2(150 if settings_on_board else 210, 36)
	var box := StyleBoxFlat.new()
	box.bg_color = Color("FBF7EE")
	box.border_color = JADE
	box.set_border_width_all(2)
	box.set_corner_radius_all(6)
	box.content_margin_left = 14
	for state: String in ["normal", "hover", "pressed", "focus"]:
		picker.add_theme_stylebox_override(state, box)
	for state: String in ["font_color", "font_hover_color", "font_focus_color", "font_pressed_color"]:
		picker.add_theme_color_override(state, INK)
	picker.add_theme_font_size_override("font_size", 17)
	picker.item_selected.connect(func(index: int) -> void: prefs.difficulty = index; persist())
	difficulty_row.add_child(picker)
	jade_toggle(option_row(right, "Flashes de impacto"), prefs.flashes, func(on: bool) -> void: prefs.flashes = on; persist())
	jade_toggle(option_row(right, "Vibração do gamepad"), prefs.vibration, func(on: bool) -> void: prefs.vibration = on; persist())
	jade_toggle(option_row(right, "Mostrar áreas de colisão"), arena.show_boxes, func(on: bool) -> void: arena.show_boxes = on)

func build_control_options(body: VBoxContainer) -> void:
	var sub := HBoxContainer.new()
	sub.add_theme_constant_override("separation", 0)
	body.add_child(sub)
	gold_rule(sub)
	for tab: Array in [["teclado", "TECLADO"], ["gamepad", "GAMEPAD"]]:
		plate_button(sub, String(tab[1]), settings_input == tab[0], Vector2(190, 30), 15, func() -> void:
			settings_input = tab[0]
			show_settings())
	gold_rule(sub)
	var hint_row := HBoxContainer.new()
	body.add_child(hint_row)
	var left_pad := Control.new()
	left_pad.custom_minimum_size.x = 60 if settings_on_board else 150
	hint_row.add_child(left_pad)
	rebind_label = ink_label(hint_row, "Selecione uma tecla para remapear. Esc cancela." if settings_input == "teclado" else "Mapa do controle. O remapeamento do gamepad chega em uma próxima versão.", 15)
	rebind_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	rebind_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var restore_slot := Control.new()
	restore_slot.custom_minimum_size.x = 140 if settings_on_board else 150
	hint_row.add_child(restore_slot)
	if settings_input == "teclado":
		var restore := button(restore_slot, "RESTAURAR PADRÕES", restore_default_keys)
		restore.add_theme_font_size_override("font_size", 13)
		for state: String in ["normal", "hover", "pressed", "focus"]:
			restore.add_theme_stylebox_override(state, StyleBoxEmpty.new())
		for state: String in ["font_color", "font_hover_color", "font_focus_color"]:
			restore.add_theme_color_override(state, JADE)
		restore.add_theme_constant_override("outline_size", 0)
	var columns := HBoxContainer.new()
	columns.add_theme_constant_override("separation", 26 if settings_on_board else 60)
	body.add_child(columns)
	for player in 2:
		var list := VBoxContainer.new()
		list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		list.add_theme_constant_override("separation", 0)
		columns.add_child(list)
		var header := HBoxContainer.new()
		header.add_theme_constant_override("separation", 14)
		list.add_child(header)
		ink_label(header, "JOGADOR %d" % (player + 1), 21, INK, cinzel(700, 3))
		gold_rule(header)
		for action in GalePreferences.ACTIONS.size():
			var row := PanelContainer.new()
			var stripe := StyleBoxFlat.new()
			stripe.bg_color = Color(0.55, 0.45, 0.30, 0.07 if action % 2 == 1 else 0.0)
			stripe.content_margin_left = 14
			stripe.content_margin_right = 14
			row.add_theme_stylebox_override("panel", stripe)
			list.add_child(row)
			var line := HBoxContainer.new()
			line.custom_minimum_size.y = 21 if settings_on_board else 24
			row.add_child(line)
			var name := ink_label(line, ACTION_LABELS[action], 16)
			name.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			if settings_input == "teclado":
				var active: bool = listening == [player, action]
				var pill := key_pill(line, key_label(prefs.keys[player][action]), active, func() -> void:
					listening = [player, action]
					show_settings()
					rebind_label.text = "Pressione a nova tecla para %s do Jogador %d. Esc cancela." % [ACTION_LABELS[action], player + 1])
				if active:
					var pulse := pill.create_tween().set_loops()
					pulse.tween_property(pill, "modulate", Color(1.25, 1.25, 1.25), 0.45).set_trans(Tween.TRANS_SINE)
					pulse.tween_property(pill, "modulate", Color.WHITE, 0.45).set_trans(Tween.TRANS_SINE)
			else:
				var pill := key_pill(line, PAD_LABELS[action], false, func() -> void: pass)
				pill.disabled = true

func gamepad_legend(parent: Node) -> void:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 6)
	parent.add_child(row)
	for entry: Array in [["A", "Confirmar", Color("2E7D4F")], ["X", "Áudio", Color("2A5BA8")], ["Y", "Padrões", Color("D6A21E")], ["B", "Voltar", Color("B3322B")], ["LB/RB", "Abas", Color("4C5A52")]]:
		var badge := PanelContainer.new()
		var round := StyleBoxFlat.new()
		round.bg_color = entry[2]
		round.set_corner_radius_all(11)
		round.content_margin_left = 7; round.content_margin_right = 7
		badge.add_theme_stylebox_override("panel", round)
		row.add_child(badge)
		ink_label(badge, String(entry[0]), 12, Color.WHITE)
		ink_label(row, String(entry[1]) + "   ", 13, INK)

func restore_default_keys() -> void:
	prefs.restore_default_keys()
	listening.clear()
	show_settings()
	rebind_label.text = "Teclas padrão restauradas."

func open_arcade_select() -> void:
	mode = "arcade"
	in_arcade_select = true
	if is_instance_valid(menu):
		menu.hide()
	arena.show_select_fighter(data, fighter1, palette1)
	show_arcade_select()

func leave_arcade_select() -> void:
	in_arcade_select = false
	close_modal()
	arena.hide_select_fighter()
	show_menu()

func start_arcade_from_select() -> void:
	in_arcade_select = false
	arcade_index = 1
	close_modal()
	begin_fight()

func choose_arcade_fighter(id: String) -> void:
	fighter1 = id
	palette1 = 0
	arcade_outfit_page = 0
	arena.show_select_fighter(data, fighter1, palette1)
	show_arcade_select(true)

func choose_arcade_outfit(index: int) -> void:
	palette1 = index
	arena.show_select_fighter(data, fighter1, palette1)
	show_arcade_select(true)

func turn_select_fighter(amount: float) -> void:
	arena.select_turn += amount

func outfit_preview(parent: Node, id: String, palette: int) -> SubViewportContainer:
	"""Live full-body render of a fighter in one palette, for the outfit cards."""
	var holder := SubViewportContainer.new()
	# In the tree before building: the fighter view reads global transforms.
	parent.add_child(holder)
	holder.stretch = true
	holder.custom_minimum_size = Vector2(118, 132)
	holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var viewport := SubViewport.new()
	viewport.own_world_3d = true
	viewport.transparent_bg = true
	viewport.size = Vector2i(118, 132)
	holder.add_child(viewport)
	var camera := Camera3D.new()
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.size = 2.25
	camera.position = Vector3(0.9, 1.05, 4.0)
	camera.basis = Basis.looking_at(Vector3(0, 0.98, 0) - camera.position)
	viewport.add_child(camera)
	var view := GaleFighterView.new()
	viewport.add_child(view)
	view.build(data, id, palette)
	view.rotation.y = PI - 0.3
	view.aura.visible = false
	view.contact_shadow.visible = false
	view.play_clip("idle", 0.0)
	return holder

func select_card(parent: Node, size: Vector2, selected: bool, callback: Callable) -> Button:
	var card := Button.new()
	card.custom_minimum_size = size
	card.focus_mode = Control.FOCUS_ALL
	var box := StyleBoxFlat.new()
	box.bg_color = Color("FBF6EA") if selected else Color("F1E9D8")
	box.border_color = JADE if selected else Color("D9C9A6")
	box.set_border_width_all(4 if selected else 2)
	box.set_corner_radius_all(8)
	var focus := box.duplicate() as StyleBoxFlat
	focus.border_color = GOLD
	for state: String in ["normal", "hover", "pressed"]:
		card.add_theme_stylebox_override(state, box)
	card.add_theme_stylebox_override("focus", focus)
	card.pressed.connect(func() -> void:
		audio.play("click")
		callback.call())
	card.mouse_entered.connect(func() -> void: audio.play("hover"))
	parent.add_child(card)
	if selected:
		var seal := TextureRect.new()
		seal.texture = load("res://assets/ui/board/selo-confirmar.png")
		seal.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		seal.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT
		seal.size = Vector2(34, 34)
		seal.position = Vector2(size.x - 30, -8)
		seal.mouse_filter = Control.MOUSE_FILTER_IGNORE
		card.add_child(seal)
	return card

func section_plate(parent: Node, text: String) -> void:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)
	parent.add_child(row)
	var plate := PanelContainer.new()
	var style := atlas_style("button_focus", 14)
	style.content_margin_left = 26
	style.content_margin_right = 26
	plate.add_theme_stylebox_override("panel", style)
	row.add_child(plate)
	var title := ink_label(plate, text, 16, Color("F4EFE4"), cinzel(700, 3))
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	gold_rule(row)

func show_arcade_select(redraw: bool = false) -> void:
	close_modal()
	if is_instance_valid(menu):
		menu.hide()
	modal = overlay(0.0)
	modal.set_meta("arcade_select", true)
	var cat := GaleVisualCatalog.load_for(fighter1)

	# Left: the fighter's name and title over the beach, and rotate arrows.
	var name_box := VBoxContainer.new()
	name_box.position = Vector2(56, 452)
	name_box.add_theme_constant_override("separation", 2)
	modal.add_child(name_box)
	var slanted := FontVariation.new()
	slanted.base_font = cinzel(700, 1)
	slanted.variation_transform = Transform2D(Vector2(1, 0), Vector2(-0.22, 1), Vector2.ZERO)
	var big := ink_label(name_box, cat.display_name.to_upper(), 58, Color("C6A052"), slanted)
	big.add_theme_color_override("font_outline_color", Color(0.12, 0.09, 0.05, 0.85))
	big.add_theme_constant_override("outline_size", 6)
	var rule := ColorRect.new()
	rule.color = Color("C6A052")
	rule.custom_minimum_size = Vector2(260, 2)
	name_box.add_child(rule)
	var italic := FontVariation.new()
	italic.base_font = ThemeDB.fallback_font
	italic.variation_transform = Transform2D(Vector2(1, 0), Vector2(-0.2, 1), Vector2.ZERO)
	var subtitle := ink_label(name_box, cat.subtitle, 20, Color("FFF8EA"), italic)
	subtitle.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.55))
	subtitle.add_theme_constant_override("outline_size", 5)
	var turns := HBoxContainer.new()
	turns.position = Vector2(150, 610)
	turns.add_theme_constant_override("separation", 170)
	modal.add_child(turns)
	for pair: Array in [["↶", -0.6], ["↷", 0.6]]:
		var arrow := button(turns, String(pair[0]), turn_select_fighter.bind(float(pair[1])))
		arrow.add_theme_font_size_override("font_size", 30)
		for state: String in ["normal", "hover", "pressed", "focus"]:
			arrow.add_theme_stylebox_override(state, StyleBoxEmpty.new())
		arrow.add_theme_color_override("font_color", Color("1F3B2E"))
		arrow.add_theme_constant_override("outline_size", 0)

	# Right: the selection card.
	var card := TextureRect.new()
	card.texture = load(OPTIONS_DIR + "frame.png")
	card.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	card.stretch_mode = TextureRect.STRETCH_SCALE
	card.size = Vector2(650, 618)
	card.position = Vector2(596, 12)
	modal.add_child(card)
	if not redraw:
		fade_in(card, 0.28, Vector2(24, 0))
		fade_in(name_box, 0.35, Vector2(-20, 0))
	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	for side: String in ["left", "right"]:
		margin.add_theme_constant_override("margin_" + side, 40)
	margin.add_theme_constant_override("margin_top", 22)
	margin.add_theme_constant_override("margin_bottom", 26)
	card.add_child(margin)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 6)
	margin.add_child(column)
	var brand := ink_label(column, "GALE BREAKER", 12, INK, cinzel(600, 6))
	brand.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	var title := ink_label(column, "ARCADE", 40, INK, cinzel(700, 6))
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	var sub := ink_label(column, "ESCOLHA SEU LUTADOR", 14, INK, cinzel(700, 5))
	sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER

	section_plate(column, "PERSONAGEM")
	var roster := HBoxContainer.new()
	roster.alignment = BoxContainer.ALIGNMENT_CENTER
	roster.add_theme_constant_override("separation", 10)
	column.add_child(roster)
	var focus_target: Control = null
	for id: String in GaleData.IDS:
		var fighter_card := select_card(roster, Vector2(124, 138), id == fighter1, choose_arcade_fighter.bind(id))
		var inner := VBoxContainer.new()
		inner.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		inner.add_theme_constant_override("separation", 0)
		inner.mouse_filter = Control.MOUSE_FILTER_IGNORE
		fighter_card.add_child(inner)
		var portrait := TextureRect.new()
		portrait.texture = load("res://assets/ui/portraits/%s.png" % id)
		portrait.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		portrait.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
		portrait.custom_minimum_size = Vector2(116, 108)
		portrait.size_flags_vertical = Control.SIZE_EXPAND_FILL
		portrait.mouse_filter = Control.MOUSE_FILTER_IGNORE
		inner.add_child(portrait)
		var label_name := ink_label(inner, GaleVisualCatalog.load_for(id).display_name.to_upper(), 14, INK, cinzel(700, 2))
		label_name.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		if id == fighter1:
			focus_target = fighter_card

	section_plate(column, "ROUPA")
	var outfits := HBoxContainer.new()
	outfits.alignment = BoxContainer.ALIGNMENT_CENTER
	outfits.add_theme_constant_override("separation", 10)
	column.add_child(outfits)
	var count := cat.palettes.size()
	var prev := plate_button(outfits, "‹", true, Vector2(40, 52), 24, func() -> void:
		arcade_outfit_page = posmod(arcade_outfit_page - 1, count)
		show_arcade_select(true))
	prev.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	for offset in 3:
		var index := posmod(arcade_outfit_page + offset, count)
		var outfit_card := select_card(outfits, Vector2(128, 158), index == palette1, choose_arcade_outfit.bind(index))
		var inner := VBoxContainer.new()
		inner.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		inner.mouse_filter = Control.MOUSE_FILTER_IGNORE
		outfit_card.add_child(inner)
		outfit_preview(inner, fighter1, index)
		var short_name := String(cat.palettes[index].name).split(" ")[0]
		var outfit_label := ink_label(inner, short_name, 14, INK)
		outfit_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	var next := plate_button(outfits, "›", true, Vector2(40, 52), 24, func() -> void:
		arcade_outfit_page = posmod(arcade_outfit_page + 1, count)
		show_arcade_select(true))
	next.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	var caption := HBoxContainer.new()
	caption.add_theme_constant_override("separation", 12)
	column.add_child(caption)
	gold_rule(caption)
	var italic_ink := FontVariation.new()
	italic_ink.base_font = ThemeDB.fallback_font
	italic_ink.variation_transform = Transform2D(Vector2(1, 0), Vector2(-0.2, 1), Vector2.ZERO)
	ink_label(caption, String(cat.palettes[palette1].name), 17, INK, italic_ink)
	gold_rule(caption)
	var counter := ink_label(column, "%02d / %02d" % [palette1 + 1, count], 13, INK_SOFT)
	counter.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER

	# Footer: back on the left, skills and start on the right.
	var footer := HBoxContainer.new()
	footer.position = Vector2(56, 650)
	footer.size = Vector2(1170, 52)
	footer.add_theme_constant_override("separation", 12)
	modal.add_child(footer)
	var esc := key_pill(footer, "ESC", false, leave_arcade_select)
	esc.custom_minimum_size = Vector2(56, 30)
	var back := button(footer, "VOLTAR", leave_arcade_select)
	back.add_theme_font_override("font", cinzel(700, 2))
	back.add_theme_font_size_override("font_size", 19)
	for state: String in ["normal", "hover", "pressed", "focus"]:
		back.add_theme_stylebox_override(state, StyleBoxEmpty.new())
	for state: String in ["font_color", "font_hover_color", "font_focus_color", "font_pressed_color"]:
		back.add_theme_color_override(state, Color("FFF8EA"))
	back.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.55))
	back.add_theme_constant_override("outline_size", 5)
	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	footer.add_child(spacer)
	plate_button(footer, "HABILIDADES", false, Vector2(210, 46), 16, func() -> void:
		skill_target_player = 0
		skill_target_fighter = fighter1
		show_skills())
	var start := plate_button(footer, "INICIAR ARCADE  ↵", true, Vector2(320, 50), 20, start_arcade_from_select)
	if not redraw:
		fade_in(footer, 0.3)
	call_deferred("focus_control", start if focus_target == null else focus_target)

func close_settings() -> void:
	listening.clear()
	persist()
	close_modal()
	if screen == "paused":
		resume_match()
	elif settings_on_board:
		# Fly back to the beach; the menu list returns once the camera arrives.
		settings_on_board = false
		if is_instance_valid(board_ui):
			board_ui.interactive = false
			board_ui.hover = -1
			board_ui.refresh_focus()
		if is_instance_valid(menu):
			menu.hide()
		arena.focus_board(false)
		await arena.board_closed
		if menu_fade != null and menu_fade.is_valid():
			menu_fade.kill()
		if is_instance_valid(menu) and screen == "menu":
			menu.show()
			fade_in(menu, 0.25)

func open_board_settings() -> void:
	if is_instance_valid(menu):
		menu_fade = menu.create_tween()
		menu_fade.tween_property(menu, "modulate:a", 0.0, 0.2)
		menu_fade.tween_callback(menu.hide)
	settings_on_board = true
	if not is_instance_valid(board_ui):
		board_ui = GaleBoardOptions.new()
		arena.scenery.add_child(board_ui)
		board_ui.setup(self, arena.board_panel)
	if not is_instance_valid(rebind_label):
		rebind_label = Label.new()
		rebind_label.visible = false
		ui.add_child(rebind_label)
	rebind_label.text = ""
	board_ui.rebuild()
	arena.focus_board(true)
	await arena.board_ready
	if screen == "menu" and settings_on_board:
		board_ui.interactive = true
		board_ui.refresh_focus()

func persist() -> void:
	var error := prefs.save_to_disk()
	audio.apply_settings(prefs)
	apply_presentation_options()
	if error != OK:
		push_warning("Não foi possível salvar preferências: %s" % error_string(error))

func _input(event: InputEvent) -> void:
	if settings_on_board and is_instance_valid(board_ui) and board_ui.interactive and listening.is_empty():
		if event.is_action_pressed("ui_cancel"):
			get_viewport().set_input_as_handled()
			close_settings()
			return
		if event is InputEventJoypadButton and event.pressed and event.button_index in [JOY_BUTTON_LEFT_SHOULDER, JOY_BUTTON_RIGHT_SHOULDER, JOY_BUTTON_X, JOY_BUTTON_Y]:
			get_viewport().set_input_as_handled()
			match event.button_index:
				JOY_BUTTON_LEFT_SHOULDER, JOY_BUTTON_RIGHT_SHOULDER:
					board_ui.switch_tab("controles" if settings_tab == "geral" else "geral")
				JOY_BUTTON_X:
					prefs.muted = not prefs.muted
					persist()
					board_ui.rebuild()
				JOY_BUTTON_Y:
					restore_default_keys()
			return
		if board_ui.handle_input(event):
			get_viewport().set_input_as_handled()
			return
	if event is InputEventJoypadButton and event.pressed:
		if event.button_index == JOY_BUTTON_START:
			if is_instance_valid(modal) and screen in ["menu","selection"]:close_modal()
			elif screen == "playing": pause_match()
			elif screen == "paused": resume_match()
			elif screen == "menu": show_menu(true)
			elif screen == "selection": begin_fight()
			get_viewport().set_input_as_handled()
			return
		elif event.button_index == JOY_BUTTON_BACK and mode == "training" and screen == "playing":
			show_training_tools()
			return
		elif is_instance_valid(modal) and modal.has_meta("settings") and event.button_index in [JOY_BUTTON_LEFT_SHOULDER, JOY_BUTTON_RIGHT_SHOULDER, JOY_BUTTON_X, JOY_BUTTON_Y]:
			# Options screen pad shortcuts shown in its legend.
			get_viewport().set_input_as_handled()
			match event.button_index:
				JOY_BUTTON_LEFT_SHOULDER, JOY_BUTTON_RIGHT_SHOULDER:
					settings_tab = "controles" if settings_tab == "geral" else "geral"
					show_settings()
				JOY_BUTTON_X:
					prefs.muted = not prefs.muted
					persist()
					show_settings()
				JOY_BUTTON_Y:
					restore_default_keys()
			return
		elif event.button_index==JOY_BUTTON_B and screen!="playing":
			if screen=="paused":resume_match()
			elif screen in ["intro","outcome","selection"]:show_menu()
			elif is_instance_valid(modal) and modal.has_meta("settings"):close_settings()
			elif is_instance_valid(modal) and modal.has_meta("arcade_select"):leave_arcade_select()
			elif is_instance_valid(modal):close_modal()
			get_viewport().set_input_as_handled()
			return
	if not event is InputEventKey or not event.pressed or event.echo:
		return
	var key_event := event as InputEventKey
	if not listening.is_empty():
		get_viewport().set_input_as_handled()
		if key_event.keycode == KEY_ESCAPE:
			listening.clear()
			show_settings()
			rebind_label.text = "Remapeamento cancelado."
			return
		var error := prefs.remap(listening[0], listening[1], key_event.physical_keycode)
		if error.is_empty():
			listening.clear()
			show_settings()
		else:
			rebind_label.text = error
		return
	if is_instance_valid(modal):
		if key_event.keycode == KEY_ESCAPE:
			get_viewport().set_input_as_handled()
			if screen == "paused":
				resume_match()
			elif screen in ["intro","outcome"]:
				show_menu()
			elif modal.has_meta("settings"):
				close_settings()
			elif modal.has_meta("arcade_select"):
				leave_arcade_select()
			else:
				close_modal()
		return
	match key_event.keycode:
		KEY_F2:
			if mode == "training" and screen == "playing": show_training_tools()
		KEY_ESCAPE, KEY_P:
			if screen == "playing":
				pause_match()
				get_viewport().set_input_as_handled()
			elif screen=="selection":show_menu()
		KEY_R:
			if screen == "playing":
				start_match()
				get_viewport().set_input_as_handled()
		KEY_M:
			prefs.muted = not prefs.muted
			persist()
			get_viewport().set_input_as_handled()

func _physics_process(_delta: float) -> void:
	if screen != "playing" or is_instance_valid(modal):
		return
	var input1 := GalePreferences.input_for(1)
	var input2 := GalePreferences.input_for(2) if mode == "versus" else (training_input() if mode == "training" else sim.ai_input())
	if sim.countdown == GaleCombat.COUNTDOWN_FRAMES:
		audio.play_voice("countdown")
	var countdown_before := sim.countdown
	sim.step(input1, input2)
	if countdown_before > 0 and sim.countdown == 0:
		audio.play("fight_start")
	for player in 2:
		var attacker: Dictionary = sim.p1 if player == 0 else sim.p2
		if int(attacker.attack_serial) != attack_serials[player]:
			attack_serials[player] = int(attacker.attack_serial)
			if String(attacker.move.get("type", "")) == "elemental":
				audio.play("", attacker.id, "elemental")
		var strike := strike_sound(attacker.move)
		if attacker.action == "startup" and int(attacker.frames) <= STRIKE_SOUND_LEAD_FRAMES 				and early_sound_serials[player] != int(attacker.attack_serial) and audio.has_sample(String(attacker.id) + "_" + strike):
			early_sound_serials[player] = int(attacker.attack_serial)
			audio.play("", attacker.id, strike)
	for event: Dictionary in sim.events:
		arena.impact(event)
		var played_early := false
		if event.kind in ["hit", "heavy"] and not bool(event.get("entity", true)):
			var strike := strike_sound({"type": event.get("move_type", ""), "chain_step": event.get("chain_step", 1)})
			# The recorded strike already played just before contact.
			played_early = audio.has_sample(String(event.get("fighter", "")) + "_" + strike)
		if not played_early:
			audio.play(event.kind,event.get("fighter",""))
		if prefs.vibration and event.kind in ["hit","heavy","ko"]:
			var devices := Input.get_connected_joypads()
			var player := 0 if absf(float(sim.p1.x)-event.position.x)<absf(float(sim.p2.x)-event.position.x) else 1
			if devices.size()>player: Input.start_joy_vibration(devices[player],0.3,0.5,0.1)
	if tutorial != null and tutorial.update(sim,input1):
		if tutorial.complete:
			show_tutorial_complete()
		elif is_instance_valid(tutorial_label):
			update_tutorial_label()
	ticks += 1
	if ticks % 6 == 0:
		update_hud()
	if sim.winner != 0:
		update_hud()
		show_outcome()

## Recorded-sound key for a melee strike ("light_1".."light_3", "heavy"), or "".
func strike_sound(move: Dictionary) -> String:
	match String(move.get("type", "")):
		"light":
			return "light_%d" % clampi(int(move.get("chain_step", 1)), 1, 3)
		"heavy":
			return "heavy"
	return ""

func _process(delta: float) -> void:
	if is_instance_valid(arena) and not sim.p1.is_empty():
		arena.render(sim, delta)
		# Footsteps follow the walk animation, two per cycle.
		for view: GaleFighterView in arena.fighters:
			if view.footfall_pending:
				view.footfall_pending = false
				if screen == "playing":
					audio.play("step", view.fighter_id)

func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_FOCUS_OUT and screen == "playing":
		pause_match()

func focus_first(parent: Node) -> void:
	var controls := parent.find_children("*","BaseButton",true,false)
	if not controls.is_empty(): call_deferred("focus_control",controls[0])

func focus_control(control: Control) -> void:
	if is_instance_valid(control) and control.is_inside_tree() and control.is_visible_in_tree():
		hover_quiet_until = Time.get_ticks_msec() + 200
		control.grab_focus()

func apply_presentation_options() -> void:
	if is_instance_valid(arena):
		arena.shake_strength = prefs.shake_strength
		for view in arena.fighters:
			view.flashes_enabled = prefs.flashes
			view.shake_strength = prefs.shake_strength

func begin_fight() -> void:
	tutorial = null
	audio.play("match_start")
	if mode == "arcade": show_arcade_intro()
	else: start_match()

func show_arcade_intro() -> void:
	start_match()
	screen = "intro"
	modal = overlay(0.6)
	var column := centered(modal,760)
	label(column,"ARCADE  /  CONFRONTO %d DE 4" % arcade_index,20,Color("A3C9A8"))
	var row := HBoxContainer.new()
	column.add_child(row)
	make_portrait_box(row,sim.p1.id,140)
	var text := VBoxContainer.new()
	text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(text)
	label(text,"%s  ×  %s" % [GaleVisualCatalog.load_for(sim.p1.id).display_name,GaleVisualCatalog.load_for(sim.p2.id).display_name],26)
	label(text,String(data.stage(sim.stage_id).name),16,Color("F4CE75"))
	label(text,"CHEFE · OVERCHARGE" if sim.p2.boss else "Melhor de três · 99 segundos",16)
	make_portrait_box(row,sim.p2.id,140)
	label(column,"Dificuldade: %s. Sua escolha de habilidades permanece durante a torre." % ["Tranquilo","Normal","Intenso"][prefs.difficulty],14)
	button(column,"LUTAR",func() -> void: close_modal();screen="playing",true)
	button(column,"Voltar ao menu",show_menu)
	focus_first(column)

func resume_arcade() -> void:
	if prefs.arcade_run.is_empty(): return
	mode = "arcade"
	fighter1 = prefs.arcade_run.fighter
	arcade_index = clampi(int(prefs.arcade_run.index),1,4)
	palette1 = clampi(int(prefs.arcade_run.get("palette",0)),0,3)
	var saved_skills:Variant=prefs.arcade_run.get("skills",[])
	prefs.skills[fighter1] = data.normalize_skills(fighter1,saved_skills if saved_skills is Array else [])
	show_arcade_intro()

func start_tutorial() -> void:
	mode = "training"
	fighter2 = "ignis" if fighter1 != "ignis" else "kaze"
	start_match()
	tutorial = GaleTutorial.new()
	tutorial.prepare(sim)
	var panel := PanelContainer.new()
	panel.position = Vector2(240,142)
	panel.custom_minimum_size = Vector2(800,70)
	hud.add_child(panel)
	tutorial_label = label(panel,"",17,Color("F8F5EE"))
	tutorial_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	update_tutorial_label()
	update_hud()

func update_tutorial_label() -> void:
	tutorial_label.text = "TUTORIAL %d / %d — %s\n%s" % [tutorial.step+1,GaleTutorial.STEPS.size(),GaleTutorial.STEPS[tutorial.step][0],GaleTutorial.STEPS[tutorial.step][1]]

func show_tutorial_complete() -> void:
	screen = "paused"
	modal = overlay()
	var column := centered(modal,620)
	label(column,"TUTORIAL CONCLUÍDO",30,Color("A3C9A8"))
	label(column,"Você praticou movimento, defesa, combo e os quatro tipos de ataque.\nUse F2 / Back para configurar o adversário e continuar treinando.",17)
	button(column,"Treinar livremente",func() -> void:
		tutorial = null
		if is_instance_valid(tutorial_label): tutorial_label.get_parent().queue_free()
		resume_match(),true)
	button(column,"Voltar ao menu",show_menu)
	focus_first(column)

func training_input() -> Dictionary:
	if tutorial != null: return tutorial.dummy_input(sim)
	var input := GaleCombat.idle_input()
	match training_behavior:
		1: input.guard = true
		2: input.guard = true; input.crouch = true
		3: input.jump = sim.p2.grounded
		4: return sim.ai_input(true)
	return input

func show_training_tools() -> void:
	if mode != "training": return
	if screen == "playing": pause_match()
	close_modal()
	screen = "paused"
	modal = overlay()
	var column := centered(modal,700)
	label(column,"LABORATÓRIO DE TREINO",28,Color("A3C9A8"))
	option(column,"Adversário",["Passivo","Defende alto","Defende baixo","Pula","IA"],training_behavior,func(index:int) -> void: training_behavior=index)
	button(column,"Alternar hitboxes",func() -> void: arena.show_boxes=not arena.show_boxes)
	button(column,"Avançar um frame",func() -> void:
		sim.step(GaleCombat.idle_input(),training_input())
		arena.render(sim,GaleCombat.DT)
		update_hud())
	button(column,"Repor posição, vida e energia",func() -> void:
		sim.next_round()
		sim.countdown=0;sim.p1.meter=100;sim.p2.meter=100
		arena.build(data,sim)
		if tutorial != null: tutorial.prepare(sim)
		apply_presentation_options();update_hud())
	button(column,"Retomar treino",resume_match,true)
	focus_first(column)
