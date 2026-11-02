# Gale Breaker

O documento principal é o **GDD visual v0.10**, em [PDF](Gale_Breaker_GDD_Visual_v0_10.pdf) e [HTML editável](index.html). Inclui as 16 fichas de ataques e capturas da build nativa. Os quatro kits, três arenas, tutorial, controles, treino e Arcade foram implementados no Godot. Veja [status e limites da build](../../godot/IMPLEMENTATION_STATUS.md). O texto abaixo preserva o rascunho histórico v0.1; suas pendências foram superadas onde o status atual indicar.

Game Design Document — rascunho v0.1

## 1. Como ler este documento

Este GDD consolida decisões do usuário, comportamento do protótipo e propostas ainda em discussão. **Definido** significa decisão expressa; **protótipo** significa algo que existe no código, sujeito a revisão; **proposta** e **pendente** não são requisitos aprovados. As regras finais não devem ser inferidas apenas dos ícones ou das concepts.

Destino atual da produção: Godot, com assets produzidos no Blender. A versão web permanece como protótipo e referência. Plano técnico complementar: [Blender → Godot](../../godot/IMPLEMENTATION_PLAN.md).

## 2. Visão do jogo

**Definido:** combate caótico e exagerado, com foco em diversão. O jogador escolhe habilidades livremente antes da luta, respeitando um limite de pontos.

**Proposta de apresentação:** um jogo de luta elemental em que quatro figuras improváveis se enfrentam em arenas interativas, combinando golpes exagerados, poderes e objetos arremessáveis. O espetáculo e as situações inesperadas são parte da diversão.

**Base do protótipo:** luta 1 contra 1 com personagens 3D em um plano lateral, Arcade, Treino e Versus local. A confirmação do escopo de lançamento ainda está pendente.

### Pilares propostos a partir da direção escolhida

- **Bagunça legível:** efeitos e eventos exagerados, mas com pistas suficientes para o jogador entender o que o acertou e como reagir.
- **Personagens com personalidade:** aparência, movimento e golpes devem diferenciar o monge, o caipira, a cavaleira de pedra e o inventor da sucata.
- **Diversão com poucos comandos:** quatro ações principais, movimento e defesa, com combinações contextuais acessíveis.
- **Arena como parte da luta:** objetos e eventos devem criar oportunidades e situações engraçadas, sem tornar o resultado puramente aleatório.
- **Experimentação livre:** habilidades são escolhas de configuração, não uma vantagem obtida por grind.

Não está decidido que o jogo terá física de ragdoll, destruição total, dano entre espectadores, quedas para fora da arena ou eventos aleatórios. Esses recursos precisam ser avaliados individualmente.

## 3. Público, plataformas e limites de escopo

| Item | Situação |
|---|---|
| Tom do combate | Definido: caótico, exagerado e divertido |
| Público-alvo e faixa etária pretendida | Pendente |
| Plataforma inicial | Protótipo validado em PC/Windows; lançamento pendente |
| Formato 1 contra 1 / plano lateral | Base atual do protótipo; confirmar como escopo final |
| Controles | Teclado com remapeamento no protótipo; suporte e prioridade de gamepad pendentes |
| Multiplayer | Versus local no protótipo; online não implementado e fora da proposta inicial de MVP |
| Modelo de distribuição/preço | Pendente; não necessário para fechar o primeiro teste de combate |
| Duração desejada de uma luta/campanha | Pendente |

## 4. Loop de jogo

**Fluxo proposto:** menu → modo → personagem → habilidades dentro do orçamento → arena/adversário → luta → resultado → revanche, próxima etapa ou seleção.

**Dentro da luta:** aproximar/posicionar → atacar ou defender → aproveitar abertura, combo ou objeto → responder ao contra-ataque → vencer rounds e partida.

**Definido sobre habilidades:** seleção livre antes da luta e limite de pontos. O protótipo usa **4 pontos**, mas o orçamento final e os custos ainda devem ser ajustados. Não há decisão de criar XP, moeda, loot ou desbloqueio obrigatório para obter esses modificadores. Salvar a configuração escolhida não equivale a criar progressão de poder.

**Pendente:** P2 terá sua própria configuração de habilidades? Haverá presets para partida rápida? A IA usará as mesmas restrições ou chefes terão exceções explícitas?

## 5. Personagens e direção visual

| Personagem | Direção visual atual | Papel de gameplay a validar |
|---|---|---|
| Kaze | V2: monge alto, careca, ereto, roupa jade e pés descalços | Mobilidade e controle de vento; decidir se será o personagem mais simples de aprender |
| Ignis | V2: caipira brutamontes, corcunda, cowboy, sem camisa, braços/cabeça vermelhos de sol e peito claro, jeans e botas | Força bruta e impacto; definir relação entre fogo, calor do sol e humor rural |
| Tophia | V4/V5: cavaleira com corpo inteiro em pedra laranja, cabeça exposta, cabelo curto preto; pose sorridente com sinal de paz | Peso e domínio de espaço; decidir se a armadura tem efeito mecânico ou apenas visual |
| Volt | V4/V5: jovem loiro chamuscado, armadura de sucata/lixo e canhão de mão; pose agachada mirando para o lado | Ataques com canhão e eletricidade; decidir funcionamento dos disparos e oportunidades de punição |

A v3 simplificada não é a referência escolhida. Poses de concept não obrigam o personagem a permanecer nessa posição durante o combate. A armadura integral de Tophia pode se mover por licença fantástica; não precisa de justificativa física realista.

Referências: [personagens v2](../../concept-art/personagens-v2.png), [Tophia v5](../../concept-art/tophia-v5.png), [Volt v5](../../concept-art/volt-v5.png).

### O que falta na ficha de cada lutador

Personalidade e motivação; estilo de movimento; força e fraqueza; dificuldade; alcance; vida e mobilidade relativas; golpes; custo/ganho de energia; habilidades disponíveis; interações especiais com objetos; animações e sons que comunicam cada ação.

Os atributos atuais foram herdados de versões anteriores dos personagens. Não considerar os kits antigos automaticamente aprovados para os novos designs.

## 6. Combate

### Base existente no protótipo

Movimento lateral, pulo, agachamento, dash, defesa alta/baixa, parry, combo breaker, cadeia de três socos, lançador, ataque aéreo, forte/rasteira, elemental e ultimate. Há hitstop, cancelamentos, juggle, wall bounce, proteção contra stunlock, vida e medidor elemental.

Quatro comandos principais correspondem a básico, forte, elemental e ultimate. Existem variantes contextuais, portanto **16 ícones principais não significam necessariamente apenas 16 golpes em todo o jogo**.

O protótipo usa melhor de três, timer de 99 segundos e ultimate com custo de 50 de um medidor de 100. Essas regras são pontos de partida, não decisões finais do GDD.

### Decisões prioritárias

1. Acessibilidade: manter todos os comandos auxiliares ou simplificar defesa, parry, dash e breaker?
2. Combos: quão longos, quão fáceis de executar e quanta oportunidade de escapar?
3. Exagero: quais lançamentos, pancadas, quicadas, efeitos e consequências produzem a diversão desejada?
4. Energia: como é ganha, qual é o custo das ações, o que permanece entre rounds e se o ultimate pode ser bloqueado/interrompido?
5. Diferenças de personagem: determinar fraquezas e respostas, mesmo com foco casual e caótico.
6. Resultado: confirmar rounds, timer, empate, KO duplo e condições especiais de vitória.

### Questões específicas de Volt

O canhão precisa de uma regra concreta: projétil com tempo de viagem ou impacto instantâneo? Disparo simples, carregado e ultimate têm diferenças de alcance e área? Usa munição, recarga, calor, energia ou apenas recuperação? É possível defender, desviar, rebater ou destruir um tiro? Há limite de projéteis simultâneos? O ataque básico continua tendo variante aérea/agachada?

### Questões específicas de Tophia

A pedra aumenta resistência, concede super armor em certos golpes ou apenas define a aparência? Ela pode ser rápida apesar da massa? Há dano/rachadura visual? A armadura pode quebrar ou se recompor, e isso muda a luta? Essas possibilidades ainda não foram aprovadas.

## 7. Kit principal e ícones

### Primeiro esboço de ataque de Kaze

Sequência desenhada pelo usuário e ilustrada em `concept-art/attacks/kaze-j123-v1.png`: **J1** palma frontal, **J2** movimento de duas palmas (a seta vertical foi interpretada como mãos em alturas diferentes), **J3** chute frontal. São três golpes encadeados. As fases de preparação/execução/impacto de cada um, dano, alcance, timing e reação do alvo continuam em aberto. A versão visual dedica uma página a essa sequência e preserva o esboço original. Nenhuma regra de combate foi alterada.

### Primeiro esboço de ataque de Ignis

Sequência desenhada pelo usuário e ilustrada em `concept-art/attacks/ignis-j123-v2.png`: **J1** braço direito, **J2** braço esquerdo à frente e direito escondido atrás do tronco; **J3** finalizador descendente. O finalizador foi representado com os dois braços acima da cabeça e trajetória para baixo. A marca no chão comunica a direção do golpe; não define automaticamente tremor, dano em área ou outra regra. Dano, alcance, timing e reação do alvo continuam em aberto. Incluído na página 7 do GDD visual v0.9. Nenhuma regra de combate foi alterada.

Os 16 ícones estão produzidos. Os nomes abaixo foram propostos para identificar a arte e ainda não substituem oficialmente os nomes e efeitos dos golpes no código.

| Lutador | Básico | Forte | Elemental | Ultimate |
|---|---|---|---|---|
| Kaze | Palma de Jade | Chute do Vendaval | Rajada de Vento | Tufão Celestial |
| Ignis | Soco de Roça | Marreta Caipira | Pisada da Fornalha | Fúria do Meio-Dia |
| Tophia | Punho de Arenito | Martelo de Pedra | Erupção Rochosa | Colosso de Terra |
| Volt | Tiro de Sucata | Disparo Carregado | Curto-Circuito | Sobrecarga Total |

Para fechar cada golpe, preencher: intenção; comando e variantes; descrição visual; alcance/área; dano; startup/ativo/recuperação; deslocamento; reação/lançamento; defesa e contra-jogo; custo/ganho de energia; interação com arena; requisitos de animação/VFX/SFX. Começar pelo comportamento e depois ajustar números nos testes.

Arte: [galeria dos ícones](../../concept-art/attack-icons/index.html). Novos efeitos sugeridos pelos ícones ainda precisam ser implementados e testados.

## 8. Habilidades antes da luta

**Definido:** escolhas livres com orçamento de pontos. **Protótipo:** quatro pontos, seis nós por lutador, níveis com pré-requisito e modificadores de atributos.

**Pendente:** lista final por personagem, custos, pré-requisitos, possibilidade de efeitos novos em vez de apenas bônus numéricos, configuração de P2, restrições de chefes e momento exato de travar as escolhas.

**Proposta:** priorizar escolhas que mudam o jeito de jogar e tenham vantagens/limitações compreensíveis. Evitar uma configuração universalmente superior. A interface precisa mostrar o efeito real antes da confirmação.

## 9. Arenas e caos

| Arena | Identidade artística | Decisões que faltam |
|---|---|---|
| Zephyr Peak | Santuário de montanha, torii, cerejeiras, lanternas e vento | Como o vento e os objetos influenciam o combate? |
| Crimson Anvil | Forja, correntes, bigorna, lava e eclipse vermelho | A lava é fundo ou perigo? Há eventos de forja? |
| Golden Bazaar | Mercado dourado, arcos, lanternas, tapetes e especiarias | Quais objetos geram as interações mais divertidas? |

**Protótipo:** objetos são arremessados por ataques, causam dano, quebram e reaparecem. **Pendente:** frequência, sinalização, respawn, responsabilidade por dano, defesa contra objetos e diferença entre arenas.

**Decisão importante:** o caos será acionado pelos jogadores, por eventos previsíveis do cenário ou por aleatoriedade? Definir limites e avisos antes de adicionar eventos. Não transformar automaticamente toda decoração em objeto físico.

Referência: [cenários](../../concept-art/cenarios-v1.png).

## 10. Modos e objetivos

- **Arcade — protótipo:** torre de quatro etapas, dificuldade crescente e chefe com overcharge. Faltam motivo da competição, apresentação, comportamento de chefes, continue/derrota, encerramento e duração-alvo.
- **Versus local — protótipo:** dois jogadores no mesmo teclado. Faltam configuração de habilidades de P2, gamepad, revanche e regras configuráveis.
- **Treino — protótipo:** adversário passivo, recuperação de vida e energia. Faltam tutorial, comandos visíveis, opções do boneco e recursos necessários para aprender o jogo.

**Proposta de MVP:** quatro lutadores, três arenas, Arcade, Versus local e Treino. Confirmar esse recorte antes de ampliar modos, elenco ou multiplayer online.

## 11. Universo, humor e apresentação

Ainda faltam: premissa do mundo, por que os quatro lutam, relação entre eles, personalidade em falas/reações e tom do humor. O contraste visual do elenco já existe; não há uma história final aprovada. Decidir quanto de narrativa será necessário para o Arcade e se haverá locução ou apenas texto e gestos.

## 12. Interface e acessibilidade

**Direção visual:** menu principal minimalista v2. **Referências de linguagem:** HUD e pausa existentes, com atualização dos retratos antigos para os designs atuais.

Faltam fluxos finais de seleção, habilidades, confirmação, resultado, revanche, derrota e encerramento do Arcade; telas funcionais para lista de golpes e configurações; tratamento de teclado/gamepad; prompts que acompanhem remapeamento.

Definir legibilidade na distância da câmera, diferenciação além da cor, intensidade de flashes/shake, volume de música/SFX, tamanho de texto e indicações visuais/sonoras de perigo. São decisões de experiência a integrar ao design, não apenas tarefas de acabamento.

## 13. Áudio e feedback

**Protótipo:** música e efeitos sintetizados. **Pendente:** direção musical de cada arena, assinatura sonora dos quatro personagens, impacto de pedra/carne/sucata, tiros/carga do canhão, avisos de perigo, vitória/derrota, locução e falas.

Hierarquia proposta: sinais que ajudam a jogar devem continuar audíveis em momentos caóticos. O ultimate deve ter preparação e impacto reconhecíveis sem cobrir todo o feedback da partida.

## 14. Produção e validação

Há protótipo Godot, concepts e ícones. Ainda faltam modelos Blender finais, UVs/texturas, rigs, animações, cenas finais, integração das artes e validação do novo combate. Testes do protótipo não comprovam o balanceamento nem a diversão do redesign.

Primeiro teste proposto: Kaze × Ignis em uma arena com uma interação de cenário bem definida; habilidades livres e HUD com os novos ícones. Observar se os jogadores entendem os controles, reconhecem golpes/perigos, encontram respostas e querem revanche. Depois validar Tophia e Volt, que trazem mudanças maiores de volume visual e alcance.

Objetivos de teste a definir: duração de luta, facilidade de aprender, frequência de ações divertidas, tempo sem poder agir, clareza do caos e desempenho-alvo. Não há números finais de balanceamento aprovados.

## 15. Pendências por prioridade

| Prioridade | Decisão | Por que vem agora |
|---|---|---|
| P0 | Kits dos quatro personagens e variantes dos quatro comandos | Define animações, efeitos, som e regras |
| P0 | Regras do canhão e respostas contra ele | Muda alcance, defesa e ritmo de Volt |
| P0 | Origem e limites do caos dos cenários | Define o principal diferencial da experiência |
| P0 | Controles finais, duração de combos e formas de escapar | Define se o combate divertido é acessível |
| P1 | Habilidades, custos e seleção de P2/IA | Fecha as escolhas antes da luta |
| P1 | Rounds, duração-alvo, dificuldade e regras de vitória | Fecha o ritmo de partida e Arcade |
| P1 | Escopo de MVP e prioridade de gamepad | Evita produção sem limite e orienta o Versus local |
| P2 | História, relações, falas, áudio e encerramentos | Dá identidade à apresentação |
| P2 | Distribuição e requisitos finais de plataforma | Prepara publicação depois de validar o jogo |

## 16. Decisões registradas

- Experiência desejada: **combate caótico e exagerado, com foco em diversão**.
- Habilidades: **escolhas livres antes da luta, com limite de pontos**.
- Arte: Kaze/Ignis v2; Tophia/Volt com designs v4 e poses v5; menu minimalista v2.
- Produzir as próximas definições sem confundir propostas artísticas, implementação atual e decisões aprovadas.
