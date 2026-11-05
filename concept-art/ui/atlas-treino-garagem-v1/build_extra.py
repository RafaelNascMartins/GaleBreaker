from pathlib import Path
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
import numpy as np
import json
import shutil
import zipfile
import hashlib
from font_package import build_font, WORDS

BASE=Path(__file__).resolve().parent
ROOT=BASE/'extra-v1'
REPO=BASE.parents[2]
SIZE=1254
IDS=['saco-pancadas-costura','anilha-sextavada-10','cabo-serrilhado','painel-perfurado',
     'concreto-oleo-pegadas','madeira-wing-chun','lona-equipamento','corrente',
     'ferramentas','janela-interior','lampada-pendente','lanterna-bancada',
     'toalha-listra-jade','caneca-branca','feixes-luz','respingos-tinta']


def region(i):
    row,col=divmod(i,4)
    x0,x1=round(col*SIZE/4),round((col+1)*SIZE/4)
    y0,y1=round(row*SIZE/4),round((row+1)*SIZE/4)
    return x0,y0,x1,y1


def clean_alpha(image, additive=False):
    arr=np.array(image.convert('RGBA'))
    a=arr[:,:,3].copy()
    if additive:
        yy,xx=np.indices(a.shape)
        edge=np.minimum.reduce([xx,yy,a.shape[1]-1-xx,a.shape[0]-1-yy])
        a=np.round(a.astype(float)*np.clip(edge/10.0,0,1)).astype('uint8')
        arr[:,:,3]=a
        return Image.fromarray(arr)
    mask=a>=128
    labels,n=ndi.label(mask)
    areas=np.bincount(labels.ravel())
    keep=areas>=4; keep[0]=False
    mask=keep[labels]
    inside=ndi.distance_transform_edt(mask)
    outside=ndi.distance_transform_edt(~mask)
    aa=np.zeros_like(a)
    aa[mask]=255
    border=mask & (inside<=1)
    aa[border]=np.maximum(a[border],128)
    fringe=(~mask)&(outside<=1)&(a>4)
    aa[fringe]=np.minimum(a[fringe],127)
    # RGB bleed from opaque interiors, including transparent holes and outer edge.
    core=aa==255
    assert core.any()
    dist,indices=ndi.distance_transform_edt(~core,return_indices=True)
    near=(dist<=16)&(~core)
    rgb=arr[:,:,:3].copy()
    rgb[near]=rgb[indices[0][near],indices[1][near]]
    rgb[(aa==0)&(dist>16)]=0
    arr[:,:,:3]=rgb; arr[:,:,3]=aa
    return Image.fromarray(arr)


def chain_strip(cell):
    arr=np.asarray(cell.convert('RGB')).astype(float)
    band=arr[round(cell.height*.31):round(cell.height*.69)]
    candidates=range(80,min(165,cell.width//2+1))
    period=min(candidates,key=lambda p:np.mean(np.abs(band[:,p:]-band[:,:-p])))
    start=min(range(0,cell.width-period+1),key=lambda x:np.mean(np.abs(band[:,x]-band[:,x+period-1])))
    out=np.array(cell.crop((start,0,start+period,cell.height)))
    for i in range(4):
        avg=((out[:,i].astype(float)+out[:,-1-i].astype(float))/2).round().astype('uint8')
        out[:,i]=avg; out[:,-1-i]=avg
    im=Image.fromarray(out)
    assert np.array_equal(np.array(im)[:,0],np.array(im)[:,-1])
    return im,period,start


def build():
    tex=ROOT/'textures'; tex.mkdir(exist_ok=True,parents=True)
    surfaces=Image.open(ROOT/'sources/detalhes-rgb-source.png').convert('RGB')
    cutouts=Image.open(ROOT/'sources/recortes-source.png').convert('RGBA')
    atlas=Image.new('RGBA',(SIZE,SIZE),(0,0,0,0))
    entries=[]
    for i,name in enumerate(IDS):
        x0,y0,x1,y1=region(i); w,h=x1-x0,y1-y0
        if i<8:
            cell=surfaces.crop((x0,y0,x1,y1)).convert('RGB')
        else:
            j=i-8; row,col=divmod(j,4)
            sw,sh=cutouts.size
            raw=cutouts.crop((round(col*sw/4),round(row*sh/2),round((col+1)*sw/4),round((row+1)*sh/2)))
            cell=clean_alpha(raw.resize((w,h),Image.Resampling.LANCZOS),additive=i==14)
        file=f'textures/{i+1:02d}_{name}.png'
        cell.save(ROOT/file)
        atlas.paste(cell.convert('RGBA'),(x0,y0))
        item={'id':name,'row':i//4,'column':i%4,'rect_px':[x0,y0,w,h],
              'uv_rect':[i%4/4,i//4/4,.25,.25], 'repeat':'none',
              'type':'material' if i<8 else ('effect' if i==14 else 'cutout'),
              'file':file,'mode':cell.mode,'size_px':[w,h]}
        if i>=8:
            a=np.asarray(cell)[:,:,3]
            assert a.min()==0
            assert (a==255).any() or i==14
            item['alpha_range']=[int(a.min()),int(a.max())]
            bbox=cell.getchannel('A').point(lambda p:255 if p>=128 else 0).getbbox()
            if bbox:
                l,t,r,b=bbox; item['opaque_content_rect_px']=[x0+l,y0+t,r-l,b-t]
            item['blend']='add' if i==14 else 'mix'
        if i==7:
            strip,period,start=chain_strip(cell)
            strip.save(tex/'08_corrente_faixa-x.png')
            preview=Image.new('RGB',(strip.width*3,strip.height))
            for k in range(3):preview.paste(strip,(k*strip.width,0))
            preview.save(ROOT/'preview-corrente-3x.png')
            item['repeat_file']='textures/08_corrente_faixa-x.png'
            item['repeat_file_size_px']=list(strip.size)
            item['repeat_file_axis']='x'
            item['repeat_file_source_rect_px']=[start,0,period,cell.height]
        if i==8:
            mask=np.asarray(cell.getchannel('A'))>=128
            labels,n=ndi.label(mask)
            areas=np.bincount(labels.ravel()); areas[0]=0
            selected=sorted(range(1,n+1),key=lambda c:areas[c],reverse=True)[:4]
            selected.sort(key=lambda c:int(np.where(labels==c)[1].min()))
            names=['chave-boca','chave-estrela','martelo','alicate']
            item['subsprites']=[]
            for name2,c in zip(names,selected):
                ys,xs=np.where(labels==c)
                l,t=max(0,int(xs.min())-3),max(0,int(ys.min())-3)
                r,b=min(w,int(xs.max())+4),min(h,int(ys.max())+4)
                tool=cell.crop((l,t,r,b))
                sub=f'textures/09_{name2}.png';tool.save(ROOT/sub)
                item['subsprites'].append({'id':name2,'file':sub,'rect_px':[x0+l,y0+t,r-l,b-t]})
            assert len(item['subsprites'])==4
        entries.append(item)
    atlas.save(ROOT/'atlas-detalhes-garagem-v1.png')
    alpha=np.asarray(atlas)[:,:,3]
    assert (alpha[:627]==255).all()
    yy,xx=np.indices((SIZE,SIZE))
    check=np.where(((xx//24+yy//24)%2)[:,:,None],np.array([67,79,84]),np.array([101,112,115]))
    bg=Image.fromarray(check.astype('uint8')).convert('RGBA');bg.alpha_composite(atlas)
    bg.convert('RGB').save(ROOT/'preview-atlas-checker.png')
    glass=entries[14]
    beam=Image.open(ROOT/glass['file'])
    proof=Image.new('RGBA',beam.size,(0,0,0,255));proof.alpha_composite(beam)
    proof.convert('RGB').save(ROOT/'preview-feixes-preto.png')
    font=build_font(ROOT,REPO)
    local={'version':1,'grid':[4,4],'origin':'top-left',
           'atlases':[{'file':'atlas-detalhes-garagem-v1.png','type':'mixed','size_px':[SIZE,SIZE],
                       'mode':'RGBA','cells':entries}],
           'fonts':{'manifest':'fonts/manifest-fonte.json','ttf':'fonts/StardosStencil-Bold.ttf',
                    'bitmap':'fonts/PortaoStencil-Desgastado.fnt'},
           'notes':['Células 1–8: arquivos individuais RGB; 9–16: RGBA.',
                    'O atlas misto é RGBA: regiões de superfície têm alfa 255.',
                    'A faixa de corrente separada repete em X; não repetir o atlas inteiro.',
                    'Feixes de luz mantêm alfa gradual e usam mistura aditiva.']}
    (ROOT/'manifest.json').write_text(json.dumps(local,ensure_ascii=False,indent=2),encoding='utf-8')
    parent_path=BASE/'manifest.json'
    parent=json.loads(parent_path.read_text(encoding='utf-8'))
    backup=BASE/'manifest-antes-extra-v1.json'
    if not backup.exists():shutil.copy2(parent_path,backup)
    parent['atlases']=[a for a in parent['atlases'] if a['file']!='extra-v1/atlas-detalhes-garagem-v1.png']
    entry=json.loads(json.dumps(local['atlases'][0]))
    entry['file']='extra-v1/'+entry['file']
    for c in entry['cells']:
        c['file']='extra-v1/'+c['file']
        if 'repeat_file' in c:c['repeat_file']='extra-v1/'+c['repeat_file']
        for sub in c.get('subsprites',[]):sub['file']='extra-v1/'+sub['file']
    parent['atlases'].append(entry)
    parent['fonts']={k:'extra-v1/'+v for k,v in local['fonts'].items()}
    parent_path.write_text(json.dumps(parent,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'feixes-add.canvas.gdshader').write_text('''shader_type canvas_item;
render_mode blend_add, unshaded;
uniform float gain : hint_range(0.0, 4.0) = 1.0;
uniform vec4 light_tint : source_color = vec4(1.0);
void fragment() {
    vec4 beam = texture(TEXTURE, UV);
    COLOR = vec4(beam.rgb * light_tint.rgb * gain, beam.a * light_tint.a);
}
''',encoding='utf-8')
    (ROOT/'LEIA-ME.txt').write_text('''DETALHES EXTRA DA GARAGEM — V1

Atlas 4×4, 1254×1254, no mesmo esquema do manifest anterior. O manifest principal foi ampliado para 48 células; manifest.json deste subdiretório descreve somente as 16 novas. Cada célula tem 313–314 px por lado, em resolução nativa das superfícies. Recortes foram reduzidos da fonte maior.

1 saco com costura/faixa; 2 anilha sextavada 10; 3 cabo serrilhado; 4 pegboard; 5 concreto escuro; 6 madeira wing chun; 7 lona EQUIP.; 8 corrente; 9 ferramentas; 10 janela; 11 pendente; 12 lanterna; 13 toalha; 14 caneca; 15 feixes; 16 respingos.

O atlas único é RGBA por conter materiais e recortes. Em textures/, as superfícies 1–8 são RGB sem alfa e os recortes 9–16 são RGBA. As quatro ferramentas também têm PNGs separados e sub-regiões no manifest. Os recortes sólidos têm interiores alfa 255, borda curta antialiasada e RGB dilatado 16 px; os feixes preservam o degradê.
A corrente tem faixa separada repetível em X e prévia 3×. Suas colunas extremas foram igualadas após extração de um período; a prévia permite avaliar a repetição. Os demais materiais não foram certificados para repetição sem emendas. Não repita o atlas inteiro para repetir uma célula.
Para feixes, use mistura aditiva (shader canvas incluído) e reduza gain conforme iluminação. Em 3D, use material transparente aditivo numa malha plana com teste de profundidade; não use como superfície opaca. O PNG mantém a intensidade e alfa graduais.

FONTE DO PORTÃO
fonts/StardosStencil-Bold.ttf é a fonte vetorial que já existia no projeto, com sua licença OFL. É uma aproximação tipográfica reutilizável da arte das inscrições; a concept gerada não identifica uma fonte exata. O desenho da TTF não foi modificado.
fonts/PortaoStencil-Desgastado.fnt + página PNG formam uma fonte bitmap Unicode (ASCII e Latin-1) no mesmo desenho, com pequenos desgastes na tinta. Copie os dois juntos para o projeto. Cobre nomes, acentos, números, pontuação e os comportamentos do jogo, incluindo minúsculas.
fonts/palavras-portao.png e os PNGs em fonts/palavras/ incluem BABUIN, TOPHIA, VOLT, IGNIS, KAZE, PASSIVO, DEFENDE ALTO, DEFENDE BAIXO, PULA, IA, SIM, NÃO e rótulos do menu. O mapa está em fonts/manifest-fonte.json. Novas palavras podem ser renderizadas com a TTF ou FNT.
Para manter texto integrado ao portão, aplique a tinta no albedo/UV da chapa, com a iluminação e normal do metal, em vez de emissão. A fonte bitmap tem tamanho de origem 64 px; para textos grandes prefira a TTF.

Arquivos de referência em sources/ preservam a geração original e não entram no ZIP. A geração inicial mista tinha alfa incorreto; as superfícies e recortes foram exportados em formatos próprios e verificados. O pacote não inclui modelos 3D nem altera o menu do jogo.
''',encoding='utf-8')
    cards=''.join('<li>'+name.replace('-',' ')+'</li>' for name in IDS)
    (ROOT/'index.html').write_text('''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Garagem · Detalhes e fonte</title><style>body{margin:0;background:#eee9dd;color:#283b32;font:16px/1.6 system-ui}main{max-width:1200px;margin:auto;padding:32px 24px}h1,h2{font-family:Georgia,serif}img{width:100%;height:auto;display:block}ol{columns:2}a{color:#23634a}section{margin-top:40px}</style><main><a href="../index.html">← Atlas da garagem</a><h1>Detalhes da garagem e fonte estêncil</h1><p>16 células, materiais RGB, recortes RGBA, ferramentas separadas e fonte dinâmica.</p><p><a href="Garagem_Detalhes_Fonte_v1.zip" download>Baixar complemento</a> · <a href="manifest.json">Manifest</a> · <a href="LEIA-ME.txt">LEIA-ME</a></p><img src="preview-atlas-checker.png" alt="Atlas sobre xadrez de transparência"><ol>'''+cards+'''</ol><section><h2>Fonte e palavras do menu</h2><p><a href="fonts/StardosStencil-Bold.ttf" download>Fonte TTF</a> · <a href="fonts/PortaoStencil-Desgastado.fnt" download>Fonte bitmap desgastada</a> · <a href="fonts/manifest-fonte.json">Mapa da fonte</a></p><img src="preview-fonte-palavras.png" alt="Nomes e comportamentos em estêncil"></section><section><h2>Corrente repetida 3×</h2><img src="preview-corrente-3x.png" alt="Faixa repetida de corrente"></section><section><h2>Feixes sobre preto</h2><img src="preview-feixes-preto.png" alt="Feixes translúcidos sobre preto"></section></main></html>''',encoding='utf-8')
    # Link from the existing gallery without replacing the earlier assets.
    gallery=BASE/'index.html'; html=gallery.read_text(encoding='utf-8')
    link='<p><a href="extra-v1/index.html">Novo: detalhes extras e fonte estêncil</a></p>'
    if 'extra-v1/index.html' not in html:
        html=html.replace('<h1>Garagem de treinos</h1>','<h1>Garagem de treinos</h1>'+link)
        gallery.write_text(html,encoding='utf-8')
    validation={'cells':len(entries),'surface_files':8,'rgba_files':8,'tools':4,
                'font_glyphs':font['glyphs'],'words':WORDS,'size_px':[SIZE,SIZE],
                'top_half_alpha_255':bool((alpha[:627]==255).all()),
                'chain_first_last_columns_equal':True}
    (ROOT/'validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(validation,ensure_ascii=False))


if __name__=='__main__':build()
