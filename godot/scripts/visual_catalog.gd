class_name GaleVisualCatalog
extends Resource

@export var fighter_id: String = ""
@export var display_name: String = ""
@export var subtitle: String = ""
@export var element_label: String = ""
@export var accent_color: Color = Color("28654F")
@export var scene_path: String = ""
@export var glb_path: String = ""
@export var material_path: String = ""
@export var portrait_path: String = ""
@export var albedo_path: String = ""
@export var mask_path: String = ""
@export var normal_path: String = ""
@export var palettes: Array = []
@export var attack_icons: Dictionary = {}
@export var gdd_moves: Dictionary = {}
@export var clips: Dictionary = {}

const REQUIRED_CLIPS := [
	"idle", "walk_forward", "walk_back", "crouch",
	"jump_start", "jump_air", "jump_land", "dash",
	"light_1", "light_2", "light_3", "down_punch", "air_punch",
	"heavy", "sweep", "elemental", "ultimate",
	"guard_high", "guard_low", "parry",
	"hit", "knockdown", "get_up", "ko", "victory", "select", "breaker"
]

static func default_clip_map() -> Dictionary:
	var map := {}
	for clip: String in REQUIRED_CLIPS:
		map[clip] = clip
	return map

static func load_for(id: String) -> GaleVisualCatalog:
	var path := "res://resources/visuals/%s.tres" % id
	if ResourceLoader.exists(path):
		var res := load(path) as GaleVisualCatalog
		if res != null:
			return res
	return build_default(id)

static func build_default(id: String) -> GaleVisualCatalog:
	var cat := GaleVisualCatalog.new()
	cat.fighter_id = id
	cat.scene_path = "res://scenes/fighters/%s.tscn" % id
	cat.glb_path = "res://assets/characters/%s/%s.glb" % [id, id]
	cat.material_path = "res://materials/characters/%s.tres" % id
	cat.portrait_path = "res://assets/ui/portraits/%s.png" % id
	cat.albedo_path = "res://assets/characters/%s/textures/albedo.png" % id
	cat.mask_path = "res://assets/characters/%s/textures/mask.png" % id
	cat.normal_path = "res://assets/characters/%s/textures/normal.png" % id
	cat.clips = default_clip_map()
	cat.attack_icons = {
		"light": "res://assets/ui/icons/%s_light.png" % id,
		"heavy": "res://assets/ui/icons/%s_heavy.png" % id,
		"elemental": "res://assets/ui/icons/%s_elemental.png" % id,
		"ultimate": "res://assets/ui/icons/%s_ultimate.png" % id,
	}
	match id:
		"kaze":
			cat.display_name = "Babuin"
			cat.subtitle = "Monge do Vento Jade"
			cat.element_label = "VENTO"
			cat.accent_color = Color("28654F")
			cat.palettes = [
				{"name": "Jade Monástico", "primary": "#357A57", "secondary": "#C6D1A8", "accent": "#4AD69D"},
				{"name": "Jade Dourado", "primary": "#8A6A12", "secondary": "#F2D27A", "accent": "#FACC15", "page": "res://assets/characters/kaze/textures/page_dourado.png"},
				{"name": "Peixão", "primary": "#2E8C7E", "secondary": "#E9DDB8", "accent": "#F08A7A", "page": "res://assets/characters/kaze/textures/page_peixao.png", "hand": "res://assets/characters/kaze/textures/hand_peixao.png", "body": "kaze_PeixeBody"},
				{"name": "Executivo", "primary": "#2B2B2E", "secondary": "#F2F2F2", "accent": "#D62828", "page": "res://assets/characters/kaze/textures/page_executivo.png", "body": "kaze_ExecBody"},
			]
			cat.gdd_moves = {
				"light": {"name": "Palma de Jade", "sequence": "J1 palma frontal; J2 duas palmas verticais; J3 chute frontal.", "behavior": "Curto alcance. Três golpes encadeados; J3 afasta o alvo.", "counter": "Bloquear a sequência ou punir o chute se errar."},
				"heavy": {"name": "Chute do Vendaval", "sequence": "Recolhe a perna com giro do quadril; chute lateral amplo com arco jade.", "behavior": "Arco médio à frente. Impacto único com empurrão forte.", "counter": "Recuar na preparação e punir a recuperação."},
				"elemental": {"name": "Rajada de Vento", "sequence": "Reúne ar entre as mãos; lança ambas as palmas em onda horizontal.", "behavior": "Onda de vento com deslocamento visível que arremessa objetos da arena.", "counter": "Pular a onda ou bloquear; aproximar na recuperação."},
				"ultimate": {"name": "Tufão Celestial", "sequence": "Abaixa a base; ergue os braços em espiral; tornado vertical explode à frente.", "behavior": "Área fixa adiante com vórtice ascendente e expulsão final.", "counter": "Sair da área sinalizada antes da formação do tornado."},
			}
		"ignis":
			cat.display_name = "Dale"
			cat.subtitle = "Brutamontes do Sol escaldante"
			cat.element_label = "FOGO"
			cat.accent_color = Color("A54332")
			cat.palettes = [
				{"name": "Sol do Meio-Dia", "primary": "#5B7088", "secondary": "#5C4028", "accent": "#F97316"},
				{"name": "Preto", "primary": "#1F1F22", "secondary": "#2B2B2E", "accent": "#FACC15", "page": "res://assets/characters/ignis/textures/page_preto.png"},
				{"name": "Coronel", "primary": "#EDE4D3", "secondary": "#4A2E1E", "accent": "#E9DDB8", "page": "res://assets/characters/ignis/textures/page_coronel.png", "body": "ignis_CoronelBody"},
				{"name": "Men's Physique", "primary": "#C8692E", "secondary": "#1C1C1C", "accent": "#F08A3A", "page": "res://assets/characters/ignis/textures/page_physique.png", "body": "ignis_PhysiqueBody", "face": "res://assets/characters/ignis/textures/face_physique.png"},
			]
			cat.gdd_moves = {
				"light": {"name": "Soco de Roça", "sequence": "J1 direito; J2 esquerdo com direito oculto; J3 marretada descendente com os dois braços.", "behavior": "Curto alcance. Três entradas pesadas; o último contato empurra para baixo.", "counter": "Bloquear ou recuar; a marretada expõe recuperação maior."},
				"heavy": {"name": "Marreta Caipira", "sequence": "Trava os pés e junta os punhos; ergue os braços; desce a marretada no chão.", "behavior": "Golpe único descendente com alto impacto e super armor.", "counter": "Sair do alcance; punir quando os punhos chegam ao chão."},
				"elemental": {"name": "Pisada da Fornalha", "sequence": "Ergue o joelho concentrando calor na bota; pisa espalhando fogo e poeira.", "behavior": "Explosão baixa próxima ao pé que afasta oponentes e objetos.", "counter": "Pular na preparação ou manter distância do círculo de calor."},
				"ultimate": {"name": "Fúria do Meio-Dia", "sequence": "Ajusta o chapéu e agacha; avança com o ombro em explosão solar.", "behavior": "Investida frontal comprometida com impacto explosivo de calor.", "counter": "Saltar sobre a investida ou evitar a linha sinalizada."},
			}
		"tophia":
			cat.display_name = "Tophia"
			cat.subtitle = "Cavaleira de Arenito"
			cat.element_label = "TERRA"
			cat.accent_color = Color("98531F")
			cat.palettes = [
				{"name": "Arenito Laranja", "primary": "#C86428", "secondary": "#8C421A", "accent": "#FFA834"},
				{"name": "Geodo Ametista", "primary": "#7E22CE", "secondary": "#4C1D95", "accent": "#38BDF8"},
				{"name": "Rocha Rubi", "primary": "#BE123C", "secondary": "#4C0519", "accent": "#FDE047"},
				{"name": "Monólito de Mármore", "primary": "#CBD5E1", "secondary": "#475569", "accent": "#10B981"},
			]
			cat.gdd_moves = {
				"light": {"name": "Punho de Arenito", "sequence": "J1 soco reto direito; J2 cruzado esquerdo; J3 pisão frontal com bota de pedra.", "behavior": "Três entradas; pisão final gera poeira e empurrão curto.", "counter": "Bloquear os socos; recuar para fazer o pisão errar."},
				"heavy": {"name": "Martelo de Pedra", "sequence": "Recolhe o punho no ombro; gira o tronco; golpeia de cima para baixo.", "behavior": "Golpe único em arco pesado. Armadura é visual, sem invencibilidade automática.", "counter": "Recuar ou punir o arco quando errar."},
				"elemental": {"name": "Erupção Rochosa", "sequence": "Encosta a manopla no chão; fissura laranja avança; três espinhos surgem.", "behavior": "Faixa frontal fixa com aviso no piso e arremesso de objetos.", "counter": "Saltar a sequência ou sair da faixa anunciada."},
				"ultimate": {"name": "Colosso de Terra", "sequence": "Finca os pés e cruza os braços; placas flutuam; projeta punho colossal à frente.", "behavior": "Ataque amplo frontal de grande alcance com punho de pedra projetado.", "counter": "Sair da frente durante a formação; punir a recuperação."},
			}
		"volt":
			cat.display_name = "Volt"
			cat.subtitle = "Inventor da Sucata Elétrica"
			cat.element_label = "RAIO"
			cat.accent_color = Color("206A7C")
			cat.palettes = [
				{"name": "Sucata Ciano", "primary": "#D49B38", "secondary": "#435C6E", "accent": "#22E4FF"},
				{"name": "Sobrecarga Neon", "primary": "#DB2777", "secondary": "#31102F", "accent": "#38BDF8"},
				{"name": "Curto Carmesim", "primary": "#DC2626", "secondary": "#18181B", "accent": "#FDE047"},
				{"name": "Bateria Tóxica", "primary": "#16A34A", "secondary": "#14532D", "accent": "#FACC15"},
			]
			cat.gdd_moves = {
				"light": {"name": "Tiro de Sucata", "sequence": "J1 tiro em pé; J2 tiro agachado baixo; J3 disparo curto com as duas mãos.", "behavior": "Três tiros visíveis; J2 muda a altura do disparo. Sem munição ou calor.", "counter": "Bloquear ou saltar conforme a altura; aproximar entre disparos."},
				"heavy": {"name": "Disparo Carregado", "sequence": "Firma o canhão com as duas mãos; acumula esfera ciano; dispara com recuo.", "behavior": "Carga fixa e projétil grande de maior impacto, sem carga infinita.", "counter": "Pressionar durante a carga ou saltar o projétil."},
				"elemental": {"name": "Curto-Circuito", "sequence": "Abaixa o canhão e aciona a bateria no peito; pulso elétrico circular expande.", "behavior": "Área curta ao redor que interrompe aproximação e arremessa objetos.", "counter": "Recuar diante do aviso elétrico; atacar após o pulso."},
				"ultimate": {"name": "Sobrecarga Total", "sequence": "Ancora os pés e conecta a bateria ao canhão; dispara feixe horizontal enorme.", "behavior": "Feixe frontal em linha fixa com recuo extremo.", "counter": "Saltar antes do feixe ou sair da linha durante o aviso."},
			}
	return cat
