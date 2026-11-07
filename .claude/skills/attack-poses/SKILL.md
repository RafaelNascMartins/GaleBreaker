---
name: attack-poses
description: Cria, refaz ou revisa poses e animações de ataque dos lutadores do Gale Breaker com o peso e o game feel de jogos de luta (Street Fighter, Guilty Gear, FighterZ, Absolver) - pose de contato forte, corpo inteiro indo para o golpe, contrapeso, silhueta legível, animação limitada e juice no impacto (hitstop, vibração, faísca, reação). Use ao animar ou ajustar golpes, reações de dano, vitórias e poses de qualquer lutador (Babuin/kaze, Dale/ignis, X12, Orsted), ao mexer em hitstop, tremida, flash ou contra-ataque, ou quando o usuário falar em "pose", "mais exagerado", "dinâmico", "peso do golpe", "game feel", "juice" ou "impacto".
---

# Poses de ataque e game feel

O estudo completo, com fontes e comparações, está em `docs/estudos/poses-de-ataque-e-game-feel.md`. Leia a seção que precisar antes de mexer num golpe. Esta skill traz as regras e o fluxo de trabalho.

O usuário quer, pelo roadmap, golpes **mais exagerados e dinâmicos: poses irrealistas, mas com anatomia humana básica**.

## Regras de pose

Desenhe primeiro a **pose de contato**. Ela tem que funcionar como ilustração parada, na câmera do jogo (lateral).

1. **O corpo inteiro vai para o golpe.** A base muda no contato:
   - no soco forte, avanço longo;
   - no chute, apoio alto e esticado;
   - no golpe de cima, o corpo sobe ou cai.
   
   O quadril se desloca tanto quanto o membro. É o maior defeito atual: corpo parado numa base média e só o braço ou a perna saindo.
2. **Linha de ação reta, do calcanhar de trás ao ponto de impacto.** A perna de trás fica reta e continua na linha do tronco. As curvas em C ficam para a antecipação e a recuperação ("é uma luta, não uma dança").
3. **A força vem do chão:** o quadril gira antes do ombro e o ombro antes do punho, que termina em saca-rolha. No contato os ombros ficam de lado, com o ombro que bate à frente.
4. **Contrapeso e oposição:**
   - no soco, o braço de trás recua até o peito ou o quadril;
   - no chute, o tronco inclina para longe do pé e os braços abrem;
   - no giro, os braços vão para o lado contrário.
5. **Extensão total.** O membro que bate fica esticado até o fim. O chute alto sai na altura do peito ou da cabeça.
6. **Cabeça e queixo para dentro do golpe**, atrás do ombro. A expressão aparece na antecipação e na recuperação.
7. **Silhueta com espaço vazio:**
   - de perfil, o membro que bate fica fora do contorno do tronco;
   - dá para ler qual perna está na frente;
   - dois golpes do mesmo lutador nunca têm a mesma forma.
8. **Exagero seletivo:** mão ou pé que bate de 1,2× a 1,4×, antebraço ou canela esticados no quadro de smear, peito ou ombro inchados na pancada. O resto fica normal.
9. **Anatomia básica é o limite:** as juntas dobram para o lado certo e o peso cai sobre a base.
10. **Assinatura do lutador:**
    - o Babuin chicoteia: rápido, linhas longas, tecido atrasando;
    - o Dale esmaga: grappler, preparação curta, corpo inteiro, pose larga e baixa segurada.

## Regras novas (diagnóstico da X12, estudo seção 9)

- **Teste de 3 quadros:** o contato tem que ler como silhueta preta.
- **Antecipação de 4 a 6 quadros nos socos leves,** visível, mas sem parecer atraso de comando.
- **Quadro de borrão antes do contato,** com o membro esticado 1,3 a 1,4×.
- **Quadro passando do ponto** depois do contato, antes de recolher.
- **Amplitude mínima:** quadril e passo de 30 a 40 cm nos socos, giro de tronco de 40° a 60°.
- **Secundário em todo golpe:** saia ou manto, cabeça e cabelo atrasam e passam do ponto.
- **Arcos:** gancho e golpes circulares abrem por fora.
- **Jab sem preparação:** a pose-chave já aparece no quadro de borrão, e no fim vem um estalo para trás. Só o direto e os golpes pesados preparam (carregar e puxar). Estudo, seção 10.
- **Tronco inclinado para dentro do golpe e cabeça baixa,** escondida atrás do ombro. Nunca o tronco ereto com a cabeça erguida virada para o oponente (o erro do soco do SF5).

## Regras de tempo

- **Animação limitada:** poses fortes seguradas, com corte seco entre elas e sem interpolação mole. Antecipação curta, corte direto para o contato, **segura a pose no acerto**. O usuário pediu exatamente isso.
- **Antecipação contrária:** antes de ir para a frente, o corpo vai para trás.
  - Leves: uma pose.
  - Pesados: uma ou duas poses, com pausa visível.
  - Especiais: de três a quatro poses.
- **Contato e hold** com a mesma pose (a segunda levemente assentada), coberta pelo hitstop. Depois vem o follow-through, passando do ponto, e a recuperação, que é cara nos golpes pesados.
- **Encadeamento:** a pose final de um golpe é a pose inicial do próximo (`'from': ('light_1', 17)`).

## Fluxo

1. **Ler** o golpe atual: o sheet em `art-source/tools/legends_<id>_anim.py`, os tempos em `art-source/tools/anim_timing.py` e o hitstop em `godot/scripts/combat.gd` (`LIGHT_FEEL`, `HEAVY_CHAIN`).
2. **Ver antes:** rode `godot --path godot --script res://tests/capture_silhouettes.gd -- <pasta no scratchpad> [clipe]`.
   - Sem clipe, ela gera cada golpe no quadro de contato em **três vistas**: perfil (a câmera do jogo), 3/4 e frente.
   - Com um clipe, gera esse clipe a cada 3 quadros.
   - Cada pixel é um **mapa de calor de profundidade** em torno do quadril: perto da câmera fica vermelho ou amarelo, longe fica azul.
   
   Compare com a referência; o Absolver tem silhuetas por golpe no [wiki](https://absolver.wiki.fextralife.com/Bare-hands_Attacks).
   - **Cuidado com o lado:** de perfil, um golpe com o braço esquerdo e outro com o direito na mesma posição dão a mesma silhueta. É a cor que diz qual braço ou perna está na frente. Dois golpes "iguais" de perfil podem ser golpes diferentes, e isso não é defeito.
   - **O jogo é 3D e os lutadores giram:** o golpe tem profundidade e precisa ler também em 3/4 e de frente. Na frente, o membro que bate tem que vir para a câmera (vermelho) e a perna de trás ficar atrás (azul).
3. **Escrever as chaves** no sheet, usando o `legends_anim.place()` com IK:

   | Chave | O que controla | Faixa inicial |
   |---|---|---|
   | `feet` | Base e passo | Pé da frente avança de 0,4 a 0,7 m nos avanços; o de trás fica longe o bastante para a perna esticar; o calcanhar sobe com `up` |
   | `hips` | (avanço, afundo) | Avanço de 0,25 a 0,45 nos golpes que se deslocam |
   | `turn` | Graus por osso (`hips`, `spine`, `chest`, `head`) | Inclinação de 20° a 40° para o golpe nos socos e de -20° a -45° nos chutes; giro em z de 35° a 60° no contato |
   | `shrug` | Ombro para a frente ou para cima | O ombro que bate para a frente |
   | `hands`, `elbow`, `aim` | Mão, polo do cotovelo e direção do punho | A mão de trás recua; cotovelos para fora do tronco |
   | `knee`, `sole`, `pivot`, `foot_turn`, `spin` | Joelhos, sola, giro do pé de apoio e do corpo | `pivot` do apoio de 60° a 90° nos chutes |
   | `scale` | Exagero por osso | Mão ou pé de 1,2 a 1,4; smear `(1, 1.35, 1)` no antebraço |
   | `from` | Começar na pose de outro clipe | — |

4. **Os tempos** ficam em `anim_timing.py` (`wind`, `contact`, `hold`, `follow`, `recover`, `end`). Exporte com `python art-source/tools/anim_timing.py`, que grava `godot/data/anim_timing.json`. O Godot mapeia startup para [0, contact], ativo para [contact, follow] e recuperação para [follow, end]: o frame data do combate não muda.
5. **Gravar no Blender** (MCP):
   - Recarregue os módulos e rode `legends_<id>_anim.author(rig, [clipes], force=True)`.
   - O `author()` pula clipes editados à mão. Use `force` só em clipes que você mesmo escreveu, ou com o ok do usuário.
   - Clipe novo: `ensure_clip` cria a ação e a trilha NLA, e o nome entra em `AUTHORED_STEPPED` no `godot/scripts/fighter_view.gd`.
   - **Antes de exportar, rode `legends_anim.sync_strips(rig)`** (o `author()` do Dale já roda). Uma trilha NLA mais curta ou mais longa que o clipe sai cortada ou congelada no GLB. O K2 do Dale foi exportado parado por isso: a trilha foi criada com o clipe vazio, de 1 quadro. Se um golpe aparece imóvel no Godot, confira isso primeiro.
   - Um teste ou uma checagem que assume "a mão direita bate" quebra quando o golpe usa a outra mão. Corrija o teste para olhar o membro da frente, não a pose.
   - Exporte (`legends_<id>.export_godot()`, que deixa o rig editável com `edit()`) e salve o `.blend`.
6. **Conferir:**
   - `look` em modo `frames` nos quadros-chave;
   - silhuetas de novo, comparadas com as de antes;
   - `capture_gdd.gd` para os renders bonitos;
   - testes com `./godot/tools/test.ps1 -GodotPath <Godot console exe>`.
   
   Só Godot; nunca rode testes do `web/`.
7. **Responder ao checklist abaixo** antes de mostrar ao usuário.

## Juice (só no Godot)

Mudanças de sensação de combate vão nas tabelas do Godot (`combat.gd`), não em `web/` com sincronização.

As camadas sobem juntas com a força do golpe:
- hitstop (os dois congelam, com teto);
- vibração da vítima durante o congelamento (no chão para os lados, no ar para cima e para baixo, decrescente, só visual);
- faísca no soquete do membro que bateu;
- flash curto;
- tremida de câmera só a partir dos pesados;
- reação em níveis.

Quando o golpe "forte" não tem nenhuma camada a mais que o leve, ele não parece forte.

**Já feito (2026-11-06):**
- **Vibração no hitstop:** a vítima vibra durante o congelamento, de um lado para o outro no chão e para cima e para baixo no ar, decrescente. A arena passa `hitstop_left` e `hitstop_total`, e o efeito fica em `fighter_view._update_motion_fx`. O atacante vibra de leve nos golpes com 10 quadros ou mais de hitstop.
  - No espaço da vista, o lutador olha para -Z: **o horizontal da tela é o Z**, e um deslocamento em X vai para a profundidade.
- **Flash:** 3 quadros, contados também durante o congelamento.
- **Contra-ataque:** +4 quadros de hitstop e `sim.slow = 24`. Durante o `slow`, a simulação avança um quadro sim, um não, e a apresentação anda a 45%.
- **KO:** `slow = 50`, só na apresentação.

**Pendente:** há uma reação `hit` só por lutador, sem níveis de força nem alto/baixo. Também falta a faísca no soquete do membro que bateu, crescendo com a força.

Câmera dramática e câmera lenta ficam reservadas a finalizações, ultimates e vitórias, nunca nos golpes comuns.

A tabela inicial de hitstop, vibração, tremida e reação por tipo de golpe está na seção 7.3 do estudo. O Dale fica no alto das faixas e o Babuin embaixo.

## Checklist (na câmera do jogo, pose parada)

- [ ] O contato funciona como ilustração? Dá para saber o golpe sem ver o movimento?
- [ ] O corpo inteiro foi para o golpe (a base mudou e o quadril se deslocou)?
- [ ] Há linha reta do calcanhar de trás ao ponto de impacto?
- [ ] Os ombros estão de lado e há saca-rolha no soco?
- [ ] Há contrapeso e oposição?
- [ ] O membro que bate está totalmente esticado, fora do contorno do tronco?
- [ ] A cabeça entra no golpe?
- [ ] O exagero está só no membro que bate? As juntas estão certas e o peso sobre a base?
- [ ] A silhueta é diferente da dos outros golpes do lutador, levando em conta o lado (cor do mapa de calor)?
- [ ] O golpe lê também em 3/4 e de frente (o membro que bate vem para a câmera, a perna de trás fica atrás)?
- [ ] A antecipação é contrária e proporcional, com poses seguradas e corte seco?
- [ ] O contato fica parado durante o hitstop? Há follow-through?
- [ ] Tecido e chapéu atrasam e passam do ponto?
- [ ] A pose final encaixa no próximo golpe?
- [ ] O juice está proporcional à força?
- [ ] O golpe tem a assinatura do lutador?
