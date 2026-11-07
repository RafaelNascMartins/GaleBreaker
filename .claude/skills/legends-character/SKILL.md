---
name: legends-character
description: Cria ou refaz um personagem do Gale Breaker no estilo Mega Man Legends (PS1) - peças rígidas low-poly, página de textura 256 com 15 cores e rosto por troca de expressões. Use ao modelar, texturizar ou revisar qualquer lutador ou roupa nesse estilo (Babuin/Kaze, Ignis, Tophia, Volt, Peixão, Executivo), ao gerar prompts de imagem para as referências deles, ou quando o usuário falar em "estilo Legends", "PS1", "peças", "página 256" ou "expressões no rosto".
---

# Personagem estilo Mega Man Legends

O piloto foi o Babuin (`kaze`), aprovado pelo usuário em 2026-11-04. A modelagem, a textura, o rosto, o esqueleto e a mão aberta foram validados no Blender. A exportação, o Godot e as animações ainda não (veja **Pendente**).

Referência real: `concept-art/referencias/Megaman.obj` e `Megaman.png`. São 486 triângulos em 18 peças, duas páginas de 256 com 15 cores cada, nenhuma luz (toda sombra é pintada) e um rosto com 24 expressões de cerca de 43×51 px.

## Construção: os modelos de referência mandam

Antes de modelar, leia o estudo `docs/estudos/legends-modelagem.md`. Ele foi aprovado pelo usuário em 2026-11-07, depois de muitas tentativas automáticas fracassadas na X12.

Os modelos de referência são `concept-art/referencias/`:
- `Megaman.obj`, `Roll_(Cutscene).obj`, `Old_Man.obj` e `Wily_the_Boatshop_Owner.obj`;
- os vídeos e anúncios do SuitNTie, em especial a Tifa (`tifa.mp4`) para lutadoras adultas.

Os modelos definem **como cada peça é construída**: quantas faces, onde ficam os cortes e o formato. A concept do personagem define **só tamanho e forma**.

1. **Molde primeiro.** Antes de cada peça, abra a peça equivalente da referência e conte faces e lados de seção. A peça nova fica nessa faixa.
2. **Cada triângulo tem um motivo:** silhueta, volume ou uma dobra que a textura precisa. O detalhe vai para a textura pixelada.
3. **Simetria exata.** Modele a metade esquerda e espelhe; os vértices do centro ficam em x = 0. Só as pontas do cabelo podem variar.
4. **Nenhum vértice com mais de ~8 triângulos em volta.** Nada de leque fechando uma peça num ponto só.
5. **Cabeça e cabelo numa peça só,** dividida pela pintura. O cabelo é a casca, com lâminas ou placas apoiadas no rosto. **Sem textura, o modelo já tem que ler** o que é cabelo, rosto, nariz e orelha.
6. **Rosto:**
   - linha do centro com ~7 vértices;
   - faixa dos olhos com 1 a 2 faces por lado, para a textura do olho não distorcer;
   - nariz saindo ~2 cm, com uma pontinha;
   - boca recuando, queixo em V;
   - orelha em placa.
7. **Corpo:**
   - ombro esférico de ~6 lados;
   - braço fino de 4 lados;
   - antebraço em cilindro de 6 lados (o braço afina e cresce de novo);
   - punho e luva como caixas grandes;
   - pernas retas, quase dois retângulos;
   - pés e botas em bloco.
8. **Juntas se sobrepõem** (ombro sobre o tronco, coxa dentro do quadril, pescoço dentro da cabeça), sem costura.
9. **Sombreamento suave,** com normais por vértice, como o Gouraud dos `.obj`. Aresta dura só onde a forma pede. O sombreamento chapado deixa cada corte aparecendo.
10. **Antes de mostrar ao usuário:**
    - meça a simetria;
    - meça o máximo de triângulos por vértice;
    - compare as faces de cada peça com o molde;
    - renderize sem textura, lado a lado com o Mega Man e a Tifa (a coleção `Ref_Legends` no Blender).

    Se algo falhar, não mostre.
11. **Nunca gere topologia automaticamente.** Casco visual, voxels, marching cubes, redução de malha, triangulação de cantos e "calota com espetos" geraram sopa de triângulos todas as vezes.
12. **Uma peça por vez,** cada uma aprovada pelo usuário: cabeça e cabelo, depois tronco, braço, perna.
13. **Nível de detalhe de herói para todos os lutadores.** É jogo de luta, então nenhum lutador fica no nível dos NPCs Old Man e Wily, que têm metade dos triângulos.

## Fluxo de modelagem (repetível, validado na X12 em 2026-11-07)

As ferramentas ficam em `art-source/tools/`:

| Arquivo | Para quê |
|---|---|
| `legends_kit.py` | Formas sem Blender: `named` (malha por vértices nomeados, metade esquerda espelhada; cabeça), `loft_sym` (peças centrais por seções de 5 pontos; peito, saia, gola), `loft` + `along`/`tilted`/`ring` (membros), `prism` (pescoço), `part`/`with_mirrors`. Tampas sempre em faixa, nunca leque; tudo orientado para fora. |
| `<nome>_<peça>.py` | Uma por grupo de peças (ex.: `x12_cabeca`, `x12_tronco`, `x12_braco`, `x12_perna`). **Só dados medidos e comentários dizendo de onde cada número saiu** (coluna/linha do recorte da concept) e qual peça da referência foi o molde. Cada um tem `parts()`. Assimetria proposital (franja) vai em `ASYMMETRIC = {peça: [coordenadas]}`. |
| `<nome>_modelo.py` | O personagem: `NAME`, `ID`, `SRC`, `HEIGHT`, `PREFIX`, `COLLECTION`, `PIECES`. |
| `legends_build.py <nome>_modelo` | Junta as peças, espelha as `_l`, **falha** se uma peça não for fechada, se um vértice tiver mais de 9 faces ou se uma peça central não for simétrica. Grava `<nome>_pecas.json` e imprime faces e triângulos por peça. |
| `legends_blender.py` (no Blender) | `load_refs()` (coleção `Ref_Legends`), `load_parts(json, coleção, prefixo)`, `compare(prefixo, pasta, região)` (cinza liso + arame, 4 vistas, personagem e Mega Man). |
| `legends_compare.py <nome>_modelo <pasta> <região>` | A folha: concept, modelo, arame do modelo, arame do Mega Man. |

Regiões: `corpo`, `cabeca`, `tronco`, `braco`, `perna`.

Ordem de trabalho, **uma peça por vez, aprovada pelo usuário antes da próxima**:
1. Medir: grade sobre os recortes da concept (frente e perfil) na região da peça. Abrir a peça equivalente do Mega Man ou da Tifa e anotar faces e lados de seção.
2. Escrever os dados no arquivo da peça, citando a medida.
3. `legends_build.py` até passar sem erro.
4. No Blender: `load_parts` e `compare` da região, depois `legends_compare.py`.
5. Olhar a folha: silhueta contra a concept, construção contra o Mega Man. Só então mostrar ao usuário, dizendo o que ainda difere.

**UV e página do corpo**, seguindo a seção 10 do estudo:

1. `legends_uv.py <nome>_modelo` gera a UV, sem smart project do Blender, a partir de três dados no módulo do personagem:
   - **`UV_METHOD`** diz como cada peça abre: `cyl` é o membro como cilindro aberto, com a costura atrás; `front_back` é o tronco, com frente e costas; `box` é a cabeça, o punho e a bota, por direção.
   - **`UV_OWN`** lista as peças da direita com detalhe próprio. As outras repetem a UV da esquerda.
   - **`UV_HIDDEN`** lista as faces escondidas, que recebem quase nenhum pixel.
   
   A página é de 256, com densidade de cerca de 1 px/cm (`UV_DENSITY`).
2. `legends_paint.py <nome>_modelo` pinta a página a partir de outros quatro dados:
   - **`PAINT`** diz, para cada (peça, ilha), se ela vem de um painel, de uma projeção da concept ou de um tom chapado. O rosto fica em pele lisa, porque os olhos vêm do atlas.
   - **`PANEL_CROP`** recorta cada painel na área da peça, deixando de fora o fundo escuro dele. O recorte automático errou, então os recortes são feitos à mão.
   - **`PANELS`** é a folha de painéis do personagem.
   - **`TONE_PANEL`** diz de onde vêm os tons chapados.
   
   Gera `<nome>_pagina_256_gerada.png` com 15 cores, mais uma prévia em 4×. A página que o modelo usa e que o usuário pinta no Blender, `<nome>_pagina_256.png`, só é criada se não existir e **nunca é sobrescrita**. Para aplicar uma página gerada nova, copie por cima de propósito, e só com o ok do usuário. O `load_parts` não recarrega uma imagem com pintura não salva.
3. `legends_face.py <nome>_modelo` faz o rosto:
   - a `FaceUV` da cabeça, com o quadrado do rosto em `FACE_BOX` no módulo;
   - o atlas `<nome>_rosto_atlas.png` (6×4 quadros de 42 px, 15 cores próprias), a partir de `EXPRESSIONS`. A pele do atlas é levada ao tom da pele da página pintada, para não aparecer emenda.

**Ordem dos comandos:** `legends_build` (recria o JSON sem UV) → `legends_uv` (transfere a página pintada para a UV nova e guarda cópia) → `legends_face` → `legends_paint` (só a página gerada; `legends_paint.py merge <módulo> peça:ilha` copia ilhas escolhidas para a página do usuário).

**UV deste projeto:** nunca há sobreposição. Cada peça, incluindo o lado direito, tem área própria, e as faces que cairiam umas sobre as outras viram ilhas separadas. A página é arrumada como o corpo visto de frente. É uma diferença em relação ao Mega Man, pedida pelo usuário para que pintar uma peça nunca pinte outra.

**Nunca chame `image.reload()` direto** sobre a página do usuário. Se `is_dirty` estiver ligado, salve a imagem antes. Num script avulso eu recarreguei a página e perdi pintura não salva.
5. **Esqueleto**, no Blender: `legends_rig.build('<nome>_modelo')`. Usa três dados do módulo:
   - `RIG_SOURCE`, o rig do lutador no jogo;
   - `JOINTS`, as juntas lidas nas peças;
   - `UNUSED_BONES`, os ossos que esse lutador não usa.

   Ele gera `<NAME>_Rig` e `<NAME>_Body` (uma malha com UVMap e FaceUV, cada vértice com peso 1 no osso da sua peça) e baixa os braços para a pose de descanso. Termina com a conferência: todo vértice em exatamente um osso.
   A X12 ficou com 20 ossos, e a saia acompanha o osso `hips`, rígida.
4. No Blender, `legends_blender.load_parts(json, coleção, prefixo, page=..., atlas=...)`. A cabeça ganha a propriedade `expressao`, de 0 a 23. O rosto só aparece no modo Rendered com EEVEE: o Workbench mostra apenas a página. A prévia usa luz `FLAT`, porque a sombra é pintada.

Ordem das peças: cabeça com cabelo, tronco (peito, gola, pescoço), braço (ombreira, braço, antebraço, faixa, punho), saia, pernas e botas.

**Orçamento:** os lutadores ficam com o detalhe de herói. A X12 tem 914 triângulos e o usuário não quer reduzir; o teto de 724 do Babuin não vale para personagens novos. O Babuin ainda é do fluxo antigo e será refeito neste fluxo depois.

## Regras do estilo

- **Proporção:** não é chibi. **Adultos seguem a Tifa: cabeça com ~18% da altura**, pernas longas, peso visual nas luvas e nas botas. O corpo tem cerca de 6 cabeças, com a cabeça em torno de 17% da altura. Cabeça, mãos e pés são grandes, e os membros são retos e finos. O estilo vem desse contraste.
  - "4,5 cabeças" saiu chibi e foi recusado.
  - "6,5 cabeças, esguio" saiu com 7,2 e também foi recusado.
  - A cabeça do Mega Man ocupa 25% da altura por causa do cabelo e da idade. Não use esse número como regra.
- **Peças:** cada peça é rígida e segue um único osso. As peças são fechadas, sem pontas abertas aparecendo. A peça de baixo entra de 1 a 3 cm dentro da de cima, para a junta dobrada não mostrar o interior.
- **Orçamento:** nível de herói; cada peça na faixa da peça equivalente da referência. O Babuin (724, fluxo antigo) não é mais o teto; a X12 ficou com 914.
  - Detalhes pintados, como olhos, vinco dos dedos e lapela, vão para a textura, não para a geometria.
- **Textura:** uma página de 256×256 com 15 cores, NEAREST, sem mapa de normais e com a sombra pintada.
  - No Blender, o material de prévia é emissão pura. Com luz de estúdio o modelo "parece plástico", e o usuário notou isso.
- **Rosto:** a frente da cabeça é pele lisa na página. O rosto vem de um atlas de expressões por uma segunda UV (`FaceUV`).
- **Peças trocáveis:** formas alternativas viram peças separadas presas ao mesmo osso, e só uma aparece por vez, como os braços e as mãos do Mega Man. A mão aberta é o exemplo.
  - Não use ossos de dedo. O punho é rígido e os dedos são pintados.
  - **A origem de toda peça trocável fica na cabeça do osso dela** (o pulso, no caso da mão), alinhada aos eixos do osso. A peça é presa ao osso com `parent_type = 'BONE'`, não por deformação.
  - A origem no centro do mundo faz a peça girar em torno do corpo inteiro. O usuário pegou esse erro.
- **Esqueleto:** o esqueleto humano básico tem os mesmos nomes em todos os lutadores, porque as animações e a IK por código usam esses nomes. Por cima dele, cada personagem só tem os ossos extras que usa.
  - Exemplos: o Babuin tem `robe_front`, `robe_back`, `robe_side` e `sash`; o Volt tem `cannon`.
  - Remova o resto com `prune_rig` (`UNUSED_BONES`). O Babuin ficou com 25 ossos.
  - O jogo ignora um osso de ponto de ancoragem que não existe.
- **Peso:** cada vértice segue um único osso. Abas de tecido, como as quinas do avental, vão para o osso de tecido delas (`skirt_weights`), para a perna não atravessar o pano no chute.
- **Conferir a IK de verdade:** não diga que o esqueleto está correto só porque girou uns ossos à mão. Rode `animate_fighter` no rig novo e meça, com o personagem atual como base:
  - a distância entre a mão e o alvo da guarda;
  - o pé no chão;
  - o alcance do braço;
  - os eixos dos ossos comparados com os do rig antigo.
- **Imagens coladas na conversa:** confira se elas existem como arquivo antes de usar. Uma imagem colada nem sempre chega à pasta; nesse caso, peça ao usuário para salvar com nome e versão.

## Fluxo

Os arquivos de cada personagem ficam em `art-source/characters/<id>/legends/`.

### 1. Referências (gerador de imagem)

São três imagens por roupa, salvas em `concept-art/characters/<nome>/`:

- **Turnaround:** frente, perfil e costas, em A-pose e mesma escala, com fundo cinza liso. O prompt pede "Mega Man Legends 1997, NORMAL anime proportions, ~6 heads, head ~17% of height, BIG blocky hands and feet, lean straight limbs, flat angular facets, ~15 colors, hard-edged painted shading, no gradients".
- **Expressões:** 24 quadros numa grade de 6×4. Cada quadro é só o rosto de frente, das sobrancelhas ao queixo, **preenchido de pele até a borda**. Não use fundo transparente: o gerador cria halo nas bordas. Olhos e boca ficam sempre na mesma posição. A ordem é:
  1. neutro;
  2. piscada;
  3. grito;
  4. dor;
  5. KO;
  6. vitória;
  7. esforço;
  8. foco;
  9. semicerrado;
  10. surpreso;
  11. raiva;
  12. confiante;
  13. risada;
  14. dor forte;
  15. nervoso;
  16. determinado;
  17. olhando à esquerda;
  18. olhando à direita;
  19. falando A;
  20. falando O;
  21. falando com a boca fechada;
  22. cansado;
  23. envergonhado;
  24. meditação.
- **Painéis de textura:** retângulos chapados para cada parte (túnica na frente e nas costas, avental, faixa, cinto, orbe, calça, faixa do punho, braço, antebraço, mão, punho, peito do pé, sola, topo da cabeça, lateral da cabeça e pescoço), com a sombra pintada em faixas duras.

### 2. Medir a concept

- Recorte as três vistas em `<id>_frente/perfil/costas.png`, todas na mesma escala, com os pés na mesma linha. A escala vem da altura do personagem dividida pela altura da figura em pixels.
- Rode `art-source/tools/concept_facets.py`, que usa o OpenCV:
  - ele achata as cores (mean shift), separa as faces (gradiente Lab com `EDGE = 4.0`) e as divide pelo watershed;
  - no fim, ajusta um polígono a cada face e grava `*_facetas.png` e `*_facetas.json`, com os cantos em metros.
- Se faltarem linhas (aconteceu na nuca, onde as faces têm tons parecidos), baixe o `EDGE` e o `sr` do mean shift.
- **Roupa escura (terno grafite do Executivo):** o traçador trata como contorno todo pixel com L < 85, e o pano inteiro some como "linha". Use `--dark 38` (só o contorno preto), `--edge 3.2 --sr 6` e `--min-area 150` contra as manchas de pintura. Gere a sobreposição com `--fade 0.2` para o desenho aparecer forte e dar para conferir se alguma linha faltou.
- Coloque as `*_facetas.png` como Empty de imagem no Blender:
  - frente em y = +0,6;
  - perfil girado 90°;
  - costas giradas 180°;
  - cada vista visível só pelo lado dela.

### 3. Modelar, peça por peça, nas três vistas

- O código fica em `legends_model.py` (`stack`, `tilted`, `poly`, `part`) e em `legends_<id>.py` (as medidas, com comentários dizendo de onde cada uma saiu).
- **A construção de cada peça vem do molde** (veja **Construção**, acima). As medidas vêm dos contornos da concept na frente, no perfil e nas costas.
  - Não monte anéis por fatias da silhueta. O usuário recusou duas vezes: a silhueta encostava, mas as faces e as linhas internas não batiam e sobravam polígonos.
- Membros inclinados levam anéis perpendiculares ao membro (`tilted`), não horizontais.
- Formas complexas, como a cabeça, viram malha explícita com os vértices nomeados (`legends_kit.named`).
- `part()` achata cada polígono (`planar_faces`) antes de triangular. Uma face não plana vira duas faces visíveis ou um sulco.
- Para o vértice de uma dobra ficar no plano da face grande, use `_onto_plane`.
- **Conferência:**
  - conte as faces visíveis de cada peça em cada vista (com `dissolve_limit` de 2°) e compare com a contagem da concept;
  - sobreponha o wireframe às `*_facetas.png` em cada região;
  - dobre joelho, cotovelo, punho e quadril e levante o braço, procurando oco ou peça furando;
  - confira se há bordas abertas e normais para dentro.
- Para encaixar o antebraço no cotovelo, copie o anel do cotovelo, reduza e leve até dentro da faixa do punho. Um anel diferente torce o antebraço, e encaixar fundo demais fura o bíceps e aparece como um risco.
- Para os olhos não dobrarem na quina, a face da frente da cabeça precisa ser larga o bastante para cobrir os cantos dos olhos.

### 4. Juntar, UV e textura

- `assemble()` junta tudo num mesh `<id>_Body`. Cada peça vira um grupo de vértices com peso 1 no seu osso, e a peça de origem fica gravada no atributo `part`. Depois disso vêm a UV automática (smart project com pack) e a `face_uv()`.
- `dump_triangles()` escreve `<id>_uv_tris.json`. Com ele, `legends_texture.py` faz o seguinte:
  - **Painéis:** detecta os 20 painéis da folha sozinho e mapeia cada peça no seu (classe `Mapper`). O usuário aprovou a frente da túnica e do avental assim.
  - Membros e faixas usam o painel cilíndrico dobrado na frente, para não aparecer emenda atrás.
  - Laterais da roupa usam a faixa lateral do painel da frente.
  - Pé: o topo usa o peito do pé, os dedos só ficam na face da frente e o calcanhar fica liso. Antes saíam dedos no calcanhar.
  - **Projeção:** o que não tem painel vem das três vistas, com teste de profundidade e sem usar o fundo nem o contorno.
  - **Paleta:** k-means com 15 cores sobre a concept e os painéis juntos.
  - **Borda das ilhas:** cada ilha recebe uma borda da própria cor (`distanceTransformWithLabels`), não `inpaint`.
  - **Redução:** para 256, com nearest.
  - **Atlas de rosto:** `face_atlas()` gera `<id>_rosto_atlas.png`, com 6×4 quadros de 42 px (252×168), paleta própria de 15 cores e a pele mais comum de cada quadro transparente.
- **Pintura à mão:** depois que o usuário pinta a página no Texture Paint, **nunca rode o gerador por cima dela**.
  - Salve a imagem (Image > Save). O gerador grava em `*_pagina_256_gerada.png`, nunca na página pintada.
  - Se precisar mudar a geometria, mova os vértices do `<id>_Body` direto, mantendo as UVs, e espelhe no `legends_<id>.py`.
  - Rodar `assemble()` refaz a UV e tira a pintura do lugar.

### Roupas (skins) sobre o personagem base

- **Troca de paleta** (Jade Dourado): gere uma página nova a partir da página pintada, mudando só a matiz das cores do pano (a pele fica). Nunca grave por cima da página pintada. No Godot, a paleta da roupa no catálogo (`visual_catalog.gd` e `resources/visuals/<id>.tres`) leva `"page"`, e o `fighter_view` troca a página ao escolher a roupa.
- **Roupa com peças novas** (Executivo, Peixão):
  - Meça a concept da roupa na mesma escala do personagem base. Confira que as juntas caem no mesmo lugar (ombro, cotovelo, punho, quadril, joelho, tornozelo). As peças novas seguem os **eixos dos ossos do base**, nunca juntas novas; assim o esqueleto, as animações e os hitboxes servem sem mudança.
  - Peças que a roupa não muda (cabeça, orelhas, pescoço, mãos, pés) são **copiadas do corpo base com as mesmas UVs**, para manter a pele e o rosto pintados à mão.
  - A página da roupa começa como cópia da página base. As ilhas das peças novas são empacotadas no espaço que era das peças de roupa do base e repintadas a partir do painel de texturas da roupa.
  - As peças novas são modeladas em A-pose e recebem a mesma transformação rígida que o base recebeu de A-pose para repouso (`arms_to_rest`), medida osso a osso no corpo base.
  - Todas as roupas ficam no mesmo GLB, com o mesmo esqueleto. O jogo mostra só as peças da roupa escolhida.

### 5. Esqueleto e peças trocáveis

- `fit_skeleton(arm, joints())` coloca os ossos nas juntas tiradas das peças: centro do deltoide, cotovelo, ponta da faixa do punho, punho, quadril sob a roupa, dobra do joelho, tornozelo e ponta do pé.
- `arms_to_rest` desce os braços da A-pose para a pose de descanso das animações. Só os vértices se movem; a UV e a pintura continuam no lugar. Guarde uma cópia oculta do corpo em A-pose (`<id>_Body_Apose`), porque as peças trocáveis são construídas nela.
- Depois, rode `prune_rig` e `skirt_weights`.
- **Mão aberta** (ou outra peça trocável):
  1. Faça um turnaround de 3 vistas só da peça.
  2. Recorte e rode `concept_facets.py <recortes> --mpp`.
  3. Meça os anéis nos cantos das faces. A mão não é simétrica, então meça o lado do polegar e o lado oposto separadamente.
  4. Construa com `add_open_hands`: a peça é montada na A-pose, levada à pose de descanso pelo movimento rígido do punho, com a origem no pulso e presa ao osso.
  - **Textura da peça:** página própria pequena (`legends_texture.py --hand`), com as 3 vistas lado a lado, 15 cores e o fundo preenchido com a cor da borda. Assim a página pintada do corpo não é tocada.
  - **Prévia no Blender:** um modificador Mask (`hide_fist_l/r`) esconde o punho.

### 6. Rosto

- `FACE_BOX` em metros é um quadrado do queixo até um pouco acima das sobrancelhas. Subir o quadrado sobe o rosto: 1 px do quadro equivale a cerca de 0,56 cm.
- A `FaceUV` vale para toda face da cabeça que esteja virada para a frente e **encoste** no quadrado. As outras recebem (-1, -1).
- Se a face precisar ter um vértice dentro do quadrado, as faces grandes e as bochechas ficam de fora e o rosto aparece cortado.
- Na prévia do Blender, o nó `face_cell` do material é controlado pela propriedade `expressao` do objeto. A linha do tempo vai de 1 a 24, uma expressão por quadro.

## Cuidados com o MCP do Blender

- O `look` em modo `angles`, com alvo pequeno e distância curta, corta a geometria e parece mostrar buracos. Confira pela vista (`bl_view` no `driver_namespace`) antes de concluir que algo está quebrado.
- O contorno laranja nas capturas é a seleção do Blender.
- Os scripts recarregam com `importlib.reload(legends_model); importlib.reload(legends_<id>)`, com `art-source/tools` no `sys.path`.

## Pendente (ainda não validado no piloto)

- Os scripts estão presos ao Babuin:
  - `legends_texture.py` e o modo padrão do `concept_facets.py` usam `kaze/legends` e o prefixo `babuin_`;
  - os nomes dos 20 painéis (`PANEL_NAMES`) e as medidas são do Babuin.
  
  O `concept_facets.py` já aceita recortes quaisquer. Ao fazer o segundo personagem, parametrize o resto por `<id>`.
- **Build:** o esqueleto, a limpeza dos ossos e as mãos abertas estão prontos em `legends_babuin.py`, mas ainda não foram ligados ao `build_blender_assets.py`. O Babuin hoje vive em `art-source/characters/kaze/legends/babuin_legends.blend`.
- **Troca de mão no jogo:** mostrar a mão aberta nos golpes de palma e na reverência, e o punho no resto.
- **Exportação e jogo:**
  - glTF para `godot/assets/characters/<id>/`;
  - página com NEAREST e sem mipmap;
  - `face.png` no formato do atlas novo, ajustando `face_grid` no `toon.gdshader` para 6×4 e o mapeamento das expressões em `fighter_view.gd`;
  - o shader toon só complementando a sombra pintada.
- **Animação:** as chaves de rotação já são quatérnios, e o teste de giro maior que 150° está em `visual_regression.gd`. Os alvos de IK em `character_polish.finalize_pose` estão em metros do corpo antigo e precisam passar a usar proporções do corpo.
- **Roupas:** Jade Dourado será troca de paleta. Peixão e Executivo (descalço) terão peças e página próprias, compartilhando o atlas de rosto.
- **Testes do orçamento:** triângulos, tamanho da textura e vértice com um único osso.
- **GDD:** registrar o estilo em `docs/gdd/`.
