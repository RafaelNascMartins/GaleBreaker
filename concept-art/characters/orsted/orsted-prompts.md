# Orsted (ex-Volt): prompts das referências

Salvar as imagens em `concept-art/characters/orsted/` com o nome indicado em cada prompt.
Todos os turnarounds seguem a mesma escala da X12 (1,80 m de referência), os pés na mesma linha
e as juntas no mesmo lugar em todas as roupas: assim o esqueleto e as animações servem para todas.

Base de estilo, que entra em todos os prompts (já está colada em cada um):
> Mega Man Legends 1997 PS1 style, NORMAL anime proportions, about 6 heads tall, head about 17% of
> height, BIG blocky hands and feet, lean straight limbs, flat angular low-poly facets, about 15
> colors, hard-edged painted shading in flat bands, no gradients, no texture noise, no outlines
> inside the shapes, flat light grey background (#8c8c8c)

---

## 1. Roupa padrão: inventor da sucata

### 1a. Turnaround (`orsted-turnaround-psx-v1.png`)
```
Character turnaround sheet of ORSTED, an adult male scrap inventor (around 25 years old, 1.80 m),
three views side by side at the same scale: FRONT, LEFT PROFILE, BACK. Relaxed A-pose, arms 30
degrees away from the body, palms facing the thighs, feet shoulder width apart, both feet on the
same ground line, looking straight ahead, neutral face.
Look: messy spiky hair, blond on top with dark brown roots and underside; a short dark charcoal
work shirt with rolled sleeves; riveted scrap-metal armor plates in mustard yellow with rusty
blue-grey patches: a big shoulder plate on the right shoulder, a chest plate with a round glowing
cyan energy core in the centre, plates on both knees; brown leather straps and a utility belt with
pouches; a torn mustard cloth hanging from the belt at the front and a red rag at the back; dark
baggy cargo trousers tucked into chunky boots with mustard toe caps and thick black soles;
fingerless dark gloves with leather wrist cuffs; a glass energy cell (cyan glow) strapped on his
back with copper and red cables running to the chest core. Empty hands (the weapon is a separate
model). Colors: mustard #D49B38, rust blue-grey #435C6E, charcoal, brown leather, skin, cyan
glow #22E4FF.
Mega Man Legends 1997 PS1 style, NORMAL anime proportions, about 6 heads tall, head about 17% of
height, BIG blocky hands and feet, lean straight limbs, flat angular low-poly facets, about 15
colors, hard-edged painted shading in flat bands, no gradients, no texture noise, flat light grey
background, no text, no labels.
```

### 1b. Expressões (`orsted-expressoes-24-psx-v1.png`)
```
Sheet of 24 facial expressions of ORSTED (adult male scrap inventor, blond spiky hair with dark
roots, a small soot smudge on the left cheek), 6 columns x 4 rows, every cell the same size. Each
cell shows ONLY the front of the face from the eyebrows to the chin, filled with skin to the cell
borders (no background, no hair, no ears, no transparency). Eyes, eyebrows and mouth always at the
same position and size in every cell, only their shapes change.
Order, left to right, top to bottom: 1 neutral, 2 blink, 3 shout, 4 pain, 5 KO (eyes as X marks),
6 victory grin, 7 effort (gritted teeth), 8 focus, 9 half-closed eyes, 10 surprised, 11 angry,
12 confident smirk, 13 laughing, 14 strong pain, 15 nervous sweat, 16 determined, 17 looking left,
18 looking right, 19 talking "A", 20 talking "O", 21 talking with closed mouth, 22 tired,
23 embarrassed blush, 24 meditating (eyes closed, calm).
Mega Man Legends 1997 PS1 face texture style: big simple anime eyes painted flat, thick eyebrows,
small mouth, about 15 colors, hard-edged flat shading, no gradients, no outlines around the
cells, no text, no numbers.
```

### 1c. Painéis de textura (`orsted-texturas-20-paineis-psx-v1.png`)
```
Texture panel sheet for a PS1 low-poly character: 20 square panels in a 5 x 4 grid on a flat grey
background, each panel with a small number tag in its top-left corner (1 to 20). Each panel is a
flat front view of ONE surface, filling the panel, painted with hard-edged flat shading bands:
1 chest plate front with the round cyan energy core in the centre, 2 shirt back with the energy
cell straps, 3 right shoulder plate (mustard, rivets, rust patches), 4 shirt side / rolled sleeve,
5 upper arm skin, 6 forearm skin with leather wrist cuff, 7 fingerless glove back of hand,
8 glove palm and fingers, 9 belt with pouches (front), 10 torn mustard cloth hanging from the belt,
11 cargo trousers front (dark charcoal, stitched patches), 12 cargo trousers back with the red rag,
13 knee plate (mustard with blue-grey rust), 14 boot front with mustard toe cap,
15 boot side, 16 boot sole (thick black tread), 17 back energy cell (glass with cyan glow, copper
caps, red cables), 18 top of the head hair (blond with dark roots), 19 side of the head hair,
20 neck skin with the collar of the shirt.
Mega Man Legends 1997 PS1 texture style, about 15 colors, hard-edged painted shading, no
gradients, no noise, flat colors, no text other than the number tags.
```

---

## 2. Roupa de cores invertidas
Não precisa de concept: sai da página pintada da roupa padrão pela ferramenta de troca de cor
(`legends_recolor.py`), como a Obsidiana da X12 (amarelo das placas vira azul aço, o azul vira
laranja, o tecido escuro vira claro e o brilho ciano vira magenta). Se quiser ver antes, use este:

### 2a. Prévia opcional (`orsted-invertido-turnaround-psx-v1.png`)
```
Same character, same pose, same three views and same scale as the ORSTED scrap inventor
turnaround (front, left profile, back, A-pose), only the colors inverted: armor plates steel blue
#3A6FB0 with orange rust patches, shirt and trousers light bone white, leather straps dark
charcoal, the energy core and the back cell glowing magenta #FF3DCB instead of cyan, hair stays
blond with dark roots. Mega Man Legends 1997 PS1 style, about 6 heads tall, flat angular low-poly
facets, about 15 colors, hard-edged flat shading, no gradients, flat light grey background, no text.
```

---

## 3. Roupa de pistoleiro (com o moveset de revólver)

### 3a. Turnaround (`orsted-pistoleiro-turnaround-psx-v1.png`)
```
Character turnaround sheet of ORSTED as a GUNSLINGER: the same adult male (blond spiky hair with
dark roots), same body, same scale and same joint positions as his scrap inventor sheet; three
views side by side: FRONT, LEFT PROFILE, BACK, relaxed A-pose, arms 30 degrees away from the body,
both feet on the same ground line, neutral face.
Look: a wide-brim cowboy hat in dark brown leather with a copper band; a short dusty tan duster
coat open at the front, reaching mid-thigh, with a scrap-metal plate on the right shoulder;
a red bandana around the neck; a dark vest over a cream shirt; a gun belt with a low holster on the
right thigh (EMPTY holster, the revolver is a separate model) and a row of bullet loops with
cyan-tipped cartridges; dark brown trousers; tall pointed cowboy boots with copper spurs and a
small cyan glow at the heel; leather gloves. Colors: tan #C9A46A, dark brown, red bandana,
cream, copper, cyan accent #22E4FF.
Mega Man Legends 1997 PS1 style, NORMAL anime proportions, about 6 heads tall, head about 17% of
height, BIG blocky hands and feet, lean straight limbs, flat angular low-poly facets, about 15
colors, hard-edged painted shading in flat bands, no gradients, no texture noise, flat light grey
background, no text, no labels.
```

### 3b. Painéis de textura (`orsted-pistoleiro-texturas-paineis-psx-v1.png`)
```
Texture panel sheet for a PS1 low-poly character outfit: numbered square panels (1 to 18) in a
grid on a flat grey background, small number tag top-left in each. Flat front view of one surface
per panel, filling it, hard-edged flat shading: 1 duster coat front (open, with the vest and shirt
inside), 2 duster coat back, 3 coat sleeve, 4 coat tail / hem, 5 scrap shoulder plate,
6 red bandana, 7 vest front with buttons, 8 gun belt with bullet loops (cyan tips), 9 holster
(empty, dark leather with copper stitches), 10 trousers front, 11 trousers back, 12 leather glove
back of hand, 13 glove palm, 14 cowboy boot front, 15 cowboy boot side with spur, 16 boot sole,
17 hat crown with copper band, 18 hat brim seen from above.
Mega Man Legends 1997 PS1 texture style, about 15 colors, no gradients, no noise, no text other
than the number tags.
```

---

## 4. Roupa de cientista maluco

### 4a. Turnaround (`orsted-cientista-turnaround-psx-v1.png`)
```
Character turnaround sheet of ORSTED as a MAD SCIENTIST: the same adult male, same body, same scale
and same joint positions as his scrap inventor sheet; three views side by side: FRONT, LEFT
PROFILE, BACK, relaxed A-pose, arms 30 degrees away from the body, both feet on the same ground
line, neutral face.
Look: his blond hair blown up wild and frizzy by static electricity (dark roots), round brass
welding goggles pushed up on the forehead with cyan lenses; a long white lab coat reaching the
knees, scorched and stained at the hem, sleeves rolled to the elbow, a pocket with pens and a
screwdriver; a dark turtleneck under it; long black rubber gloves up to the elbow; a small tesla
coil backpack with copper coils and a cyan spark on top, cables running to a chest battery;
grey trousers; chunky black rubber boots. Colors: white coat with grey shading, black rubber,
brass and copper, grey, cyan glow #22E4FF.
Mega Man Legends 1997 PS1 style, NORMAL anime proportions, about 6 heads tall, head about 17% of
height, BIG blocky hands and feet, lean straight limbs, flat angular low-poly facets, about 15
colors, hard-edged painted shading in flat bands, no gradients, no texture noise, flat light grey
background, no text, no labels.
```

### 4b. Painéis de textura (`orsted-cientista-texturas-paineis-psx-v1.png`)
```
Texture panel sheet for a PS1 low-poly character outfit: numbered square panels (1 to 17) in a
grid on a flat grey background, small number tag top-left in each. Flat front view of one surface
per panel, filling it, hard-edged flat shading: 1 lab coat front (open over the dark turtleneck,
chest battery), 2 lab coat back with the tesla backpack straps, 3 coat sleeve rolled to the elbow,
4 coat hem scorched, 5 coat pocket with pens and screwdriver, 6 turtleneck, 7 long black rubber
glove forearm, 8 rubber glove back of hand, 9 rubber glove palm, 10 grey trousers front,
11 grey trousers back, 12 rubber boot front, 13 rubber boot side, 14 boot sole, 15 tesla coil
backpack (copper coils, cyan spark), 16 brass goggles with cyan lenses, 17 wild frizzy hair top.
Mega Man Legends 1997 PS1 texture style, about 15 colors, no gradients, no noise, no text other
than the number tags.
```

---

## 5. Arma de energia (roupa padrão, invertida e cientista)

### 5a. Turnaround da arma (`orsted-arma-energia-turnaround-psx-v1.png`)
```
Prop turnaround sheet of a hand cannon held in one hand, for a PS1 low-poly fighting game: five
views at the same scale on a flat light grey background: LEFT SIDE, RIGHT SIDE, TOP, FRONT (muzzle)
and BACK. A chunky scrap-built energy pistol about 55 cm long: a thick barrel made of a riveted
mustard-yellow metal tube with blue-grey rust patches, a glass chamber in the middle glowing cyan
#22E4FF, a round muzzle ring with a cyan glow inside, a copper carry handle on top, red and copper
cables looping from the chamber to the grip, a black grip wrapped in tape and a simple trigger
guard. Blocky, few big flat shapes, readable from far away.
Mega Man Legends 1997 PS1 style, flat angular low-poly facets, about 15 colors, hard-edged painted
shading in flat bands, no gradients, no text, no hand, no character.
```

### 5b. Painéis da arma (`orsted-arma-energia-texturas-paineis-psx-v1.png`)
```
Texture panel sheet for a PS1 low-poly prop: 8 numbered square panels in a grid on a flat grey
background, small number tag top-left. Flat view of one surface per panel, filling it, hard-edged
flat shading: 1 barrel side (mustard riveted metal, rust patches), 2 barrel top with the copper
handle, 3 glass energy chamber glowing cyan, 4 muzzle front (ring with cyan glow), 5 back cap,
6 grip wrapped in black tape, 7 trigger guard and trigger, 8 cables (red and copper).
Mega Man Legends 1997 PS1 texture style, about 15 colors, no gradients, no noise, no text other
than the number tags.
```

---

## 6. Revólver (roupa de pistoleiro)

### 6a. Turnaround do revólver (`orsted-revolver-turnaround-psx-v1.png`)
```
Prop turnaround sheet of a big six-shooter revolver held in one hand, for a PS1 low-poly fighting
game: five views at the same scale on a flat light grey background: LEFT SIDE, RIGHT SIDE, TOP,
FRONT (muzzle) and BACK. An oversized western revolver about 40 cm long, slightly chunky and
cartoonish: a long octagonal barrel in dark gunmetal with a copper front sight, a big cylinder with
six chambers showing cyan glowing tips, a copper frame plate with a small scrap patch, a hammer,
a curved wooden grip in reddish brown with a copper medallion, a trigger guard. Blocky, few big
flat shapes, readable from far away.
Mega Man Legends 1997 PS1 style, flat angular low-poly facets, about 15 colors, hard-edged painted
shading in flat bands, no gradients, no text, no hand, no character.
```

### 6b. Painéis do revólver (`orsted-revolver-texturas-paineis-psx-v1.png`)
```
Texture panel sheet for a PS1 low-poly prop: 8 numbered square panels in a grid on a flat grey
background, small number tag top-left. Flat view of one surface per panel, filling it, hard-edged
flat shading: 1 barrel side (dark gunmetal, octagonal facets), 2 barrel top with the copper sight,
3 cylinder side (six chambers), 4 cylinder front with cyan glowing tips, 5 frame side with the
copper plate and hammer, 6 wooden grip side with the copper medallion, 7 grip back, 8 trigger
guard and trigger.
Mega Man Legends 1997 PS1 texture style, about 15 colors, no gradients, no noise, no text other
than the number tags.
```
