from pathlib import Path
from PIL import Image
import json
import zipfile

ROOT = Path(__file__).resolve().parent
SHEETS = {
    'atlas-casas-pedras-madeiras-v1.png': [
        'reboco-branco', 'reboco-envelhecido', 'alvenaria-calcario', 'pedra-laranja',
        'calcamento-pedras', 'pedra-degraus', 'terra-arenosa', 'pedra-musgo',
        'madeira-stand-mobiliario', 'madeira-vigas-postes', 'madeira-persianas-jade', 'madeira-clara-caixas',
        'terracota-vasos', 'ceramica-marfim', 'latao-lanternas', 'ferro-suportes',
    ],
    'atlas-tecidos-acessorios-v1.png': [
        'lona-jade-stand', 'tecido-estandarte', 'almofada-marfim', 'almofada-salvia',
        'tapete-palha', 'tapete-trama-verde', 'toalha-branca', 'toalha-listrada',
        'corda', 'papel-etiquetas', 'bronze-grade-lanterna', 'vidro-ambar-lanterna',
        'casca-arvore', 'musgo', 'madeira-placas', 'vime-cesto',
    ],
    'atlas-recortes-ornamentos-v1.png': [
        'emblema-vento-marfim', 'ornamento-vaso-marfim', 'ornamento-ceramica-jade', 'motivo-ondas-almofada',
        'hibisco', 'flores-brancas', 'bougainvillea', 'monstera',
        'ramo-folhas', 'cipo', 'petalas-caidas', 'sublinhado-jade',
        'seta-esquerda', 'seta-direita', 'etiqueta-vazia', 'pino-latao',
    ],
}
CUTOUTS = {'hibisco', 'flores-brancas', 'bougainvillea', 'monstera', 'ramo-folhas', 'cipo', 'etiqueta-vazia', 'pino-latao'}
manifest = {
    'version': 1,
    'concept': 'concept-patio-babuin-v6.png',
    'roof_textures_included': False,
    'grid': [4, 4],
    'origin': 'top-left',
    'purpose': 'Fontes artísticas do pátio, casas, stand de roupas e área de descanso.',
    'coverage': {
        'casas': ['rebocos', 'alvenaria', 'madeiras', 'persianas'],
        'pedras': ['calcamento', 'degraus', 'pedra-laranja', 'pedra-musgo'],
        'lanternas': ['latao-lanternas', 'bronze-grade-lanterna', 'ferro-suportes', 'vidro-ambar-lanterna'],
        'board-stand': ['madeira-stand-mobiliario', 'madeira-placas', 'lona-jade-stand', 'corda', 'papel-etiquetas'],
        'descanso': ['tapetes', 'almofadas', 'toalhas', 'vime'],
        'vasos': ['terracota-vasos', 'ceramica-marfim', 'ornamentos'],
    },
    'notes': [
        'Coordenadas de cada célula e conteúdo principal em pixels, UVs normalizadas.',
        'Materiais em RGB; recortes e ornamentos em RGBA com alfa preservado.',
        'Não certificado para repetição sem emendas, dilatação de bordas ou mipmaps.',
        'Textos, retrato de Babuin, personagem e roupas são assets separados das texturas do ambiente.',
    ],
    'atlases': [],
}
for file, names in SHEETS.items():
    with Image.open(ROOT / file) as im:
        w, h = im.size
        alpha = im.getchannel('A') if 'A' in im.getbands() else None
        sheet = {'file': file, 'size_px': [w, h], 'mode': im.mode, 'cells': []}
        if alpha:
            sheet['alpha_range'] = list(alpha.getextrema())
            assert sheet['alpha_range'] == [0, 255]
        for i, name in enumerate(names):
            row, col = divmod(i, 4)
            x0, x1 = round(w*col/4), round(w*(col+1)/4)
            y0, y1 = round(h*row/4), round(h*(row+1)/4)
            item = {'id': name, 'row': row, 'column': col,
                    'type': ('cutout' if name in CUTOUTS else 'decal') if alpha else 'material',
                    'rect_px': [x0, y0, x1-x0, y1-y0],
                    'uv_rect': [col/4, row/4, .25, .25], 'repeat': 'none'}
            if alpha:
                bbox = alpha.crop((x0,y0,x1,y1)).point(lambda p: 255 if p >= 128 else 0).getbbox()
                assert bbox is not None, name
                a,b,c,d = bbox
                item['opaque_content_rect_px'] = [x0+a,y0+b,c-a,d-b]
            sheet['cells'].append(item)
        manifest['atlases'].append(sheet)
assert sum(len(a['cells']) for a in manifest['atlases']) == 48
(ROOT / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
(ROOT / 'LEIA-ME.txt').write_text('''PÁTIO DAS CASAS — CONCEPT E ATLAS V1

Concept atualizada: somente a ficha de Babuin; fichas de Ignis, Tophia e Volt removidas. Stand e área de descanso preservados.

Três atlas, 16 células cada (48 regiões):
1. Casas, pedras e madeiras: rebocos, alvenaria, calçamento, degraus, pedra laranja, pedra com musgo, madeiras, persianas jade, terracota, cerâmica, latão e ferro.
2. Tecidos e acessórios: lona do stand, estandarte, almofadas, tapetes, toalhas, corda, papel, bronze, vidro âmbar, casca, musgo, madeira de placas e vime.
3. Recortes e ornamentos: emblema, desenhos de vasos/almofadas, flores, folhas, cipó, pétalas, sublinhado, setas, etiqueta vazia e pino.
Não inclui texturas de telhado. A lona é o tecido do stand.

As três imagens mantêm sua resolução nativa de 1254×1254. Cada célula ocupa aproximadamente 313–314 px por lado. Os dois atlas de superfícies são RGB; recortes/ornamentos RGBA com alfa. manifest.json contém nomes, retângulos em pixels e UVs. opaque_content_rect_px indica o conteúdo principal dos recortes, sem margens.

Use as regiões na UV/AtlasTexture. Repetir UV comum repete o atlas inteiro, não a célula: materiais que precisarem repetir requerem recorte ou remapeamento UV. Estas são fontes artísticas para prototipagem; não houve certificação de emendas invisíveis, dilatação ou mipmaps de produção. Ajuste a densidade de texel conforme a câmera final.
Vidro âmbar é albedo RGB; emissão/transparência da lanterna são configurações do material no Godot. O metal fornece a cor da armação; grades, cantos e suportes precisam de geometria. Recortes foram inspecionados compostos sobre jade; a prévia de QA não substitui o PNG com alfa.
Textos das placas, retrato, personagem e roupas continuam separados; as referências desses trajes já existem na pasta de Babuin. Não inclui modelos 3D ou implementação da tela.
''', encoding='utf-8')
cards = []
for file, names in SHEETS.items():
    cards.append('<section><h2>'+file.replace('atlas-','').replace('-v1.png','').replace('-',' ')+'</h2><img class="atlas" src="'+file+'" alt="Atlas de materiais do pátio"><ol>'+''.join('<li>'+n.replace('-',' ')+'</li>' for n in names)+'</ol><a download href="'+file+'">Baixar PNG</a></section>')
(ROOT / 'index.html').write_text('''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Pátio · Concept e atlas</title><style>*{box-sizing:border-box}body{margin:0;background:#f5efe1;color:#234333;font:16px/1.6 system-ui}main{max-width:1200px;margin:auto;padding:32px 24px}h1,h2{font-family:Georgia,serif;text-transform:capitalize}a{color:#2b6b4b}img{display:block;width:100%;height:auto}section{margin-top:42px}ol{columns:2}li{break-inside:avoid}.atlas{background-color:#394c45;background-image:conic-gradient(#52665c 25%,transparent 0 50%,#52665c 0 75%,transparent 0);background-size:32px 32px}</style><main><a href="../index.html">← Galeria de UI</a><h1>Pátio das casas</h1><p>Somente Babuin na ficha. Stand, descanso e materiais do cenário; telhados excluídos.</p><img src="concept-patio-babuin-v6.png" alt="Concept do pátio com somente a ficha de Babuin"><p><a download href="Patio_Casas_Atlas_v1.zip">Baixar pacote completo</a> · <a href="manifest.json">Mapa das 48 regiões</a> · <a href="LEIA-ME.txt">LEIA-ME</a></p>'''+''.join(cards)+'<section><h2>Inspeção de transparência</h2><img src="qa-recortes-sobre-jade.png" alt="Recortes compostos sobre fundo jade para inspeção"></section></main></html>', encoding='utf-8')
files = list(SHEETS) + ['concept-patio-babuin-v6.png', 'manifest.json', 'LEIA-ME.txt', 'index.html', 'qa-recortes-sobre-jade.png']
archive = ROOT / 'Patio_Casas_Atlas_v1.zip'
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
    for file in files:
        z.write(ROOT / file, 'atlas-patio-casas-v1/' + file)
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
print(json.dumps({'zip':str(archive),'files':len(files),'regions':48,'bytes':archive.stat().st_size,
                  'atlases':[{k:v for k,v in a.items() if k!='cells'} for a in manifest['atlases']]}))
