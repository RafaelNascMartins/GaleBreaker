from pathlib import Path
from PIL import Image
import json
import zipfile

ROOT = Path(__file__).resolve().parent
SHEETS = {
    'atlas-materiais-floresta-v1.png': [
        'caminho-arenoso', 'terra-umida', 'serrapilheira', 'grama',
        'casca-arvore', 'casca-galho', 'musgo-na-casca', 'pedra-laranja',
        'madeira-quadro', 'madeira-banco', 'topo-madeira', 'latao',
        'telhas-azul-marinho', 'tecido-jade', 'pergaminho', 'pedra-fundacao',
    ],
    'atlas-vegetacao-floresta-v1.png': [
        'monstera', 'folha-bananeira', 'folha-larga', 'folha-palmeira',
        'samambaia-folha', 'samambaia-touceira', 'cipo', 'galho-folhas',
        'hibisco', 'flores-brancas', 'tufo-grama', 'arbusto',
        'folha-seca', 'graveto-folhas', 'musgo-recorte', 'folhagem-pendente',
    ],
    'atlas-quadro-ui-floresta-v1.png': [
        'quadro-completo-vazio', 'telhado', 'banco', 'lanterna',
        'estandarte-jade', 'cantoneira-latao', 'pedras', 'raiz',
        'painel-pergaminho', 'botao-neutro', 'botao-selecionado', 'botao-hover',
        'slider', 'toggle-ligado', 'toggle-desligado', 'selo-confirmar',
    ],
}
manifest = {
    'version': 1,
    'purpose': 'Atlas conceitual para a floresta e o quadro de opções. Não é um kit de modelos 3D.',
    'concept': 'concept-passagem-folhas-v1.png',
    'grid': [4, 4],
    'coordinates': 'Origem no canto superior esquerdo; retângulos em pixels. UVs normalizadas [x, y, largura, altura].',
    'notes': [
        'Resolução nativa preservada; não houve ampliação artificial.',
        'Células de materiais não foram certificadas para repetição sem emendas.',
        'Imagens com transparência preservam o alfa gerado. Não houve certificação de dilatação, mipmaps ou halos.',
        'Textos e valores das opções devem ser renderizados pela engine.',
        'Banco, quadro e outros objetos são referências/sprites, não substituem modelos para movimento real de câmera.',
    ],
    'atlases': [],
}
for filename, names in SHEETS.items():
    with Image.open(ROOT / filename) as im:
        w, h = im.size
        entry = {'file': filename, 'size_px': [w, h], 'mode': im.mode, 'cells': []}
        if 'A' in im.getbands():
            entry['alpha_range'] = list(im.getchannel('A').getextrema())
        for i, name in enumerate(names):
            row, col = divmod(i, 4)
            x0, x1 = round(col*w/4), round((col+1)*w/4)
            y0, y1 = round(row*h/4), round((row+1)*h/4)
            entry['cells'].append({
                'id': name, 'row': row, 'column': col,
                'rect_px': [x0, y0, x1-x0, y1-y0],
                'uv_rect': [col/4, row/4, 0.25, 0.25],
                'repeat': 'none',
            })
        manifest['atlases'].append(entry)
(ROOT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
(ROOT / 'LEIA-ME.txt').write_text('''FLORESTA E QUADRO DE OPÇÕES — CONCEPT E ATLAS V1

Conteúdo: uma concept 1672×941 e três atlas 1254×1254, com 16 células por prancha (48 elementos).
Materiais em RGB; vegetação e quadro/interface em RGBA com transparência real.
O manifest.json descreve cada célula por nome, coordenadas e UVs. As células têm aproximadamente 313–314 px.

Transição sugerida: câmera avança por folhas próximas, atravessa o corredor entre troncos e desacelera ao revelar o quadro. A praia não aparece.
Use folhas em planos separados para paralaxe; troncos, chão, quadro e banco precisam de geometria para uma passagem com profundidade real. Desfoque e raios de luz ficam na engine.

Estes são atlas conceituais para referência e prototipagem. Não foram certificados como texturas repetíveis sem emendas nem para filtragem/mipmaps de produção. Os recortes preservam o alfa original gerado; revise bordas no material final. Não há modelos 3D nem animação de câmera neste pacote.
Renderize textos e valores da interface no Godot, separados dos sprites.
''', encoding='utf-8')
cards = []
for filename, names in SHEETS.items():
    cards.append('<section><h2>' + filename.replace('.png', '') + '</h2><img class="atlas" src="' + filename + '"><ol>' + ''.join('<li>' + n.replace('-', ' ') + '</li>' for n in names) + '</ol><a download href="' + filename + '">Baixar atlas</a></section>')
(ROOT / 'index.html').write_text('''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Floresta · Concept e atlas</title><style>*{box-sizing:border-box}body{margin:0;background:#f6f2e7;color:#203f31;font:16px/1.6 system-ui}main{max-width:1200px;margin:auto;padding:32px 24px}h1,h2{font-family:Georgia,serif}img{display:block;width:100%;height:auto}a{color:#216b4c}section{margin-top:48px}.atlas{background-color:#c3c5b7;background-image:conic-gradient(#dce0d3 25%,transparent 0 50%,#dce0d3 0 75%,transparent 0);background-size:32px 32px}ol{columns:2}li{break-inside:avoid}</style><main><a href="/concept-art/ui/index.html">← Concepts de UI</a><h1>Entre as árvores</h1><p>Passagem entre folhas até o quadro de opções. Apenas floresta ao fundo.</p><img src="concept-passagem-folhas-v1.png" alt="Vista entre árvores e folhas próximas com quadro ao fundo"><p><a download href="Floresta_Concept_Atlas_v1.zip">Baixar pacote completo</a> · <a href="manifest.json">Mapa das 48 células</a></p>''' + ''.join(cards) + '<p>Atlas conceituais para prototipagem. Leia o <a href="LEIA-ME.txt">LEIA-ME</a> para limites técnicos.</p></main></html>', encoding='utf-8')
files = list(SHEETS) + ['concept-passagem-folhas-v1.png', 'manifest.json', 'LEIA-ME.txt', 'index.html']
archive = ROOT / 'Floresta_Concept_Atlas_v1.zip'
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
    for filename in files:
        z.write(ROOT / filename, 'floresta-atlas/' + filename)
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
print(json.dumps({'zip': str(archive), 'files': len(files), 'cells': 48, 'size_bytes': archive.stat().st_size}))
