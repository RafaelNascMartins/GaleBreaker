class_name GaleAudio
extends Node

var players: Array[AudioStreamPlayer] = []
var music: AudioStreamPlayer
var tones: Dictionary = {}
var songs: Dictionary = {}
var cursor := 0
var sfx_volume := 0.85

func _ready() -> void:
	for i in 8:
		var player := AudioStreamPlayer.new()
		add_child(player)
		players.append(player)
	music = AudioStreamPlayer.new()
	music.volume_db = -23
	add_child(music)
	for kind: String in ["hit", "heavy", "block", "parry", "clash", "ultimate", "ko", "click"]:
		var frequency: float = {"hit": 140.0, "heavy": 75.0, "block": 280.0, "parry": 880.0, "clash": 620.0, "ultimate": 110.0, "ko": 440.0, "click": 700.0}[kind]
		tones[kind] = synth(frequency, 0.32 if kind in ["ko", "ultimate"] else 0.1)
	for id: String in ["kaze","ignis","tophia","volt"]:
		for kind: String in ["hit","heavy","elemental","ultimate","step"]:
			tones[id+"_"+kind] = signature(id,kind)

func signature(id: String, kind: String) -> AudioStreamWAV:
	var duration := 0.48 if kind == "ultimate" else 0.26 if kind == "elemental" else 0.09 if kind == "step" else 0.14
	var samples := int(22050*duration)
	var bytes := PackedByteArray()
	bytes.resize(samples*2)
	var rng := RandomNumberGenerator.new()
	rng.seed = (id+kind).hash()
	var frequency: float = {"kaze":260.0,"ignis":65.0,"tophia":95.0,"volt":520.0}[id]
	for i in samples:
		var t := float(i)/22050.0
		var envelope := sin(minf(t*180.0,PI/2.0))*pow(1.0-float(i)/samples,2.0)
		var noise := rng.randf_range(-1.0,1.0)
		var tone := sin(TAU*frequency*t*(1.0-t*0.7))
		var sample := tone*0.6+noise*0.35
		match id:
			"kaze": sample = noise*0.45+sin(TAU*frequency*t)*0.18
			"ignis": sample = tone*0.7+noise*exp(-t*45.0)*0.5
			"tophia": sample = tone*0.35+noise*exp(-t*18.0)*0.65+sin(TAU*frequency*2.73*t)*0.2
			"volt": sample = sin(TAU*frequency*t*(1.0-t*1.5))*0.5+sin(TAU*frequency*1.013*t)*0.3+noise*0.12
		bytes.encode_s16(i*2,int(clampf(sample*envelope,-1,1)*13000))
	var stream := AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = 22050
	stream.data = bytes
	return stream

func synth(frequency: float, duration: float) -> AudioStreamWAV:
	var samples := int(22050 * duration)
	var bytes := PackedByteArray()
	bytes.resize(samples * 2)
	for i in samples:
		var t := float(i) / 22050.0
		var envelope := pow(1.0 - float(i) / samples, 2.0)
		var signal_value := sin(TAU * frequency * t * (1.0 - t * 0.7)) + sin(TAU * frequency * 2.01 * t) * 0.25
		bytes.encode_s16(i * 2, int(signal_value * envelope * 9000))
	var stream := AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = 22050
	stream.data = bytes
	return stream

func play(kind: String, fighter: String = "") -> void:
	var aliases := {"bolt":"elemental","charged_bolt":"heavy","wave":"elemental","pulse":"elemental","stomp":"elemental","spikes":"elemental","vortex":"ultimate","fist":"ultimate","beam":"ultimate"}
	var category: String = aliases.get(kind,kind)
	if not fighter.is_empty() and tones.has(fighter+"_"+category):
		kind = fighter+"_"+category
	if not tones.has(kind):
		return
	var player := players[cursor]
	cursor = (cursor + 1) % players.size()
	player.stream = tones[kind]
	player.volume_db = linear_to_db(maxf(0.001,sfx_volume))
	player.play()

func apply_settings(prefs: GalePreferences) -> void:
	sfx_volume = prefs.sfx_volume
	if is_instance_valid(music): music.volume_db = linear_to_db(maxf(0.001,prefs.music_volume))-18.0
	AudioServer.set_bus_mute(0, prefs.muted or prefs.volume <= 0)
	AudioServer.set_bus_volume_db(0, linear_to_db(maxf(0.001, prefs.volume)))

func set_music(stage: String, playing: bool) -> void:
	if not playing:
		music.stream_paused = true
		return
	if not songs.has(stage):
		songs[stage] = compose(stage)
	if music.stream != songs[stage]:
		music.stream = songs[stage]
		music.play()
	elif not music.playing:
		music.play()
	music.stream_paused = false

func compose(stage: String) -> AudioStreamWAV:
	var scales := {"zephyr_dojo":[0,2,4,7,9],"molten_forge":[0,1,5,7,10],"storm_market":[0,2,3,7,8]}
	var notes: Array = scales.get(stage,scales.zephyr_dojo)
	var base := 146.83 if stage == "molten_forge" else 164.81
	var beat := 0.24
	var samples := int(22050*beat*32)
	var bytes := PackedByteArray()
	bytes.resize(samples*2)
	var motif := [0,2,3,1,4,3,2,1,0,1,3,4,2,1,3,0]
	var rng := RandomNumberGenerator.new()
	rng.seed = stage.hash()
	for i in samples:
		var t := float(i)/22050.0
		var tick := int(t/beat)
		var local := fmod(t,beat)
		var freq := base*pow(2.0,float(notes[motif[tick%16]])/12.0)
		var pluck := sin(TAU*freq*local)*exp(-local*17.0)*0.32
		var bass := sin(TAU*base*0.5*t)*exp(-fmod(t,beat*4)*5.0)*0.21
		var kick := sin(TAU*70.0*local*(1.0-local*2.0))*exp(-local*35.0)*(0.24 if tick%4==0 else 0.08)
		var hat := rng.randf_range(-1,1)*exp(-local*85.0)*0.07
		var chord := sin(TAU*freq*0.5*local)*0.025*sin(PI*local/beat)
		var seam := clampf(minf(t/0.008,(float(samples-i)/22050.0)/0.008),0,1)
		bytes.encode_s16(i*2,int(clampf((pluck+bass+kick+hat+chord)*seam,-0.85,0.85)*22000))
	var song := AudioStreamWAV.new()
	song.format = AudioStreamWAV.FORMAT_16_BITS
	song.mix_rate = 22050
	song.data = bytes
	song.loop_mode = AudioStreamWAV.LOOP_FORWARD
	song.loop_end = samples
	return song
