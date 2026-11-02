class_name GaleTutorial
extends RefCounted

const STEPS := [
	["Movimento","Ande para os lados e percorra 1,5 m."],
	["Pulo","Pule para sair de ataques baixos e projéteis."],
	["Agachar","Agache para mudar sua postura e os golpes disponíveis."],
	["Defender","Segure a defesa ou apare o golpe do adversário."],
	["Combo básico","Aproxime-se e acerte J1, J2 e J3 usando básico três vezes."],
	["Golpe forte","Acerte um golpe forte. Observe a preparação e a recuperação."],
	["Elemental","Acerte seu elemental. A marca no chão avisa onde haverá impacto."],
	["Ultimate","Use a energia disponível e acerte seu ultimate."]]
var step := 0
var elapsed := 0
var origin_x := 0.0
var complete := false

func prepare(sim: GaleCombat) -> void:
	sim.countdown = 0
	sim.attacks.clear()
	sim.p1.x = -0.65
	sim.p2.x = 0.65
	sim.p1.action = "idle"
	sim.p2.action = "idle"
	for f: Dictionary in [sim.p1,sim.p2]:
		f.y = 0.0
		f.vy = 0.0
		f.vx = 0.0
		f.grounded = true
		f.frames = 0
		f.invuln = 0
		f.immunity = 0
		f.buffer = ""
		f.hp = f.max_hp
	sim.p1.move = {}
	sim.p2.move = {}
	sim.p1.combo = 0
	sim.p1.chain = 1
	sim.p1.chain_frames = 0
	sim.p1.blocks = 0
	sim.p1.parries = 0
	sim.p1.meter = 100
	sim.p2.hp = sim.p2.max_hp
	sim.freeze = 0
	sim.banner_frames = 0
	origin_x = sim.p1.x
	elapsed = 0

func update(sim: GaleCombat, input: Dictionary) -> bool:
	if complete:
		return false
	elapsed += 1
	var done := false
	match step:
		0: done = absf(float(sim.p1.x)-origin_x) >= 1.5
		1: done = not bool(sim.p1.grounded) and float(sim.p1.y) > 0.25
		2: done = bool(sim.p1.crouch) and bool(input.crouch)
		3: done = int(sim.p1.blocks)+int(sim.p1.parries) > 0
		4: done = sim.p1.connected and int(sim.p1.move.get("chain_step",0)) == 3
		5,6,7:
			done = sim.p1.connected and sim.p1.move.get("type","") == ["heavy","elemental","ultimate"][step-5]
	if done:
		step += 1
		complete = step >= STEPS.size()
		if not complete:
			prepare(sim)
	return done

func dummy_input(sim: GaleCombat) -> Dictionary:
	var input := GaleCombat.idle_input()
	if step == 3 and elapsed % 65 == 30:
		input.attack = "light"
	return input
