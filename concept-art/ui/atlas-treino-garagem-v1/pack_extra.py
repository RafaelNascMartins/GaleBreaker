from pathlib import Path
from PIL import Image
import json
import zipfile
import hashlib

BASE=Path(__file__).resolve().parent
ROOT=BASE/'extra-v1'


def export():
    data=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
    cells=data['atlases'][0]['cells']
    assert len(cells)==16
    for i,c in enumerate(cells):
        with Image.open(ROOT/c['file']) as im:
            assert im.mode==('RGB' if i<8 else 'RGBA'), c['id']
            if i>=8:
                a=im.getchannel('A')
                assert a.getextrema()[0]==0
                assert a.crop((0,0,im.width,1)).getextrema()[1]==0
                assert a.crop((0,im.height-1,im.width,im.height)).getextrema()[1]==0
    parent=json.loads((BASE/'manifest.json').read_text(encoding='utf-8'))
    assert len(parent['atlases'])==3
    assert sum(len(a['cells']) for a in parent['atlases'])==48
    qa=json.loads((ROOT/'validation-godot.json').read_text(encoding='utf-8'))
    assert qa['passed']
    parent_gallery=BASE/'index.html'
    html=parent_gallery.read_text(encoding='utf-8')
    html=html.replace('Dois atlas, 32 regiões.', 'Três atlas, 48 regiões e fonte estêncil.')
    html=html.replace('Atlas_Treino_Garagem_v1.zip', 'Atlas_Treino_Garagem_Completo_v2.zip')
    parent_gallery.write_text(html,encoding='utf-8')
    extra_files=[p for p in ROOT.rglob('*') if p.is_file() and 'sources' not in p.relative_to(ROOT).parts
                 and p.suffix.lower() not in {'.zip','.py','.pyc','.import'}]
    standalone=ROOT/'Garagem_Detalhes_Fonte_v1.zip'
    with zipfile.ZipFile(standalone,'w',zipfile.ZIP_DEFLATED) as z:
        for p in extra_files:
            z.write(p,'extra-v1/'+p.relative_to(ROOT).as_posix())
    combined=BASE/'Atlas_Treino_Garagem_Completo_v2.zip'
    base_files=[BASE/x for x in ['atlas-materiais-treino-garagem-v1.png',
                                'atlas-inscricoes-treino-garagem-v1.png','manifest.json',
                                'LEIA-ME.txt','index.html','qa-inscricoes-sobre-metal.png']]
    combined_readme='''GARAGEM — PACOTE COMPLETO V2

Os dois atlas originais continuam incluídos. O terceiro atlas tem 16 detalhes extras.
O manifest principal mantém o esquema anterior e agora descreve 48 células; o campo fonts aponta para a TTF, FNT e manifest da fonte.

Veja extra-v1/LEIA-ME.txt para formatos RGB/RGBA, quatro ferramentas separadas, corrente repetível em X, shader aditivo dos feixes e uso das fontes. extra-v1/fonts/ contém a fonte vetorial original do projeto e a fonte bitmap com desgaste; a correspondência com as letras da concept é aproximada, não uma identificação exata.

Nomes disponíveis: BABUIN, TOPHIA, VOLT, IGNIS e KAZE.
Comportamentos atuais do jogo: PASSIVO, DEFENDE ALTO, DEFENDE BAIXO, PULA e IA.
Os dois formatos de fonte foram carregados no Godot 4.7.2 e verificaram todos os nomes, comportamentos e acentos usados. Resultado em extra-v1/validation-godot.json.

As imagens não foram instaladas no menu do jogo nem aplicadas automaticamente a modelos 3D.
'''
    with zipfile.ZipFile(combined,'w',zipfile.ZIP_DEFLATED) as z:
        for p in base_files:
            if p.name=='LEIA-ME.txt':
                z.writestr('atlas-treino-garagem-v2/LEIA-ME.txt',combined_readme)
            else:
                z.write(p,'atlas-treino-garagem-v2/'+p.name)
        for p in extra_files:
            z.write(p,'atlas-treino-garagem-v2/extra-v1/'+p.relative_to(ROOT).as_posix())
    summary={'cells_extra':16,'cells_total':48,'font_glyphs':191,'font_engine_test':qa,
             'archives':[]}
    for file in [standalone,combined]:
        with zipfile.ZipFile(file) as z:
            assert z.testzip() is None
            count=len(z.namelist())
        summary['archives'].append({'file':str(file),'bytes':file.stat().st_size,'entries':count,
                                    'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
    (ROOT/'verification-package.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False))


if __name__=='__main__':export()
