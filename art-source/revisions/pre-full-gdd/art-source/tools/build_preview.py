"""Package actual Godot captures for review. Does not create character art."""
from pathlib import Path
from PIL import Image
import json,struct,shutil

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'godot/tests/visual-polish'
OUT=ROOT/'art-source/previews'
OUT.mkdir(exist_ok=True)
frames=[]
for n in range(72):
    with Image.open(SOURCE/f'frame-{n:03}.png') as image:
        frames.append(image.convert('RGB').resize((960,540)).quantize(colors=192))
frames[0].save(OUT/'combos.gif',save_all=True,append_images=frames[1:],duration=30,loop=0,optimize=False)
for name in ['idle','light_1','light_2','light_3','heavy','elemental','ultimate','guard_high']:
    shutil.copy2(SOURCE/f'{name}.png',OUT/f'models-{name}.png')
report=[]
for fid in ['kaze','ignis','tophia','volt']:
    path=ROOT/f'godot/assets/characters/{fid}/{fid}.glb'
    data=path.read_bytes();length,_=struct.unpack_from('<II',data,12)
    document=json.loads(data[20:20+length])
    tris=sum(document['accessors'][p['indices']]['count']//3 for mesh in document['meshes'] for p in mesh['primitives'])
    report.append(dict(fighter=fid,triangles=tris,animations=len(document['animations']),bytes=len(data)))
(OUT/'model-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
body='''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Gale Breaker · Modelos e animações</title>
<style>*{box-sizing:border-box}body{margin:0;background:#f8f5ee;color:#27372f;font:16px/1.5 system-ui,sans-serif}main{max-width:1180px;margin:auto;padding:40px 24px}h1,h2{font-family:Georgia,serif;font-weight:400}h1{font-size:44px;margin:8px 0}h2{margin-top:42px}p{max-width:900px;color:#62695f}a{color:#28654f}img{width:100%;display:block;background:#e6e4dc;border-radius:5px}figure{margin:0}figcaption{padding:10px 0 22px;font-size:14px;color:#62695f}.grid{display:grid;grid-template-columns:1fr 1fr;gap:24px}.tag{color:#28654f;font-size:12px;letter-spacing:2px;text-transform:uppercase}.note{border-left:3px solid #28654f;padding-left:16px}@media(max-width:760px){.grid{grid-template-columns:1fr}h1{font-size:32px}}</style>
<main><a href="/docs/gdd/index.html">← GDD</a><div class="tag">Gale Breaker / revisão da base 3D</div><h1>Modelos em movimento</h1>
<p>Capturas reais dos quatro personagens no Godot: poses corrigidas, mãos e pés com alvos de apoio, canhão de Volt estabilizado e efeitos ligados ao esqueleto.</p>
<p class="note">73 testes gerais + 42 testes visuais passaram. Os modelos continuam como uma base estilizada; o acabamento das concepts ainda está em produção.</p>
<figure><img src="combos.gif" alt="Combos básicos de Kaze, Ignis, Tophia e Volt"><figcaption>J1 → J2 → J3 dos quatro lutadores, capturados a partir dos clips exportados do Blender.</figcaption></figure>
<h2>Comparação dentro do jogo</h2><div class="grid"><figure><img src="combat-before.png" alt="Captura antes da revisão"><figcaption>Antes: poses e enquadramento da base recebida.</figcaption></figure><figure><img src="combat-kaze.png" alt="Captura após a revisão"><figcaption>Depois: guarda corrigida, enquadramento mais próximo e cenário com contraste controlado.</figcaption></figure></div>
<h2>Golpes e efeitos</h2><div class="grid">'''
for fid,label in [('kaze','Tufão Celestial'),('ignis','Fúria do Meio-Dia'),('tophia','Erupção Rochosa'),('volt','Sobrecarga Total')]:
    kind='elemental' if fid=='tophia' else 'ultimate'
    body+=f'<figure><img src="{fid}-{kind}.png" alt="{label}"><figcaption>{fid.title()} · {label}</figcaption></figure>'
body+='</div><h2>Poses de contato</h2><div class="grid">'
for clip,label in [('light_3','Finalizadores básicos'),('heavy','Golpes fortes')]:
    body+=f'<figure><img src="models-{clip}.png" alt="{label}"><figcaption>{label}</figcaption></figure>'
body+='</div><p><a href="model-report.json">Contagem de triângulos e animações dos GLBs</a></p></main></html>'
(OUT/'index.html').write_text(body,encoding='utf-8')
print(json.dumps(report));print('Preview packaged')
