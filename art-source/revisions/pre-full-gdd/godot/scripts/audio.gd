class_name GaleAudio
extends Node

var players: Array[AudioStreamPlayer] = []
var music: AudioStreamPlayer
var tones: Dictionary = {}
var songs: Dictionary = {}
var cursor := 0

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

func play(kind: String) -> void:
	if not tones.has(kind):
		return
	var player := players[cursor]
	cursor = (cursor + 1) % players.size()
	player.stream = tones[kind]
	player.play()

func apply_settings(prefs: GalePreferences) -> void:
	AudioServer.set_bus_mute(0, prefs.muted or prefs.volume <= 0)
	AudioServer.set_bus_volume_db(0, linear_to_db(maxf(0.001, prefs.volume)))

func set_music(stage: String, playing: bool) -> void:
	if not playing:
		music.stream_paused = true
		return
	if not songs.has(stage):
		var scales: Dictionary = {"zephyr_dojo": [164.81, 185.0, 196.0, 246.94, 261.63], "molten_forge": [146.83, 155.56, 185.0, 196.0, 220.0], "storm_market": [164.81, 174.61, 207.65, 220.0, 246.94]}
		var notes: Array = scales[stage]
		var bytes := PackedByteArray()
		for i in 16:
			bytes.append_array(synth(notes[[0, 2, 3, 1, 4, 3, 2, 1][i % 8]], 0.155).data)
		var song := AudioStreamWAV.new()
		song.format = AudioStreamWAV.FORMAT_16_BITS
		song.mix_rate = 22050
		song.data = bytes
		song.loop_mode = AudioStreamWAV.LOOP_FORWARD
		song.loop_end = bytes.size() / 2
		songs[stage] = song
	if music.stream != songs[stage]:
		music.stream = songs[stage]
		music.play()
	elif not music.playing:
		music.play()
	music.stream_paused = false
