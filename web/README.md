# Gale Breaker: Elemental Clash

Jogo de luta web em React, TypeScript e Three.js, com quatro lutadores, três arenas, Arcade, Treino, Versus local, habilidades e áudio procedural.

Uma primeira versão nativa jogável para Godot está em [`../godot/`](../godot/README.md). Abra `godot/project.godot` no Godot 4.7+. A implementação web continua independente.

## Executar

Todos os comandos abaixo são executados dentro de `web/`.

Use uma versão de Node.js compatível com o Vite instalado.

```sh
npm install
npm run dev
```

Abra http://localhost:3000. Não é necessária uma chave Gemini nem um servidor de API. As fontes do Google Fonts usam internet, com fontes alternativas locais.

## Verificar e compilar

```sh
npm run lint
npm test
npm run build
npm run preview
```

`lint` verifica os tipos TypeScript. Os testes usam o test runner do Node via `tsx`. A pasta `web/dist` contém os arquivos estáticos para publicação.

## Controles padrão

| Ação | Jogador 1 | Jogador 2 |
|---|---|---|
| Mover | A / D | Setas esquerda / direita |
| Pular / agachar | W / S | Setas cima / baixo |
| Soco / golpe forte | J / K | Numpad 1 / 2 |
| Elemental / ultimate | L / U | Numpad 3 / 4 |
| Guarda / dash | Espaço / Shift esquerdo | Numpad 0 / Enter |
| Combo breaker | B | Numpad 5 |

Escape ou P pausa, R reinicia e M alterna o áudio. Esses atalhos são reservados. O remapeamento impede teclas duplicadas entre jogadores. Perder o foco pausa uma luta em andamento.

Configurações e habilidades são salvas automaticamente no armazenamento local deste navegador. Dados inválidos usam valores seguros; com armazenamento bloqueado, as alterações ficam apenas na sessão.

## Organização

- `src/App.tsx`: telas, entradas e integração dos sistemas.
- `src/game/combatEngine.ts`: regras e estado de combate.
- `src/game/fixedStep.ts`: simulação com passo fixo de 60 Hz.
- `src/game/fighters.ts`: lutadores, golpes, habilidades e arenas.
- `src/game/threeScene.ts` e `src/game/render/`: renderização e recursos gráficos.
- `src/game/preferences.ts`: persistência e validação de controles e habilidades.
- `src/game/soundEngine.ts`: síntese de efeitos e música.
- `src/components/`: interface e HUD.

Os testes verificam combate e regressões de persistência, temporização e descarte. Aparência, uso real de GPU e jogabilidade exigem validação no navegador.

## Dados compartilhados com o Godot

`npm run sync-godot-data` regenera `../godot/data/game_data.json` a partir de `src/game/fighters.ts` e `src/game/arcadeTower.ts`.
