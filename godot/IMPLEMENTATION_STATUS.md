# Implementação do GDD - build v0.10

Escopo: Godot local. O projeto web permanece independente.

- [x] Backups anteriores em `../art-source/revisions/`.
- [x] 16 ataques principais, entidades independentes, avisos, colisões, respostas e variantes contextuais.
- [x] Gamepad por dispositivo, reconexão, navegação e loadouts livres separados de P1/P2.
- [x] Tutorial de oito objetivos com os quatro personagens; laboratório de treino.
- [x] Arcade com apresentação, dificuldade, continue salvo, retomada e encerramento.
- [x] Áudio por personagem, música por arena e opções de acessibilidade.
- [x] Quatro modelos skinned com dedos e 27 clips cada; transições, apoio, hitstop, queda e vitória.
- [x] Três arenas Blender refinadas, objetos e ciclos anunciados de perigo.
- [x] Parâmetros iniciais de combate; 158 verificações e 16 confrontos automáticos concluídos.
- [x] Capturas reais OpenGL, galeria, documentação e GDD visual v0.10.
- [x] Executável Windows x64 com recursos embutidos em `builds/GaleBreaker.exe`.

## Evidências

`tools/test.ps1`: 73 verificações gerais, 42 de animação e 43 dos novos sistemas.
`tests/balance_sweep.gd`: os 16 confrontos terminam dentro de 24.000 ticks.
`tests/capture_gdd_release.gd`: menus, três arenas e avisos, tutorial, treino, opções e Arcade.
`tests/capture_models.gd` e `capture_combat_polish.gd`: poses, combos e ataques no renderer real.
`../art-source/previews/`: capturas e relatórios de assets/confrontos.

O executável exportado inicializou com renderer OpenGL e áudio, sem erros nos logs. O teste `release_smoke.gd`, executado pelo Godot sobre o pack embutido do executável, carregou as 12 combinações de arena/personagem, executou 48 ataques e abriu os menus nativos. A captura de janela pelo helper do Windows falhou por timeout; essa navegação manual não foi confirmada. Relatório consolidado: `builds/validation.json`.

## Validação humana pendente

Dano, alcance, ritmo e custos são valores iniciais. Testes de código não comprovam diversão, conforto, fidelidade artística final, mixagem ou balanceamento competitivo.

Gamepad requer teste físico. A validação visual ocorreu em Windows, GTX 1060/OpenGL e 1280x720. Outras configurações precisam de avaliação. História, diálogos, público, preço e escopo comercial de lançamento continuam em aberto no GDD.
