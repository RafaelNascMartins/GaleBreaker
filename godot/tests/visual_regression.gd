extends SceneTree
## Tests semantic pose outcomes, not only whether animation names exist.

var failures := 0
var checks := 0

func _initialize() -> void:
	call_deferred("run")

func check(ok: bool, message: String) -> void:
	checks += 1
	if ok:
		print("PASS: " + message)
	else:
		failures += 1
		push_error("FAIL: " + message)

func run() -> void:
	var data := GaleData.new()
	for id: String in ["kaze", "ignis", "tophia", "volt"]:
		var view := GaleFighterView.new()
		root.add_child(view)
		view.build(data, id, 0)
		check(view.is_valid_asset(), id + " imports complete rig, clips and materials")
		view.play_clip("idle", 0.0)
		var hand_idle := view.socket_position("socket_hand_r")
		var chest_idle := view.socket_position("socket_chest").y
		for low: String in ["crouch", "guard_low"]:
			view.play_clip(low, 0.1)
			check(view.socket_position("socket_chest").y < chest_idle - 0.25, id + " " + low + " visibly lowers the body")
		view.play_clip("light_1", GaleAnimTiming.contact_sec(id, "light_1"))
		var hand_contact := view.socket_position("socket_hand_r")
		check(hand_contact.z < -0.2, id + " striking hand points in the fighting direction")
		check(hand_contact.distance_to(hand_idle) > 0.01, id + " hand socket follows the animated skeleton")
		if id == "kaze":
			view.play_clip("light_3", GaleAnimTiming.contact_sec(id, "light_3"))
			check(view.socket_position("socket_foot_r").z < -0.45, "Kaze J3 extends the foot forward")
		if id == "volt":
			for clip: String in ["idle", "light_1", "light_2", "heavy", "ultimate"]:
				view.play_clip(clip, 0.1)
				var muzzle := view.socket_position("socket_muzzle")
				var hand := view.socket_position("socket_hand_r")
				check(muzzle.z < hand.z - 0.25 and absf(muzzle.y - hand.y) < 0.15, "Volt " + clip + " barrel stays forward and level")
		for clip: String in ["light_1", "light_2", "light_3", "heavy", "elemental", "ultimate"]:
			var marks := GaleAnimTiming.attack(id, clip)
			var length := view.anim_player.get_animation(view.catalog.clips.get(clip, clip)).length
			check(absf(length - float(marks.end) / 60.0) < 0.02, id + " " + clip + " clip length matches its timing table")
			check(int(marks.wind) < int(marks.contact) and int(marks.contact) < int(marks.follow) and int(marks.follow) < int(marks.end), id + " " + clip + " markers are ordered")
		if id in ["kaze", "ignis"]:
			# The exaggeration pass must visibly move the torso between wind-up and contact.
			for clip: String in ["light_1", "heavy", "ultimate"]:
				var marks := GaleAnimTiming.attack(id, clip)
				view.play_clip(clip, float(marks.wind) / 60.0)
				var chest_wind := view.socket_position("socket_chest")
				view.play_clip(clip, float(marks.contact) / 60.0)
				check(view.socket_position("socket_chest").distance_to(chest_wind) > 0.05, id + " " + clip + " throws the body into the strike")
		if id == "kaze":
			var robe := view.skeleton.find_bone("robe_side_l")
			view.play_clip("heavy", GaleAnimTiming.attack(id, "heavy").wind / 60.0)
			var robe_wind := view.skeleton.get_bone_pose_rotation(robe)
			view.play_clip("heavy", GaleAnimTiming.attack(id, "heavy").contact / 60.0)
			check(robe >= 0 and view.skeleton.get_bone_pose_rotation(robe).angle_to(robe_wind) > 0.2, "Kaze side robe panels swing with the kick")
		var sim := GaleCombat.new(data)
		sim.start(id, "kaze", "zephyr_dojo", "versus")
		var state: Dictionary = sim.p1.duplicate(true)
		state.x = 0.0
		state.action = "active"
		state.frames = 2
		state.phase_total = 6
		state.move = data.move(id, "elemental", [])
		view.sync(state, 0.0)
		view.sync(state, 1.0 / 60.0)
		check(not view.move_effects.visible, id + " entity attacks do not duplicate local placeholder effects")
		var frozen_time := view.current_anim_time
		var frozen_hand := view.socket_position("socket_hand_r")
		view.sync(state, 1.0 / 60.0)
		check(is_equal_approx(view.current_anim_time, frozen_time) and view.socket_position("socket_hand_r").is_equal_approx(frozen_hand), id + " hitstop freezes both time and the blended pose")
		state.action = "idle"
		state.move = {}
		view.sync(state, 2.0 / 60.0)
		check(not view.move_effects.visible, id + " effects are cleared after the attack")
		state.action = "hitstun"
		view.sync(state, 3.0 / 60.0)
		view.sync(state, 4.0 / 60.0)
		check(view.current_clip == "hit" and view.current_anim_time > 0.0, id + " hit reaction progresses instead of staying on one frame")
		state.presentation_victory = true
		view.sync(state, 5.0 / 60.0)
		check(view.current_clip == "victory", id + " match winner plays the presentation animation")
		state.presentation_victory = false
		state.hp = 0
		view.sync(state, 6.0 / 60.0)
		view.sync(state, 7.0 / 60.0)
		check(view.current_clip == "ko" and view.current_anim_time > 0.0, id + " knockout plays its fall timeline")
		view.queue_free()
		await process_frame
	check(GaleAnimTiming.attack("kaze", "heavy").contact < GaleAnimTiming.attack("ignis", "heavy").contact, "Ignis winds up heavier than Kaze")
	check(GaleAnimTiming.state_frames("kaze", "walk") != GaleAnimTiming.state_frames("ignis", "walk"), "Kaze and Ignis walk at their own rhythm")
	print("VISUAL TESTS: %d checks, %d failures" % [checks, failures])
	quit(1 if failures > 0 else 0)
