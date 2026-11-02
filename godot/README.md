# Gale Breaker - Godot v0.10

Build nativa de avaliação Windows x64, Godot 4.7.2, Compatibility/OpenGL. Abra `builds/GaleBreaker.exe` para jogar sem instalar Godot, Node ou navegador. Para editar, importe `project.godot` e pressione F5.

## Implementado

- Quatro lutadores skinned com 27 clips cada, dedos articulados, alvos de mãos/pés, canhão estabilizado, transições, reações, quedas, vitória e hitstop.
- 16 ataques principais e variantes contextuais. Projéteis viajam depois da animação; tornado, espinhos, pulso e feixe têm colisões próprias, avisos e respostas por bloqueio, parry, salto ou deslocamento.
- Três arenas Blender com objetos arremessáveis, quebra e reaparecimento. Eventos previsíveis com aviso de 1,5 segundo: rajada, erupção e carga em queda. Desativados no treino.
- Melhor de três, timer de 99 segundos, combos, cancelamentos, launcher, rasteira, guardas alta/baixa, chip sem KO, parry, breaker e proteção contra stunlock.
- Habilidades livres dentro de quatro pontos, sem bloqueios de tier/pré-requisitos; configurações independentes e salvas para P1/P2.
- Arcade com quatro etapas, chefe, três dificuldades, apresentação, continue salvo, retomada depois de fechar e encerramento.
- Versus local, tutorial de oito objetivos e laboratório de treino com dummy configurável, hitboxes, reposição e avanço de frame.
- Menu vazio Gale Breaker, pausa, HUD com ícones e lista ilustrada de golpes.
- Teclado remapeável, dois gamepads associados por dispositivo, navegação e reconexão.
- Música sintetizada por arena; impactos, poderes e passos por personagem. Volumes separados, flashes, shake e vibração configuráveis.

## Controles

| Ação | P1 | P2 | Controle |
|---|---|---|---|
| Mover | A / D | Setas esquerda / direita | Stick esquerdo / direcional |
| Pular / agachar | W / S | Setas cima / baixo | A / stick para baixo |
| Básico / forte | J / K | Numpad 1 / 2 | X / Y |
| Elemental / ultimate | L / U | Numpad 3 / 4 | B / RB |
| Defesa / dash | Espaço / Shift | Numpad 0 / Enter | LB / R3 |
| Breaker | B | Numpad 5 | L3 |

Escape/P pausa; Start no controle. R reinicia durante a luta; M alterna o áudio. F2 ou Back abre as ferramentas no treino. Botões seguem o padrão Xbox. Primeiro controle conectado = P1; segundo = P2. Teclado permanece disponível. Remapeamento rejeita conflitos e atalhos reservados.

Escolha modo, lutadores, paletas e arena, ajuste habilidades e inicie. Arcade usa os adversários/arenas da torre. Retomar Arcade aparece quando há campanha salva. O checkpoint salva a etapa, não o instante no meio do round.

Preferências: `user://preferences.cfg`. O nome interno do projeto foi preservado para manter compatibilidade com saves anteriores. Saves do navegador não são importados.

## Fontes e arquitetura

| Arquivo | Responsabilidade |
|---|---|
| `scripts/combat.gd` | Simulação fixa de 60 Hz, regras, rounds e IA |
| `scripts/move_rules.gd` | Parâmetros iniciais dos kits |
| `scripts/attack_entities.gd` | Projéteis, zonas e colisões |
| `scripts/arena_cycle.gd` | Avisos e perigos de arena |
| `scripts/attack_renderer.gd` | Apresentação das entidades reais |
| `scripts/fighter_view.gd` | Rig, clips, transições, paletas e sockets |
| `scripts/arena.gd` | Cenário, câmera, objetos e impactos |
| `scripts/main.gd` | Menus, HUD, treino e Arcade |
| `scripts/tutorial.gd` | Objetivos e dummy do tutorial |
| `scripts/preferences.gd` | Persistência, remapeamento e gamepads |
| `scripts/audio.gd` | Composição e síntese de áudio |

Fontes Blender em `../art-source/`; GLBs em `assets/`. O gerador `../art-source/tools/build_blender_assets.py` usa `character_polish.py` e `stage_polish.py`. Execute com Blender em background: `--python ../art-source/tools/build_blender_assets.py -- --characters-only` ou `--stages-only`; `--fighter volt` limita a um lutador. Reimporte no Godot após gerar.

Backups: `../art-source/revisions/`. Capturas reais: `../art-source/previews/index.html`. GDD: `../docs/gdd/index.html` e PDF v0.10. O projeto web permanece independente.

## Testes e capturas

Na raiz do projeto, PowerShell:

```powershell
./godot/tools/test.ps1 -GodotPath 'C:/caminho/Godot.exe'
```

158 verificações: 73 gerais, 42 de animação e 43 dos novos sistemas. O runner rejeita erros de script mesmo se o processo retornar zero. Persistência é testada em arquivos separados das preferências reais.

`tests/balance_sweep.gd` executa os 16 confrontos e grava `../art-source/previews/balance-report.json`. Todos terminaram. O teste encontra travamentos e problemas grosseiros; não comprova equilíbrio competitivo.

Capturas com GPU: `--audio-driver Dummy --script res://tests/capture_gdd_release.gd`. Poses/combos: `capture_models.gd -- --animate`. Ataques em combate: `capture_combat_polish.gd`. Modo headless não gera imagens válidas. `../art-source/tools/build_preview.py` monta a galeria.

## Exportação e limites

Preset Windows Desktop x64, PCK embutido, testes/ferramentas/logs excluídos. Com templates 4.7.2 instalados, exporte pelo editor ou use `--headless --path ./godot --export-release 'Windows Desktop'` e um caminho absoluto para o executável. A build foi gerada neste ambiente.

Validação visual em Windows, GTX 1060/OpenGL e 1280x720. Mapeamentos de gamepad foram testados por código; falta avaliação com controles físicos. Outras GPUs, sistemas e resoluções não foram certificados.

Esta entrega cobre o escopo jogável local do GDD. Modelos/animações são adaptações estilizadas para tempo real. Acabamento artístico, mix, conforto e balanceamento final exigem playtests. História, diálogos, público-alvo, distribuição e plataforma de lançamento continuam decisões abertas. Online/rollback, touch e destruição total não fazem parte desta build.
