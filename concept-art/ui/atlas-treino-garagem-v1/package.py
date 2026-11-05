from pathlib import Path
from PIL import Image
import json
import zipfile

root = Path(__file__).resolve().parent
sheets = {
    'atlas-materiais-treino-garagem-v1.png': [
        'portao-canelado', 'aco-gasto', 'madeira-tabua', 'madeira-viga',
        'concreto', 'tijolo', 'reboco', 'telhado-metal',
        'tatame-jade', 'couro-saco-pancadas', 'borracha-pneu', 'tecido-jade',
        'latao', 'ferro', 'papelao', 'vidro-ambar',
    ],
    'atlas-inscricoes-treino-garagem-v1.png': [
        'treino', 'lutador', 'adversario', 'comportamento',
        'exibir-hitboxes', 'iniciar-treino', 'esc-voltar', 'kaze',
        'ignis', 'passivo', 'nao', 'sim',
        'seta-esquerda', 'seta-direita', 'indicador-selecao', 'sublinhado',
    ],
}
data = {'version': 1, 'grid': [4, 4], 'origin': 'top-left', 'atlases': [],
        'notes': ['Inscrições são tinta com transparência para aplicação sobre o portão.',
                  'Materiais não foram certificados como repetíveis sem emendas.',
                  'Sem mapas de normal, emissão ou modelos 3D neste pacote.']}
for file, names in sheets.items():
    with Image.open(root / file) as im:
        w, h = im.size
        alpha = im.getchannel('A') if 'A' in im.getbands() else None
        sheet = {'file': file, 'type': 'decal' if alpha else 'material', 'size_px': [w, h], 'mode': im.mode, 'cells': []}
        if alpha:
            sheet['alpha_range'] = list(alpha.getextrema())
            assert sheet['alpha_range'] == [0, 255]
        for i, name in enumerate(names):
            row, col = divmod(i, 4)
            x0, x1 = round(w*col/4), round(w*(col+1)/4)
            y0, y1 = round(h*row/4), round(h*(row+1)/4)
            cell = {'id': name, 'row': row, 'column': col, 'rect_px': [x0,y0,x1-x0,y1-y0],
                    'uv_rect': [col/4,row/4,.25,.25], 'repeat': 'none'}
            if alpha:
                bbox = alpha.crop((x0,y0,x1,y1)).point(lambda p: 255 if p>=128 else 0).getbbox()
                assert bbox, name
                a,b,c,d = bbox
                cell['opaque_content_rect_px'] = [x0+a,y0+b,c-a,d-b]
            sheet['cells'].append(cell)
        data['atlases'].append(sheet)
(root/'manifest.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
(root/'LEIA-ME.txt').write_text('''GARAGEM DE TREINOS — ATLAS V1

Dois atlas com 16 células cada: materiais RGB e inscrições RGBA transparentes, em resolução nativa. O manifest.json informa tamanho real e recortes em pixels/UVs. São 32 regiões de aproximadamente 313–314 px por lado.

O atlas de materiais cobre portão, aço, madeiras, concreto, tijolo, reboco, telhado, tatame, saco de pancadas, pneus, tecido, latão, ferro, papelão e vidro.
O atlas de inscrições contém a tinta das opções e os indicadores. Não contém placas ou fundos: aplique sobre a malha/material do portão, acompanhando seus UVs, ranhuras e iluminação. Para manter a tinta integrada, use albedo com alfa, não emissão. Valores e seleções devem continuar independentes para serem alterados no jogo. Os nomes e valores desta prancha são os exemplos da concept; outras escolhas podem ser renderizadas com fonte/material equivalente.

Cada célula de atlas é uma região: UV repeat comum repete o atlas inteiro. Para repetição de um material, use recorte individual ou remapeamento UV apropriado. Não foram certificados emendas invisíveis, dilatação de bordas ou mipmaps de produção. Vidro âmbar é albedo RGB; transparência e emissão da iluminação ficam no material. Não inclui modelos 3D nem implementação.

qa-inscricoes-sobre-metal.png é uma prévia das inscrições compostas sobre cinza, apenas para inspeção. O arquivo utilizável com alfa é atlas-inscricoes-treino-garagem-v1.png.
''',encoding='utf-8')
cards = ''.join('<section><h2>'+file.replace('.png','')+'</h2><img class="atlas" src="'+file+'" alt="Atlas da garagem de treinos"><ol>'+''.join('<li>'+n.replace('-',' ')+'</li>' for n in names)+'</ol><a href="'+file+'" download>Baixar PNG</a></section>' for file,names in sheets.items())
(root/'index.html').write_text('''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Atlas · Garagem de treino</title><style>*{box-sizing:border-box}body{margin:0;background:#f3eee3;color:#333c36;font:16px/1.6 system-ui}main{max-width:1100px;margin:auto;padding:32px 24px}h1,h2{font-family:Georgia,serif}a{color:#30684c}img{display:block;width:100%;height:auto}.atlas{background-color:#45525b;background-image:conic-gradient(#53616a 25%,transparent 0 50%,#53616a 0 75%,transparent 0);background-size:32px 32px}section{margin-top:40px}ol{columns:2}li{break-inside:avoid}</style><main><a href="../index.html">← Concepts de UI</a><h1>Garagem de treinos</h1><p>Materiais do cenário e tinta para as opções no portão. Dois atlas, 32 regiões.</p><p><a href="Atlas_Treino_Garagem_v1.zip" download>Baixar pacote</a> · <a href="manifest.json">Mapa de recortes</a> · <a href="LEIA-ME.txt">LEIA-ME</a></p>'''+cards+'<section><h2>Inscrições sobre cinza</h2><img src="qa-inscricoes-sobre-metal.png" alt="Inscrições compostas sobre cinza para inspeção"></section></main></html>',encoding='utf-8')
files = list(sheets)+['manifest.json','LEIA-ME.txt','index.html','qa-inscricoes-sobre-metal.png']
archive = root/'Atlas_Treino_Garagem_v1.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for file in files:
        z.write(root/file,'atlas-treino-garagem-v1/'+file)
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
print(json.dumps({'zip':str(archive),'files':len(files),'regions':32,'bytes':archive.stat().st_size,
                  'images':[{k:v for k,v in s.items() if k!='cells'} for s in data['atlases']]}))
