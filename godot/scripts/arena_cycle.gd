class_name GaleArenaCycle
extends RefCounted
## Predictable arena events, with a 90-tick warning and no random placement.

var clock := 0
var event_index := 0
var x := 0.0
var width := 1.8
var label := ""
var stage := ""

func reset(id: String) -> void:
	clock=0;event_index=0;stage=id
	select_event()

func select_event() -> void:
	x=[-3.0,0.0,3.0][event_index%3]
	width=1.8 if stage=="molten_forge" else 1.4
	label="FORNALHA" if stage=="molten_forge" else "CARGA CAINDO"
	if stage=="zephyr_dojo":
		x=0.0;width=GaleCombat.EDGE*2.0;label="RAJADA DA ARENA"

func visible_now() -> bool: return clock>=810
func active_now() -> bool: return clock>=900

func update(sim: GaleCombat, inputs: Array) -> void:
	if sim.mode=="training": return
	clock+=1
	if clock==900:
		var direction:=1.0 if event_index%2==0 else -1.0
		if stage=="zephyr_dojo":
			for hazard:Dictionary in sim.hazards:
				if hazard.hp>0: hazard.vx=direction*10.0;hazard.owner=-1
			for f:Dictionary in [sim.p1,sim.p2]:
				if not inputs[int(f.player)].guard: f.vx+=direction*3.0
		else:
			for f:Dictionary in [sim.p1,sim.p2]:
				if absf(float(f.x)-x)>width*0.5+0.525 or f.invuln>0: continue
				if stage=="molten_forge" and f.y>1.0: continue
				var guarded:bool=inputs[int(f.player)].guard or f.parry_frames>0
				f.hp=maxf(1.0 if guarded else 0.0,float(f.hp)-(3.0 if guarded else 50.0))
				if not guarded:
					f.action="hitstun";f.frames=20;f.vx=direction*3.0;f.flash=6
				sim.events.append({"kind":"block" if guarded else "heavy","position":Vector3(f.x,0.5,0),"color":Color("f5a344"),"fighter":"ignis" if stage=="molten_forge" else "tophia"})
	if clock>=912:
		clock=0;event_index+=1;select_event()
