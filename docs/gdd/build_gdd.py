"""Gale Breaker GDD (single document, v0.10): a 1997 fighting-game instruction booklet.

One source: this script writes index.html (pages of 1080 x 675 px, HTML + CSS) and Edge prints
it to Gale_Breaker_GDD_Visual_v0_10.pdf. Images come from the real game where they exist:
  docs/gdd/assets/renders/  fighter renders (godot/tests/capture_gdd.gd)
  docs/readme/              screens of the game (godot/tests/capture_readme.gd)
X12 and Orsted (ex-Tophia, ex-Volt) still show their old concepts, marked as in revitalization.

python docs/gdd/build_gdd.py
"""
import html
import json
import shutil
import subprocess
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
ASSETS = OUT / 'assets'
EDGE = Path(r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe')
PDF = OUT / 'Gale_Breaker_GDD_Visual_v0_10.pdf'
EDITION, DATE = '0.10', 'NOVEMBRO 2026'

JADE, SUN, GOLD, STONE, CYAN = '#2fb58a', '#e8572f', '#e2b04a', '#e08a3c', '#3cc6e0'

# Two families for the whole document: Barlow Condensed for titles and labels, Barlow for text.
FONTS = [('Title', 'BarlowCondensed-ExtraBoldItalic.ttf', 800, 'italic'), ('Title', 'BarlowCondensed-SemiBold.ttf', 600, 'normal'),
         ('Text', 'Barlow-Regular.ttf', 400, 'normal'), ('Text', 'Barlow-SemiBold.ttf', 600, 'normal'), ('Text', 'Barlow-Italic.ttf', 400, 'italic')]


def asset(src, sub='img'):
    """Copy a project file into assets/<sub>/ and return its path relative to index.html."""
    src = ROOT / src
    (ASSETS / sub).mkdir(parents=True, exist_ok=True)
    dst = ASSETS / sub / src.name
    if src.exists() and src.resolve() != dst.resolve():
        shutil.copy2(src, dst)
    return f'assets/{sub}/{src.name}'


def render(name):
    return f'assets/renders/{name}.png'


def screen(name):
    """A game screen: assets/screens/ holds the GDD captures (capture_readme.gd with this folder as
    out_dir); a screen not captured there yet falls back to the README's copy."""
    if not (ASSETS / 'screens' / f'{name}.png').exists():
        asset(f'docs/readme/{name}.png', 'screens')
    return f'assets/screens/{name}.png'


e = html.escape
pages = []


def page(chapter, title, accent, body, kicker='', cls=''):
    pages.append((chapter, title, accent, body, kicker, cls))


def tag(text, color):
    return f'<span class="tag" style="--c:{color}">{e(text)}</span>'


# ---------------------------------------------------------------- content
FIGHTERS = [
    dict(id='kaze', name='Babuin', sub='Monge do Vento Jade', color=JADE, element='VENTO', hp=1000,
         style='Rápido e fluido. Palmas, chutes giratórios e tecido que acompanha cada golpe.',
         bio='Monge alto e careca de postura ereta, túnica verde de jade e pés descalços. Silhueta vertical e calma: o vento aparece no movimento do tecido e na direção dos golpes.',
         stats=[('VELOCIDADE', 5), ('FORÇA', 3), ('ALCANCE', 4), ('DEFESA', 3)],
         outfits=['Jade Monástico', 'Jade Dourado', 'Peixão', 'Executivo'],
         moves=[('light_3', 'Palma de Jade', 'BÁSICO · J1 J2 J3', 'Duas palmas rápidas e um terceiro golpe de palma aberta com o peso do corpo.'),
                ('heavy_2', 'Chute do Vendaval', 'FORTE · K1 K2 K3', 'Corrente de chutes: canela baixa, chute frontal e chute giratório para trás.'),
                ('elemental', 'Rajada de Vento', 'ELEMENTAL', 'Junta o vento entre as palmas na cintura e solta a rajada com um passo à frente.'),
                ('ultimate', 'Tufão Celestial', 'ULTIMATE · 50 DE ENERGIA', 'Gira uma volta inteira enquanto o tufão cresce e dispara uma palma dupla gigante.'),
                ('victory', 'Saudação', 'VITÓRIA', 'Punho na palma diante do peito e uma reverência profunda.')]),
    dict(id='ignis', name='Dale', sub='Brutamontes do Sol Escaldante', color=SUN, element='FOGO', hp=1200,
         style='Grappler pesado, à la luta livre: antecipação curta, corte seco para o contato e pose segurada no impacto.',
         bio='Brutamontes caipira, mais alto que o Babuin, queimado de sol e de chapéu de cowboy. Base larga e baixa, braços abertos para agarrar; cada golpe leva o corpo inteiro.',
         stats=[('VELOCIDADE', 2), ('FORÇA', 5), ('ALCANCE', 3), ('DEFESA', 5)],
         outfits=['Sol do Meio-Dia', 'Preto', 'Coronel', "Men's Physique"],
         moves=[('light_3', 'Soco de Roça', 'BÁSICO · J1 J2 J3', 'Antebraço que desce como clava, lariat curto e martelo com os dois punhos.'),
                ('heavy', 'Botada', 'FORTE · K1 (K2 MARRETA CAIPIRA)', 'O joelho sobe e a bota entra chapada na barriga. Em seguida, a marreta no chão.'),
                ('elemental', 'Pisada da Fornalha', 'ELEMENTAL', 'Joelho alto, punhos recolhidos e uma pisada que derruba todo o peso no chão.'),
                ('ultimate', 'Fúria do Meio-Dia', 'ULTIMATE · 50 DE ENERGIA', 'Ajeita o chapéu, se abaixa atrás do ombro e explode numa ombrada quase horizontal.'),
                ('victory', 'Duplo Bíceps', 'VITÓRIA', 'Planta os pés e flexiona os dois braços, cabeça para trás, rindo.')]),
]
REVAMP = [
    dict(name='X12', was='Tophia', color=STONE, element='TERRA', art='concept-art/tophia-retrato-gdd-v1.png',
         why='O nome vem da origem: ela é um experimento. Armadura de pedra, cavaleira.',
         moves=['Punho de Arenito', 'Martelo de Pedra', 'Erupção Rochosa', 'Colosso de Terra']),
    dict(name='Orsted', was='Volt', color=CYAN, element='RAIO', art='concept-art/volt-v5.png',
         why='Mesmo nome do cientista. Armadura de sucata e canhão de mão.',
         moves=['Tiro de Sucata', 'Disparo Carregado', 'Curto-Circuito', 'Sobrecarga Total']),
]


def stats(f):
    rows = ''.join(f'<div class="stat"><b>{k}</b><i>{"".join("<s class=on></s>" if j < v else "<s></s>" for j in range(5))}</i></div>' for k, v in f['stats'])
    return f'<div class="stats">{rows}</div>'


# 01 cover
page('', '', JADE, f'''
<div class="cover-band"></div>
<h1 class="cover-logo">GALE<br>BREAKER</h1>
<div class="cover-sub">QUATRO ELEMENTOS. UMA BOA CONFUSÃO.</div>
<img class="cover-hero a" src="{render('ignis_heavy')}" alt="Dale">
<img class="cover-hero b" src="{render('kaze_light_3')}" alt="Babuin">
<div class="cover-foot"><span>GAME DESIGN DOCUMENT</span><span>EDIÇÃO {EDITION} · {DATE}</span></div>
''', cls='cover')

# 02 contents
CONTENTS = [('01', 'Visão do jogo'), ('02', 'Estilo de arte'), ('03', 'Elenco'), ('04', 'Babuin'), ('05', 'Dale'),
            ('06', 'X12 e Orsted'), ('07', 'Combate'), ('08', 'Animação'), ('09', 'Modos'), ('10', 'Interface'),
            ('11', 'Arenas'), ('12', 'Produção'), ('13', 'Roadmap')]
page('00', 'Índice', JADE, '<ol class="toc">' + ''.join(f'<li><b>{n}</b><span>{e(t)}</span></li>' for n, t in CONTENTS) + '</ol>'
     + f'<img class="toc-hero" src="{render("kaze_frente")}" alt="">')

# 03 vision
page('01', 'Combate exagerado e divertido', JADE, f'''
<div class="grid3">
 <div class="card"><h3>CAOS COM CLAREZA</h3><p>Golpes grandes, reações exageradas e arenas que participam da luta. Mesmo no exagero, o jogador sempre vê de onde vem o perigo e tem uma resposta.</p></div>
 <div class="card"><h3>PESO EM CADA PANCADA</h3><p>Antecipação curta, corte seco para o contato e a pose segurada no impacto. Cada lutador tem o próprio ritmo: o Babuin chicoteia, o Dale esmaga.</p></div>
 <div class="card"><h3>ESCOLHA LIVRE</h3><p>Habilidades escolhidas antes da luta com um limite de pontos. Sem XP, moeda ou grind: são escolhas de estilo, não vantagem comprada.</p></div>
</div>
<h4 class="sec">FLUXO DE PARTIDA</h4>
<div class="flow">{''.join(f'<span>{s}</span>' for s in ['MENU', 'MODO', 'LUTADOR', 'HABILIDADES', 'LUTA', 'RESULTADO'])}</div>
<img class="corner-shot" src="{screen('luta_molten_forge')}" alt="">
''')

# 04 art style
page('02', 'Estilo PS1 · Legends 1997', GOLD, f'''
<div class="split">
 <div>
  <p class="lead">Os lutadores seguem o visual dos jogos 3D de 1997: peças rígidas, poucas faces e toda a sombra pintada à mão na textura.</p>
  <ul class="rules">
   <li><b>~6 cabeças</b> de altura. Cabeça, mãos e pés grandes; membros retos.</li>
   <li><b>Peças rígidas</b>, cada uma num osso só. Cerca de 700 triângulos por lutador.</li>
   <li><b>Uma página de 256 px</b> com 15 cores, filtro nearest, sombra pintada.</li>
   <li><b>Rosto trocável</b>: 24 expressões num atlas, sem animar a malha.</li>
   <li><b>Roupas</b> com peças próprias sobre o mesmo esqueleto e as mesmas animações.</li>
  </ul>
 </div>
 <div class="texgrid">
  <figure><img class="px" src="{asset('godot/assets/characters/ignis/textures/page.png', 'style/dale')}"><figcaption>PÁGINA 256 · DALE</figcaption></figure>
  <figure><img class="px" src="{asset('godot/assets/characters/kaze/textures/page.png', 'style/babuin')}"><figcaption>PÁGINA 256 · BABUIN</figcaption></figure>
  <figure class="wide"><img class="px" src="{asset('godot/assets/characters/ignis/textures/face.png', 'style/dale')}"><figcaption>ATLAS DE EXPRESSÕES · 6 × 4</figcaption></figure>
 </div>
</div>
''')

# 05 cast
cast = ''.join(f'''<div class="fighter" style="--c:{f['color']}"><img src="{render(f['id'] + '_0')}" alt=""><h3>{f['name']}</h3><small>{e(f['sub'])}</small>{tag(f['element'], f['color'])}</div>''' for f in FIGHTERS)
cast += ''.join(f'''<div class="fighter wip" style="--c:{r['color']}"><img src="{asset(r['art'], 'concepts')}" alt=""><h3>{r['name']}</h3><small>ex-{r['was']} · em revitalização</small>{tag(r['element'], r['color'])}</div>''' for r in REVAMP)
page('03', 'Quatro lutadores', SUN, f'<div class="cast">{cast}</div>')

# fighter spreads
for n, f in zip(('04', '05'), FIGHTERS):
    outfits = ''.join(f'<figure><img src="{render(f["id"] + "_" + str(i))}"><figcaption>{e(o)}</figcaption></figure>' for i, o in enumerate(f['outfits']))
    page(n, f['name'], f['color'], f'''
<div class="hero">
 <img class="hero-img" src="{render(f['id'] + '_0')}" alt="">
 <div class="hero-text">
  <div class="sub">{e(f['sub'])}</div>
  {tag('ELEMENTO · ' + f['element'], f['color'])} {tag(f'VIDA {f["hp"]}', f['color'])}
  <p class="lead">{e(f['bio'])}</p>
  <p>{e(f['style'])}</p>
  {stats(f)}
 </div>
</div>
<h4 class="sec">ROUPAS</h4>
<div class="outfits">{outfits}</div>
''', kicker=f['sub'])
    moves = ''.join(f'''<div class="move"><div class="mimg"><img src="{render(f['id'] + '_' + clip)}" alt=""></div><em>{e(kind)}</em><h3>{e(name)}</h3><p>{e(desc)}</p></div>''' for clip, name, kind, desc in f['moves'])
    page(n, f'{f["name"]} · Golpes', f['color'], f'<div class="moves">{moves}</div><p class="note">Poses capturadas no quadro de contato de cada animação, no próprio jogo.</p>')

# X12 / Orsted
wip = ''.join(f'''<div class="wipcard" style="--c:{r['color']}"><img src="{asset(r['art'], 'concepts')}" alt="">
<div><h3>{r['name']}</h3><small>ex-{r['was']}</small>{tag(r['element'], r['color'])}<p>{e(r['why'])}</p>
<ul>{''.join(f'<li>{e(m)}</li>' for m in r['moves'])}</ul>
<div class="stamp">EM REVITALIZAÇÃO</div></div></div>''' for r in REVAMP)
page('06', 'X12 e Orsted', STONE, f'<div class="wipgrid">{wip}</div><p class="note">Próximos na revitalização Legends: turnaround, expressões, painéis de textura, modelo, rig e animações. Concepts antigas apenas como referência.</p>')

# combat
cmds = [('BÁSICO', JADE, 'J1 J2 J3', 'Corrente de três golpes. Variantes agachado e no ar.'),
        ('FORTE', SUN, 'K1 K2', 'Impacto maior, abertura mais evidente.'),
        ('ELEMENTAL', GOLD, 'ENERGIA', 'Poder do lutador e interação com a arena.'),
        ('ULTIMATE', CYAN, '50 / 100', 'Golpe de grande impacto ligado ao medidor.')]
page('07', 'Entender a pancada', JADE, f'''
<div class="grid4">{''.join(f'<div class="card cmd" style="--c:{c}"><h3>{t}</h3><em>{k}</em><p>{d}</p></div>' for t, c, k, d in cmds)}</div>
<h4 class="sec">RITMO DE UM GOLPE</h4>
<div class="timeline"><span class="s">PREPARAÇÃO</span><span class="a">CONTATO + HITSTOP</span><span class="r">RECUPERAÇÃO</span></div>
<div class="grid3 small">
 <div><h3>REGRAS</h3><p>Melhor de três, 99 segundos por round, ultimate custa 50 de um medidor de 100.</p></div>
 <div><h3>DEFESA</h3><p>Bloqueio alto e baixo, parry com janela curta e dash para fugir da pressão.</p></div>
 <div><h3>ARENA</h3><p>Objetos arremessáveis e eventos anunciados 1,5 s antes, a cada ~15 s. O Treino os desliga.</p></div>
</div>
<img class="strip" src="{screen('luta_molten_forge')}" alt="">''')

# animation
f = FIGHTERS[1]
page('08', 'Animação limitada', SUN, f'''
<p class="lead">Poses fortes seguradas por quadros, como desenho animado: nada de interpolação mole. A cada golpe, três ideias.</p>
<div class="beats">
 <figure><img src="{render('ignis_0')}"><figcaption><b>1 · GUARDA</b>Base larga, braços abertos para agarrar.</figcaption></figure>
 <figure><img src="{render('ignis_heavy')}"><figcaption><b>2 · CORTE PARA O CONTATO</b>Antecipação curta e salto direto para a pose do impacto.</figcaption></figure>
 <figure><img src="{render('ignis_victory')}"><figcaption><b>3 · SEGURA A POSE</b>O hitstop congela o acerto; o corpo exagera a forma.</figcaption></figure>
</div>
<p class="note">Próximo passo do roadmap: poses ainda mais exageradas e dinâmicas, irrealistas mas com anatomia humana básica, e vitórias com cutscene.</p>''')

# modes
page('09', 'Modos de jogo', GOLD, f'''
<div class="modes">
 <figure><img src="{screen('arcade')}"><figcaption><b>ARCADE</b>Torre de quatro etapas com chefe, três dificuldades, continue salvo e encerramento. Escolha de lutador e roupa no pátio.</figcaption></figure>
 <figure><img src="{screen('treino')}"><figcaption><b>TREINO</b>Garagem com dummy configurável, hitboxes, reposição e avanço de quadro.</figcaption></figure>
</div>
<div class="grid3 small">
 <div><h3>VERSUS</h3><p>Hoje local, dois controles e loadouts separados. Roadmap: Online e LAN dentro do Versus.</p></div>
 <div><h3>TUTORIAL</h3><p>Oito lições: mover, saltar, agachar, defender, combo, forte, elemental e ultimate.</p></div>
 <div><h3>HABILIDADES</h3><p>Seleção livre com limite de pontos. Roadmap: aba Lutadores, com as habilidades de cada um.</p></div>
</div>''')

# interface
page('10', 'Interface', JADE, f'''
<div class="ui">
 <figure class="big"><img src="{screen('menu')}"><figcaption><b>MENU NA PRAIA</b>Título e lista de texto sobre a praia ao vivo.</figcaption></figure>
 <figure><img src="{screen('opcoes')}"><figcaption><b>OPÇÕES NO QUADRO</b>Pergaminho no quadro de missões da floresta.</figcaption></figure>
 <figure><img src="{screen('luta_zephyr_dojo')}"><figcaption><b>HUD DE LUTA</b>Vida, tempo e rounds no alto; energia nos cantos.</figcaption></figure>
</div>''')

# arenas
arenas = [('luta_zephyr_dojo', 'ZEPHYR PEAK', JADE, 'Santuário entre cerejeiras. Rajada anunciada empurra lutadores e lança objetos.'),
          ('luta_molten_forge', 'CRIMSON ANVIL', SUN, 'Forja de lava e correntes. Erupção marcada no chão: saltar, sair ou bloquear.'),
          ('luta_storm_market', 'GOLDEN BAZAAR', GOLD, 'Arcos, lanternas e especiarias. Queda de carga anunciada sobre a marca.')]
page('11', 'Três arenas', SUN, '<div class="arenas">' + ''.join(f'<figure style="--c:{c}"><img src="{screen(s)}"><figcaption><b>{t}</b>{d}</figcaption></figure>' for s, t, c, d in arenas) + '</div>')

# production
steps = [('CONCEPT', 'Turnaround, expressões e 20 painéis de textura'), ('BLENDER', 'Peças rígidas medidas na concept'),
         ('TEXTURA', 'Página 256, pintura à mão'), ('RIG + ANIM', 'Poses-chave por código e à mão'), ('GODOT', 'GLB, shader toon e combate')]
page('12', 'Da concept ao jogo', CYAN, f'''
<div class="flow steps">{''.join(f'<span><b>{t}</b><small>{d}</small></span>' for t, d in steps)}</div>
<div class="pipe">
 <img src="{asset('concept-art/characters/dale/dale-turnaround-psx-v1.png', 'pipeline')}">
 <img src="{asset('art-source/characters/ignis/legends/dale_frente_facetas.png', 'pipeline')}">
 <img class="px" src="{asset('godot/assets/characters/ignis/textures/page.png', 'style/dale')}">
 <img class="fit" src="{render('ignis_heavy')}">
 <img src="{screen('luta_storm_market')}">
</div>
<div class="grid3 small">
 <div><h3>AUTORIDADE DO COMBATE</h3><p>Dano e movimento vivem na simulação. A animação acompanha preparação, contato e recuperação, sem mudar os quadros de jogo.</p></div>
 <div><h3>VERIFICAÇÃO</h3><p>Testes do Godot a cada mudança: combate, regressão visual e recursos do jogo. Capturas do próprio motor neste documento.</p></div>
 <div><h3>FONTES</h3><p>Blender em art-source/, jogo em godot/, este GDD em docs/gdd/build_gdd.py.</p></div>
</div>''')

# roadmap
ROADMAP = [('REVITALIZAÇÃO DOS PERSONAGENS', JADE, [(1, 'Babuin'), (1, 'Dale'), (0, 'X12 (ex-Tophia): ela é um experimento'), (0, 'Orsted (ex-Volt): mesmo nome do cientista')]),
           ('REVITALIZAR ANIMAÇÕES', SUN, [(0, 'Mais exageradas e dinâmicas: poses irrealistas, anatomia humana básica'), (0, 'Vitórias com cutscene')]),
           ('REVITALIZAR MENUS', GOLD, [(0, 'Versus com Online e Local (LAN)'), (0, 'Aba "Lutadores" com as habilidades'), (0, 'Retrabalhar habilidades'), (0, 'Tutorial')]),
           ('CUTSCENE INICIAL', STONE, [(0, 'Primeira pessoa num quarto de adolescente: um CD no PS1 antigo e o jogo abre')]),
           ('COMBOS E BALANCEAMENTO', CYAN, [(0, 'Retrabalhar combos e balanceamento'), (0, 'Hitboxes e game feel')]),
           ('TOQUES FINAIS', JADE, [(0, 'Detalhamento de todos os pontos'), (0, 'Preparação para a Alpha 0.1')])]
road = ''.join(f'''<div class="road" style="--c:{c}"><b>{i + 1}</b><h3>{t}</h3><ul>{''.join(f'<li class="{"done" if d else ""}">{e(x)}</li>' for d, x in items)}</ul></div>''' for i, (t, c, items) in enumerate(ROADMAP))
page('13', 'Rumo à Alpha 0.1', JADE, f'<div class="roadmap">{road}</div>')

# ---------------------------------------------------------------- render
CSS = ''.join(f"@font-face{{font-family:{k};src:url('assets/fonts/{f}');font-weight:{w};font-style:{st}}}" for k, f, w, st in FONTS) + '''
:root{--ink:#14111c;--ink2:#1f1b2b;--paper:#efe6d2;--muted:#a59db3;--line:#3a3348}
*{box-sizing:border-box}
body{margin:0;background:#0b0a10;font-family:Text,Arial,sans-serif;color:var(--paper)}
.page{position:relative;width:1080px;height:675px;margin:28px auto;overflow:hidden;background:
 repeating-linear-gradient(0deg,#ffffff05 0 1px,transparent 1px 3px),
 radial-gradient(120% 90% at 85% 0%,#2a2340 0%,var(--ink) 60%);box-shadow:0 8px 30px #000a}
.page::before{content:"";position:absolute;right:-160px;top:-40px;width:520px;height:900px;background:var(--a);opacity:.13;transform:skewX(-18deg)}
.page::after{content:"";position:absolute;left:0;top:0;width:100%;height:6px;background:linear-gradient(90deg,var(--a) 0 30%,transparent 30%)}
header{position:absolute;left:44px;top:26px;right:44px;display:flex;align-items:flex-end;gap:18px}
header .ch{font:italic 800 46px Title;color:var(--ink);background:var(--a);padding:0 14px 2px 10px;transform:skewX(-12deg);line-height:1}
header h1{margin:0;font:italic 800 40px Title;text-transform:uppercase;letter-spacing:.5px;color:var(--paper);text-shadow:3px 3px 0 var(--a);line-height:1}
header .k{margin-left:auto;font:600 12px Title;color:var(--muted);letter-spacing:2px;text-transform:uppercase}
main{position:absolute;left:44px;right:44px;top:104px;bottom:46px}
footer{position:absolute;left:44px;right:44px;bottom:14px;display:flex;font:600 10px Title;color:var(--muted);letter-spacing:2px}
footer b{margin-left:auto;font:italic 800 22px Title;color:var(--a);letter-spacing:0;margin-top:-10px}
h3{margin:0 0 6px;font:italic 800 20px Title;letter-spacing:.5px;color:var(--a);text-transform:uppercase}
p{margin:0 0 8px;font-size:13px;line-height:1.45}
.lead{font:18px/1.4 Text;color:var(--paper)}
.note{position:absolute;bottom:0;left:0;font:600 11px Title;color:var(--muted)}
.sec{margin:22px 0 10px;font:600 13px Title;letter-spacing:3px;color:var(--a)}
.sec::after{content:"";display:inline-block;width:60px;height:2px;background:var(--a);margin-left:10px;vertical-align:middle}
.tag{display:inline-block;font:italic 800 13px Title;letter-spacing:1px;color:var(--ink);background:var(--c);padding:2px 10px;transform:skewX(-12deg);margin:0 6px 6px 0}
.card{background:var(--ink2);border-left:4px solid var(--c,var(--a));padding:16px 18px;clip-path:polygon(0 0,100% 0,100% calc(100% - 18px),calc(100% - 18px) 100%,0 100%)}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}
.grid3.small{margin-top:20px}.grid3.small h3{font-size:16px}
.flow{display:flex;gap:6px}.flow span{flex:1;background:var(--ink2);padding:12px 14px;font:italic 800 17px Title;letter-spacing:1px;clip-path:polygon(0 0,calc(100% - 14px) 0,100% 50%,calc(100% - 14px) 100%,0 100%,14px 50%)}
.flow span:first-child{clip-path:polygon(0 0,calc(100% - 14px) 0,100% 50%,calc(100% - 14px) 100%,0 100%)}
.flow span:nth-child(odd){background:#2a2438}
.steps span{padding:14px 22px}.steps small{display:block;font:11px Text;color:var(--muted);margin-top:6px;letter-spacing:0}.steps b{color:var(--a);font-weight:400}
.corner-shot{position:absolute;right:0;bottom:0;width:430px;border:3px solid var(--a);transform:rotate(-2deg);box-shadow:8px 8px 0 #0008}
img.px{image-rendering:pixelated}
.split{display:grid;grid-template-columns:1fr 1.05fr;gap:30px}
.rules{list-style:none;padding:0;margin:14px 0}.rules li{font-size:13px;line-height:1.4;padding:8px 0 8px 22px;border-bottom:1px solid var(--line);position:relative}
.rules li::before{content:"";position:absolute;left:0;top:13px;width:10px;height:10px;background:var(--a);transform:rotate(45deg)}
.rules b{color:var(--a)}
.texgrid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.texgrid img{width:100%;display:block;border:2px solid var(--line)}
.texgrid .wide{grid-column:span 2}.texgrid .wide img{height:150px;object-fit:contain;background:var(--ink2)}
figure{margin:0}figcaption{font:600 10px Title;letter-spacing:1.5px;color:var(--muted);margin-top:5px}
.cast{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;height:100%}
.fighter{position:relative;background:linear-gradient(180deg,transparent 40%,color-mix(in srgb,var(--c) 30%,transparent));border-bottom:5px solid var(--c);padding:10px 12px;display:flex;flex-direction:column;justify-content:flex-end}
.fighter img{position:absolute;left:0;right:0;top:0;bottom:90px;margin:auto;max-width:100%;max-height:calc(100% - 100px);object-fit:contain;filter:drop-shadow(5px 5px 0 #0009)}
.fighter.wip img{filter:grayscale(.65) brightness(.7);object-fit:cover;width:100%;height:calc(100% - 100px);max-height:none}
.fighter h3{font-size:34px;color:var(--paper);text-shadow:3px 3px 0 var(--c);margin:0}.fighter small{font:600 11px Title;color:var(--muted);margin-bottom:6px}
.fighter .tag{align-self:flex-start}
.hero{display:grid;grid-template-columns:300px 1fr;gap:30px;height:300px}
.hero-img{height:300px;margin:auto;filter:drop-shadow(6px 6px 0 #000a)}
.sub{font:italic 22px Text;color:var(--a);margin-bottom:10px}
.stats{display:grid;grid-template-columns:1fr;gap:7px;margin-top:14px;width:330px}.stat{display:flex;align-items:center;justify-content:space-between;font:600 11px Title;letter-spacing:2px}
.stat i{display:flex;gap:3px}.stat s{width:22px;height:10px;background:var(--line);transform:skewX(-20deg)}.stat s.on{background:var(--a)}
.outfits{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.outfits figure{background:var(--ink2);height:150px;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;padding:6px;clip-path:polygon(0 0,100% 0,100% calc(100% - 14px),calc(100% - 14px) 100%,0 100%)}
.outfits img{height:118px;filter:drop-shadow(3px 3px 0 #0009)}.outfits figcaption{font:italic 800 13px Title;letter-spacing:1px;color:var(--paper)}
.moves{display:grid;grid-template-columns:repeat(5,1fr);gap:12px}
.mimg{height:330px;background:linear-gradient(160deg,#2a2438,var(--ink2));display:flex;align-items:center;justify-content:center;margin-bottom:10px;border-bottom:4px solid var(--a);clip-path:polygon(0 0,100% 0,100% 100%,0 100%)}
.mimg img{max-width:94%;max-height:92%;filter:drop-shadow(4px 4px 0 #000a)}
.move em{font:600 10px Title;letter-spacing:1px;color:var(--muted);font-style:normal}.move h3{font-size:19px;margin-top:4px;color:var(--paper)}.move p{font-size:12px}
.wipgrid{display:grid;grid-template-columns:1fr 1fr;gap:20px}
.wipcard{display:grid;grid-template-columns:190px 1fr;gap:16px;background:var(--ink2);border-top:5px solid var(--c);padding:14px;height:420px}
.wipcard img{width:190px;height:390px;object-fit:cover;filter:grayscale(.5) brightness(.8)}
.wipcard h3{font-size:42px;color:var(--paper);text-shadow:3px 3px 0 var(--c)}.wipcard small{display:block;font:600 11px Title;color:var(--muted);margin-bottom:10px}
.wipcard ul{padding-left:18px;font-size:13px;line-height:1.7}.stamp{display:inline-block;margin-top:14px;font:italic 800 20px Title;color:var(--c);border:3px solid var(--c);padding:4px 12px;transform:rotate(-6deg)}
.cmd em{display:block;font:600 11px Title;color:var(--muted);font-style:normal;margin-bottom:8px}.cmd{height:130px}
.timeline{display:flex;height:46px;font:italic 800 16px Title;letter-spacing:1px;color:var(--ink)}
.timeline span{display:flex;align-items:center;padding-left:16px;transform:skewX(-12deg)}.timeline .s{width:28%;background:var(--muted)}.timeline .a{width:30%;background:var(--a)}.timeline .r{width:42%;background:#e08a3c}
.beats{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin-top:10px}
.beats figure{background:var(--ink2);height:420px;padding:12px;display:flex;flex-direction:column;justify-content:flex-end;align-items:center}
.beats img{max-height:310px;max-width:100%;filter:drop-shadow(4px 4px 0 #000a);margin-bottom:auto}
.beats figcaption{font:12px Text;color:var(--paper);letter-spacing:0;text-align:center}.beats b{display:block;font:italic 800 18px Title;color:var(--a);letter-spacing:1px;margin-bottom:4px}
.modes{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.modes img,.ui img,.arenas img{width:100%;display:block;border:3px solid var(--a)}.modes img{height:290px;object-fit:cover}
.modes figcaption,.ui figcaption,.arenas figcaption{font:12px Text;color:var(--paper);letter-spacing:0;margin-top:8px}
.modes b,.ui b,.arenas b{display:block;font:italic 800 18px Title;color:var(--a);letter-spacing:1px}
.ui{display:grid;grid-template-columns:1.6fr 1fr;grid-template-rows:1fr 1fr;gap:14px 18px;height:100%}.ui .big{grid-row:span 2}
.ui figure:not(.big) img{height:150px;object-fit:cover}
.arenas{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.arenas img{border-color:var(--c);height:390px;object-fit:cover}.arenas b{color:var(--c)}
.strip{position:absolute;left:0;right:0;bottom:0;width:100%;height:170px;object-fit:cover;object-position:50% 45%;border:3px solid var(--a)}
.pipe{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin:14px 0 4px}.pipe img{width:100%;height:150px;object-fit:cover;object-position:50% 20%;border:2px solid var(--line);background:var(--ink2)}.pipe .fit{object-fit:contain}
.roadmap{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.road{background:var(--ink2);border-top:4px solid var(--c);padding:14px 16px 10px 16px;height:250px;position:relative}
.road>b{position:absolute;right:12px;top:2px;font:italic 800 46px Title;color:var(--c);opacity:.35}
.road h3{color:var(--c);font-size:17px;padding-right:40px}.road ul{list-style:none;padding:0;margin:8px 0}
.road li{font-size:12.5px;line-height:1.35;padding:5px 0 5px 24px;position:relative}
.road li::before{content:"";position:absolute;left:0;top:6px;width:13px;height:13px;border:2px solid var(--c)}
.road li.done{color:var(--muted)}.road li.done::before{background:var(--c)}
.road li.done::after{content:"";position:absolute;left:4px;top:8px;width:5px;height:8px;border:solid var(--ink);border-width:0 2px 2px 0;transform:rotate(45deg)}
.toc{columns:2;column-gap:40px;list-style:none;padding:0;margin:10px 0;width:600px}
.toc li{display:flex;gap:16px;align-items:baseline;padding:9px 0;border-bottom:1px solid var(--line);break-inside:avoid}
.toc b{font:italic 800 26px Title;color:var(--a);width:40px}.toc span{font:italic 800 20px Title;letter-spacing:.5px;text-transform:uppercase}
.toc-hero{position:absolute;right:10px;bottom:0;height:500px;filter:drop-shadow(8px 8px 0 #000a)}
.cover{background:radial-gradient(90% 90% at 70% 40%,#3a2a3a 0%,#120f18 70%)}
.cover::before{right:-40px;width:640px;opacity:.9;background:linear-gradient(180deg,#e8572f,#e2b04a)}
.cover-band{position:absolute;right:120px;top:-40px;width:90px;height:900px;background:#2fb58a;transform:skewX(-18deg);opacity:.9}
.cover-logo{position:absolute;left:52px;top:60px;margin:0;font:italic 800 112px/0.86 Title;letter-spacing:1px;color:#e2b04a;text-shadow:6px 6px 0 #000,10px 10px 0 #2fb58a}
.cover-sub{position:absolute;left:58px;top:270px;font-size:21px!important;font:italic 800 22px Title;letter-spacing:2px;color:var(--paper)}
.cover-hero{position:absolute;filter:drop-shadow(10px 10px 0 #000b)}.cover-hero.a{right:40px;bottom:56px;height:500px}.cover-hero.b{right:330px;bottom:60px;height:240px}
.cover-foot{position:absolute;left:56px;right:56px;bottom:22px;display:flex;justify-content:space-between;font:600 12px Title;letter-spacing:3px;color:var(--paper)}
@page{size:1080px 675px;margin:0}
@media print{body{background:none}.page{margin:0;box-shadow:none;break-after:page}.page:last-child{break-after:auto}*{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
'''


def build():
    sections = []
    for i, (ch, title, accent, body, kicker, cls) in enumerate(pages, start=1):
        head = '' if cls == 'cover' else f'<header><span class="ch">{ch}</span><h1>{e(title)}</h1><span class="k">{e(kicker)}</span></header>'
        foot = '' if cls == 'cover' else f'<footer><span>GALE BREAKER · MANUAL DE DESIGN · EDIÇÃO {EDITION}</span><b>{i:02d}</b></footer>'
        sections.append(f'<section class="page {cls}" style="--a:{accent}" aria-label="Página {i} {e(title or "Capa")}">{head}<main>{body}</main>{foot}</section>')
    doc = (f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
           f'<title>Gale Breaker GDD</title><style>{CSS}</style></head><body>{"".join(sections)}</body></html>')
    (OUT / 'index.html').write_text(doc, encoding='utf-8')
    (OUT / 'page_index.json').write_text(json.dumps([{'page': i, 'title': p[1] or 'Capa'} for i, p in enumerate(pages, start=1)], ensure_ascii=False, indent=2), encoding='utf-8')
    if EDGE.exists():
        import tempfile
        profile = tempfile.mkdtemp(prefix='gdd-edge-')            # a running Edge would swallow the call
        before = PDF.stat().st_mtime if PDF.exists() else 0
        subprocess.run([str(EDGE), '--headless=new', '--disable-gpu', f'--user-data-dir={profile}', '--no-pdf-header-footer', '--run-all-compositor-stages-before-draw',
                        '--virtual-time-budget=8000', f'--print-to-pdf={PDF}', (OUT / 'index.html').as_uri()], check=True, timeout=180)
        import time                                              # Edge returns before the PDF is written
        for _ in range(240):
            if PDF.exists() and PDF.stat().st_mtime > before:
                size = -1
                while size != PDF.stat().st_size:
                    size = PDF.stat().st_size
                    time.sleep(1)
                break
            time.sleep(.5)
        assert PDF.exists() and PDF.stat().st_mtime > before, 'Edge did not write the PDF'
    print(f'{len(pages)} pages: index.html' + (f' and {PDF.name}' if EDGE.exists() else ''))


if __name__ == '__main__':
    build()
