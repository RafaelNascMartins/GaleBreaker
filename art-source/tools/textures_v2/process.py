"""Deterministic technical finishing explicitly requested for textures-v2.

No creative material is synthesized here. ImageGen supplies each individual
painted source; this code performs UV-periodic quilting, exact sizing, alpha
normalization/color dilation, paired emission extraction and QA previews.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import argparse, hashlib, json, math, time, zipfile
import numpy as np
from PIL import Image, ImageDraw, ImageOps, PngImagePlugin
from scipy import ndimage as ndi
from catalog import ROOT, WORK, JOBS

PACKAGE=WORK/'package'
TEXTURES=PACKAGE/'textures-v2'
QA=WORK/'qa'
PIPELINE_VERSION=4
STRUCTURED={'piso-calcario','telhas-azul-ardosia','parede-arenito','azulejo-cobalto-marfim','piso-basalto','tijolos-escuros','tijolo-branco','telhas-azul-marinho'}

def save_png(image:Image.Image,path:Path):
    path.parent.mkdir(parents=True,exist_ok=True)
    info=PngImagePlugin.PngInfo()
    info.add(b'sRGB',b'\x00')
    image.save(path,format='PNG',pnginfo=info,compress_level=6)

def shortest_cut(cost:np.ndarray, closed=False):
    """Minimum-error overlap path; closed paths join on torus boundaries."""
    cost=cost.astype(np.float32)
    length,width=cost.shape
    guard=max(4,min(20,width//12))
    cost[:,:guard]=1e12;cost[:,-guard:]=1e12
    if closed:
        ordered=np.argsort(cost.mean(axis=0))
        starts=[]
        for n in ordered:
            if guard<=n<width-guard and all(abs(int(n)-s)>max(8,width//10) for s in starts):starts.append(int(n))
            if len(starts)==4:break
    else:starts=[None]
    best_score=math.inf;best_path=None
    for start in starts:
        previous=cost[0].copy()
        if start is not None:
            previous[:]=1e12;previous[start]=cost[0,start]
        back=np.zeros((length,width),np.int8)
        for row in range(1,length):
            neighbors=np.stack([np.r_[1e12,previous[:-1]],previous,np.r_[previous[1:],1e12]])
            choice=neighbors.argmin(axis=0)
            previous=cost[row]+neighbors[choice,np.arange(width)]
            back[row]=choice.astype(np.int8)-1
        end=int(previous.argmin()) if start is None else start
        score=float(previous[end])
        if score<best_score:
            path=np.empty(length,np.int32);path[-1]=end
            for row in range(length-1,0,-1):path[row-1]=path[row]+back[row,path[row]]
            best_score=score;best_path=path
    return best_path,best_score/max(1,length)

def wrap_horizontal(source:np.ndarray,period:int,closed=False):
    """Overlap two copies, cut inside the overlap; the wrap uses adjacent pixels."""
    overlap=source.shape[1]-period
    assert overlap>=16
    left=source[:,:overlap].astype(np.float32)
    right=source[:,period:period+overlap].astype(np.float32)
    # Color + local gradient agreement preserves visible grout/vein structure.
    diff=((left-right)**2).mean(axis=2)
    gl=np.diff(left,axis=1,prepend=left[:,:1]);gr=np.diff(right,axis=1,prepend=right[:,:1])
    cost=diff+((gl-gr)**2).mean(axis=2)*.35
    path,score=shortest_cut(cost,closed)
    width=np.arange(overlap)[None,:]
    feather=3.0
    weight=np.clip((width-path[:,None]+feather)/(feather*2),0,1)
    weight=weight*weight*(3-2*weight)
    result=source[:,:period].astype(np.float32).copy()
    result[:,:overlap]=right*(1-weight[:,:,None])+left*weight[:,:,None]
    return result,score

def matching_period(rgb:np.ndarray,target:int):
    """Choose an integer phase near native resolution for bricks/ceramic grids."""
    length=rgb.shape[1]
    first=max(int(length*.70),min(target,length-80))
    last=length-max(64,int(length*.08))
    if first>=last:return max(16,int(length*.8))
    sample=rgb[::4].astype(np.float32)
    gradient=np.diff(sample,axis=1,prepend=sample[:,:1])
    best=None
    for p in range(first,last+1,2):
        overlap=length-p
        color=((sample[:,:overlap:2]-sample[:,p::2])**2).mean()
        shape=((gradient[:,:overlap:2]-gradient[:,p::2])**2).mean()
        score=float(color+shape*1.5)
        if best is None or score<best[0]:best=(score,p)
    return best[1]

def periodic(source:Image.Image,size,repeat,structured=False):
    width,height=size
    if structured:
        rgb=np.asarray(source.convert('RGB'),dtype=np.float32).copy()
        if 'x' in repeat:
            period=matching_period(rgb,width)
            rgb,score_x=wrap_horizontal(rgb,period,False)
        if 'y' in repeat:
            transpose=rgb.transpose(1,0,2)
            period=matching_period(transpose,height)
            rgb,score_y=wrap_horizontal(transpose,period,'x' in repeat)
            rgb=rgb.transpose(1,0,2)
        reduced=Image.fromarray(np.uint8(np.clip(rgb,0,255)),'RGB').resize((width,height),Image.Resampling.LANCZOS)
        rgb=np.asarray(reduced,dtype=np.float32).copy()
        scores={'native_phase_x':score_x,'native_phase_y':score_y}
        if 'x' in repeat:
            edge=(rgb[:,0]+rgb[:,-1])*.5;rgb[:,0]=edge;rgb[:,-1]=edge
        if 'y' in repeat:
            edge=(rgb[0]+rgb[-1])*.5;rgb[0]=edge;rgb[-1]=edge
        return Image.fromarray(np.uint8(np.rint(rgb)),'RGB'),scores
    extra_x=round(width*.25) if 'x' in repeat else 0
    extra_y=round(height*.25) if 'y' in repeat else 0
    rgb=np.array(source.convert('RGB').resize((width+extra_x,height+extra_y),Image.Resampling.LANCZOS),dtype=np.float32)
    scores={}
    if 'x' in repeat:rgb,scores['x']=wrap_horizontal(rgb,width,False)
    if 'y' in repeat:
        rgb, scores['y']=wrap_horizontal(rgb.transpose(1,0,2),height,'x' in repeat)
        rgb=rgb.transpose(1,0,2)
    # Natural adjacent samples already continue. Lock the extreme texel pair
    # identically (subpixel-sized correction) for filtering/mipmap seam tests.
    if 'x' in repeat:
        edge=(rgb[:,0]+rgb[:,-1])*.5;rgb[:,0]=edge;rgb[:,-1]=edge
    if 'y' in repeat:
        edge=(rgb[0]+rgb[-1])*.5;rgb[0]=edge;rgb[-1]=edge
    return Image.fromarray(np.uint8(np.clip(np.rint(rgb),0,255)),'RGB'),scores

def straight_alpha(source:Image.Image,size):
    image=source.convert('RGBA')
    raw_alpha=np.array(image.getchannel('A'))
    if raw_alpha.min()>8:
        raise ValueError('Source has no actual transparent background; ImageGen extraction required')
    # Reconstruct coverage independently from the model's almost-opaque alpha.
    native_mask=raw_alpha>=128
    labels,count=ndi.label(native_mask)
    counts=np.bincount(labels.ravel())
    keep=counts>=max(24,int(native_mask.sum()*.00008));keep[0]=False
    native_mask=keep[labels]
    assert native_mask.any()
    coverage=Image.fromarray(np.uint8(native_mask)*255,'L').resize(tuple(size),Image.Resampling.LANCZOS)
    alpha=np.asarray(coverage).copy()
    alpha[alpha<8]=0;alpha[alpha>247]=255
    # All subpixel fringe is confined to at most a two-pixel coverage rim.
    hard=alpha>=128
    inner=ndi.distance_transform_edt(hard)
    outer=ndi.distance_transform_edt(~hard)
    alpha[(hard)&(inner>2)]=255
    alpha[(~hard)&(outer>2)]=0
    rgb=np.array(image.convert('RGB').resize(tuple(size),Image.Resampling.LANCZOS))
    solid=alpha==255
    donor=solid & (ndi.distance_transform_edt(solid)>=2)
    if not donor.any():donor=solid
    if not donor.any():raise ValueError('No fully opaque interior')
    distance,indices=ndi.distance_transform_edt(~donor,return_indices=True)
    distance_visible=ndi.distance_transform_edt(alpha==0)
    # Straight color, not premultiplication: extrapolate opaque pigment into
    # AA pixels and exactly 16 pixels of zero-alpha background.
    extend=(~solid)&(distance_visible<=16)
    rgb[extend]=rgb[indices[0][extend],indices[1][extend]]
    rgb[(alpha==0)&(distance_visible>16)]=0
    result=np.dstack([rgb,alpha])
    assert (alpha==255).sum()>100 and (alpha==0).sum()>100
    assert not alpha[:3].any() and not alpha[-3:].any() and not alpha[:,:3].any() and not alpha[:,-3:].any(),'Cutout touches canvas'
    return Image.fromarray(result,'RGBA')

def emission_mask(image:Image.Image,job):
    rgb=np.asarray(image.convert('RGB'),dtype=np.float32)/255
    r,g,b=rgb[:,:,0],rgb[:,:,1],rgb[:,:,2]
    # Colored hot channels, not dark cool crust, brass or red cloth.
    heat=np.clip((r-np.maximum(g*.98,b*1.25)-.055)/.36,0,1)
    heat*=np.clip((r-b-.12)/.4,0,1)
    heat*=np.clip((r-.28)/.5,0,1)
    heat=np.maximum(heat,np.clip((np.minimum(r,g)-b-.2)/.55,0,1)*np.clip((r-.45)/.4,0,1))
    heat[heat<.035]=0
    if image.mode=='RGBA':heat*=np.asarray(image.getchannel('A'),dtype=np.float32)/255
    channel=np.uint8(np.rint(np.clip(heat,0,1)*255))
    if job['material']=='abertura-forja':
        height,width=channel.shape
        yy,xx=np.mgrid[:height,:width]
        center=(abs(xx-width*.5)<width*.13)&(yy>height*.12)&(yy<height*.9)
        labels,count=ndi.label((channel>10)&center)
        counts=np.bincount(labels.ravel());counts[0]=0
        if count:
            selected=labels==int(counts.argmax())
            channel[~selected]=0
    assert channel.max()>40 and (channel==0).sum()>100,'Emission must contain dark and luminous pixels'
    return Image.fromarray(np.repeat(channel[:,:,None],3,axis=2),'RGB')

def entry(job,path,kind=None,pair=None):
    return {'file':path.relative_to(PACKAGE).as_posix(),'type':kind or job['type'],
            'size_px':job['size_px'],'world_size_m':job['world_size_m'],
            'repeat':job['repeat'],'pair':pair,
            'color_space':'sRGB','bit_depth':8,
            'alpha':'straight' if (job['type'] in ['cutout','decal'] and job['material']!='tapete-central' and kind!='emission') else 'none'}

def process_job(job,force=False):
    source=WORK/'sources'/job['arena']/(job['key']+'.png')
    if not source.exists():return {'key':job['key'],'status':'pending'}
    target=TEXTURES/job['arena']/(job['key']+('_cutout.png' if job['type']=='cutout' else '_albedo.png'))
    marker=QA/'entries'/(job['key']+'.json')
    if marker.exists() and target.exists() and not force:
        old=json.loads(marker.read_text())
        if old.get('pipeline_version')==PIPELINE_VERSION and old.get('source_mtime')==source.stat().st_mtime:
            return old
    with Image.open(source) as native:
        native.load()
        if job['repeat']!='none':image,scores=periodic(native,job['size_px'],job['repeat'],job['material'] in STRUCTURED)
        elif job['type'] in ['cutout','decal'] and job['material']!='tapete-central':image=straight_alpha(native,job['size_px']);scores={}
        elif job['type']=='backdrop':
            image=ImageOps.fit(native.convert('RGB'),tuple(job['size_px']),Image.Resampling.LANCZOS,centering=(.5,1.0 if job['arena']=='praia' else 0.0));scores={}
        else:image=native.convert('RGB').resize(tuple(job['size_px']),Image.Resampling.LANCZOS);scores={}
        native_size=list(native.size)
    save_png(image,target)
    ep=target.with_name(job['key']+'_emission.png') if job['emission'] else None
    records=[entry(job,target,pair=ep.relative_to(PACKAGE).as_posix() if ep else None)]
    if ep:
        save_png(emission_mask(image,job),ep)
        records.append(entry(job,ep,'emission',target.relative_to(PACKAGE).as_posix()))
        records[-1]['sampling']='data; do not apply source_color/sRGB decoding to mask samples'
    if job['type']=='tileable':
        repeated=Image.new('RGB',(image.width*2,image.height*2))
        for y in range(2):
            for x in range(2):repeated.paste(image,(x*image.width,y*image.height))
        preview=target.with_name('preview_'+target.name)
        save_png(repeated,preview)
        records[0]['preview']=preview.relative_to(PACKAGE).as_posix()
        offset=np.roll(np.asarray(image),shift=(image.height//2,image.width//2),axis=(0,1))
        save_png(Image.fromarray(offset,'RGB'),QA/'offset'/target.name)
    result={'key':job['key'],'status':'processed','source_native_size':native_size,
            'source_mtime':source.stat().st_mtime,'pipeline_version':PIPELINE_VERSION,
            'cut_scores':scores,'entries':records}
    marker.parent.mkdir(parents=True,exist_ok=True)
    marker.write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result

def audit(records):
    failures=[];results=[]
    for record in records:
        path=PACKAGE/record['file']
        with Image.open(path) as image:
            image.load();pixels=np.array(image)
            assert image.format=='PNG'
            errors=[]
            if list(image.size)!=record['size_px']:errors.append('size')
            if image.mode!=('RGBA' if record['alpha']=='straight' else 'RGB'):errors.append('mode')
            if 'srgb' not in image.info:errors.append('missing sRGB chunk')
            if pixels.dtype!=np.uint8:errors.append('bit-depth')
            result={'file':record['file'],'mode':image.mode,'size_px':list(image.size)}
            if 'x' in record['repeat']:
                error=int(np.abs(pixels[:,0].astype(int)-pixels[:,-1].astype(int)).max())
                result['edge_x_max_delta']=error
                if error>0:errors.append('x seam')
            if 'y' in record['repeat']:
                error=int(np.abs(pixels[0].astype(int)-pixels[-1].astype(int)).max())
                result['edge_y_max_delta']=error
                if error>0:errors.append('y seam')
            if image.mode=='RGBA':
                alpha=pixels[:,:,3];solid=alpha==255;visible=alpha>0;transparent=alpha==0
                if not solid.any() or not transparent.any():errors.append('alpha endpoints')
                distance=ndi.distance_transform_edt(~visible)
                band=transparent&(distance<=16)
                if np.any(np.all(pixels[band,:3]==0,axis=1)):errors.append('missing dilated RGB')
                # AA pixels must be within the requested narrow silhouette rim.
                inner=ndi.distance_transform_edt(alpha>=128);outer=ndi.distance_transform_edt(alpha<128)
                aa=(alpha>0)&(alpha<255)
                aa_width=float(np.maximum(inner[aa],outer[aa]).max()) if aa.any() else 0
                if aa_width>2.01:errors.append('AA wider than 2px')
                result.update(opaque_pixels=int(solid.sum()),transparent_pixels=int(transparent.sum()),aa_max_distance=aa_width,dilation_px=16)
            if record['type']=='emission':
                if not np.array_equal(pixels[:,:,0],pixels[:,:,1]) or not np.array_equal(pixels[:,:,0],pixels[:,:,2]):errors.append('mask not grayscale')
                if not pixels.max()>40 or not (pixels==0).any():errors.append('invalid emission range')
            if record['pair']:
                pair=next((r for r in records if r['file']==record['pair']),None)
                if not pair or pair['pair']!=record['file'] or pair['size_px']!=record['size_px']:errors.append('pair mismatch')
            result['errors']=errors
            if errors:failures.append(result)
            results.append(result)
    return {'files':len(records),'failures':failures,'results':results}

def contacts(records):
    QA.mkdir(parents=True,exist_ok=True)
    for arena in ['santuario','bazaar','forja','praia']:
        group=[r for r in records if r['file'].split('/')[1]==arena and r['type']=='tileable']
        if not group:continue
        size=320;cols=4;rows=math.ceil(len(group)/cols)
        sheet=Image.new('RGB',(cols*size,rows*(size+24)),(231,230,223));draw=ImageDraw.Draw(sheet)
        for i,r in enumerate(group):
            with Image.open(PACKAGE/r['preview']) as image:
                thumb=image.resize((size,size),Image.Resampling.LANCZOS)
            x=i%cols*size;y=i//cols*(size+24)
            sheet.paste(thumb,(x,y+24));draw.text((x+6,y+4),Path(r['file']).stem.replace(arena+'_',''),fill=(30,45,40))
        save_png(sheet,QA/f'contact-repeat-{arena}.png')
        # Offset diagnostic contact sheet centers the original wrap boundaries.
        for i,r in enumerate(group):
            with Image.open(QA/'offset'/Path(r['file']).name) as image:thumb=image.resize((size,size),Image.Resampling.LANCZOS)
            x=i%cols*size;y=i//cols*(size+24);sheet.paste(thumb,(x,y+24))
        save_png(sheet,QA/f'contact-offset-{arena}.png')
    transparent=[r for r in records if r['alpha']=='straight']
    if transparent:
        size=256;cols=5;rows=math.ceil(len(transparent)/cols)
        sheet=Image.new('RGB',(cols*size,rows*(size+24)),(40,47,59));draw=ImageDraw.Draw(sheet)
        for i,r in enumerate(transparent):
            with Image.open(PACKAGE/r['file']) as image:thumb=image.resize((size,size),Image.Resampling.LANCZOS)
            x=i%cols*size;y=i//cols*(size+24)
            # Two backgrounds expose light/dark edge contamination.
            bg=Image.new('RGB',(size,size),(29,38,50) if i%2==0 else (219,230,220))
            bg.paste(thumb,(0,0),thumb.getchannel('A'))
            sheet.paste(bg,(x,y+24));draw.text((x+4,y+4),Path(r['file']).stem[:38],fill=(245,245,230))
        save_png(sheet,QA/'contact-alpha.png')

README='''# Gale Breaker - Textures v2

61 texturas individuais + 36 previas 2x2. PNG 8 bits com sinalizacao sRGB.
Pastas: textures-v2/santuario, forja, bazaar, praia. O manifest informa tamanho,
tipo, repeticao, escala em metros e os pares de albedo/emissao.

Importe os PNGs com mipmaps no Godot 4. Use albedo com source_color; para
mascaras de emissao use sampler de dados, sem source_color. Mascara preta
nao emite; combine o valor com a cor do albedo e ajuste a energia no shader.
Toon unshaded: cor_final = albedo * faixa + albedo * mascara * energia.
O shader toon deve calcular as tres faixas de luz; as texturas nao trazem
iluminacao direcional. Superficies solidas sao RGB sem alfa.

Tileaveis: uma textura completa por material, Repeat XY, UV a cada world_size_m.
Faixas: repita somente no eixo indicado (X do friso; Y da lava e da orla).
Decalques e recortes: Repeat OFF, alfa reto, interior 255, AA de ate 2 px e
RGB dilatado 16 px sob alfa zero. Nao premultiplique o PNG. Use alpha scissor
ou alpha hash conforme o material. Tapete: RGB opaco, peca unica.

world_size_m e uma sugestao de cobertura: numero = metros por lado; [w,h]
= largura/altura. Fundos usam planos de referencia 200x50 m; posicione-os
longe da camera e ajuste a escala. Nao sao cubemaps nem panoramas 360.

As artes foram regeneradas individualmente a partir das quatro concepts.
O acabamento tecnico faz costura periodica, normalizacao de alfa, dilatacao,
extracao alinhada de emissao e dimensoes exatas. Resolucao nativa das fontes
fica registrada no manifest; os fundos sao reamostrados para 4096x1024.
Nenhum atlas v1 ou cena do jogo foi substituido.
'''

def finalize(results,allow_partial=False):
    done=[r for r in results if r.get('status')=='processed']
    records=[e for r in done for e in r['entries']]
    for r in done:
        for e in r['entries']:e['source_native_size_px']=r['source_native_size']
    if len(done)!=len(JOBS) and not allow_partial:
        raise RuntimeError(f'Only {len(done)}/{len(JOBS)} sources processed')
    report=audit(records)
    report.update(tileable_previews=sum(r['type']=='tileable' for r in records),processed_sources=len(done),expected_sources=len(JOBS))
    QA.mkdir(parents=True,exist_ok=True)
    (QA/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    if report['failures']:raise RuntimeError('Technical audit failed: '+json.dumps(report['failures'],ensure_ascii=False))
    manifest={'version':2,'project':'Gale Breaker','units':'meters','world_size_convention':'number = side length of square; [width,height] = coverage of rectangle','source_references':{a:str(p.relative_to(ROOT)).replace('\\','/') for a,p in __import__('catalog').REFERENCES.items()},'textures':records}
    previews=[]
    for r in records:
        if 'preview' in r:
            previews.append({'file':r['preview'],'type':'tileable','size_px':[n*2 for n in r['size_px']],
                             'world_size_m':r['world_size_m']*2,'repeat':'none','pair':None,
                             'usage':'2x2 preview only; not a production material',
                             'source':r['file'],'color_space':'sRGB','bit_depth':8,'alpha':'none'})
    manifest['previews']=previews
    (PACKAGE/'manifest-v2.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    (PACKAGE/'LEIA-ME.txt').write_text(README,encoding='utf-8')
    contacts(records)
    if not allow_partial:
        with zipfile.ZipFile(WORK/'Gale_Breaker_Textures_v2.zip','w',zipfile.ZIP_DEFLATED,compresslevel=3) as archive:
            for file in sorted(PACKAGE.rglob('*')):
                if file.is_file():archive.write(file,file.relative_to(PACKAGE).as_posix())
    return {'processed_sources':len(done),'texture_files':len(records),'previews_2x2':report['tileable_previews'],'audit_failures':len(report['failures'])}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--force',action='store_true');parser.add_argument('--partial',action='store_true');parser.add_argument('--workers',type=int,default=3);parser.add_argument('--key')
    args=parser.parse_args()
    jobs=[job for job in JOBS if not args.key or job['key']==args.key]
    results=[];errors=[]
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures={executor.submit(process_job,j,args.force):j['key'] for j in jobs}
        for future in as_completed(futures):
            key=futures[future]
            try:
                result=future.result();results.append(result)
                print(json.dumps({'key':key,'status':result['status']}),flush=True)
            except Exception as error:
                errors.append({'key':key,'error':str(error)});print(json.dumps(errors[-1]),flush=True)
    if errors:
        QA.mkdir(parents=True,exist_ok=True);(QA/'processing-errors.json').write_text(json.dumps(errors,indent=2),encoding='utf-8')
        raise SystemExit(1)
    if args.key:print('Single source finished');return
    print(json.dumps(finalize(results,args.partial),ensure_ascii=False),flush=True)

if __name__=='__main__':main()
