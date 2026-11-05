from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
import json
import shutil


WORDS = ['BABUIN', 'TOPHIA', 'VOLT', 'IGNIS', 'KAZE', 'PASSIVO', 'DEFENDE ALTO',
         'DEFENDE BAIXO', 'PULA', 'IA', 'SIM', 'NÃO', 'TREINO', 'LUTADOR',
         'ADVERSÁRIO', 'COMPORTAMENTO', 'EXIBIR HITBOXES', 'INICIAR TREINO', 'ESC VOLTAR']


def chipped(mask, seed):
    """Small reproducible paint chips; preserve glyph shape and bridges."""
    a = np.asarray(mask).copy()
    rng = np.random.default_rng(seed)
    solid = np.argwhere(a > 220)
    if len(solid):
        for y, x in solid[rng.choice(len(solid), max(1, len(solid)//115), replace=False)]:
            r = int(rng.choice([0, 0, 1]))
            a[max(0,y-r):y+r+1, max(0,x-r):x+r+1] = 0
    return Image.fromarray(a)


def text_paint(text, font_path, width, height, seed):
    size = min(100, height-16)
    while size > 10:
        font = ImageFont.truetype(str(font_path), size)
        box = font.getbbox(text)
        if box[2]-box[0] <= width-24 and box[3]-box[1] <= height-20:
            break
        size -= 1
    mask = Image.new('L', (width, height))
    d = ImageDraw.Draw(mask)
    box = font.getbbox(text)
    pos = ((width-(box[2]-box[0]))//2-box[0], (height-(box[3]-box[1]))//2-box[1])
    d.text(pos, text, font=font, fill=255)
    mask = chipped(mask, seed)
    out = Image.new('RGBA', mask.size, (236,218,180,0))
    out.putalpha(mask)
    return out


def build_font(root, repo):
    target = root/'fonts'
    target.mkdir(exist_ok=True)
    source = repo/'godot/assets/ui/fonts'
    ttf = target/'StardosStencil-Bold.ttf'
    shutil.copy2(source/ttf.name, ttf)
    shutil.copy2(source/'StardosStencil-OFL.txt', target/'StardosStencil-OFL.txt')
    font = ImageFont.truetype(str(ttf), 64)
    chars = [chr(i) for i in range(32,127)] + [chr(i) for i in range(160,256)]
    # All glyphs use a shared baseline and retain the TTF advance/kerning metrics.
    page = Image.new('RGBA', (1024,2048), (255,255,255,0))
    x=y=4
    row_h=0
    entries=[]
    for ch in chars:
        box=font.getbbox(ch, anchor='ls')
        w,h=box[2]-box[0],box[3]-box[1]
        advance=round(font.getlength(ch))
        if not ch.strip() or w<=0 or h<=0:
            entries.append({'id':ord(ch),'x':0,'y':0,'width':0,'height':0,'xoffset':0,'yoffset':0,'xadvance':advance,'page':0,'chnl':15})
            continue
        if x+w+4>page.width:
            x=4; y+=row_h+8; row_h=0
        mask=Image.new('L',(w,h))
        ImageDraw.Draw(mask).text((-box[0],-box[1]),ch,font=font,fill=255,anchor='ls')
        mask=chipped(mask,ord(ch)*7919)
        glyph=Image.new('RGBA',(w,h),(255,255,255,0)); glyph.putalpha(mask)
        page.paste(glyph,(x,y))
        entries.append({'id':ord(ch),'x':x,'y':y,'width':w,'height':h,
                        'xoffset':box[0],'yoffset':68+box[1],'xadvance':advance,'page':0,'chnl':15})
        row_h=max(row_h,h); x+=w+8
    used_h=y+row_h+4
    assert used_h<=2048
    page=page.crop((0,0,1024,used_h))
    page.save(target/'PortaoStencil-Desgastado_0.png')
    lines=['info face="Portao Stencil Desgastado" size=64 bold=1 italic=0 charset="" unicode=1 stretchH=100 smooth=1 aa=1 padding=0,0,0,0 spacing=0,0 outline=0',
           f'common lineHeight=84 base=68 scaleW=1024 scaleH={used_h} pages=1 packed=0',
           'page id=0 file="PortaoStencil-Desgastado_0.png"', f'chars count={len(entries)}']
    lines += ['char '+' '.join(f'{k}={v}' for k,v in e.items()) for e in entries]
    kern=[]
    for a in chars:
        for b in chars:
            delta=round(font.getlength(a+b)-font.getlength(a)-font.getlength(b))
            if delta:
                kern.append(f'kerning first={ord(a)} second={ord(b)} amount={delta}')
    lines += [f'kernings count={len(kern)}']+kern
    (target/'PortaoStencil-Desgastado.fnt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    cw,ch=420,128
    word_page=Image.new('RGBA',(cw*4,ch*5),(236,218,180,0))
    word_dir=target/'palavras'; word_dir.mkdir(exist_ok=True)
    word_entries=[]
    for i,text in enumerate(WORDS):
        row,col=divmod(i,4)
        im=text_paint(text,ttf,cw,ch,1000+i)
        file=f'{i+1:02d}.png'; im.save(word_dir/file)
        word_page.paste(im,(col*cw,row*ch))
        word_entries.append({'text':text,'file':'palavras/'+file,'rect_px':[col*cw,row*ch,cw,ch]})
    word_page.save(target/'palavras-portao.png')
    proof=Image.new('RGB',word_page.size,(48,60,68)); proof.paste(word_page,(0,0),word_page)
    proof.save(root/'preview-fonte-palavras.png')
    meta={'ttf':'StardosStencil-Bold.ttf','bitmap':'PortaoStencil-Desgastado.fnt',
          'bitmap_page':'PortaoStencil-Desgastado_0.png','glyphs':len(entries),
          'source_size':64,'base':68,'lineHeight':84,'unicode':[32,255],
          'family':'Stardos Stencil Bold','license':'StardosStencil-OFL.txt',
          'note':'A TTF mantém a fonte original. A bitmap usa os mesmos desenhos com pequenos desgastes pintados; não é uma identificação exata da tipografia gerada nas concepts.',
          'word_sheet':{'file':'palavras-portao.png','grid':[4,5],'size_px':list(word_page.size),'words':word_entries}}
    (target/'manifest-fonte.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    return meta
