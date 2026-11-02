class_name GaleAttackEntities
extends RefCounted
## Fixed-tick, deterministic attacks. Rendering consumes these same entities.

var items: Array[Dictionary] = []
var next_id := 1

func clear() -> void:
	items.clear()

func spawn(f: Dictionary) -> void:
	var delivery := String(f.move.get("delivery", "melee"))
	if delivery == "melee":
		return
	var count := 3 if delivery == "spikes" else 1
	for i in count:
		var move: Dictionary = f.move.duplicate(true)
		var speed := 0.0
		var width := 1.0
		var height := 1.0
		var life := 8
		var y := float(f.y) + 1.2
		var distance := 0.8
		var interval := 999
		match delivery:
			"bolt":
				speed = 12.0; width = 0.38; height = 0.30; life = 34
				y = float(f.y) + (0.55 if int(move.get("chain_step",1)) == 2 else 1.2)
			"charged_bolt":
				speed = 6.0; width = 0.85; height = 0.85; life = 58
			"wave":
				speed = 8.0; width = 0.85; height = 1.1; life = 46; y = 0.70
			"fist":
				speed = 7.0; width = 1.0; height = 1.1; life = 44
			"vortex":
				width = 1.65; height = 3.2; y = 1.6; distance = 1.9; life = 40; interval = 12
				move.multi = true
			"spikes":
				width = 0.75; height = 1.9; y = 0.95; distance = 1.2 + i * 0.9; life = 7
			"pulse":
				width = 3.2; height = 1.5; y = 0.75; distance = 0.0
			"stomp":
				width = 3.0; height = 0.65; y = 0.325; distance = 0.0
			"beam":
				width = 6.5; height = 0.50; y = 1.15; distance = width * 0.5 + 0.65; life = 12
		var attack := {"id":next_id,"owner":int(f.player),"fighter":f.id,"serial":int(f.attack_serial),
			"kind":delivery,"move":move,"x":float(f.x)+float(f.facing)*distance,"y":y,
			"facing":float(f.facing),"speed":speed,"width":width,"height":height,"life":life,
			"delay":int(move.startupFrames)+(i*8 if delivery=="spikes" else 0),"age":0,
			"hits":{},"interval":interval,"spawned":false}
		items.append(attack)
		next_id += 1

static func rect(e: Dictionary) -> Rect2:
	return Rect2(Vector2(e.x-e.width*0.5,e.y-e.height*0.5),Vector2(e.width,e.height))

func update(sim: GaleCombat, inputs: Array) -> void:
	for index in range(items.size()-1,-1,-1):
		var e: Dictionary = items[index]
		if e.life <= 0:
			items.remove_at(index)
			continue
		var owner: Dictionary = sim.p1 if e.owner == 0 else sim.p2
		var defender: Dictionary = sim.p2 if e.owner == 0 else sim.p1
		if e.delay > 0:
			# An interrupted wind-up does not leave an invisible attack scheduled.
			if not e.spawned and (owner.attack_serial != e.serial or owner.action not in ["startup","active"]):
				items.remove_at(index)
				continue
			e.delay -= 1
			continue
		if not e.spawned:
			e.spawned = true
			sim.events.append({"kind":e.kind,"position":Vector3(e.x,e.y,0),"fighter":e.fighter,"color":Color(sim.data.fighter(e.fighter).primaryColor)})
		var previous := float(e.x)
		e.x += e.facing * e.speed * GaleCombat.DT
		# Swept box prevents fast bolts tunneling between 60 Hz ticks.
		var box := rect(e)
		box.position.x = minf(previous,float(e.x)) - float(e.width)*0.5
		box.size.x += absf(float(e.x)-previous)
		var can_hit: bool = not e.hits.has(defender.player) or int(e.age)-int(e.hits[defender.player]) >= int(e.interval)
		if can_hit and box.intersects(GaleCombat.hurt_rect(defender)):
			var move: Dictionary = e.move.duplicate(true)
			if e.kind == "vortex":
				move.finisher = int(e.age) >= 36
				move.damage = roundi(float(e.move.damage) * (0.46 if move.finisher else 0.18))
				move.launchY = 6.0 if move.finisher else 0.0
				move.knockback = 5.5 if move.finisher else 0.0
			var result := sim.resolve_hit(owner,defender,inputs[1-int(e.owner)],move,float(e.facing))
			if result != "miss":
				e.hits[defender.player] = e.age
				if owner.attack_serial == e.serial:
					owner.connected = true
				if e.speed > 0 or result == "parry":
					e.life = 0
		if e.kind in ["wave","pulse","stomp","spikes","vortex","beam","fist"]:
			for hazard: Dictionary in sim.hazards:
				if hazard.hp > 0 and absf(float(hazard.x)-float(e.x)) < float(e.width)*0.5+0.3:
					hazard.vx = float(e.facing) * float(e.move.get("gustForce",10.0))
					hazard.owner = e.owner
		# Opposed projectiles cancel, with a visible clash rather than ghosting.
		if e.speed > 0:
			for other: Dictionary in items:
				if other.id != e.id and other.owner != e.owner and other.delay <= 0 and other.speed > 0 and rect(e).intersects(rect(other)):
					e.life = 0; other.life = 0
					sim.events.append({"kind":"clash","position":Vector3(e.x,e.y,0),"color":Color.GOLD})
					break
		e.life -= 1
		e.age += 1
		if e.life <= 0 or absf(float(e.x)) > GaleCombat.EDGE+1.0:
			items.remove_at(index)
