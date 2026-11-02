from pathlib import Path
import base64
import html
import json
import shutil
from io import BytesIO
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
ASSETS = OUT / 'assets'
ASSETS.mkdir(exist_ok=True)
W, H = 1080, 675
BG, PANEL, WHITE, MUTED = '#F8F5EE', '#EDE8DD', '#27372F', '#62695F'
GREEN, RED, ORANGE, CYAN, GOLD = '#28654F', '#A54332', '#98531F', '#206A7C', '#806531'
pdfmetrics.registerFont(TTFont('Arial', 'C:/Windows/Fonts/arial.ttf'))
pdfmetrics.registerFont(TTFont('ArialBold', 'C:/Windows/Fonts/arialbd.ttf'))
FONT_FILES={'Editorial':'georgia.ttf','Jade':'georgia.ttf','Rural':'impact.ttf','Stone':'georgiab.ttf','Tech':'consolab.ttf'}
for family,filename in FONT_FILES.items():
    pdfmetrics.registerFont(TTFont(family,'C:/Windows/Fonts/'+filename))
    shutil.copy2('C:/Windows/Fonts/'+filename,ASSETS/filename)
DISPLAY={GREEN:'Jade',RED:'Rural',ORANGE:'Stone',CYAN:'Tech'}
PDF = OUT / 'Gale_Breaker_GDD_Visual_v0_10.pdf'
c = canvas.Canvas(str(PDF), pagesize=(W, H))
c.setTitle('Gale Breaker GDD Visual v0.10')
c.setAuthor('Gale Breaker')
pages = []
copied = {}
pdf_images = {}

def pdf_image(path):
    # Keep source assets intact; embed bounded, compressed illustrations in PDF.
    if path not in pdf_images:
        with Image.open(path) as original:
            image = original.copy()
        if image.mode == 'RGBA' and image.getextrema()[3] != (255,255):
            pdf_images[path] = ImageReader(image)
        else:
            image = image.convert('RGB')
            image.thumbnail((2400,2400),Image.Resampling.LANCZOS)
            buffer = BytesIO()
            image.save(buffer,format='JPEG',quality=92,optimize=True)
            buffer.seek(0)
            pdf_images[path] = ImageReader(buffer)
    return pdf_images[path]

def asset(name):
    source = ROOT / 'concept-art' / name
    target = ASSETS / source.name
    if source not in copied:
        shutil.copy2(source, target)
        with Image.open(target) as im:
            copied[source] = (target, im.size)
    return copied[source]

def wrap(text, size, width, bold=False):
    font = 'ArialBold' if bold else 'Arial'
    lines = []
    for block in text.split('\n'):
        line = ''
        for word in block.split():
            candidate = (line + ' ' + word).strip()
            if line and pdfmetrics.stringWidth(candidate, font, size) > width:
                lines.append(line)
                line = word
            else:
                line = candidate
        lines.append(line)
    return lines

class Page:
    def __init__(self, section, title='', intro='', accent=GREEN, cover=False):
        self.parts = []
        self.accent = accent
        self.section = section
        self.title = title
        self.number = len(pages) + 1
        self.rect(0, 0, W, H, BG)
        if not cover:
            self.rect(0,0,8,H,accent)
            self.line(48,128,1032,128,'#D7D0C2',.7)
            self.text(48, 24, section.upper(), 10, accent, True)
            self.text(48, 49, title, 30, WHITE, font=DISPLAY.get(accent,'Editorial') if section.startswith(('03','09')) else 'Editorial')
            if intro:
                self.para(48, 96, intro, 970, 12, MUTED,leading=16)
        pages.append(self)

    def rect(self, x, y, w, h, fill=PANEL, stroke=None, radius=0, dashed=False):
        c.setFillColor(HexColor(fill))
        c.setStrokeColor(HexColor(stroke or fill))
        c.setLineWidth(.8)
        if dashed:
            c.setDash(5, 4)
        if radius:
            c.roundRect(x, H-y-h, w, h, radius, fill=1, stroke=bool(stroke))
        else:
            c.rect(x, H-y-h, w, h, fill=1, stroke=bool(stroke))
        c.setDash()
        border = f'border:1px {"dashed" if dashed else "solid"} {stroke};' if stroke else ''
        self.parts.append(f'<div class="shape" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;background:{fill};{border}border-radius:{radius}px"></div>')

    def line(self, x1, y1, x2, y2, color=MUTED, width=1):
        c.setStrokeColor(HexColor(color)); c.setLineWidth(width)
        c.line(x1, H-y1, x2, H-y2)
        self.parts.append(f'<svg class="shape" style="left:0;top:0;width:{W}px;height:{H}px"><line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"/></svg>')

    def text(self, x, y, text, size=14, color=WHITE, bold=False, width=None, font=None):
        font=font or ('ArialBold' if bold else 'Arial')
        c.setFillColor(HexColor(color))
        c.setFont(font, size)
        c.drawString(x, H-y-size*.82, text)
        self.parts.append(f'<div class="txt editable" style="left:{x}px;top:{y}px;font-family:{font},Arial,sans-serif;font-size:{size}px;color:{color};font-weight:{700 if bold and font.startswith("Arial") else 400};{f"width:{width}px;" if width else ""}">{html.escape(text)}</div>')

    def para(self, x, y, text, width, size=14, color=WHITE, bold=False, leading=None):
        leading = leading or size*1.42
        lines = wrap(text, size, width, bold)
        c.setFillColor(HexColor(color)); c.setFont('ArialBold' if bold else 'Arial', size)
        for i, line in enumerate(lines):
            c.drawString(x, H-y-i*leading-size*.82, line)
        rendered = '<br>'.join(html.escape(s) for s in lines)
        self.parts.append(f'<div class="txt editable" style="left:{x}px;top:{y}px;width:{width}px;font-size:{size}px;line-height:{leading}px;color:{color};font-weight:{700 if bold else 400}">{rendered}</div>')
        return y+len(lines)*leading

    def image(self, name, x, y, w, h, crop=None, fill=None):
        path, (iw, ih) = asset(name)
        if fill:
            self.rect(x,y,w,h,fill)
        if crop:
            l,t,r,b = crop
            scale = min(w/((r-l)*iw), h/((b-t)*ih))
            cw,ch=(r-l)*iw*scale,(b-t)*ih*scale
            dx=x+(w-cw)/2-l*iw*scale
            dy=y+(h-ch)/2-t*ih*scale
            c.saveState()
            cx,cy=x+(w-cw)/2,y+(h-ch)/2
            clip=c.beginPath(); clip.rect(cx,H-cy-ch,cw,ch); c.clipPath(clip,stroke=0,fill=0)
            c.drawImage(pdf_image(path),dx,H-dy-ih*scale,width=iw*scale,height=ih*scale,mask='auto')
            c.restoreState()
            self.parts.append(f'<div class="shape" style="left:{cx}px;top:{cy}px;width:{cw}px;height:{ch}px;overflow:hidden"><img alt="{html.escape(name)}" src="assets/{path.name}" style="position:absolute;left:{dx-cx}px;top:{dy-cy}px;width:{iw*scale}px;height:{ih*scale}px"></div>')
        else:
            scale=min(w/iw,h/ih)
            dw,dh=iw*scale,ih*scale
            dx,dy=x+(w-dw)/2,y+(h-dh)/2
            c.drawImage(pdf_image(path),dx,H-dy-dh,width=dw,height=dh,mask='auto')
            self.parts.append(f'<img class="shape" alt="{html.escape(name)}" src="assets/{path.name}" style="left:{dx}px;top:{dy}px;width:{dw}px;height:{dh}px">')

    def arrow(self,x,y,w=20):
        self.line(x,y,x+w,y,self.accent,1.5)
        self.line(x+w-5,y-4,x+w,y,self.accent,1.5)
        self.line(x+w-5,y+4,x+w,y,self.accent,1.5)

    def command(self,action,x,y,size=32,color=None):
        """Document-native command glyphs, independent of keyboard/controller bindings."""
        color=color or self.accent
        self.rect(x,y,size,size,BG,stroke=color,radius=7)
        def segment(a,b,d,e):self.line(x+a*size,y+b*size,x+d*size,y+e*size,color,1.6)
        if action=='light':
            segment(.32,.68,.66,.32)
        elif action=='heavy':
            segment(.23,.68,.57,.32);segment(.44,.68,.78,.32)
        elif action=='elemental':
            for a,b,d,e in [(.5,.2,.5,.8),(.2,.5,.8,.5),(.29,.29,.71,.71),(.29,.71,.71,.29)]:segment(a,b,d,e)
        else:
            for a,b,d,e in [(.5,.17,.8,.5),(.8,.5,.5,.83),(.5,.83,.2,.5),(.2,.5,.5,.17),(.5,.32,.65,.5),(.65,.5,.5,.68),(.5,.68,.35,.5),(.35,.5,.5,.32)]:segment(a,b,d,e)

    def portrait(self,f,x,y,w,h):
        self.rect(x,y,w,h,'#F0EBE1',stroke='#D8D0C2',radius=3)
        self.image(f['art'],x+8,y+10,w-16,h-20,crop=f['crop'])
        self.rect(x,y+h-4,w,4,f['color'])

    def note(self, x, y, tag, text, width=440):
        self.text(x,y,tag.upper(),10,self.accent,True)
        return self.para(x,y+20,text,width,14,WHITE)

    def finish(self):
        self.line(48,637,1032,637,'#D7D0C2',.6)
        self.text(48,649,'GALE BREAKER  /  DOCUMENTO DE DESIGN',8,MUTED)
        self.text(840,649,'EDIÇÃO 0.10',8,MUTED)
        self.text(1008,646,f'{self.number:02d}',13,self.accent,font='Editorial')
        c.showPage()

icons=json.loads((ROOT/'concept-art/attack-icons/manifest.json').read_text(encoding='utf-8'))['icons']
fighter_info=[
    dict(id='kaze',name='Kaze',color=GREEN,art='personagens-v2.png',crop=(0,.03,.245,.63),
         desc='Monge alto e careca, postura ereta, roupas verdes de jade e pés descalços.',
         identity='Silhueta vertical e calma. O vento aparece no movimento do tecido e na direção dos golpes.',
         pending='Jogável: combo de palmas e chute, onda de vento e tornado com quatro impactos. Validar facilidade de aprendizado e mobilidade.'),
    dict(id='ignis',name='Ignis',color=RED,art='personagens-v2.png',crop=(.252,.03,.494,.63),
         desc='Brutamontes caipira e corcunda. Chapéu de cowboy, peito claro, cabeça e braços vermelhos de sol, jeans e botas.',
         identity='Massa, peso e humor rural. Preservar o contraste entre a pele queimada de sol e o peito branco.',
         pending='Jogável: socos alternados, martelo, pisada e avanço pesado. Validar alcance e recuperação para preservar o peso sem frustrar.'),
    dict(id='tophia',name='Tophia',color=ORANGE,art='tophia-retrato-gdd-v1.png',crop=(0,0,1,1),
         desc='Armadura completa de pedra laranja em estilo de cavaleiro. Apenas a cabeça exposta, cabelo curto preto.',
         identity='A pedra se move por licença fantástica. Pose de apresentação sorridente, perna recolhida e sinal de paz.',
         pending='Jogável: armadura visual sem invencibilidade automática, sequência baixa, espinhos escalonados e punho de pedra. Validar leitura e peso.'),
    dict(id='volt',name='Volt',color=CYAN,art='volt-retrato-gdd-v1.png',crop=(0,0,1,1),
         desc='Jovem loiro de pontas chamuscadas. Armadura de sucata e lixo reaproveitado, com um canhão de mão.',
         identity='Equipamento improvisado, assimétrico e gasto. Energia ciano; pose agachada, mirando o canhão para o lado.',
         pending='Jogável: tiros independentes, disparo carregado, pulso e feixe anunciado. Bloqueio, salto e parry respondem aos disparos.')
]

# 01 — Cover
p=Page('Capa',cover=True)
p.rect(0,0,12,H,GREEN)
p.text(48,35,'PROJETO DE JOGO  /  DOCUMENTO DE DESIGN',10,GREEN,True)
p.text(48,72,'GALE BREAKER',49,WHITE,font='Editorial')
p.text(50,137,'Quatro elementos. Uma boa confusão.',17,MUTED,font='Editorial')
p.image('menu-principal-v3.png',48,186,984,360,crop=(0,.22,1,.86))
p.line(48,572,1032,572,'#CFC6B5',.8)
p.text(48,592,'GAME DESIGN DOCUMENT',12,GREEN,True)
p.text(48,621,'Direção visual, personagens e sistemas de combate',12,MUTED)
p.text(820,592,'EDIÇÃO 0.10',13,WHITE,font='Editorial')
p.text(820,621,'02 NOVEMBRO 2026',10,MUTED)
c.showPage()

# 02 — Product vision and loop
p=Page('01  Visão do jogo','Combate exagerado e divertido','As duas decisões centrais orientam o restante do documento.')
p.note(48,146,'Definido','Combate caótico e exagerado, com foco em diversão.',460)
p.note(570,146,'Definido','Habilidades escolhidas livremente antes da luta, respeitando um limite de pontos.',450)
p.text(48,247,'Fluxo de partida proposto',19,WHITE,True)
flow=['MENU','MODO','LUTADOR','HABILIDADES','LUTA','RESULTADO']
for i,title in enumerate(flow):
    x=48+i*166
    p.rect(x,283,146,60,PANEL,radius=7)
    p.text(x+15,304,title,12,WHITE,True)
    if i<5:p.arrow(x+148,313,14)
p.note(48,385,'Direção proposta','A arena participa da luta. Ações e objetos criam oportunidades, surpresas e vontade de pedir revanche.',450)
p.note(570,385,'Clareza do caos','Mesmo com exagero, o jogador precisa perceber de onde vem o perigo e ter uma forma de reagir.',450)
p.para(48,528,'Leitura do GDD: DEFINIDO = decisão tomada; PROTÓTIPO = regra atual sujeita a revisão; EM ABERTO = decisão de design ainda necessária.',980,13,MUTED)
p.finish()

# 03 — Current cast overview
p=Page('02  Elenco','Quatro silhuetas bem diferentes','Referências atuais de personagem. A simplificação v3 não é a direção escolhida.')
for i,f in enumerate(fighter_info):
    x=48+i*251
    p.portrait(f,x,143,231,320)
    p.text(x,484,f['name'].upper(),22,f['color'],font=DISPLAY[f['color']])
    p.para(x,518,f['desc'],225,12,MUTED)
p.finish()

# 04–07 — Character sheets with actual concepts and icons
for f in fighter_info:
    p=Page('03  Personagens',f['name'],f['desc'],f['color'])
    p.portrait(f,48,147,350,458)
    p.note(438,150,'Identidade visual',f['identity'],594)
    p.note(438,250,'Gameplay implementado',f['pending'],594)
    p.line(438,350,1032,350,'#D7D0C2',.6)
    p.text(438,369,'Repertório de combate',19,WHITE,font='Editorial')
    fi=[item for item in icons if item['fighter']==f['id']]
    for j,item in enumerate(fi):
        x=438+j*151
        p.rect(x,407,139,174,PANEL,radius=5)
        p.image('attack-icons/'+item['filename'],x+18,416,102,102)
        p.command(['light','heavy','elemental','ultimate'][j],x+10,522,25)
        p.text(x+43,529,['BÁSICO','FORTE','ELEMENTAL','ULTIMATE'][j],9,f['color'],True)
        p.para(x+10,557,item['name'],122,10,MUTED,leading=13)
    p.para(438,601,'Movimentos e respostas nas fichas de ataque. Regras finais dependem de teste.',594,11,MUTED)
    p.finish()
# 08 — Arenas with full-width panoramic crops
p=Page('04  Arenas','Três lugares para criar confusão','Três arenas nativas com objetos arremessáveis e ciclos previsíveis de perigo. Concepts preservadas como direção visual.')
arenas=[('ZEPHYR PEAK','Santuário, cerejeiras e vento.','Rajada anunciada empurra lutadores e lança objetos.',(.0,.045,.797,.355)),
        ('CRIMSON ANVIL','Forja, lava e correntes.','Erupção localizada: aviso de 1,5 s; saltar, sair ou bloquear.',(.0,.365,.797,.668)),
        ('GOLDEN BAZAAR','Arcos, lanternas e especiarias.','Queda de carga anunciada; sair da marca ou bloquear.',(.0,.675,.797,.985))]
for i,(name,desc,question,crop) in enumerate(arenas):
    y=145+i*155
    p.image('cenarios-v1.png',48,y,658,135,crop=crop)
    p.text(730,y+3,name,17,[GREEN,RED,GOLD][i],True)
    p.para(730,y+34,desc,300,13,WHITE)
    p.para(730,y+78,question,300,12,MUTED)
p.finish()

# 09 — Combat and arena interaction
p=Page('05  Combate','O jogador precisa entender a pancada','Base do protótipo: quatro comandos principais, movimento e ações auxiliares.')
for i,(title,body) in enumerate([
    ('BÁSICO','Pode ter variantes no chão, agachado e no ar.'),
    ('FORTE','Impacto maior e uma abertura mais evidente.'),
    ('ELEMENTAL','Poder do lutador e interação com a arena.'),
    ('ULTIMATE','Ação de grande impacto ligada ao medidor.')]):
    x=48+i*251
    p.rect(x,145,231,116,PANEL,radius=6)
    p.command(['light','heavy','elemental','ultimate'][i],x+14,157,32,[GREEN,RED,ORANGE,CYAN][i])
    p.text(x+57,169,title,13,[GREEN,RED,ORANGE,CYAN][i],True)
    p.para(x+16,202,body,198,12,MUTED)
p.text(48,299,'Ritmo de um golpe',19,WHITE,True)
for x,width,label,color in [(48,225,'PREPARAÇÃO',MUTED),(273,180,'CONTATO',GREEN),(453,220,'RECUPERAÇÃO',ORANGE)]:
    p.rect(x,337,width,47,color)
    p.text(x+14,353,label,12,BG,True)
p.para(48,401,'Startup, frames ativos e recuperação existem no protótipo. Seus valores finais dependem dos novos ataques e dos testes de diversão.',625,13,MUTED)
p.note(735,299,'No protótipo','Melhor de três, timer de 99 segundos e ultimate com custo de 50 em um medidor de 100.',290)
p.note(48,492,'Caos de cenário','Objetos arremessáveis causam dano, quebram e reaparecem. Eventos de arena têm aviso de 1,5 s e ciclo de cerca de 15 s.',630)
p.note(735,492,'Implementado','Jogador lança objetos; a arena acrescenta eventos previsíveis. Treino desativa esses eventos.',290)
p.finish()

# 10 — Illustrated pre-match choices and mode overview
p=Page('06  Modos e habilidades','Escolha. Combine. Entre na luta.','Habilidades escolhidas livremente antes da luta, com limite de pontos. Quatro pontos é a referência atual do protótipo.')
p.image('infografico-habilidades-v1.png',48,143,984,328)
for i,(title,body,pending) in enumerate([
    ('ARCADE','Torre de quatro etapas e chefe com overcharge.','Implementado: três dificuldades, introduções, continue salvo e encerramento.'),
    ('VERSUS LOCAL','Dois jogadores disputam uma partida.','Implementado: loadouts separados, dois controles e teclado remapeável.'),
    ('TREINO','Adversário passivo e recuperação de vida e energia.','Implementado: oito lições, dummy configurável, hitboxes e avanço de frame.')]):
    x=48+i*337
    p.text(x,491,title,14,GREEN,True)
    p.para(x,516,body,307,12,WHITE,leading=16)
    p.para(x,556,pending,307,11,MUTED,leading=15)
p.para(48,600,'Seleção livre sem pré-requisitos. P1 e P2 têm configurações salvas separadas. Custos finais dependem de playtest.',984,10,MUTED)
p.para(48,618,'Escolhas de estilo de jogo; não há decisão de criar XP, moeda ou grind para obter vantagem.',984,10,MUTED)
p.finish()

# 11 — Main menu approved concept
p=Page('07  Interface','Menu principal minimalista','Referência visual escolhida: menu principal v3.')
p.image('menu-principal-v3.png',48,145,756,425)
p.note(830,153,'Direção','Lista textual, bastante respiro e destaque discreto de jade.',202)
p.note(830,296,'No jogo','Título apenas Gale Breaker, sem subtítulo. Santuário vazio, sem Kaze ou outros personagens.',202)
p.note(830,470,'A preservar','Legibilidade e navegação por teclado e mouse.',202)
p.para(48,591,'Concept de referência; menu nativo implementado. Captura real na página 32.',756,12,MUTED)
p.finish()

# 12 — Updated pause and combat HUD concepts
p=Page('07  Interface','Pausa e combate, na mesma linguagem','Concepts atuais: Kaze monge careca, Ignis cowboy e interface minimalista com detalhes de jade e marfim.')
p.text(48,143,'01  PAUSA',11,GREEN,True)
p.text(552,143,'02  HUD DE COMBATE',11,RED,True)
p.image('menu-pausa-v2.png',48,167,480,270)
p.image('hud-combate-v2.png',552,167,480,270)
p.note(48,462,'Pausa','Combate congelado, fundo suavizado e Continuar em destaque. O painel mantém os lutadores visíveis.',302)
p.note(385,462,'Informação essencial','Vida, tempo e rounds no alto. Energia e elemento nos cantos inferiores; espaço livre para acompanhar os golpes.',302)
p.note(722,462,'Leitura e acesso','Nomes e símbolos acompanham as cores. Validar tamanho do texto, contraste, flashes e intensidade do shake.',310)
p.para(48,591,'Pausa e HUD nativos implementados. Opções de flashes, shake e vibração disponíveis; validar conforto com jogadores.',984,11,MUTED)
p.finish()

# 13 — Complete icons atlas, document-native layout
p=Page('08  Ataques','Os 16 ícones principais','Nomes artísticos propostos. As imagens não definem sozinhas dano, alcance ou efeitos de gameplay.')
for j,label in enumerate(['BÁSICO','FORTE','ELEMENTAL','ULTIMATE']):
    p.command(['light','heavy','elemental','ultimate'][j],203+j*205,137,23,GREEN)
    p.text(235+j*205,143,label,10,MUTED,True)
for i,f in enumerate(fighter_info):
    y=170+i*108
    p.text(48,y+30,f['name'].upper(),15,f['color'],True)
    for j,item in enumerate([k for k in icons if k['fighter']==f['id']]):
        x=203+j*205
        p.image('attack-icons/'+item['filename'],x,y-5,78,78)
        p.para(x+87,y+16,item['name'],110,11,WHITE)
p.finish()

# Illustrated attack chapter: four actions per fighter.
sequences=json.loads((ROOT/'concept-art/attacks/sequences.json').read_text(encoding='utf-8'))
action_labels={'light':'BÁSICO','heavy':'FORTE','elemental':'ELEMENTAL','ultimate':'ULTIMATE'}
for attack in sequences:
    f=next(f for f in fighter_info if f['id']==attack['fighter'])
    p=Page('09  '+f['name']+' / '+action_labels[attack['action']],attack['name'],'Implementado no Godot; ilustração de referência. Dano, alcance e tempos em ajuste de playtest.',f['color'])
    p.command(attack['action'],982,45,42,f['color'])
    p.image('attacks/'+attack['filename'],48,143,984,328)
    original=attack['action']=='light' and attack['fighter'] in ['kaze','ignis']
    if original:
        p.text(48,486,'ESBOÇO DO AUTOR',10,f['color'],True)
        p.image('attacks/'+attack['fighter']+'-j123-esboco.png',48,507,270,112)
        p.text(344,486,'SEQUÊNCIA E EFEITO PROPOSTO',10,f['color'],True)
        p.para(344,506,attack['sequence']+' '+attack['behavior'],415,12,WHITE,leading=17)
        p.text(786,486,'RESPOSTA DO ADVERSÁRIO',10,f['color'],True)
        p.para(786,506,attack['counter'],245,12,WHITE,leading=17)
        p.para(786,578,attack['cost'],245,11,MUTED)
    else:
        for x,label,body in [(48,'MOVIMENTO',attack['sequence']),(385,'FUNÇÃO EM COMBATE',attack['behavior']),(722,'RESPOSTA DO ADVERSÁRIO',attack['counter'])]:
            p.text(x,486,label,10,f['color'],True)
            p.para(x,506,body,310,12,WHITE,leading=17)
        p.para(48,598,attack['cost']+' Parâmetros iniciais no jogo; balanceamento final depende de playtest.',980,11,MUTED)
        p.text(48,620,'J1/J2/J3 = três ataques encadeados.' if attack['action']=='light' else 'Três poses de referência de um golpe. O jogo já possui animação de preparação, contato e recuperação.',10,MUTED)
    p.finish()

# 18 — Open creative decisions
p=Page('10  Próximas definições','Próxima rodada de avaliação','Sistemas implementados; decisões criativas e qualidade final continuam em avaliação.')
columns=[
    ('KITS E ARENAS',GREEN,[
        ('Golpes','16 ataques principais jogáveis. Avaliar alcance, dano, cancelamentos e tempo sem agir.'),
        ('Canhão de Volt','Projéteis visíveis, carga fixa e sem munição/calor. Avaliar pressão à distância e respostas.'),
        ('Pedra de Tophia','Armadura visual implementada. Avaliar clareza dos espinhos e do punho de pedra.'),
        ('Caos','Objetos acionados por golpes e eventos anunciados. Avaliar frequência e diversão.')]),
    ('MUNDO E FEEDBACK',ORANGE,[
        ('Universo','Por que estes quatro lutam? Quais são suas relações e motivações?'),
        ('Humor','Como o exagero aparece em falas, reações, vitórias e derrotas?'),
        ('Áudio','Música sintetizada por arena e efeitos por personagem. Avaliar mix e clareza dos avisos.'),
        ('Arcade','Fluxo, chefe, continue e encerramento funcionam. Narrativa e diálogos permanecem em aberto.')]),
    ('REGRAS E ESCOPO',CYAN,[
        ('Ritmo','Duração de luta e combos, formas de escapar, rounds e timer.'),
        ('Habilidades','P1/P2 livres e separados. Avaliar custos e combinações dominantes.'),
        ('Controles','Mapeamento de gamepad e acessibilidade disponíveis. Validar controles físicos e conforto.'),
        ('Lançamento','Confirmar público, plataforma, modos e conteúdo da primeira versão.')])]
for i,(heading,color,items) in enumerate(columns):
    x=48+i*337
    p.text(x,148,heading,15,color,True)
    for j,(label,body) in enumerate(items):
        y=193+j*99
        p.text(x,y,label,15,WHITE,True)
        p.para(x,y+26,body,302,12,MUTED)
p.finish()

# 19 — Asset production pipeline and next actions
p=Page('11  Produção','Da concept ao jogo','Pipeline em uso: arquivos Blender, exportação GLB, simulação e apresentação no Godot.')
stages=[('CONCEPT','Referência e vistas'),('BLENDER','Malha e materiais'),('RIG','Ossos e animação'),('GLB','Exportação'),('GODOT','Cena e gameplay')]
for i,(title,subtitle) in enumerate(stages):
    x=48+i*201
    p.rect(x,150,179,88,PANEL,radius=6)
    p.text(x+14,167,title,16,[GREEN,GOLD,ORANGE,CYAN,GREEN][i],True)
    p.text(x+14,202,subtitle,11,MUTED)
    if i<4:p.arrow(x+183,194,14)
p.note(48,287,'Marco entregue','Quatro lutadores jogáveis, três arenas e menu minimalista. Cada personagem tem rig e 27 clips exportados do Blender.',460)
p.note(570,287,'Autoridade do combate','Movimento e dano continuam na simulação. A animação acompanha preparação, contato, recuperação, cancelamentos e hitstop.',460)
p.note(48,426,'Animação integrada','Transições, apoio de mãos e pés, canhão estabilizado e hitstop. Kaze e Ignis preservam a direção dos esboços do autor.',460)
p.note(570,426,'Critério de teste','O jogador entende o que acontece, encontra uma resposta e quer revanche. Observar legibilidade, tempo sem agir e desempenho.',460)
p.para(48,563,'Build Windows de avaliação disponível. 158 verificações passaram e 16 confrontos automáticos terminaram. Acabamento artístico e balanceamento competitivo exigem avaliação humana.',980,13,MUTED)
p.finish()

# Native build evidence: real captures, kept separate from approved concepts.
p=Page('12  Build nativa','O documento virou jogo','Capturas reais do Godot 4.7.2 / Windows / OpenGL. Build de avaliação v0.10.')
p.image('../art-source/previews/gdd-build/menu.png',48,145,608,342)
p.image('../art-source/previews/gdd-build/pause.png',678,145,354,199)
p.image('../art-source/previews/gdd-build/selection.png',678,358,354,199)
p.note(48,513,'Fluxo completo','Menu sem personagens, seleção, habilidades, luta e resultado. Arcade com apresentação, continue salvo e encerramento.',600)
p.para(48,602,'Executável: godot/builds/GaleBreaker.exe  |  Prévia: art-source/previews/index.html',984,11,MUTED)
p.finish()

p=Page('12  Build nativa','Três arenas em funcionamento','Geometria Blender, materiais toon e perigos anunciados ligados à simulação.')
for i,(file,title,body) in enumerate([
    ('zephyr_dojo','ZEPHYR PEAK','Rajada e objetos. Treino mantém a arena tranquila.'),
    ('molten_forge','CRIMSON ANVIL','Erupção localizada com marcação e tempo para reagir.'),
    ('storm_market','GOLDEN BAZAAR','Carga em queda anunciada; bloquear ou sair da área.')]):
    y=145+i*155
    p.image('../art-source/previews/gdd-build/'+file+'.png',48,y,440,140)
    p.image('../art-source/previews/gdd-build/'+file+'-warning.png',505,y,249,140)
    p.text(777,y+5,title,15,[GREEN,RED,GOLD][i],True)
    p.para(777,y+38,body,255,12,MUTED)
p.finish()

p=Page('12  Build nativa','Aprender, configurar e continuar','Tutorial guiado, laboratório de treino e acessibilidade disponíveis no jogo.')
for i,(file,title,body) in enumerate([
    ('tutorial','OITO LIÇÕES','Mover, saltar, agachar, defender, combo, forte, elemental e ultimate.'),
    ('training','LABORATÓRIO','Dummy configurável, hitboxes, reposição e avanço de frame com F2.'),
    ('settings','PREFERÊNCIAS','Volumes separados, flashes, shake, vibração, dificuldade e remapeamento.'),
    ('arcade-ending','ARCADE','Quatro etapas, chefe, continue e retomada após fechar o jogo.')]):
    x=48+(i%2)*504;y=145+(i//2)*231
    p.image('../art-source/previews/gdd-build/'+file+'.png',x,y,270,152)
    p.text(x+286,y+5,title,12,GREEN,True)
    p.para(x+286,y+32,body,194,12,MUTED)
p.para(48,609,'Gamepad: mapeamentos validados por código. Teste físico de controles e playtests de conforto ainda necessários.',984,10,MUTED)
p.finish()

c.save()

font_css=''.join(f"@font-face{{font-family:{name};src:url('assets/{filename}')}}" for name,filename in FONT_FILES.items())
style=font_css+'''*{box-sizing:border-box}body{margin:0;background:#DEDAD0;font-family:Arial,sans-serif;color:#27372F}.toolbar{position:sticky;top:0;z-index:9;background:#FAF8F2F5;border-bottom:1px solid #CFC8BA;padding:14px 24px;display:flex;align-items:center;gap:12px;flex-wrap:wrap;backdrop-filter:blur(12px)}.toolbar strong{margin-right:auto;font-family:Editorial,Georgia,serif;font-weight:400}button,a.action{font:inherit;font-size:13px;border:1px solid #B9C5B9;background:#F7F5EE;color:#285B48;border-radius:4px;padding:9px 14px;cursor:pointer;text-decoration:none}button:hover{background:#E9EFE5}.page{position:relative;width:1080px;height:675px;margin:32px auto;overflow:hidden;box-shadow:0 5px 24px #39342119}.shape,.txt{position:absolute}.shape{pointer-events:none}.txt{white-space:nowrap}.txt[contenteditable=true]{outline:1px dashed #28654F70;white-space:normal;min-height:1em}.txt:focus{outline:2px solid #28654F;background:#EBF1E6}.hint{font-size:11px;color:#62695F}body.editing .hint{color:#28654F}@page{size:1080px 675px;margin:0}@media print{body{background:white}.toolbar{display:none}.page{margin:0;box-shadow:none;break-after:page;page-break-after:always}.page:last-child{break-after:auto}.txt[contenteditable=true]{outline:0}*{-webkit-print-color-adjust:exact;print-color-adjust:exact}}'''
body='\n'.join(f'<section class="page" aria-label="Página {p.number} {html.escape(p.title or p.section)}">'+''.join(p.parts)+'</section>' for p in pages)
script='''let editing=false;function toggleEdit(){editing=!editing;document.body.classList.toggle('editing',editing);document.querySelectorAll('.editable').forEach(e=>e.contentEditable=editing?'true':'false');document.getElementById('edit').textContent=editing?'Concluir edição':'Editar textos'}function saveDocument(){document.querySelectorAll('.editable').forEach(e=>e.contentEditable='false');editing=false;document.body.classList.remove('editing');document.getElementById('edit').textContent='Editar textos';const blob=new Blob(['<!doctype html>\\n'+document.documentElement.outerHTML],{type:'text/html;charset=utf-8'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='Gale_Breaker_GDD_Visual_editado.html';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)}'''
html_doc=f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Gale Breaker GDD visual</title><style>{style}</style></head><body><nav class="toolbar"><strong>GALE BREAKER · GDD VISUAL v0.10</strong><button id="edit" onclick="toggleEdit()">Editar textos</button><button onclick="saveDocument()">Salvar edição HTML</button><button onclick="window.print()">Imprimir PDF</button><span class="hint">Ao salvar, mantenha o HTML ao lado da pasta assets.</span></nav>{body}<script>{script}</script></body></html>'''
(OUT/'index.html').write_text(html_doc,encoding='utf-8')
(OUT/'page_index.json').write_text(json.dumps([{'page':p.number,'title':p.title or p.section} for p in pages],ensure_ascii=False,indent=2),encoding='utf-8')
print(f'Created {len(pages)} pages: {PDF.name} and index.html')
