# Plano de arte: Blender → Godot

> Registro do plano original. Estado atual em [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) e no GDD visual v0.10. Os marcos jogáveis locais foram entregues; os tempos futuros abaixo preservam o planejamento original.

## Direção aprovada e escopo

Usar `../concept-art/personagens-v2.png` como referência dos quatro personagens. A v3 simplificada fica arquivada e não orienta esta produção. Usar `menu-principal-v3.png` para o menu minimalista, `cenarios-v1.png` para as arenas e `hud-combate-v2.png` / `menu-pausa-v2.png` para linguagem de HUD e pausa, atualizando todos os retratos para as identidades v2.

Destino desta etapa: a versão Godot. A versão React/Three.js permanece independente. Este documento é um plano de execução; não implica que modelos Blender, rigs ou cenas finais já foram produzidos.

A v2 define silhueta, roupa, anatomia, materiais e personalidade. A implementação será uma adaptação para tempo real: detalhes pequenos podem virar textura/normal map, preservando o aspecto da concept. Não reproduzir cada peça com geometria nem interpretar a imagem como uma vista ortográfica perfeita.

## Ordem de produção e critérios de conclusão

| Marco | Trabalho | Entrega verificável |
|---|---|---|
| 1. Preparação | Confirmar Blender local, fixar versão de produção, organizar referências e medir a câmera do protótipo | Arquivo-base `.blend`, estrutura de pastas e teste simples de exportação/reimportação |
| 2. Pipeline com Kaze | Blockout, malha final, UV, materiais, rig e animações essenciais | Kaze jogável no Godot, sem depender da geometria procedural |
| 3. Primeira arena e apresentação | Santuário modular, iluminação, câmera e menu minimalista | Uma luta apresentável, com HUD e pausa funcionais |
| 4. Ignis | Produzir o segundo personagem completo e testar os dois juntos | Partida Kaze × Ignis com modelos, poses e ataques finais |
| 5. Elenco | Tophia e Volt no pipeline já validado | Quatro personagens com animações e paletas consistentes |
| 6. Arenas restantes | Forja vulcânica e bazar dourado | Três arenas no Arcade, Treino e Versus |
| 7. Acabamento | Efeitos, retratos, seleção, sons, otimização e regressões | Build de avaliação com os modos existentes e checklist concluído |

Cada marco inclui inspeção na câmera real do jogo. Não produzir os quatro personagens até o acabamento antes de validar o primeiro no Godot. Prazos devem ser estimados após o marco 2, que revela o custo real de modelagem, rig e animação; não há estimativa de calendário validada ainda.

## 1. Organização dos arquivos

Estrutura proposta, a criar durante a implementação:

```text
art-source/                         # fontes Blender fora da raiz importada pelo Godot
  characters/kaze/kaze.blend
  characters/ignis/ignis.blend
  characters/tophia/tophia.blend
  characters/volt/volt.blend
  environments/zephyr/zephyr.blend
  environments/forge/forge.blend
  environments/bazaar/bazaar.blend
  renders/portraits.blend
godot/
  assets/characters/<id>/<id>.glb
  assets/characters/<id>/textures/
  assets/environments/<stage>/
  assets/ui/portraits/
  assets/ui/icons/
  materials/characters/
  materials/environments/
  scenes/fighters/<id>.tscn
  scenes/stages/<stage>.tscn
  scenes/ui/main_menu.tscn
  scenes/ui/pause_menu.tscn
  scenes/ui/combat_hud.tscn
  resources/visuals/<id>.tres
```

Guardar fontes e exports separadamente. Usar GLB como entrega entre Blender e Godot; o projeto executável não dependerá de uma instalação de Blender. Versionar também configurações de importação, nomes de clipes e materiais. Fazer alterações de gameplay em cenas próprias que instanciam o GLB, para sobreviver à reimportação.

## 2. Modelagem dos personagens no Blender

### Etapas comuns

1. Colocar a v2 como referência e criar vistas coerentes de frente, lado e costas. Resolver volumes ocultos antes de detalhar.
2. Fazer blockout com a silhueta e a postura de cada personagem. Testar imediatamente na câmera de combate, com os dois lados e durante cruzamento.
3. Modelar formas principais e topologia de deformação: ombros, cotovelos, punhos, quadris, joelhos e tornozelos. Detalhar cabeça e mãos na proporção em que serão vistas.
4. Usar escultura/high-poly somente quando contribuir para rosto, dobras ou materiais. Fazer retopologia e bake dos detalhes úteis.
5. Criar UVs, texturas e materiais com paleta controlada. Evitar reproduzir iluminação dramática da prancha dentro da textura base.
6. Gerar LODs e conferir a malha triangulada exportada, especialmente em articulações e roupas.

### Tratamento de cada personagem

| Personagem | Identidade obrigatória | Solução de produção |
|---|---|---|
| Kaze | Monge alto, careca, ereto, jade e descalço | Corpo esguio, silhueta vertical, roupa com dobras grandes. Faixas e partes longas da túnica com poucos ossos auxiliares; pés com boa silhueta. Sem cabelo, headband ou equipamento ninja antigo. |
| Ignis | Brutamontes caipira, chapéu, sem camisa, corcunda, jeans e botas | Corpo largo e pesado, mãos grandes e postura animada com coluna/ombros curvados. Vermelho de sol na cabeça e braços, peito claro definido na textura. Chapéu preso a um osso; jeans e botas com poucos materiais. Sem a antiga armadura e manoplas de fogo. |
| Tophia | Armadura de pedra e postura dinâmica | Poucas famílias de placas grandes com geometria secundária controlada e relevo em normal map. Peças rígidas seguem ossos sem dobrar como borracha. Espaços de articulação nos ombros, quadris e joelhos. |
| Volt | Jovem adulto, armadura high-tech artesanal, loiro chamuscado | Placas reaproveitadas assimétricas, bateria e condutores com leitura clara. Marcas de construção manual em textura. Cabelo por mechas sólidas; fios com curvas convertidas ou malhas simples, pesos limitados e sem física individual. |

Orçamentos iniciais propostos, sujeitos a perfilamento: cerca de **20–45 mil triângulos por personagem em LOD0**, 2–4 superfícies/materiais principais, textura base de 2K e mapas adicionais apenas quando visíveis. É uma hipótese de produção para o enquadramento atual, não uma medição de desempenho. Conferir contagem real após exportar; manter mais detalhe no rosto/mãos do que na parte traseira pouco visível.

Não alterar automaticamente as hurtboxes para acompanhar a altura ou a largura das novas malhas. Primeiro ajustar escala visual ao combate atual; qualquer mudança de alcance/colisão deve ser deliberada e validada nos testes.

## 3. Rig e animações

### Rig

- Esqueleto humanoide com nomes e hierarquia compatíveis entre personagens, mas proporções próprias. Não forçar o corpo de Ignis a usar os mesmos comprimentos de Kaze.
- Root no centro do chão, pés na origem de altura; escala previsível entre personagens e cenário. Usar 1 unidade de cena como 1 metro no pipeline.
- Trabalhar com pose de repouso consistente. A corcunda de Ignis e a postura dinâmica de Tophia entram nas animações, sem deformação acidental ao exportar.
- Controles IK/FK para braços/pernas no Blender; exportar a deformação resultante dos ossos, com constraints necessárias baked. Exportar somente ossos de deformação quando apropriado.
- Ossos auxiliares limitados para túnica, faixa, chapéu e cabos. Começar com movimento animado; adicionar dinâmica apenas depois de validar custo e estabilidade.

### Biblioteca por personagem

Primeiro pacote: idle, andar para frente/trás, agachar, salto, queda, dash, jab/cross/finisher, lançador baixo, soco aéreo, forte, rasteira, elemental, ultimate, defesa alta/baixa, parry, reação de hit, knockdown, levantar e KO. Depois, vitória, seleção, breaker e variações de reações/transições.

Adotar nomes estáveis, por exemplo `idle`, `walk_forward`, `walk_back`, `jump_start`, `jump_air`, `jump_land`, `light_1`, `light_2`, `light_3`, `down_punch`, `air_punch`, `heavy`, `sweep`, `elemental`, `ultimate`, `guard_high`, `guard_low`, `parry`, `hit`, `knockdown`, `get_up`, `ko`, `victory`.

As animações de deslocamento serão **in-place**: posição, salto e knockback continuam controlados por `combat.gd`. Nenhum deslocamento duplicado por root motion. `fighter_view.gd` passará a traduzir o estado da simulação para o modelo importado, usando `AnimationPlayer` e, onde ajudar, blends com `AnimationTree`.

**O combate manda no tempo.** Para o jab base de Kaze, os dados atuais têm 4 frames de startup, 3 ativos e 7 de recovery. A animação precisa respeitar essas fases, inclusive quando uma habilidade reduz startup para 3. Planejar pontos/segmentos por fase e ajustar seu avanço ao contador da simulação. Hitstop e super freeze congelam a progressão do clipe de combate; cancels interrompem a ação na mesma fase em que a simulação permite. Blends de locomoção não podem atrasar o contato de um golpe.

Golpes usam os volumes lógicos existentes. Ossos de mãos/pés e pontos de VFX orientam os efeitos visuais; não passam a aplicar dano por eventos de animação. Validar também facing, troca de lado, recuperação aérea, rounds e reinício.

## 4. Exportação Blender → Godot

1. Padronizar a orientação antes do primeiro asset. Seguir a convenção de asset do Godot/glTF: frente em +Z no Godot; -Y no Blender. O modelo procedural atual usa frente local -Z: adaptar essa diferença em um pivô visual ou atualizar sua rotação no adaptador, sem girar o estado do combate.
2. Conferir transformações de malha/armature e pose de repouso antes do binding/export. Evitar corrigir escala de forma destrutiva em um rig já animado.
3. Usar materiais exportáveis como base, nomes de superfícies estáveis, UVs e texturas com caminhos previsíveis. Exportar malha, skin e animações em GLB.
4. Fazer bake das animações dependentes de controles/constraints. Verificar cada Action/clipe no GLB importado, não apenas na viewport do Blender.
5. Manter toon shading e efeitos específicos como materiais/shaders do Godot. Nós arbitrários de shader do Blender não serão tratados como materiais prontos para o motor.
6. Instanciar o GLB em uma cena de lutador própria e atribuir materiais externos/override de forma persistente. Reexportar uma mudança pequena e verificar que a cena, rig e clipes não perdem suas ligações.
7. Adicionar uma validação que detecta ausência de `Skeleton3D`, clipes obrigatórios, materiais, texturas, sockets e escala inválida.

O atual `toon.gdshader` só recebe cor uniforme. Ele precisará suportar textura base e máscaras apropriadas para reproduzir roupas, pele e materiais da v2. Preservar a queimadura de sol de Ignis ao aplicar paletas; usar máscaras de roupa/equipamento em vez de recolorir toda a textura.

## 5. Cenários: kits modulares e montagem

Produzir no Blender peças reutilizáveis; montar e iluminar a arena no Godot. Manter o plano de combate em Z=0, piso em Y=0 e os limites lógicos atuais em X ±9,5. Cenário e efeitos não devem esconder os pés, hurtboxes importantes ou bordas jogáveis.

| Arena | Kit inicial | Fundo e atmosfera | Objetos interativos |
|---|---|---|---|
| Zephyr Peak | Piso de pedra, degraus, torii, pilares, módulos de pagoda | Montanhas em camadas, nuvens, cerejeiras e bandeiras | Lanterna, caixa de bambu |
| Crimson Anvil | Piso de ferro/basalto, suportes, módulos de forja e correntes | Bigorna monumental, lava emissiva, fumaça e sol eclipsado | Braseiro e pilar de basalto |
| Golden Bazaar | Arcos, colunas, bancas, bordas de azulejo e tapetes | Abóbadas, lanternas e silhuetas distantes de mercadores | Lanterna de latão e caixa de especiarias |

Priorizar o santuário: piso e volumes principais → props → iluminação/câmera → detalhes. Montanhas e arquitetura distante recebem geometria mais simples ou cartões quando funcionarem na câmera. Correntes, pétalas, tecidos e cabos não exigem simulação física completa.

Criar cenas independentes para props intactos e quebrados. Seus nós visuais acompanham posição, vida e respawn de `sim.hazards`; a simulação existente continua responsável por dano e arremesso. O tamanho aparente do objeto precisa corresponder ao volume lógico.

Substituir a construção visual em `arena.gd` por instâncias de `scenes/stages/`, mantendo um contrato comum para piso, limites, efeitos e props. Começar com o renderer Compatibility atual e perfilá-lo antes de adotar recursos que exijam outra configuração. Iluminação, contraste e emissivos serão ajustados no motor.

## 6. Menu minimalista, pausa e HUD

### Menu principal

- Recriar a composição de `menu-principal-v3.png`: título discreto, lista textual à esquerda, pequeno indicador jade e paisagem de santuário sem personagens. Mostrar apenas Gale Breaker, sem o subtítulo Elemental Clash.
- Renderizar o cenário e Kaze como cena 3D com câmera própria de menu; idle calmo e movimento leve da túnica. Pode reutilizar o kit do santuário.
- Fazer título, botões e prompts com `Control` e tema nativo, sem gravar textos dentro da imagem de fundo. Texto pode mudar com idioma e remapeamento.
- Estados claros de normal, selecionado, hover e pressionado. Navegação por teclado e mouse; Escape fecha modais sem acionar controles atrás deles.

### Pausa

- Manter a hierarquia da concept de pausa, reduzindo ornamentos para acompanhar o novo menu minimalista.
- Congelar a simulação e manter a cena de combate escurecida ao fundo. Uma coluna de opções com Continuar selecionado.
- Expor apenas ações funcionais. A concept contém Lista de golpes: implementar essa tela antes de exibir a opção; usar dados reais dos golpes e binds atuais.
- Atualizar retratos: Kaze careca, Ignis cowboy, Tophia em pedra e Volt com tecnologia artesanal. Não reaproveitar retratos v1 de identidades antigas.

### HUD e seleção

- Barras, timer, rounds, combo, meter e prompts feitos como componentes editáveis. Ícones/frames podem ser imagens, mas números e rótulos são nativos.
- Renderizar retratos no Blender com enquadramento, luz e expressão padronizados; exportar imagens com alpha.
- Validar em 1280×720 e 1920×1080, além de uma proporção ultrawide. Manter áreas seguras e texto legível sobre as três arenas.
- Extrair progressivamente a criação de UI de `main.gd` para cenas e scripts próprios, preservando fluxo e handlers já testados.

## 7. Alterações concretas no código

| Arquivo/sistema atual | Mudança planejada |
|---|---|
| `scripts/fighter_view.gd` | Instanciar cena importada, controlar animações/facing/paletas e sockets; remover dependência de caixas como corpo final |
| `scripts/arena.gd` | Instanciar cenas de arena e props; câmeras de menu/combate; efeitos ligados aos eventos existentes |
| `scripts/main.gd` | Conectar cenas de menu, seleção, habilidades, HUD e pausa, em vez de construí-las integralmente por código |
| `scripts/toon.gdshader` | Suportar texturas/máscaras e linguagem visual da v2, com contraste calibrado no Godot |
| Novo catálogo visual | Recursos por lutador com cena, materiais, paletas, mapeamento de clipes e retratos |
| `data/game_data.json` | Manter stats, golpes e IDs estáveis; não usar os antigos campos de aparência como fonte do novo visual |
| `scripts/combat.gd` | Preservar a autoridade da simulação; expor progresso de fase se necessário para sincronizar animações |
| `tests/` | Acrescentar testes de importação, clipes, freeze, cancel, reset, paletas e troca de lado |

Separar o catálogo visual dos dados exportados pelo script `tools/sync-data.ts`, para uma futura sincronização não restaurar a aparência antiga. Os IDs de lutador e habilidades existentes permanecem válidos para os saves.

## 8. Validação antes de avançar cada entrega

- Comparação lado a lado com a v2 em três-quartos e na câmera real; silhueta reconhecível em tamanho pequeno.
- Deformação de ombros/quadris em guarda, agachamento, chute e queda; pés estáveis no chão e sem atravessar a roupa.
- Materiais após exportação, normal maps, transparências, máscaras de paleta e emissivos em todas as arenas.
- Animação sincronizada com startup/active/recovery e habilidades; nenhum frame extra introduzido por blends.
- Parry, hitstop, ultimate, freeze, cancels, combo breaker, KO, troca de round e reinício sem animações residuais.
- Reimportação do GLB preserva cenas próprias, materiais e referências.
- Capturas de menu, pausa, seleção e luta em duas resoluções; textos sem clipping e modais isolados.
- Manter as 53 verificações nativas como base, acrescentando novas verificações para os assets. Rodar uma build exportada quando os templates estiverem instalados.
- Objetivo inicial de desempenho: 60 FPS a 1080p no PC de referência. Medir CPU/GPU, draw calls, memória, sombras e overdraw com dois lutadores, arena e efeitos; os orçamentos de arte serão ajustados pelos resultados.

## Primeiro trabalho a executar

Criar `kaze.blend` com blockout, proporção, pés descalços e túnica jade da v2; exportar `kaze.glb`, instanciá-lo no Godot e comparar sua escala/facing com o oponente procedural. Só depois concluir UV, rig, materiais e animações. Esse primeiro ciclo valida o pipeline e evita detalhar um modelo que não funciona no enquadramento real.

## Referências técnicas consultadas

- Godot: [formatos 3D e glTF/Blender](https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/importing_3d_scenes/available_formats.html).
- Godot: [convenções de orientação, transformações e iluminação](https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/importing_3d_scenes/model_export_considerations.html).
- Blender: [exportador glTF 2.0, skinning e animações](https://docs.blender.org/manual/en/4.0/addons/import_export/scene_gltf2.html). As opções exatas deverão ser conferidas na versão local escolhida no marco 1.
