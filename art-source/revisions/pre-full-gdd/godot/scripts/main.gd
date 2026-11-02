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

func _ready() -> void:
	get_window().min_size = Vector2i(1000, 650)
	prefs.load_from_disk(data)
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
	parent.add_child(node)
	return node

func button(parent: Node, text: String, callback: Callable, primary_style: bool = false) -> Button:
	var node := Button.new()
	node.text = text
	node.focus_mode = Control.FOCUS_NONE
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
	parent.add_child(node)
	return node

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

func centered(parent: Control, width: float = 1020, ivory_card: bool = false) -> VBoxContainer:
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

func show_menu() -> void:
	close_modal()
	clear_menu()
	if is_instance_valid(hud):
		ui.remove_child(hud)
		hud.queue_free()
	screen = "menu"
	audio.set_music(stage, false)
	# Sanctuary background without characters per GDD v0.9 page 11 & IMPLEMENTATION_PLAN Section 6
	arena.set_menu_mode(true, true)

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
		var btn := button(nav_col, prefix + String(mode_titles[m_key]), func() -> void:
			mode = m_key
			show_menu(), is_active)
		btn.alignment = HORIZONTAL_ALIGNMENT_LEFT

	var sk_btn := button(nav_col, "      HABILIDADES", func() -> void:
		skill_target_fighter = fighter1
		show_skills())
	sk_btn.alignment = HORIZONTAL_ALIGNMENT_LEFT

	var mv_btn := button(nav_col, "      LISTA DE GOLPES", show_moves)
	mv_btn.alignment = HORIZONTAL_ALIGNMENT_LEFT

	var op_btn := button(nav_col, "      OPÇÕES", show_settings)
	op_btn.alignment = HORIZONTAL_ALIGNMENT_LEFT

	var start_btn := button(nav_col, "—   INICIAR COMBATE", func() -> void:
		arcade_index = 1
		start_match(), true)
	start_btn.alignment = HORIZONTAL_ALIGNMENT_LEFT

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
		show_menu())

	var p1_pal_names: Array = []
	for p: Dictionary in cat1.palettes:
		p1_pal_names.append(p.name)
	option(setup, "Paleta P1", p1_pal_names, palette1, func(index: int) -> void:
		palette1 = index
		preview())

	option(setup, "Adversário (Treino / Versus)", names, GaleData.IDS.find(fighter2), func(index: int) -> void:
		fighter2 = GaleData.IDS[index]
		preview()
		show_menu())

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
		skill_target_fighter = fighter1
		show_skills())
	button(quick_row, "Habilidades P2 (%s)" % cat2.display_name, func() -> void:
		skill_target_fighter = fighter2
		show_skills())
	button(quick_row, "Inspecionar Modelos 3D", preview)

	# Bottom Minimalist Prompt Bar (matching menu-principal-v3.png)
	var footer_row := HBoxContainer.new()
	main_vbox.add_child(footer_row)
	label(footer_row, "↑ ↓  NAVEGAR        ENTER  CONFIRMAR        P / ESC  PAUSA        R  REINICIAR        M  ÁUDIO", 13, Color("D7D0C2"))

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
	var opponent_skills: Array = prefs.skills.get(fighter2, []) if mode == "versus" else []
	var opponent_palette := palette2
	if mode == "arcade":
		var spec := data.arcade(fighter1, arcade_index)
		opponent = spec.opponentId
		arena_id = spec.stageId
		opponent_skills = spec.unlockedSkills
		opponent_palette = int(spec.opponentPalette)
	sim.start(fighter1, opponent, arena_id, mode, prefs.skills[fighter1], opponent_skills, arcade_index, palette1, opponent_palette)
	arena.build(data, sim)
	arena.set_menu_mode(false, false)
	screen = "playing"
	build_hud()
	audio.set_music(sim.stage_id, true)

func build_hud() -> void:
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
			button(center, "PAUSA", pause_match)
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
		var icons_row := HBoxContainer.new()
		icons_row.add_theme_constant_override("separation", 10)
		side_col.add_child(icons_row)
		var action_defs := [
			{"act": "light", "key_idx": 4},
			{"act": "heavy", "key_idx": 5},
			{"act": "elemental", "key_idx": 6},
			{"act": "ultimate", "key_idx": 7},
		]
		for adef: Dictionary in action_defs:
			var act_name: String = adef.act
			var icon_path: String = cat.attack_icons.get(act_name, "")
			if ResourceLoader.exists(icon_path):
				var irec := TextureRect.new()
				irec.custom_minimum_size = Vector2(30, 30)
				irec.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
				irec.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
				irec.texture = load(icon_path)
				icons_row.add_child(irec)
			var key_str := OS.get_keycode_string(prefs.keys[i][int(adef.key_idx)])
			var gdd_mname: String = cat.gdd_moves.get(act_name, {}).get("name", act_name)
			label(icons_row, "[%s] %s" % [key_str, gdd_mname], 11, Color("D7D0C2"))

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
	banner_label.text = str(ceili(sim.countdown / 60.0)) if sim.countdown > 0 else (sim.banner if sim.banner_frames > 0 else "")
	status_label.text = "%s  /  %s%s" % [mode.to_upper(), data.stage(sim.stage_id).name, "  /  ETAPA %d/4" % arcade_index if mode == "arcade" else ""]

func pause_match() -> void:
	if screen != "playing":
		return
	screen = "paused"
	audio.set_music(sim.stage_id, false)
	# Instantiate pause_menu.tscn with warm ivory card matching menu-pausa-v2.png while keeping fighters visible!
	modal = instantiate_ui_scene("res://scenes/ui/pause_menu.tscn", 0.45)
	var column := centered(modal, 380, true)
	var title := label(column, "P A U S A", 28, Color("27372F"))
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	var sep := ColorRect.new()
	sep.custom_minimum_size = Vector2(0, 1)
	sep.color = Color("C5A059")
	column.add_child(sep)

	button(column, "CONTINUAR", resume_match, true)
	button(column, "LISTA DE GOLPES", show_moves)
	button(column, "REINICIAR PARTIDA", start_match)
	button(column, "OPÇÕES", show_settings)
	button(column, "VOLTAR AO MENU", show_menu)

	var hint := label(column, "ESC  •  CONTINUAR", 12, Color("62695F"))
	hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER

func resume_match() -> void:
	close_modal()
	screen = "playing"
	audio.set_music(sim.stage_id, true)

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
	modal = overlay()
	var column := centered(modal, 560)
	var completed := mode == "arcade" and arcade_index == 4 and sim.winner == 1
	label(column, "TORRE CONCLUÍDA!" if completed else ("VITÓRIA!" if sim.winner == 1 else "FIM DE COMBATE"), 34, Color("A3C9A8"))
	var c1 := GaleVisualCatalog.load_for(sim.p1.id)
	var c2 := GaleVisualCatalog.load_for(sim.p2.id)
	label(column, "%s  %d × %d  %s" % [c1.display_name, sim.wins[0], sim.wins[1], c2.display_name], 18)
	if mode == "arcade" and arcade_index < 4 and sim.winner == 1:
		button(column, "Próximo adversário", func() -> void:
			arcade_index += 1
			start_match(), true)
	button(column, "Jogar novamente", start_match)
	button(column, "Voltar à seleção", show_menu)

func show_skills() -> void:
	close_modal()
	if is_instance_valid(menu):
		menu.hide()
	modal = overlay()
	var column := centered(modal, 920)
	var target := skill_target_fighter if skill_target_fighter in GaleData.IDS else fighter1
	var cat := GaleVisualCatalog.load_for(target)
	label(column, "HABILIDADES  /  " + cat.display_name.to_upper(), 26, Color("A3C9A8"))

	var switcher := HBoxContainer.new()
	switcher.add_theme_constant_override("separation", 10)
	column.add_child(switcher)
	for fid: String in GaleData.IDS:
		var fc := GaleVisualCatalog.load_for(fid)
		button(switcher, fc.display_name, func() -> void:
			skill_target_fighter = fid
			fighter1 = fid
			show_skills(), fid == target)

	var spent := 0
	for node: Dictionary in data.fighter(target).skillTree:
		if node.id in prefs.skills[target]:
			spent += int(node.cost)
	label(column, "Pontos disponíveis: %d / 4" % (4 - spent), 20, Color("F4CE75"))
	for node: Dictionary in data.fighter(target).skillTree:
		var chosen: bool = node.id in prefs.skills[target]
		var row := HBoxContainer.new()
		column.add_child(row)
		var action := button(row, ("✓ " if chosen else "+ ") + String(node.name), func() -> void:
			prefs.skills[target] = data.toggle_skill(target, prefs.skills[target], node.id)
			persist()
			show_skills(), chosen)
		action.custom_minimum_size.x = 270
		var description := label(row, "T%d • %d PT • %s — %s" % [node.tier, node.cost, node.statTag, node.description], 14)
		description.tooltip_text = node.description
	label(column, "Remover o nível 1 também remove a habilidade dependente.\nEscolhas livres de estilo de jogo — sem XP ou grind.", 14, Color("D7D0C2"))
	button(column, "Zerar habilidades", func() -> void:
		prefs.skills[target] = []
		persist()
		show_skills())
	button(column, "Fechar", close_modal)

func show_settings() -> void:
	var was_paused := (screen == "paused")
	close_modal()
	if is_instance_valid(menu):
		menu.hide()
	if was_paused:
		screen = "paused"
	modal = overlay()
	var column := centered(modal, 1000)
	label(column, "ÁUDIO E CONTROLES", 28, Color("A3C9A8"))
	var slider := HSlider.new()
	slider.min_value = 0
	slider.max_value = 1
	slider.step = 0.05
	slider.value = prefs.volume
	column.add_child(slider)
	slider.value_changed.connect(func(value: float) -> void:
		prefs.volume = value
		persist())
	button(column, "Alternar áudio (M)", func() -> void:
		prefs.muted = not prefs.muted
		persist())
	var debug := CheckButton.new()
	debug.text = "Mostrar hitboxes e hurtboxes"
	debug.button_pressed = arena.show_boxes
	debug.toggled.connect(func(enabled: bool) -> void: arena.show_boxes = enabled)
	column.add_child(debug)
	rebind_label = label(column, "Clique em uma tecla para remapear. Esc cancela. P, R e M são reservados.", 15, Color("F4CE75"))
	var controls := HBoxContainer.new()
	controls.add_theme_constant_override("separation", 30)
	column.add_child(controls)
	for player in 2:
		var list := VBoxContainer.new()
		list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		controls.add_child(list)
		label(list, "JOGADOR %d" % (player + 1), 20)
		for action in GalePreferences.ACTIONS.size():
			var row := HBoxContainer.new()
			list.add_child(row)
			var title := label(row, GalePreferences.ACTIONS[action], 14)
			title.custom_minimum_size.x = 140
			var key := button(row, OS.get_keycode_string(prefs.keys[player][action]), func() -> void:
				listening = [player, action]
				rebind_label.text = "Pressione a nova tecla. Esc cancela.")
			key.custom_minimum_size = Vector2(240, 0)
			key.add_theme_constant_override("outline_size", 0)
			var compact := StyleBoxFlat.new()
			compact.bg_color = Color(0.11, 0.20, 0.17, 0.92)
			compact.content_margin_top = 2
			compact.content_margin_bottom = 2
			key.add_theme_stylebox_override("normal", compact)
	button(column, "Salvar e voltar", func() -> void:
		persist()
		close_modal()
		if screen == "paused":
			resume_match())

func persist() -> void:
	var error := prefs.save_to_disk()
	audio.apply_settings(prefs)
	if error != OK:
		push_warning("Não foi possível salvar preferências: %s" % error_string(error))

func _input(event: InputEvent) -> void:
	if not event is InputEventKey or not event.pressed or event.echo:
		return
	var key_event := event as InputEventKey
	if not listening.is_empty():
		get_viewport().set_input_as_handled()
		if key_event.keycode == KEY_ESCAPE:
			listening.clear()
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
			else:
				close_modal()
		return
	match key_event.keycode:
		KEY_ESCAPE, KEY_P:
			if screen == "playing":
				pause_match()
				get_viewport().set_input_as_handled()
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
	var input2 := GalePreferences.input_for(2) if mode == "versus" else sim.ai_input()
	sim.step(input1, input2)
	for event: Dictionary in sim.events:
		arena.impact(event)
		audio.play(event.kind)
	ticks += 1
	if ticks % 6 == 0:
		update_hud()
	if sim.winner != 0:
		update_hud()
		show_outcome()

func _process(delta: float) -> void:
	if is_instance_valid(arena) and not sim.p1.is_empty():
		arena.render(sim, delta)

func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_FOCUS_OUT and screen == "playing":
		pause_match()
