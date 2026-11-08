class_name GaleAudio
extends Node

const SAMPLE_PATHS := {
	"fight_start": "res://assets/audio/sfx/fight_start_metal_punch.mp3",
	"match_start": "res://assets/audio/sfx/match_start_sword_unsheath.mp3",
	"countdown": "res://assets/audio/voice/countdown_three_two_one_fight.mp3",
	"victory": "res://assets/audio/voice/victory_male.mp3",
	"lose": "res://assets/audio/voice/you_lose.mp3",
	"kaze_light_1": "res://assets/audio/fighters/kaze/light_1_power_punch.mp3",
	"kaze_light_2": "res://assets/audio/fighters/kaze/light_2_punch_02.mp3",
	"kaze_light_3": "res://assets/audio/fighters/kaze/light_3_punch_impact_hit.mp3",
	"kaze_heavy": "res://assets/audio/fighters/kaze/heavy_wet_impact.mp3",
	"kaze_elemental": "res://assets/audio/fighters/kaze/elemental_iced_magic.mp3",
}
const MENU_MUSIC_PATH := "res://assets/audio/music/menu_deep_house_instrumental.mp3"
# Fight playlist: one track is drawn per match (never the same twice in a row).
const FIGHT_MUSIC_PATHS := [
	"res://assets/audio/music/techtheist-exdnbd-224289.mp3",
	"res://assets/audio/music/aberrantrealities-bid-or-stay-in-queue-303808.mp3",
	"res://assets/audio/music/aberrantrealities-deed-journey-dupe-303806.mp3",
	"res://assets/audio/music/u_199xuihodk-celestial-butterfly-496427.mp3",
]
# Recorded tracks are mastered louder than the synthesized arena loops.
const MENU_MUSIC_OFFSET_DB := -10.0
const ARENA_MUSIC_OFFSET_DB := -18.0
const STEP_GAIN_DB := -6.0
const HOVER_GAIN_DB := -9.0
# Sweeping the mouse over a list should not machine-gun the hover tick.
const HOVER_MIN_GAP_MS := 70
var last_hover_ms := -1000

var players: Array[AudioStreamPlayer] = []
var music: AudioStreamPlayer
var voice: AudioStreamPlayer
var tones: Dictionary = {}
var samples: Dictionary = {}
var songs: Dictionary = {}
var menu_music: AudioStream
var fight_music: Array[AudioStream] = []
var last_fight_track := -1
var cursor := 0
var sfx_volume := 0.85
var music_volume := 0.7

func _ready() -> void:
	for i in 8:
		var player := AudioStreamPlayer.new()
		add_child(player)
		players.append(player)
	music = AudioStreamPlayer.new()
	music.volume_db = -23
	add_child(music)
	# Announcer lines get their own player so they can pause with the match.
	voice = AudioStreamPlayer.new()
	add_child(voice)
	for key: String in SAMPLE_PATHS:
		var stream := load(SAMPLE_PATHS[key]) as AudioStream
		if stream != null:
			samples[key] = stream
	menu_music = load(MENU_MUSIC_PATH) as AudioStream
	if menu_music is AudioStreamMP3:
		(menu_music as AudioStreamMP3).loop = true
	for path: String in FIGHT_MUSIC_PATHS:
		var track := load(path) as AudioStream
		if track is AudioStreamMP3:
			(track as AudioStreamMP3).loop = true
			fight_music.append(track)
	for kind: String in ["hit", "heavy", "block", "parry", "clash", "ultimate", "ko", "click"]:
		var frequency: float = {"hit": 140.0, "heavy": 75.0, "block": 280.0, "parry": 880.0, "clash": 620.0, "ultimate": 110.0, "ko": 440.0, "click": 700.0}[kind]
		tones[kind] = synth(frequency, 0.32 if kind in ["ko", "ultimate"] else 0.1)
	tones["hover"] = soft_tick()
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

## Short, soft wooden tick for menu hover (two damped sines, no click at the start).
func soft_tick() -> AudioStreamWAV:
	var duration := 0.045
	var count := int(22050 * duration)
	var bytes := PackedByteArray()
	bytes.resize(count * 2)
	for i in count:
		var t := float(i) / 22050.0
		var envelope := minf(t / 0.003, 1.0) * exp(-t * 95.0)
		var sample := sin(TAU * 1180.0 * t) * 0.6 + sin(TAU * 1770.0 * t) * 0.25
		bytes.encode_s16(i * 2, int(sample * envelope * 7000))
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

## variant names a specific move sound (e.g. "light_2"); a recorded sample for
## fighter_variant wins over the synthesized signature for the event kind.
func play(kind: String, fighter: String = "", variant: String = "") -> void:
	if not fighter.is_empty() and not variant.is_empty() and samples.has(fighter+"_"+variant):
		_play_stream(samples[fighter+"_"+variant])
		return
	if samples.has(kind) and fighter.is_empty():
		_play_stream(samples[kind])
		return
	var aliases := {"bolt":"elemental","charged_bolt":"heavy","wave":"elemental","pulse":"elemental","stomp":"elemental","spikes":"elemental","stone":"elemental","rock_spike":"elemental","bomb":"heavy","vortex":"ultimate","fist":"ultimate","beam":"ultimate"}
	var category: String = aliases.get(kind,kind)
	if not fighter.is_empty() and tones.has(fighter+"_"+category):
		kind = fighter+"_"+category
	if not tones.has(kind):
		return
	if kind == "hover":
		var now := Time.get_ticks_msec()
		if now - last_hover_ms < HOVER_MIN_GAP_MS:
			return
		last_hover_ms = now
		_play_stream(tones[kind], HOVER_GAIN_DB)
		return
	_play_stream(tones[kind], STEP_GAIN_DB if category == "step" else 0.0)

func has_sample(key: String) -> bool:
	return samples.has(key)

func _play_stream(stream: AudioStream, gain_db: float = 0.0) -> void:
	var player := players[cursor]
	cursor = (cursor + 1) % players.size()
	player.stream = stream
	player.volume_db = linear_to_db(maxf(0.001,sfx_volume)) + gain_db
	player.play()

func play_voice(key: String, from_sec: float = 0.0) -> void:
	if not samples.has(key):
		return
	voice.stream = samples[key]
	voice.volume_db = linear_to_db(maxf(0.001,sfx_volume))
	voice.stream_paused = false
	voice.play(from_sec)

func pause_voice(paused: bool) -> void:
	voice.stream_paused = paused

func stop_voice() -> void:
	voice.stop()

func apply_settings(prefs: GalePreferences) -> void:
	sfx_volume = prefs.sfx_volume
	music_volume = prefs.music_volume
	_apply_music_volume()
	AudioServer.set_bus_mute(0, prefs.muted or prefs.volume <= 0)
	AudioServer.set_bus_volume_db(0, linear_to_db(maxf(0.001, prefs.volume)))

func set_music(stage: String, playing: bool) -> void:
	if not playing:
		music.stream_paused = true
		return
	if not fight_music.is_empty():
		# Keep the match's track through rounds, pauses and restarts.
		if music.stream not in fight_music:
			var pick := randi() % fight_music.size()
			if fight_music.size() > 1 and pick == last_fight_track:
				pick = (pick + 1 + randi() % (fight_music.size() - 1)) % fight_music.size()
			last_fight_track = pick
			music.stream = fight_music[pick]
			music.play()
		elif not music.playing:
			music.play()
		music.stream_paused = false
		_apply_music_volume()
		return
	# Fallback: the synthesized arena loop.
	if not songs.has(stage):
		songs[stage] = compose(stage)
	if music.stream != songs[stage]:
		music.stream = songs[stage]
		music.play()
	elif not music.playing:
		music.play()
	music.stream_paused = false
	_apply_music_volume()

func play_menu_music() -> void:
	if menu_music == null:
		music.stream_paused = true
		return
	if music.stream != menu_music:
		music.stream = menu_music
		music.play()
	elif not music.playing:
		music.play()
	music.stream_paused = false
	_apply_music_volume()

func _apply_music_volume() -> void:
	if not is_instance_valid(music):
		return
	# Recorded tracks (menu and fight playlist) are mastered louder than the synthesized loops.
	var offset := ARENA_MUSIC_OFFSET_DB if music.stream is AudioStreamWAV else MENU_MUSIC_OFFSET_DB
	music.volume_db = linear_to_db(maxf(0.001,music_volume)) + offset

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
