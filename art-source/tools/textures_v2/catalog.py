"""Explicit texture-v2 production inventory. Creative pixels come from ImageGen.

The technical pipeline implements the user's requested offset/seam, alpha,
dilation, mask, exact-size and preview operations, without modifying v1 assets.
"""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT / 'art-source/textures-v2'
REFERENCES = {
    'santuario': ROOT/'concept-art/arenas/santuario-refinado-v1.png',
    'bazaar': ROOT/'concept-art/arenas/bazaar-fechado-v1.png',
    'forja': ROOT/'concept-art/arenas/forja-sol-vermelho-v1.png',
    'praia': ROOT/'concept-art/ui/menu-principal-praia-v1.png',
}

PALETTES = {
    'santuario': 'Warm pale gray limestone, vermilion painted timber, muted slate-blue ceramic, deep jade green cloth, aged brass and soft pink cherry blossoms.',
    'bazaar': 'Closed indoor bazaar: warm ivory limestone, honey sandstone, cobalt-and-ivory zellige, muted brass, crimson, navy blue, natural tan fibers.',
    'forja': 'Volcanic forge: charcoal basalt and iron, sparse warm ember cracks, controlled molten orange-red, aged brass, dark burgundy; a crimson sun against black sky.',
    'praia': 'Sunny anime-painted coastal village: pale cream sand, clear turquoise-to-deep-blue water, warm orange rock, warm white masonry, navy glazed roof tiles, lush jade/lime foliage and honey-brown boat timber.',
}

JOBS = []

BASE = '''Use case: stylized-concept. Production GAME TEXTURE, individual file, NOT an atlas or a presentation. The attached concept is the mandatory STYLE, COLOR and FORM reference only. Maintain its painted anime / cel-shaded fantasy game look, coherent moderately sized brush marks, medium-low contrast suitable for a shader with three bands of lighting. Do not reproduce the scene. This is unlit BASE COLOR, not a rendered material ball: completely flat orthographic surface view, NO perspective, no directional illumination, no baked shine or specular spot, no cast/contact shadow, no vignette or border/frame, no writing, labels, letters, numbers, watermark, scale bars or UI. No geometry sample slab or extra props. Preserve the reference palette. '''

def add(arena, material, kind, subject, size, repeat='none', world=2.0, emission=False):
    if kind == 'tileable':
        extra = '''ONE square repeating material filling the ENTIRE image, source resolution at least 1024x1024 (prefer 1536x1536 for seam processing). Seamless across all four borders, coherent pattern phase at edges. No unique central focal detail, ornamental rim or tile-wide gradients. Opaque RGB material, not a cutout. Flat even albedo color only. Surface details repeat without obvious mirroring or a grid of repeated medallions. '''
    elif kind == 'strip':
        extra = f'''ONE edge-to-edge material STRIP, desired aspect ratio {size[0]}:{size[1]}, high resolution. Continuous repeating detail along the {'horizontal' if repeat=='x' else 'vertical'} axis ONLY. No border at either repeating edge, no labels or gutters. Fully opaque RGB. '''
    elif kind in ['cutout', 'decal'] and material != 'tapete-central':
        extra = '''ONE centered isolated shape or ONE connected botanical cluster, square image, source at least 1024x1024. True TRANSPARENT alpha background; do not draw a white, black or checkerboard backdrop. Generous 8% transparent margin around the complete silhouette; no cropping at image edges. Opaque colored interior (including white flower petals), no semitransparent face or fake glow, crisp natural 1-2 px antialiasing, no yellow fringe or white matte, NO contact/drop shadow. This is a flat albedo decal/cutout to put on a polygon, not a scene. '''
    elif kind == 'backdrop':
        extra = '''A very WIDE 4:1 distant-background panorama, intended final size 4096x1024. ONLY distant sky and faraway landscape, no foreground, NO fighting floor, no paving, platform, carpet, ground plane or railings along the bottom; landscape reaches the bottom crop as distant hazy forms only. No labels, title, text, watermark, UI or reference-image border. Continuous wide composition, painted anime game background, controlled contrast and simplified broad forms so the distant scenery cannot compete with characters. '''
    else:
        extra = '''ONE fully OPAQUE rectangular 2:1 flat material panel, fills the whole image, desired 2048x1024. Orthographic texture view, no perspective, no floor around it, no contact shadows, no rolled edges. This is a unique nonrepeating piece. '''
    JOBS.append(dict(key=f'{arena}_{material}', arena=arena, material=material, type=kind,
                     size_px=list(size), repeat=repeat, world_size_m=world,
                     emission=emission, reference=str(REFERENCES[arena]),
                     prompt=BASE+PALETTES[arena]+' '+extra+'SUBJECT: '+subject))

# Tileable individual materials: 36.
tiles = {
'santuario': [
 ('piso-calcario','Large warm pale-gray limestone pavers with softly worn irregular edges, quiet narrow grout and subtle grain. No emblem or gold inlay. A two-by-two staggered course rhythm, no dark framing at tile boundaries.',2),
 ('pedra-estrutural','Light warm-gray solid limestone structural stone grain, restrained fine pores and small mineral variation, no masonry joints, foliage or carving.',2),
 ('madeira-vermelha','Vermilion painted temple timber, vertical wood grain, tiny scuffs exposing muted warm wood, even red pigment and no knots as a huge focal point.',2),
 ('latao-envelhecido','Matte aged golden brass material, fine painted hammered grain, gentle scratches and restrained oxidation uniformly across patch. NO metal plate border, bevel, rivets, highlight or vignette.',1),
 ('telhas-azul-ardosia','Repeating courses of curved slate-blue temple roof tiles, clear hand-painted shapes and evenly shaded local material colors, moderate lip separation, no light on one side and no roof silhouette.',2),
 ('tecido-jade','Plain deep-jade woven banner cloth, fine visible thread grain, absolutely NO folds shaded across patch, no seam, hem, embroidery, crest or border.',1),
 ('madeira-caixas','Honey-brown crate planks with vertical grain, quiet narrow seams, restrained wear, no reinforcement bars, handles, corners or full crate.',2),
 ('casca-cerejeira','Brown-gray cherry-tree bark texture for wrapping branches, flowing grooves and small warmer patches, no tree silhouette or branch object.',2),
 ('flores-cerejeira','Dense all-over pink cherry-blossom canopy texture: connected clusters of simple five-petal flowers in soft blush, pink and muted mauve, fully covers patch, no background, large bare branches or isolated bouquet.',1.5),
 ('pedra-musgo','Warm-gray weathered limestone with small naturally distributed jade moss patches, matte painted grain; uniformly distributed growth without a central rock silhouette.',2),
],
'bazaar': [
 ('piso-calcario','Warm ivory limestone floor with medium rectangular pavers and quiet fine seams, subtle cream/peach material variation, no rug, symbols, directional sun or shadows.',2),
 ('parede-arenito','Pale honey sandstone wall ashlar, staggered medium rectangular blocks with subtle mineral grain, narrow warm-gray joints, no border or arches.',2),
 ('azulejo-cobalto-marfim','Cobalt-blue and ivory geometric zellige ceramic. Geometric eight-point stars and clean interlocking line work, evenly repeating four-way pattern, no text, gold frame or directional highlights.',2),
 ('latao','Muted warm golden aged brass material, very fine painted hammered grain and small scratches, NO perimeter frame, ornamental border, bevel, rivets, central highlight or vignette.',1),
 ('tecido-carmesim','Muted crimson/carmine woven canopy fabric, fine thread texture and gentle pigment mottling only, NO cloth folds, shadows, hems or embroidered border.',1),
 ('tecido-azul-marinho','Deep navy woven cloth, fine moderate-contrast thread grain, no embroidery, folds, seam, shadow or border.',1),
 ('madeira-carrinhos','Warm brown wooden merchant cart planks, vertical grain, gentle wear and narrow plank seams, no whole cart, metal strips or wheels.',2),
 ('juta','Natural tan burlap sack fabric, small tidy interlaced crosshatch fibers, all-over evenly repeated cloth texture, no bag silhouette or tied neck.',1),
 ('especiaria-amarela','Fine golden-yellow ground spice powder, modestly varied small grains filling the patch evenly, no bowl, mound, scoop, pile edge or shadow.',.5),
],
'forja': [
 ('piso-basalto','Large matte charcoal-gray basalt floor pavers, clearly legible seams and soft worn edges, very sparse thin restrained ember-orange cracks within some stones. Most surface remains unlit dark gray; cracks alone can emit. No bright rim, lava pool or extensive glow.',2),
 ('basalto-natural','Natural charcoal basalt rock material, restrained fine fractures and planes, modest dark-gray variation, NO glowing cracks, warm reflected light, big highlights or isolated rock silhouette.',2),
 ('lava','Molten lava material seen straight down: cooled dark crust islands with connected bright red-orange molten channels and small yellow-hot cores. Emissive color only in channels; no global orange glow, scenery or ash haze.',2),
 ('crosta-vulcanica','Mostly solid black cooled volcanic crust with thin very sparse deep-red/orange cooling cracks, matte quiet material, almost entirely dark gray, no bright lava river.',2),
 ('ferro-escuro','Dark matte slightly hammered wrought-iron material, faint fine scratches, very restrained rust spots and medium-dark gray surface grain; no rivets, border, plate outline or bright specular spot.',1),
 ('latao','Matte aged brass with slightly soot-darkened golden color, fine scratches, even local paint variation; NO rim, frame, bevel, rivets or baked bright highlights.',1),
 ('tecido-vinho','Heavy dark wine/burgundy woven banner cloth, fine fibers and gentle pigment variation, NO folds, shadows, crest, stitching or hems.',1),
 ('tijolos-escuros','Dark gray soot-stained stone bricks in a consistent staggered pattern, quiet seams, matte surface grain; no orange reflected illumination, windows or glow.',2),
],
'praia': [
 ('agua','Clear turquoise shallow sea WATER seen directly overhead, even average depth/color everywhere, fine soft painted water ripples and subtle restrained pale caustic lines, no shoreline, sand gradient, sky/objects reflected, specular glitter or perspective.',2),
 ('areia','Fine warm ivory beach sand, subtle small mineral grains and tiny low-contrast ripples, uniform warm cream coverage, no footprint, shell, stone, plant or shadow.',2),
 ('pedra-laranja','Weathered warm orange coastal rock surface, subtle fine grain, quiet cracks and pale mineral specks. No rock object outline or high-contrast cavities.',2),
 ('tijolo-branco','Warm whitewashed limestone bricks in clean staggered courses, subtle pale cream color variation and narrow muted grout, even frontal material color, no corner or strong relief shadow.',2),
 ('tronco-coqueiro','Coconut palm trunk bark for wrapping on a cylinder: tan fibrous horizontal growth rings, consistent scale and restrained grain, no whole palm/tree silhouette.',2),
 ('tronco-arvore','Warm brown-gray coastal tree bark, flowing organic vertical grooves and a little muted moss, medium-low contrast, no silhouette or protruding branch object.',2),
 ('madeira-barco','Old honey-brown boat timber planks running vertically, subtle warm wood grain, small wear and restrained seams; no boat, ropes, hardware or lettering.',2),
 ('grama','Lush jade/lime short grass ground texture seen straight down, evenly distributed small painted blades fully cover patch, moderate color contrast, no tuft silhouette, soil border or cast shadow.',1),
 ('telhas-azul-marinho','Repeating overlapping curved navy-blue ceramic roof tiles. Deep ink/midnight blues with mild blue variation, clear course spacing, extremely restrained ceramic scuffs. NO green glaze, directional shine, rooftop silhouette or perimeter border.',2),
]}
for arena, entries in tiles.items():
    for name, subject, world in entries:
        add(arena,name,'tileable',subject,(1024,1024),'xy',world,
            emission=(arena=='forja' and name in ['lava','piso-basalto']))

add('bazaar','friso-azul-dourado','strip','Flat cobalt/navy ceramic ornamental frieze with restrained aged-gold geometric interlace on blue, consistent horizontal rhythm across BOTH left/right ends. Top and bottom may have straight quiet edging; NO frame at the repeating ends, no lettering.',(2048,512),'x',[4,1])
add('forja','lava-vertical','strip','Narrow vertical material of bright red-orange/yellow molten channels descending between dark basalt ridges. Flow runs top to bottom; top/bottom pattern must meet for continuous vertical UV repetition. No waterfall landscape, ground, rocks in perspective or bottom pool.',(512,2048),'y',[1,4],True)
add('praia','mar-transicao','strip','Single continuous top-down coastal material, increasing water depth LEFT TO RIGHT: narrow warm ivory wet sand at far left, thin natural foam edge, clear pale aqua shallows, bright turquoise near the center, progressively deep azure sea at the right. Ocean details and beach/foam edge must match TOP AND BOTTOM for repeating along the coast; the left and right edges do NOT repeat. No horizon, sky, boat, rocks or scenery. Calm soft painted ripples and moderate caustics.',(2048,1024),'y',[8,4])

add('santuario','medalhao-vento','decal','The floor wind medallion from reference: ONE circular thin aged brass outer ring and three elegant jade wind-swirl inlays around a smaller brass central circle. Only the brass and jade inlay elements are opaque; ALL gaps between them and the area outside the ring are truly transparent, NO limestone floor/background attached, no bevel shadow or neon glow.',(1024,1024),world=2)
add('santuario','emblema-vento','decal','ONE simple flat aged-gold circular wind swirl crest matching the reference green banners. Only the golden emblem is opaque; ALL negative space including gaps and center holes is transparent. No green cloth, backdrop or banner silhouette. Clean painted edge and slight gold pigment variation, no bevel or shine.',(1024,1024),world=.65)
add('forja','emblema-fogo','decal','ONE simple strong aged-gold flame crest matching the burgundy arena banners. Opaque flat gold silhouette with transparent inner cutouts/negative space. NO cloth, red square, glow, bevel or drop shadow.',(1024,1024),world=.65)
add('bazaar','tapete-central','decal','Unique muted burgundy-red handwoven rectangular carpet, modest navy/gold border around the perimeter and ONE simple centered navy/gold diamond medallion from reference. Entire 2:1 image is the flat opaque rug surface, no floor, shadow, curled corner or perspective. Rich but moderately contrasted fine woven color texture.',(2048,1024),world=[4,2])
add('bazaar','vitral-geometrico','decal','ONE complete tall shallow-pointed-arch geometric stained-glass window panel with thin dark lead lines and narrow pale stone/metal perimeter frame. Simple ivory, pale amber and pale cobalt geometric pattern matching concept. Window pane and frame opaque albedo; fully transparent outside silhouette, no wall or exterior scenery. No cast shadow, internal backlight bloom or text.',(1024,1024),world=[1.5,1.5])
add('forja','abertura-forja','decal','ONE square dark hammered-iron furnace panel with a narrow vertical molten-orange slit in its center and four small restrained corner rivets. Complete panel silhouette, small chamfered corners, fully transparent outside. The slit is bright orange with a few yellow-orange inner variations, NOT a transparent hole, no large glow halo. Panel is otherwise dark gray, no background wall or floor. Maintain only low-contrast material paint shading.',(1024,1024),world=1.5,emission=True)

cutouts=[
('praia','hibisco','ONE red tropical hibiscus bloom with five broad petals, a small visible yellow stamen, frontal slightly organic view, no leaves or plant pot.',.55),
('praia','flores-brancas','ONE small coherent connected cluster of THREE ivory-white frangipani/plumeria flowers with warm yellow centers, clean opaque white petals, no pot or ground.',.6),
('praia','folha-monstera','ONE broad jade-green monstera leaf, clear natural internal holes and split silhouette, subtle painted veins, attached short stem, no second leaf.',.8),
('praia','folha-larga','ONE broad tropical heart/oval-shaped leaf from the concept, fresh jade/lime green, clear veins and short stem, complete isolated leaf, no second leaf.',.8),
('praia','folha-coqueiro','ONE fully spread coconut palm frond with central rib and many long thin readable leaflets, diagonal complete silhouette, small natural gaps between leaflets fully transparent, no trunk or coconut.',2.5),
('praia','coral-rosa','ONE compact coherent branching pink coral cluster with many rounded arms joined to a small base, complete silhouette, all gaps transparent, no seabed, rock, water or animals.',.85),
('praia','coral-laranja','ONE compact coherent branching orange coral cluster, arms connected at small base, clear silhouette and transparent gaps, no seabed, rocks, water or animals.',.8),
('praia','coral-roxo','ONE low lilac/purple coral cluster with connected rounded organic branches and complete base, transparent gaps, no seabed, rocks, water or animals.',.65),
('santuario','ramo-cerejeira','ONE gracefully curving small cherry-tree branch with a connected cluster of soft pink five-petal blossoms, brown twig structure visible, no trunk, leafy canopy, background or falling isolated petals.',1.5),
]
for arena,name,subject,world in cutouts:add(arena,name,'cutout',subject,(1024,1024),world=world)

add('santuario','fundo-distante','backdrop','ONLY distant mountain sanctuary landscape: layered cool blue-green ridges, quiet white waterfalls descending in the far valley, a small traditional pagoda perched on a far upper-right cliff, soft morning blue sky and thin clouds. NO torii in foreground, lantern, tree branch, blossom framing, railings, architecture at camera level or fighting floor. Bottom is still distant atmospheric slopes/mist, never a flat ground/platform.',(4096,1024),world=[200,50])
add('forja','fundo-distante','backdrop','ONLY distant volcanic panorama: black charcoal sky with ONE solid crimson-red full sun above the center, stepped black basalt fortress FAR AWAY, thin orange molten falls and dim volcanic haze among far cliffs. Sky is black, not red; sun is solid red, NOT an eclipse. No near pillars, banners, chains, cage, braziers, floating rocks, perimeter ledges or fighting floor. The bottom is distant dark terrain and haze, no foreground lava lake.',(4096,1024),world=[200,50])
add('praia','fundo-distante','backdrop','ONLY distant sunny tropical backdrop: generous blue sky with softly painted white cumulus, an ocean horizon, far blue sea and a few tiny rocky green islets at the distant horizon. No shore, sand, nearby waves, coast at camera position, village, roofs, palm tree framing, foreground coral, boat, pier or text. Lower band is distant ocean at horizon scale only, never fighting ground.',(4096,1024),world=[200,50])

def main():
    WORK.mkdir(parents=True,exist_ok=True)
    assert len(JOBS)==57, len(JOBS)
    assert sum(j['type']=='tileable' for j in JOBS)==36
    if '--keys' in sys.argv:
        print(json.dumps([job['key'] for job in JOBS if not (WORK/'sources'/job['arena']/(job['key']+'.png')).exists()]))
        return
    if '--job' in sys.argv:
        print(json.dumps(next(job for job in JOBS if job['key']==sys.argv[sys.argv.index('--job')+1]),ensure_ascii=False))
        return
    if '--pending' in sys.argv:
        pending=[job for job in JOBS if not (WORK/'sources'/job['arena']/(job['key']+'.png')).exists()]
        print(json.dumps(pending[:6],ensure_ascii=False))
        return
    (WORK/'catalog.json').write_text(json.dumps(JOBS,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'creative_sources':len(JOBS),'emission_masks':sum(j['emission'] for j in JOBS),'materials':len(JOBS)+sum(j['emission'] for j in JOBS)}))

if __name__=='__main__':main()
