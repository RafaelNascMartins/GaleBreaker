## Habilidades, pausa e HUD / GDD v0.9

`infografico-habilidades-v1.png` ilustra escolha do personagem, combinação de habilidades antes da luta, limite de quatro pontos do protótipo e os modos Arcade, Versus local e Treino. `menu-pausa-v2.png` e `hud-combate-v2.png` substituem as referências antigas na página 12, com Kaze careca e Ignis cowboy. São concepts, sem integração automática ao jogo. Feitas com ImageGen nativo; prompts em `prompts-gdd-paginas-10-12-v1.json`. Originais preservados.

## Retratos do GDD claro / v0.8

`tophia-retrato-gdd-v1.png` e `volt-retrato-gdd-v1.png` são retratos limpos de corpo inteiro para a diagramação do documento. Derivados das pranchas v5 com ImageGen nativo, preservam identidade e pose, removendo textos, paletas e vistas extras. Os originais v5 continuam como referência de produção. Prompts em `prompts-retratos-gdd-v1.json`.

## Menu principal atual: v3

`menu-principal-v3.png`: título apenas Gale Breaker, sem Elemental Clash e sem Kaze. Mantém cenário de santuário e navegação minimalista. Revisão feita com ImageGen nativo; prompt em `prompt-menu-minimalista-v3.json`. Capa e página de menu atualizadas no GDD v0.7. As versões anteriores permanecem como histórico.

# Gale Breaker — concept art v1

## Sequências de ataque

Revisão atual de Ignis: `attacks/ignis-j123-v2.png`, com J2 exibindo o braço esquerdo à frente e direito oculto atrás do tronco. O GDD visual v0.5 usa esta arte na página 7; versões anteriores foram preservadas.

`attacks/ignis-j123-v1.png` ilustra a sequência de Ignis enviada pelo usuário: braço direito, braço esquerdo e finalizador descendente com os dois braços. Incluído no GDD visual v0.4, página 7. A alternância foi revisada na arte; os prompts de geração/correção e o esboço original estão na mesma pasta. As regras ainda estão em aberto.

`attacks/kaze-j123-v1.png` ilustra o primeiro esboço enviado pelo usuário: palma frontal, movimento de duas palmas e chute frontal. Desenho original e prompt preservados na mesma pasta. Incluído no GDD visual v0.3, página 5. Os três quadros são golpes encadeados, não fases de um único golpe. A leitura de J2 como palmas em alturas diferentes é uma interpretação visual da seta do esboço.

## Ícones de ataque

`attack-icons/` contém 16 PNGs transparentes, quatro por personagem: básico, forte, elemental e ultimate. A pasta inclui galeria HTML, manifesto de arquivos, nomes propostos e prompts de ImageGen. Pacote completo em `attack-icons-v1.zip`. Os ícones ainda não foram aplicados ao HUD.

**Direção atual:** Kaze e Ignis da prancha **v2**; Tophia e Volt com designs **v4** e novas poses **v5**; menu principal minimalista **v2**. A simplificação v3 fica apenas como exploração arquivada. O plano Blender → Godot em `../godot/IMPLEMENTATION_PLAN.md` foi escrito antes das revisões v4/v5 e precisará incorporar esses designs quando a implementação começar.

## Poses v5

- `tophia-v5.png`: uma perna apoiada e outra recolhida para cima, sinal de paz com a mão blindada perto do olho, outra mão para baixo e sorriso. Design de pedra laranja da v4 preservado.
- `volt-v5.png`: agachado, apontando o canhão horizontalmente para o lado. Design de sucata e arma da v4 preservados.
- `prompts-poses-v5.json`: instruções de edição e referências usadas no ImageGen. Versões v4 mantidas.

## Revisões individuais v4 — Tophia e Volt

- `tophia-v4.png`: armadura completa de pedra laranja em estilo de cavaleiro, corpo e mãos cobertos, apenas a cabeça exposta com cabelo curto preto. A mobilidade da armadura é uma licença fantástica do jogo.
- `volt-v4.png`: armadura de sucata e lixo reaproveitado, cabelo loiro chamuscado, energia ciano e canhão de mão como arma. Inclui estudos externos da arma, sem projeto funcional.
- `prompts-tophia-volt-v4.json`: prompts usados com ImageGen e a prancha v2 como referência de estilo.

Estas alterações são apenas concept art; não alteram modelos, animações ou regras de combate. Kaze e Ignis permanecem na v2.

## Personagens v3 — simplificação para o jogo

`personagens-v3.png` simplifica as identidades da v2 em formas low-poly, cores chapadas, volumes grandes, menos peças e superfícies sem microdetalhes. Inclui poses principais, vistas frontal/traseira e paletas. O prompt está em `prompt-personagens-v3.json`, gerado com ImageGen usando a v2 como referência.

Diretrizes: Kaze com túnica e calça jade simples, careca e descalço; Ignis com chapéu, jeans, botas e contraste chapado entre braços vermelhos e peito claro; Tophia com poucas placas grandes de pedra; Volt com poucas placas improvisadas, uma bateria, cabo simples e cabelo loiro com pontas queimadas. A prancha é uma referência para modelagem e rigging, não uma malha 3D nem garantia de orçamento de polígonos.

## Ataques completos / GDD v0.6

`attacks/sequences.json` registra as 16 fichas ilustradas e os prompts. Os combos básicos de Kaze e Ignis foram mantidos; as outras 14 sequências foram desenvolvidas com ImageGen nativo a partir deles. Movimento, efeito, resposta e custo estão documentados como propostas. PDF e HTML atualizados em `docs/gdd`, com 31 páginas. Essas animações e regras novas ainda não foram implementadas no jogo.

## Revisão v2

- `personagens-v2.png`: redesign solicitado: Kaze monge alto, careca, ereto, verde-jade e descalço; Ignis brutamontes caipira corcunda, chapéu de cowboy, sem camisa, cabeça/braços vermelhos de sol e peito branco, jeans e botas; Tophia em armadura de pedra e postura dinâmica; Volt jovem adulto loiro com pontas chamuscadas e armadura high-tech artesanal.
- `menu-principal-v2.png`: navegação minimalista em texto, destaque discreto de jade, paisagem de santuário e novo Kaze.
- `prompts-redesign-v2.json` e `prompt-menu-minimalista-v2.json`: prompts usados com a ferramenta nativa ImageGen.

O último personagem descrito pelo usuário foi interpretado como Volt. As versões v1 foram preservadas. As imagens continuam sendo concepts; os personagens e menus do jogo ainda não foram modificados.

Pranchas de direção visual geradas com a ferramenta nativa ImageGen em 2 de novembro de 2026.

- `personagens-v1.png`: Kaze, Ignis, Tophia e Volt; poses, costas, equipamentos e paletas.
- `cenarios-v1.png`: Zephyr Peak Sanctuary, Crimson Anvil e Golden Bazaar; panoramas e estudos de objetos interativos.
- `ui-v1.png`: proposta de HUD, seleção de personagens e pausa/configurações. Os personagens foram ajustados usando a primeira prancha como referência de continuidade.
- `prompts-v1.json`: prompts de geração e da revisão da UI.
- `menu-principal-v1.png`: menu principal com os quatro personagens, navegação lateral e Arcade selecionado.
- `menu-pausa-v1.png`: pausa sobre o combate, com Continuar selecionado, opções de navegação e contexto da partida.
- `prompts-menus-v1.json`: prompts e referências usados nas duas concepts de menus, geradas com ImageGen.

Direção: luta elemental estilizada, cel shading, silhuetas legíveis e cores verde-esmeralda, vermelho, dourado e ciano. São referências de produção; não foram aplicadas automaticamente aos modelos, materiais ou menus do jogo. As pranchas são imagens raster, não arquivos com camadas, sprites recortados ou modelos 3D.
