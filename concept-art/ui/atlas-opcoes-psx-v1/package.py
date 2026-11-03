from pathlib import Path
from PIL import Image
import json
import zipfile

root = Path(__file__).resolve().parent
sheets = {
    'atlas-ui-opcoes-psx-v1.png': [
        'painel-pergaminho', 'papel-botao-normal', 'papel-botao-selecionado', 'papel-botao-hover',
        'slider-trilho', 'slider-marcador', 'oval-contorno', 'oval-preenchido',
        'seta-esquerda', 'seta-direita', 'confirmar', 'cancelar',
        'divisor-vertical', 'sublinhado-duplo', 'pino-latao', 'papel-acao-largo',
    ],
    'atlas-materiais-opcoes-psx-v1.png': [
        'madeira-pranchas', 'madeira-vigas', 'madeira-topo', 'latao',
        'telhas-azul-marinho', 'tecido-jade', 'tecido-marfim', 'vidro-ambar',
        'papel-marfim', 'papel-envelhecido', 'ferro-escuro', 'corda',
        'casca-arvore', 'musgo', 'folhagem', 'pedra-base',
    ],
}
manifest = {'version': 1, 'grid': [4, 4], 'origin': 'top-left', 'filter_recommended': 'nearest',
            'notes': ['Textos e valores ficam na engine.', 'Atlas com regiões: repetição da textura inteira mistura materiais.',
                      'Não foi certificado para repetição sem emendas ou mipmaps.'], 'atlases': []}
for file, ids in sheets.items():
    with Image.open(root / file) as im:
        w, h = im.size
        atlas = {'file': file, 'size_px': [w, h], 'mode': im.mode, 'cells': []}
        if 'A' in im.getbands():
            alpha = im.getchannel('A')
            atlas['alpha_range'] = list(alpha.getextrema())
            assert atlas['alpha_range'] == [0, 255]
        else:
            alpha = None
        for i, name in enumerate(ids):
            row, col = divmod(i, 4)
            x0, x1 = round(w * col / 4), round(w * (col + 1) / 4)
            y0, y1 = round(h * row / 4), round(h * (row + 1) / 4)
            item = {'id': name, 'row': row, 'column': col,
                    'rect_px': [x0, y0, x1-x0, y1-y0], 'uv_rect': [col/4, row/4, .25, .25]}
            if alpha:
                bbox = alpha.crop((x0, y0, x1, y1)).point(lambda p: 255 if p >= 128 else 0).getbbox()
                assert bbox is not None, name
                a, b, c, d = bbox
                item['opaque_content_rect_px'] = [x0+a, y0+b, c-a, d-b]
            atlas['cells'].append(item)
        manifest['atlases'].append(atlas)
(root / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
(root / 'LEIA-ME.txt').write_text('''ATLAS DE OPÇÕES — PAPEL E CANETA / PSX — V1

2 PNGs, 16 células por atlas (32 regiões), sem textos embutidos.
Interface: papéis normal/selecionado/hover, painel, trilho e marcador separados, ovais, setas, confirmar/cancelar, divisor, sublinhado e pino.
Materiais: madeiras, latão, telhas, tecidos, vidro âmbar, papéis, ferro, corda, casca, musgo, folhagem e pedra.
O manifest.json contém resolução real, modo de cor, retângulos em pixels e UVs. Interface RGBA com alfa; materiais RGB.

No Godot, use AtlasTexture com a region indicada. Renderize rótulos e valores separadamente. Recorte o marcador separado do trilho e mova-o conforme o valor. O retângulo opaque_content_rect_px indica o conteúdo principal, sem a margem transparente; rect_px preserva a célula inteira.
Para manter o PSX, comece com filtro Nearest e UI sem mipmaps. Regiões dentro de atlas não repetem independentemente: recorte o material ou use shader de remapeamento UV ao repetir.

Resolução nativa preservada: não houve ampliação artificial. Estes atlas são fontes artísticas para prototipagem; repetição sem emendas, dilatação de bordas e mipmaps de produção não foram certificados. Vidro é albedo opaco; transparência e emissão da lanterna são configuradas no material. Não inclui modelos 3D ou implementação da tela.
''', encoding='utf-8')
cards = ''.join('<section><h2>'+f.replace('.png','')+'</h2><img class="atlas" src="'+f+'" alt="Atlas de '+('interface' if 'atlas-ui' in f else 'materiais')+'"><ol>'+''.join('<li>'+n.replace('-',' ')+'</li>' for n in names)+'</ol><a download href="'+f+'">Baixar PNG</a></section>' for f,names in sheets.items())
(root / 'index.html').write_text('''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Atlas · Opções PSX</title><style>*{box-sizing:border-box}body{margin:0;background:#f7f1df;color:#183b2c;font:16px/1.6 system-ui}main{max-width:1100px;margin:auto;padding:32px 24px}h1,h2{font-family:Georgia,serif}a{color:#1b6745}img{width:100%;height:auto;display:block}.atlas{background-color:#b6baac;background-image:conic-gradient(#dadcd1 25%,transparent 0 50%,#dadcd1 0 75%,transparent 0);background-size:32px 32px}section{margin-top:40px}ol{columns:2}li{break-inside:avoid}</style><main><a href="../index.html">← Concepts de UI</a><h1>Opções · Papel e caneta / PSX</h1><p>Dois atlas e 32 regiões. Textos ficam separados, na engine.</p><p><a download href="Atlas_Opcoes_Papel_PSX_v1.zip">Baixar pacote</a> · <a href="manifest.json">Mapa de recortes</a> · <a href="LEIA-ME.txt">LEIA-ME</a></p>'''+cards+'</main></html>', encoding='utf-8')
files = list(sheets) + ['manifest.json', 'LEIA-ME.txt', 'index.html']
archive = root / 'Atlas_Opcoes_Papel_PSX_v1.zip'
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
    for file in files:
        z.write(root / file, 'atlas-opcoes-psx-v1/' + file)
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
print(json.dumps({'zip': str(archive), 'size_bytes': archive.stat().st_size,
                  'atlases': [{k:v for k,v in a.items() if k != 'cells'} for a in manifest['atlases']], 'regions': 32}))
