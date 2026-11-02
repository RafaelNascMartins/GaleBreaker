class_name GaleCombat
extends RefCounted

const DT := 1.0 / 60.0
const EDGE := 9.5
const GRAVITY := 28.0
# Long enough for the full "three, two, one, FIGHT" announcer line.
const COUNTDOWN_FRAMES := 216
var data: GaleData
var p1: Dictionary
var p2: Dictionary
var hazards: Array = []
var mode := "arcade"
var stage_id := "zephyr_dojo"
var arcade_index := 1
var round_number := 1
var wins := [0, 0]
var winner := 0
var remaining := 99.0
var countdown := COUNTDOWN_FRAMES
var freeze := 0
var round_wait := 0
var banner := "PREPARE-SE"
var banner_frames := 180
var events: Array = []
var rng := RandomNumberGenerator.new()
var attacks := GaleAttackEntities.new()
var difficulty := 1
var arena_cycle := GaleArenaCycle.new()

func _init(database: GaleData) -> void:
	data = database
	rng.seed = 472

static func idle_input() -> Dictionary:
	return {"axis": 0.0, "jump": false, "crouch": false, "guard": false,
		"parry": false, "dash": false, "breaker": false, "attack": ""}

func make_fighter(id: String, player: int, skills: Array, palette: int = 0, boss: bool = false) -> Dictionary:
	var hp := data.max_hp(id, skills)
	if boss:
		hp = roundi(hp * 1.15)
	return {"id": id, "player": player, "skills": skills.duplicate(), "palette": palette,
		"x": -1.5 if player == 0 else 1.5, "y": 0.0, "vx": 0.0, "vy": 0.0,
		"facing": 1.0 if player == 0 else -1.0, "hp": hp, "max_hp": hp,
		"meter": 50.0 if boss else 25.0, "action": "idle", "frames": 0, "phase_total": 1,
		"grounded": true, "crouch": false, "move": {}, "connected": false,
		"buffer": "", "buffer_frames": 0, "chain": 1, "chain_frames": 0,
		"combo": 0, "combo_damage": 0, "combo_frames": 0, "dribbles": 0,
		"juggle": 1.0, "breaker_cd": 0, "immunity": 0, "invuln": 0,
		"stunlock": 0, "wall_bounced": false, "hard_down": false,
		"parry_frames": 0, "armor": 0, "flash": 0, "ai_wait": 0, "boss": boss,"attack_serial":0,"blocks":0,"parries":0}

func start(id1: String, id2: String, stage: String, game_mode: String, skills1: Array = [], skills2: Array = [], index: int = 1, palette1: int = 0, palette2: int = 0) -> void:
	mode = game_mode
	stage_id = stage
	arena_cycle.reset(stage_id)
	arcade_index = index
	var boss := mode == "arcade" and index == 4
	if id1 == id2 and palette1 == palette2:
		palette2 = (palette1 + 1) % 4
	p1 = make_fighter(id1, 0, skills1, palette1)
	p2 = make_fighter(id2, 1, skills2, palette2, boss)
	wins = [0, 0]
	round_number = 1
	winner = 0
	remaining = 99.0
	countdown = COUNTDOWN_FRAMES
	freeze = 0
	round_wait = 0
	announce("ROUND 1 — PREPARE-SE", 180)
	events.clear()
	attacks.clear()
	reset_hazards()

func reset_hazards() -> void:
	hazards.clear()
	var count := int(data.stage(stage_id).hazardCount)
	for i in count:
		hazards.append({"x": -7.5 + float(i) * 15.0 / float(count - 1),
			"vx": 0.0, "hp": 100, "owner": -1, "respawn": 0})

func announce(text: String, duration: int = 80) -> void:
	banner = text
	banner_frames = duration

func emit(kind: String, f: Dictionary, color: Color = Color.WHITE) -> void:
	events.append({"kind": kind, "position": Vector3(f.x, f.y + 1.1, 0), "color": color,"fighter":f.id})

func attack(f: Dictionary, requested: String, crouching: bool) -> bool:
	var kind := requested
	if kind == "light":
		kind = "air_punch" if not f.grounded else ("down_punch" if crouching else "light")
	var move := data.move(f.id, kind, f.skills)
	if f.meter < float(move.meterCost):
		return false
	if kind == "light":
		var chain: int = f.chain if f.chain_frames > 0 else 1
		if chain == 2:
			move.damage = roundi(move.damage * 1.2)
			move.startupFrames += 1
			move.recoveryFrames += 2
			if f.id == "volt":
				move.hitHeight = "low"
				move.hitbox = move.hitbox.duplicate()
				move.hitbox.offsetY = 0.68
		elif chain == 3:
			move.damage = roundi(move.damage * 1.45)
			move.startupFrames += 2
			move.recoveryFrames += 6
			move.knockback = 5.4
			if f.id == "tophia":
				move.hitHeight = "low"
				move.hitbox = {"offsetX":0.9,"offsetY":0.3,"width":1.25,"height":0.6}
		move["chain_step"] = chain
		f.chain = chain % 3 + 1
		f.chain_frames = 54 if chain < 3 else 0
	else:
		f.chain = 1
		f.chain_frames = 0
	if kind == "heavy" and crouching and f.grounded:
		move.merge({"name": "Rasteira", "delivery":"melee", "hitHeight": "low", "animStyle": "low_sweep",
			"startupFrames": 8, "activeFrames": 4, "recoveryFrames": 18, "damage": 95,
			"launchY": 2.4, "knockback": 3.6, "armorHits": 0,
			"hitbox": {"offsetX": 1.45, "offsetY": 0.42, "width": 2.55, "height": 0.72}}, true)
	f.vx = f.vx * 0.65 if f.action == "dash" else 0.0
	f.attack_serial += 1
	f.move = move
	f.meter -= float(move.meterCost)
	f.action = "startup"
	f.frames = int(move.startupFrames)
	f.phase_total = maxi(1, int(move.startupFrames))
	f.connected = false
	f.armor = int(move.get("armorHits", 0))
	f.buffer = ""
	f.buffer_frames = 0
	attacks.spawn(f)
	if kind == "ultimate":
		freeze = 21
		announce(String(move.name).to_upper())
		emit("ultimate", f, Color(data.fighter(f.id).primaryColor))
	return true

func can_cancel(from: String, into: String) -> bool:
	return (from == "light" and into in ["light", "down_punch", "heavy", "elemental", "ultimate"]) or \
		(from in ["down_punch", "air_punch", "heavy"] and into in ["air_punch", "heavy", "elemental", "ultimate"]) or \
		(from == "elemental" and into == "ultimate")

func ai_input(force: bool = false) -> Dictionary:
	var result := idle_input()
	if mode == "training" and not force:
		return result
	p2.ai_wait = maxi(0, int(p2.ai_wait) - 1)
	var dx: float = p1.x - p2.x
	var distance := absf(dx)
	var direction := signf(dx)
	if difficulty>0:
		for e:Dictionary in attacks.items:
			if e.owner==p2.player:continue
			if e.speed==0 and e.delay>0 and absf(float(p2.x)-float(e.x))<float(e.width)*0.5+0.8:
				result.axis=signf(float(p2.x)-float(e.x))
				if result.axis==0:result.axis=-direction
				result.jump=e.kind in ["beam","spikes","stomp"] and e.delay<16
				return result
			if e.speed>0 and e.delay<=0 and absf(float(e.x)-float(p2.x))<2.2:
				result.guard=true
				result.crouch=e.move.hitHeight=="low"
				result.jump=difficulty==2 and e.height<1.2 and p2.grounded
				return result
	if p2.action in ["hitstun", "blockstun"] and p1.combo >= 4 and p2.breaker_cd == 0:
		result.breaker = true
		return result
	if p1.action in ["startup", "active"] and distance < 3.4 and (arcade_index >= 2 or p2.hp < p2.max_hp * 0.4):
		result.axis = -direction
		result.crouch = p1.move.get("hitHeight", "mid") == "low"
		result.guard = true
		result.parry = difficulty >= 1 and p1.action == "startup" and p1.frames <= (3 if difficulty == 1 else 5) and p2.ai_wait == 0
		if result.parry:
			p2.ai_wait = 35
		return result
	var ideal_range:=4.0 if p2.id=="volt" else 2.1
	result.axis=direction if distance>ideal_range else (-direction if p2.id=="volt" and distance<2.7 and absf(float(p2.x))<8.5 else 0.0)
	if p2.ai_wait > 0:
		return result
	p2.ai_wait = maxi(10, 42 - arcade_index * 3 - difficulty * 10)
	if p2.meter >= 50 and p1.hp < 380 and distance<6.0:
		result.attack="ultimate"
	elif p2.id=="volt" and distance>2.6:
		result.attack="heavy" if rng.randf()<0.25 else "light"
	elif distance > 4.0:
		if arcade_index >= 3:
			result.dash = true
		else:
			result.attack = "elemental" if distance < 6.0 else ""
	elif p2.meter >= 50 and p1.hp < 380:
		result.attack = "ultimate"
	elif not p1.grounded and p2.grounded:
		result.jump = true
	elif not p2.grounded:
		result.attack = "air_punch"
	else:
		result.attack = ["light", "light", "heavy", "down_punch"][rng.randi_range(0, 3)]
		result.crouch = result.attack == "down_punch" or (p1.crouch and rng.randf() < 0.2)
	return result

func step(input1: Dictionary, input2: Dictionary) -> void:
	events.clear()
	if banner_frames > 0:
		banner_frames -= 1
	if winner != 0:
		return
	if round_wait > 0:
		round_wait -= 1
		if round_wait == 0:
			next_round()
		return
	if countdown > 0:
		countdown -= 1
		if countdown == 0:
			announce("LUTE!", 45)
		return
	if freeze > 0:
		freeze -= 1
		for pair: Array in [[p1, input1], [p2, input2]]:
			if pair[1].attack != "":
				pair[0].buffer = pair[1].attack
				pair[0].buffer_frames = 10
		return
	if mode != "training":
		remaining = maxf(0.0, remaining - DT)
	for pair: Array in [[p1, input1], [p2, input2]]:
		var f: Dictionary = pair[0]
		var inp: Dictionary = pair[1]
		var opponent: Dictionary = p2 if f.player == 0 else p1
		update_fighter(f, opponent, inp)
	# Resolve equal active attacks together before applying either hit.
	if p1.action == "active" and p2.action == "active" and p1.move.get("delivery","melee") == "melee" and p2.move.get("delivery","melee") == "melee" and not p1.connected and not p2.connected and hit_rect(p1).intersects(hit_rect(p2)):
		for f: Dictionary in [p1, p2]:
			f.connected = true
			f.meter = minf(100, f.meter + 25)
			f.vx = -f.facing * 4.5
		freeze = 7
		announce("ELEMENTAL CLASH!")
		emit("clash", p1, Color.GOLD)
	else:
		for pair: Array in [[p1, p2, input2], [p2, p1, input1]]:
			var f: Dictionary = pair[0]
			if f.action == "active" and f.move.get("delivery","melee") == "melee" and not f.connected and hit_rect(f).intersects(hurt_rect(pair[1])):
				f.connected = true
				resolve_hit(f, pair[1], pair[2])
	attacks.update(self,[input1,input2])
	arena_cycle.update(self,[input1,input2])
	# Push boxes prevent characters occupying the same point on the ground.
	var separation: float = absf(p1.x - p2.x)
	if separation < 0.95 and absf(p1.y - p2.y) < 1.4:
		var direction := 1.0 if p2.x >= p1.x else -1.0
		p1.x = clampf(p1.x - direction * (0.95 - separation) * 0.5, -EDGE, EDGE)
		p2.x = clampf(p2.x + direction * (0.95 - separation) * 0.5, -EDGE, EDGE)
	update_hazards()
	if mode == "training":
		p1.hp = minf(p1.max_hp, maxf(1, p1.hp) + 120 * DT)
		if p2.action in ["idle", "walk"]:
			p2.hp = minf(p2.max_hp, maxf(1, p2.hp) + 240 * DT)
		p2.hp = maxf(1, p2.hp)
		p1.meter = minf(100, p1.meter + 18 * DT)
	else:
		check_round()

func update_fighter(f: Dictionary, opponent: Dictionary, inp: Dictionary) -> void:
	for key: String in ["breaker_cd", "immunity", "invuln", "flash", "parry_frames", "combo_frames", "chain_frames", "buffer_frames"]:
		f[key] = maxi(0, int(f[key]) - 1)
	if f.combo_frames == 0:
		f.combo = 0
		f.combo_damage = 0
		f.dribbles = 0
	if f.buffer_frames == 0:
		f.buffer = ""
	if inp.attack != "":
		f.buffer = inp.attack
		f.buffer_frames = 10
	if inp.breaker and f.action in ["hitstun", "blockstun", "knockdown"] and f.breaker_cd == 0:
		f.action = "idle"
		f.frames = 0
		f.breaker_cd = 360
		f.immunity = 120
		f.invuln = 20
		f.vx = -f.facing * 6.0
		opponent.vx = f.facing * 7.0
		opponent.combo = 0
		opponent.combo_frames = 0
		announce("COMBO BREAKER!")
		emit("parry", f, Color.GOLD)
	if f.action in ["startup", "active", "recovery", "hitstun", "blockstun", "knockdown", "dash", "parry"]:
		f.frames -= 1
		if f.action == "dash" and f.buffer != "":
			attack(f, f.buffer, inp.crouch)
		elif f.action in ["active", "recovery"] and f.connected and f.buffer != "" and can_cancel(f.move.type, f.buffer):
			attack(f, f.buffer, inp.crouch)
		elif f.frames <= 0:
			match f.action:
				"startup":
					f.action = "active"
					f.frames = int(f.move.activeFrames)
					f.phase_total = maxi(1, int(f.move.activeFrames))
					if f.id == "ignis" and f.move.type == "ultimate":
						f.vx = f.facing * 8.5
					elif f.id == "volt" and f.move.type in ["heavy","ultimate"]:
						f.vx = -f.facing * (3.6 if f.move.type == "ultimate" else 1.8)
					if f.move.type in ["elemental", "ultimate"] and f.move.get("delivery","melee") == "melee":
						for hazard: Dictionary in hazards:
							if hazard.hp > 0 and absf(hazard.x - f.x) <= float(f.move.range) + 2.4:
								hazard.vx = signf(opponent.x - hazard.x) * float(f.move.gustForce)
								hazard.owner = f.player
				"active":
					f.action = "recovery"
					f.frames = int(f.move.recoveryFrames) + (0 if f.connected else 5)
					f.phase_total = maxi(1, int(f.frames))
				"knockdown":
					if f.grounded:
						f.action = "idle"
						f.invuln = 9
						f.hard_down = false
				_:
					f.action = "idle" if f.grounded else "jump"
					f.armor = 0
	if f.action in ["idle", "walk", "crouch", "guard", "jump"]:
		f.facing = 1.0 if opponent.x >= f.x else -1.0
		f.crouch = inp.crouch and f.grounded
		if f.buffer != "" and attack(f, f.buffer, inp.crouch):
			pass
		elif inp.parry and f.grounded:
			f.action = "parry"
			f.parry_frames = 6
			f.frames = 16
		elif inp.dash and f.grounded:
			f.action = "dash"
			f.frames = 10
			f.vx = (signf(inp.axis) if inp.axis != 0 else f.facing) * float(data.fighter(f.id).dashSpeed)
		elif inp.guard and f.grounded:
			f.action = "guard"
			f.vx = 0.0
		else:
			if inp.jump and f.grounded:
				f.vy = float(data.fighter(f.id).jumpVelocity)
				f.grounded = false
			f.vx = inp.axis * float(data.fighter(f.id).walkSpeed) * (0.4 if f.crouch else 1.0)
			f.action = "jump" if not f.grounded else ("crouch" if f.crouch else ("walk" if inp.axis != 0 else "idle"))
	if f.action == "knockdown" and f.grounded and not f.hard_down and f.frames <= 14 and inp.axis != 0:
		f.vx = signf(inp.axis) * 9.5
		f.invuln = maxi(f.invuln, 16)
	f.x += f.vx * DT
	if f.action not in ["walk", "dash"]:
		f.vx *= pow(0.05, DT)
	if not f.grounded:
		f.y += f.vy * DT
		f.vy -= GRAVITY * float(f.juggle) * DT
		if f.y <= 0:
			f.y = 0.0
			f.vy = 0.0
			f.grounded = true
			f.juggle = 1.0
			if f.action == "knockdown":
				f.frames = maxi(24, f.frames)
			if f.action == "jump":
				f.action = "idle"
	if absf(f.x) >= EDGE:
		f.x = clampf(f.x, -EDGE, EDGE)
		if f.action == "hitstun" and absf(f.vx) > 4.0 and not f.wall_bounced:
			f.vx = -signf(f.x) * 6.0
			f.vy = 6.0
			f.grounded = false
			f.wall_bounced = true
			announce("WALL BOUNCE!")
			emit("heavy", f, Color.ORANGE)
	if f.action in ["idle", "walk", "jump", "guard", "crouch"]:
		f.stunlock = 0
		f.wall_bounced = false

static func hurt_rect(f: Dictionary) -> Rect2:
	var height := 1.36 if f.crouch and f.grounded else 2.1
	return Rect2(Vector2(f.x - 0.525, f.y), Vector2(1.05, height))

static func hit_rect(f: Dictionary) -> Rect2:
	if f.move.is_empty():
		return Rect2()
	var box: Dictionary = f.move.hitbox
	return Rect2(Vector2(f.x + f.facing * float(box.offsetX) - float(box.width) * 0.5,
		f.y + float(box.offsetY) - float(box.height) * 0.5), Vector2(box.width, box.height))

static func blocks(crouching: bool, height: String) -> bool:
	return crouching if height == "low" else (not crouching if height == "overhead" else true)

func resolve_hit(a: Dictionary, d: Dictionary, inp: Dictionary, move_override: Dictionary = {}, facing_override: float = 0.0) -> String:
	if d.invuln > 0 or (d.action == "knockdown" and d.grounded):
		return "miss"
	var move: Dictionary = a.move if move_override.is_empty() else move_override
	var direction := float(a.facing) if facing_override == 0.0 else facing_override
	if d.action == "parry" and d.parry_frames > 0:
		d.parries += 1
		d.meter = minf(100, d.meter + 22)
		if move_override.is_empty():
			a.action = "recovery"
			a.frames = int(move.recoveryFrames) + 8
		freeze = 5
		announce("PERFECT PARRY!")
		emit("parry", d, Color.GOLD)
		return "parry"
	var neutral: bool = d.grounded and d.action in ["idle", "walk", "crouch", "guard", "blockstun"]
	if neutral and (inp.guard or inp.axis * d.facing < -0.15 or d.action == "blockstun") and blocks(inp.crouch, move.hitHeight):
		d.blocks += 1
		d.hp = maxf(1, d.hp - float(move.chipDamage))
		d.action = "blockstun"
		d.frames = int(move.blockstunFrames)
		d.crouch = inp.crouch
		d.vx = direction * float(move.blockPushback)
		if absf(d.x) > EDGE - 0.5:
			a.vx = -direction * float(move.blockPushback)
		a.meter = minf(100, a.meter + float(move.meterGain) * 0.5)
		freeze = maxi(1, roundi(float(move.hitstopMs) * 0.039))
		emit("block", d, Color.SKY_BLUE)
		return "block"
	if d.immunity > 0 or (d.armor > 0 and move.type != "ultimate"):
		d.hp = maxf(1, d.hp - float(move.damage) * 0.4)
		d.armor = maxi(0, d.armor - 1)
		d.flash = 7
		a.vx = -direction * 3.5
		announce("ARMOR!")
		emit("block", d, Color.ORANGE)
		return "armor"
	var counter: bool = d.action in ["startup", "active"]
	var damage := roundi(float(move.damage) * maxf(0.45, 1.0 - a.combo * 0.08) * (1.2 if counter else 1.0))
	d.hp = maxf(0, d.hp - damage)
	d.stunlock += 1
	d.flash = 8
	a.combo += 1
	a.combo_damage += damage
	a.combo_frames = 75
	a.meter = minf(100, a.meter + float(move.meterGain))
	d.meter = minf(100, d.meter + 4)
	d.action = "knockdown" if move.animStyle == "low_sweep" or (move.type == "ultimate" and (not move.get("multi",false) or move.get("finisher",false))) else "hitstun"
	d.hard_down = d.action == "knockdown"
	d.frames = int(move.hitstunFrames) + (5 if counter else 0)
	d.armor = 0
	d.vx = direction * float(move.knockback)
	if not d.grounded and not move.get("multi",false):
		a.dribbles += 1
		d.juggle = minf(3.4, d.juggle + 0.24)
		d.vy = maxf(5.8, float(move.get("airDribblePopY", 6.8)) / pow(d.juggle, 0.55))
		if a.dribbles >= 3:
			d.vy = -8.5
			d.action = "knockdown"
			d.invuln = 20
			announce("AIR DRIBBLE FINISHER!")
	elif float(move.launchY) > 0:
		d.vy = float(move.launchY)
		d.grounded = false
	if d.stunlock >= 5:
		d.action = "idle"
		d.immunity = 120
		d.stunlock = 0
		d.vx = direction * 7.0
		announce("STUNLOCK ESCAPE!")
	elif counter:
		announce("COUNTER HIT!", 45)
	freeze = maxi(1, roundi(float(move.hitstopMs) * 0.06))
	emit("heavy" if move.type in ["heavy", "ultimate"] else "hit", d, Color(data.fighter(a.id).primaryColor))
	events[-1].fighter = a.id
	# Which move landed, so presentation can pick a per-move sound.
	events[-1].move_type = String(move.get("type", ""))
	events[-1].chain_step = int(move.get("chain_step", 1))
	events[-1].entity = not move_override.is_empty()
	return "hit"

func update_hazards() -> void:
	for hazard: Dictionary in hazards:
		if hazard.hp <= 0:
			hazard.respawn -= 1
			if hazard.respawn <= 0:
				hazard.hp = 100
				hazard.owner = -1
			continue
		var old_x: float = hazard.x
		hazard.x = clampf(hazard.x + hazard.vx * DT, -EDGE, EDGE)
		hazard.vx *= pow(0.18, DT)
		if absf(hazard.vx) < 3.5:
			continue
		for f: Dictionary in [p1, p2]:
			if f.player == hazard.owner or f.y > 1.5 or f.invuln > 0:
				continue
			if f.x >= minf(old_x, hazard.x) - 0.7 and f.x <= maxf(old_x, hazard.x) + 0.7:
				f.hp = maxf(0, f.hp - 45)
				f.action = "hitstun"
				f.frames = 18
				f.vx = signf(hazard.vx) * 5.5
				hazard.hp = 0
				hazard.vx = 0.0
				hazard.respawn = 360
				emit("heavy", f, Color.ORANGE)
				break
		if absf(hazard.x) >= EDGE:
			hazard.vx *= -0.6

func check_round() -> void:
	var result := 0
	if p1.hp <= 0 and p2.hp <= 0:
		announce("DOUBLE K.O. — REPETIR ROUND", 100)
		round_wait = 100
		return
	if p2.hp <= 0:
		result = 1
	elif p1.hp <= 0:
		result = 2
	elif remaining <= 0:
		var ratio1: float = p1.hp / p1.max_hp
		var ratio2: float = p2.hp / p2.max_hp
		if is_equal_approx(ratio1, ratio2):
			announce("EMPATE — REPETIR ROUND", 100)
			round_wait = 100
			return
		result = 1 if ratio1 > ratio2 else 2
	if result == 0:
		return
	wins[result - 1] += 1
	if wins[result - 1] >= 2:
		winner = result
		announce("VITÓRIA!" if result == 1 else "DERROTA", 300)
	else:
		announce("ROUND %d — %s VENCE" % [round_number, String(data.fighter(p1.id if result == 1 else p2.id).name).split(" ")[0]], 100)
		round_wait = 100
	emit("ko", p2 if result == 1 else p1, Color.GOLD)

func next_round() -> void:
	attacks.clear()
	arena_cycle.reset(stage_id)
	round_number = wins[0] + wins[1] + 1
	var meter1 := maxf(25, p1.meter * 0.5)
	var meter2 := maxf(25, p2.meter * 0.5)
	p1 = make_fighter(p1.id, 0, p1.skills, p1.palette)
	p2 = make_fighter(p2.id, 1, p2.skills, p2.palette, p2.boss)
	p1.meter = meter1
	p2.meter = meter2
	remaining = 99.0
	countdown = COUNTDOWN_FRAMES
	freeze = 0
	reset_hazards()
	announce("ROUND %d — PREPARE-SE" % round_number, COUNTDOWN_FRAMES)
