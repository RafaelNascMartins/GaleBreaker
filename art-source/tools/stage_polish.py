"""Authored modular details for the three concept-inspired arenas."""
import bpy,math,random
from mathutils import Vector

def enhance_stage(stage, box, cyl, material):
    rng=random.Random(718)
    def remove(prefixes):
        for obj in list(bpy.data.objects):
            if obj.type=='MESH' and any(obj.name.startswith(p) for p in prefixes):
                bpy.data.objects.remove(obj,do_unlink=True)
    def branch(name,a,b,r0,r1,mat):
        a,b=Vector(a),Vector(b);vec=b-a
        obj=cyl(name,(a+b)*.5,r0,r1,vec.length,mat,8)
        obj.rotation_mode='QUATERNION'
        obj.rotation_quaternion=Vector((0,0,1)).rotation_difference(vec)
        return obj
    def rock(name,loc,scale,mat,subdiv=1):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdiv,radius=1,location=loc)
        obj=bpy.context.object;obj.name=name;obj.scale=scale;obj.data.materials.append(mat)
        return obj
    wood=material('aged_wood',(.23,.12,.08))
    dark=material('dark_iron',(.10,.13,.15))
    gold=material('warm_brass',(.72,.46,.15))
    lamp=material('lantern_glass',(1,.63,.19),.3)
    stone_colors=[(.43,.47,.45),(.49,.51,.48),(.38,.43,.43)] if stage=='zephyr_dojo' else [(.16,.15,.17),(.20,.18,.18),(.13,.14,.16)] if stage=='molten_forge' else [(.61,.44,.25),(.68,.51,.30),(.56,.40,.23)]
    stones=[material('paving_'+str(i),color) for i,color in enumerate(stone_colors)]
    # Individual shallow pavers make the floor readable without a debug grid.
    for row in range(9):
        for col in range(23):
            x=-11+col+(.45 if row%2 else 0)
            box('Paver',(x,-4+row,.015),(.975,.975,.035),stones[rng.randrange(3)])
    if stage=='zephyr_dojo':
        remove(['Trunk_','Crown_','Mountain_','ToriiLint'])
        pinks=[material('sakura_'+str(i),color) for i,color in enumerate([(.85,.46,.59),(.95,.64,.72),(.68,.32,.45)])]
        mountains=[material('mist_'+str(i),color) for i,color in enumerate([(.31,.40,.45),(.40,.48,.52),(.52,.57,.59)])]
        for layer in range(3):
            for i in range(7):
                rock('DistantPeak',(i*5-15,14+layer*7,3.4+layer), (3.4,3.4,4.8+rng.random()*4),mountains[layer],2)
        for obj in bpy.data.objects:
            if obj.name.startswith('ToriiPillar'):
                obj.location.y=7.5
        for i in range(7):
            x=(i-3)*2.2
            z=5.25+.018*x*x
            obj=box('CurvedToriiRoof',(x,7.5,z),(2.25,.7,.26),dark)
            obj.rotation_euler.y=-math.atan(.036*x)
        box('ToriiCrossbar',(0,7.5,4.55),(14.1,.40,.27),wood)
        for x in [-9,-5.7,6.0,9.7]:
            base=Vector((x,6.2,0));top=base+Vector((rng.uniform(-.3,.3),0,3.1))
            branch('SakuraTrunk',base,top,.16,.075,wood)
            for i in range(7):
                angle=i*2.399
                end=top+Vector((math.cos(angle)*1.1,math.sin(angle)*.65,.45+(i%3)*.22))
                branch('SakuraBranch',top-Vector((0,0,.5)),end,.065,.018,wood)
                rock('SakuraBlossoms',end,(.80,.70,.48),pinks[i%3],2)
        for x in [-8,-4,4,8]:
            box('LanternPedestal',(x,3,.35),(.65,.65,.7),stones[0])
            box('LanternLight',(x,3,.95),(.42,.42,.52),lamp)
            for sx in [-1,1]:
                box('LanternFrame',(x+sx*.24,3,1.0),(.055,.52,.65),dark)
            box('LanternCap',(x,3,1.33),(.75,.72,.12),dark)
    elif stage=='molten_forge':
        remove(['BloodSun'])
        lava=material('deep_lava',(.95,.25,.035),.5)
        basalt=material('basalt_cliff',(.12,.10,.12))
        for i in range(10):
            rock('ForgeCliff',(i*3-13,13,3.3),(2.5,3,4+rng.random()*3),basalt,1)
        bpy.ops.mesh.primitive_torus_add(major_radius=2.6,minor_radius=.12,major_segments=48,minor_segments=8,location=(0,17,8.5),rotation=(math.pi/2,0,0))
        bpy.context.object.name='EclipseHalo';bpy.context.object.data.materials.append(lava)
        disc=cyl('EclipseDisc',(0,17,8.5),2.45,2.45,.1,dark,40);disc.rotation_euler.x=math.pi/2
        for x in [-7.5,7.5]:
            for i in range(13):
                z=5.0-i*.30
                bpy.ops.mesh.primitive_torus_add(major_radius=.16,minor_radius=.035,major_segments=12,minor_segments=5,location=(x,4,z),rotation=(math.pi/2,0,(i%2)*math.pi/2))
                bpy.context.object.name='HangingChain';bpy.context.object.data.materials.append(dark)
            box('BrazierBowl',(x,4,1.0),(1.0,.85,.45),dark)
            rock('CoalGlow',(x,4,1.25),(.45,.35,.3),lava,1)
        for x in [-10,-5,5,10]:
            box('ForgeButtress',(x,5,1.4),(1.1,1.7,2.8),dark)
            for z in [.4,1.3,2.2]:box('ForgeBrassBand',(x,4.10,z),(1.2,.08,.12),gold)
        for x in [-9,-3,3,9]:
            box('LavaChannel',(x,2.8,.05),(1.4,.12,.06),lava)
    else:
        remove(['Arch_'])
        tile=material('bazaar_tile',(.12,.33,.43))
        cloths=[material('market_cloth_'+str(i),color) for i,color in enumerate([(.54,.14,.22),(.12,.38,.39),(.72,.42,.14)])]
        for x in [-7.5,-2.5,2.5,7.5]:
            for i in range(9):
                angle=math.pi*(i+.5)/9
                obj=box('VaultedArch',(x+math.cos(angle)*2.25,4.4,3.4+math.sin(angle)*1.45),(.84,.55,.33),tile)
                obj.rotation_euler.y=angle-math.pi/2
        for stall,x in enumerate([-7,0,7]):
            for sx in [-1.35,1.35]:box('MarketPost',(x+sx,5.4,1.4),(.10,.10,2.8),wood)
            box('StallCounter',(x,5.0,.75),(2.9,1.1,1.5),wood)
            # Draped awning with a curved profile, colored hanging edge.
            verts=[];faces=[]
            for j in range(7):
                y=4.2+j*.35;z=2.7+math.sin(j/6*math.pi)*.22
                verts.extend([(x-1.55,y,z),(x+1.55,y,z)])
                if j<6:faces.append((j*2,j*2+1,j*2+3,j*2+2))
            mesh=bpy.data.meshes.new('AwningMesh');mesh.from_pydata(verts,[],faces);mesh.materials.append(cloths[stall])
            obj=bpy.data.objects.new('DrapedAwning',mesh);bpy.context.collection.objects.link(obj)
            box('AwningValance',(x,4.2,2.55),(3.1,.05,.30),cloths[stall])
            for j in range(5):
                rock('SpiceSack',(x-1+j*.5,4.7,1.65),(.20,.22,.22),cloths[(j+stall)%3],2)
            for sx in [-1.2,1.2]:
                branch('LanternCord',(x+sx,4.5,2.7),(x+sx,4.5,2.2),.012,.012,gold)
                cyl('MarketLantern',(x+sx,4.5,2.0),.12,.12,.40,lamp,10)
        for x in range(-9,10,3):
            obj=box('FloorMosaic',(x,-1.5,.045),(.35,.35,.02),gold)
            obj.rotation_euler.z=math.pi/4
    # Merge by material to keep this decorative detail inexpensive in Godot.
    groups={}
    for obj in list(bpy.data.objects):
        if obj.type=='MESH' and obj.data.materials:
            groups.setdefault(obj.data.materials[0].name,[]).append(obj)
    for name,objects in groups.items():
        if len(objects)<2:continue
        bpy.ops.object.select_all(action='DESELECT')
        for obj in objects:obj.select_set(True)
        bpy.context.view_layer.objects.active=objects[0]
        bpy.ops.object.join()
        objects[0].name='Stage_'+name
