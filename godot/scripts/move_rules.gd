class_name GaleMoveRules
extends RefCounted
## Playable tuning for the GDD kits. Values are starting balance, not final data.

static func apply(id: String, kind: String, move: Dictionary) -> void:
	move.delivery = "melee"
	if id == "tophia" and kind == "rock_spike":
		# half circle forward + elemental: she tosses a stone up in an arc; where it lands a stone
		# spike rises from the ground and launches (rock_flight frames in the air, its shadow shows
		# where it will fall)
		move.merge({"name": "Espinho de Queda", "delivery": "rock_spike", "startupFrames": 18, "activeFrames": 6,
			"recoveryFrames": 22, "damage": 90, "meterCost": 15, "range": 4.0, "hitHeight": "mid",
			"launchY": 4.5, "knockback": 1.5, "armorHits": 0, "rockFlight": 30, "rockDistance": 3.9}, true)
		return
	if kind not in ["light", "heavy", "elemental", "ultimate"]:
		return
	var names := {
		"kaze":["Palma de Jade","Chute do Vendaval","Rajada de Vento","Tufão Celestial"],
		"ignis":["Soco de Roça","Marreta Caipira","Pisada da Fornalha","Fúria do Meio-Dia"],
		"tophia":["Punho de Arenito","Martelo de Pedra","Erupção Rochosa","Colosso de Terra"],
		"volt":["Tiro de Sucata","Disparo Carregado","Curto-Circuito","Sobrecarga Total"]}
	move.name = names[id][["light","heavy","elemental","ultimate"].find(kind)]
	if kind == "ultimate":
		move.meterCost = 50
	if id == "volt" and kind == "light":
		move.merge({"delivery":"bolt","startupFrames":7,"activeFrames":3,"recoveryFrames":16,"damage":52,"hitHeight":"mid","range":7.0,"armorHits":0}, true)
	elif id == "volt" and kind == "heavy":
		move.merge({"delivery":"charged_bolt","startupFrames":26,"activeFrames":4,"recoveryFrames":30,"damage":155,"hitHeight":"mid","range":6.0,"armorHits":0}, true)
	elif id == "volt" and kind == "elemental":
		move.merge({"delivery":"pulse","startupFrames":18,"activeFrames":8,"recoveryFrames":24,"damage":95,"meterCost":12,"range":1.7,"launchY":0.0,"armorHits":0}, true)
	elif id == "volt" and kind == "ultimate":
		move.merge({"delivery":"beam","startupFrames":42,"activeFrames":12,"recoveryFrames":36,"damage":340,"range":6.5,"hitHeight":"mid","launchY":2.5,"armorHits":0}, true)
	elif id == "kaze" and kind == "elemental":
		move.merge({"delivery":"wave","startupFrames":16,"activeFrames":6,"recoveryFrames":24,"damage":105,"meterCost":12,"range":6.5,"hitHeight":"mid","launchY":0.0}, true)
	elif id == "kaze" and kind == "ultimate":
		move.merge({"delivery":"vortex","startupFrames":30,"activeFrames":40,"recoveryFrames":25,"damage":300,"range":2.5,"launchY":6.0,"armorHits":0}, true)
	elif id == "tophia" and kind == "elemental":
		# the stone jab: a punch that throws a stone straight across the screen
		move.merge({"delivery":"stone","startupFrames":12,"activeFrames":4,"recoveryFrames":18,"damage":70,"meterCost":15,"range":6.5,"hitHeight":"mid","launchY":0.0,"armorHits":0}, true)
	elif id == "tophia" and kind == "ultimate":
		move.merge({"delivery":"fist","startupFrames":36,"activeFrames":8,"recoveryFrames":34,"damage":330,"range":5.5,"launchY":4.0,"armorHits":0}, true)
	elif id == "ignis" and kind == "elemental":
		move.merge({"delivery":"stomp","startupFrames":22,"activeFrames":8,"recoveryFrames":28,"damage":130,"meterCost":12,"range":1.7,"hitHeight":"low","launchY":0.0,"armorHits":0}, true)
	elif id == "ignis" and kind == "ultimate":
		move.merge({"startupFrames":32,"activeFrames":22,"recoveryFrames":36,"damage":340,"range":1.7,"armorHits":0,"launchY":4.0}, true)
	if id == "tophia":
		move.armorHits = 0
	if move.delivery == "melee":
		var reach := 0.9 if kind == "light" else 1.45
		if id == "ignis" and kind == "ultimate":
			reach = 0.95
		move.hitbox = {"offsetX":reach,"offsetY":1.1,"width":1.2 if kind=="light" else 1.5,"height":1.0}
