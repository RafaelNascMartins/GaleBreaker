"""Mesh detail and pose-space corrections shared by the Blender asset builder.

The meshes remain deliberately stylized. Rigid stone/scrap plates retain one
bone per piece; skin joints overlap so bending never opens a hollow limb.
"""
import math
import bpy
from mathutils import Vector, Matrix


def add_model_detail(mb, fid):
    h = {'kaze':1.9,'ignis':1.96,'tophia':1.78,'volt':1.78}[fid]
    # Facial planes, eyes with light sclera, nose, mouth and ears. The old
    # single dark dot disappeared entirely at the fighting camera distance.
    head_z = 1.77 if fid=='kaze' else 1.76 if fid=='ignis' else 1.71
    head_y = -.20 if fid=='ignis' else -.01
    skin = 1 if fid=='ignis' else 0
    front = head_y - (.14 if fid=='ignis' else .125)
    mb.add_sphere('head',skin,(0,front+.028,head_z-.052),(.079,.052,.055),12,8)
    mb.add_sphere('head',skin,(0,front-.017,head_z-.008),(.022,.030,.034),10,6)
    mb.add_box('head',7,(0,front-.020,head_z-.063),(.050,.012,.008),bevel=0)
    for sx in (-1,1):
        mb.add_sphere('head',skin,(sx*.11,head_y,head_z-.01),(.024,.034,.040),10,8)
        mb.add_sphere('head',0,(sx*.042,front+.002,head_z+.008),(.016,.009,.011),10,8)
        mb.add_sphere('head',7,(sx*.042,front-.006,head_z+.009),(.006,.004,.007),8,6)
        mb.add_box('head',5,(sx*.042,front+.002,head_z+.030),(.034,.010,.007),rot_deg=(0,0,sx*-7),bevel=0)

    for side,sx in [('l',1),('r',-1)]:
        width={'kaze':.24,'ignis':.33,'tophia':.25,'volt':.23}[fid]
        elbow=(sx*(width+.06),-.08 if fid=='ignis' else 0,1.20 if fid in ['kaze','ignis'] else 1.18)
        zone=skin if fid!='tophia' else 3
        radius=.105 if fid=='ignis' else .074
        mb.add_sphere('forearm_'+side,zone,elbow,(radius,radius,radius),12,8)
        hand_x=sx*(width+.08)
        hand_z=.78 if fid=='ignis' else .84 if fid!='tophia' else .83
        if fid=='kaze':
            # Four separate fingers and thumb read as an open martial palm.
            for i in range(4):
                x=hand_x+sx*(1.5-i)*.016
                digit=['index','middle','ring','pinky'][i]
                mb.add_limb('finger_'+digit+'_'+side,0,(x,-.09,hand_z-.025),(x,-.09,hand_z-.095+abs(i-1.5)*.009),.009,.007,8)
            mb.add_limb('finger_thumb_'+side,0,(hand_x+sx*.028,-.08,hand_z+.01),(hand_x+sx*.055,-.09,hand_z-.025),.012,.009,8)
            # Jade wraps, folds and gold clasp stay separate readable shapes.
            for k in range(3):
                mb.add_limb('forearm_'+side,2,(hand_x,-.03,.945+k*.026),(hand_x,-.03,.96+k*.026),.063,.063,12)
            for i in range(5):
                mb.add_sphere('foot_'+side,0,(sx*.1365+(i-2)*.016,-.192,.04),(.011,.022,.019),8,6)
        elif fid=='ignis':
            mb.add_sphere('upper_arm_'+side,1,(sx*.36,-.13,1.39),(.134,.13,.19),14,10)
            for i in range(4):
                mb.add_sphere('hand_'+side,1,(hand_x+(i-1.5)*.027,-.22,hand_z+.025),(.022,.026,.026),10,6)
            mb.add_box('thigh_'+side,3,(sx*.19,-.134,.72),(.10,.025,.14),rot_deg=(0,sx*9,4))
            mb.add_box('foot_'+side,7,(sx*.17,-.10,.012),(.15,.28,.025),bevel=1)
        elif fid=='tophia':
            # Overlapping, offset sandstone scales replace large plain cubes.
            for bone,center,size in [
                ('shoulder_'+side,(sx*.25,-.09,1.51),(.20,.09,.14)),
                ('forearm_'+side,(sx*.31,-.135,1.05),(.16,.08,.19)),
                ('thigh_'+side,(sx*.15,-.145,.77),(.20,.08,.19)),
                ('shin_'+side,(sx*.15,-.145,.34),(.17,.08,.23))]:
                mb.add_box(bone,2,center,size,rot_deg=(sx*8,sx*12,sx*7),taper_top=.75)
                mb.add_box(bone,3,(center[0]+sx*.035,center[1]-.045,center[2]-.025),(size[0]*.53,.025,size[2]*.72),rot_deg=(5,sx*-13,7))
            for i in range(3):
                mb.add_box('hand_'+side,3,(hand_x+(i-1)*.043,-.145,hand_z+.025),(.037,.035,.055))
            for i,digit in enumerate(['index','middle','ring','pinky']):
                x=hand_x+sx*(1.5-i)*.030
                mb.add_limb('finger_'+digit+'_'+side,2,(x,-.09,.79),(x,-.09,.70),.022,.016,7)
            mb.add_limb('finger_thumb_'+side,2,(hand_x+sx*.028,-.08,.84),(hand_x+sx*.055,-.09,.805),.026,.020,7)
            for i in range(3):
                mb.add_rock('shoulder_'+side,2,(sx*(.20+i*.05),-.08,1.50+(i%2)*.04),(.09,.11,.08),17+i)
                mb.add_rock('forearm_'+side,2,(sx*.31,-.14,1.03+(i-1)*.07),(.10,.05,.075),41+i)
            mb.add_sphere('shin_'+side,3,(sx*.15,-.025,.51),(.108,.11,.10),8,6)
        else:
            # Visible bolts, straps and mismatched plate patches reinforce trash
            # armor rather than a pristine sci-fi suit.
            for z in [1.42,1.48]:
                mb.add_sphere('shoulder_'+side,7,(sx*.245,-.105,z),(.018,.014,.018),8,6)
            mb.add_box('forearm_'+side,2,(sx*.29,-.105,1.02),(.07,.035,.14),rot_deg=(0,sx*12,13))
            mb.add_box('thigh_'+side,6,(sx*.145,-.08,.70),(.16,.055,.065),rot_deg=(0,0,sx*10))
            mb.add_box('foot_'+side,7,(sx*.14,-.08,.016),(.13,.26,.028))
    if fid=='kaze':
        mb.add_box('hips',4,(0,-.187,1.0),(.075,.035,.075),rot_deg=(0,0,45))
    elif fid=='ignis':
        # Rounded pale pecs keep the chest distinct from red shoulder caps.
        for sx in [-1,1]:
            mb.add_sphere('chest',0,(sx*.13,-.25,1.44),(.135,.095,.115),14,10)
        mb.add_box('hat',4,(0,-.344,1.90),(.055,.018,.035))
    elif fid=='tophia':
        for sx in [-1,1]:
            mb.add_box('chest',3,(sx*.105,-.205,1.40),(.15,.055,.17),rot_deg=(0,sx*15,sx*12))
        mb.add_box('hips',3,(0,-.165,.96),(.105,.065,.10),rot_deg=(0,0,45))
        for i in range(5):
            mb.add_rock('chest',2,((i%3-1)*.12,-.22,1.33+(i//3)*.14),(.10,.055,.10),63+i)
    else:
        # Blond cap with individual locks; only the tips are singed dark.
        mb.add_sphere('head',5,(0,.015,1.785),(.118,.125,.082),14,8)
        for i in range(9):
            angle=i*2.399
            base=Vector((math.cos(angle)*.072,math.sin(angle)*.078,1.80))
            tip=base+Vector((math.cos(angle)*.045,math.sin(angle)*.035,.075+(i%3)*.014))
            mid=base.lerp(tip,.82)
            mb.add_limb('head',5,base,mid,.029,.010,7)
            mb.add_limb('head',7,mid,tip,.010,.001,7)
        for i in range(3):
            mb.add_box('chest',7,(0,.215,1.28+i*.08),(.15,.035,.024))
        for y in [-.42,-.48]:
            mb.add_limb('cannon',7,(-.31,y,.89),(-.31,y-.03,.89),.092,.092,12)
        mb.add_limb('cannon',7,(-.31,-.586,.89),(-.31,-.598,.89),.056,.056,12)
        for sx in [-1,1]:
            mb.add_box('cannon',3,(-.31+sx*.07,-.29,.89),(.028,.21,.055),rot_deg=(0,0,sx*7))


def _aim(bone, target):
    direction=target-bone.head
    if direction.length<.001:return
    rotation=(bone.tail-bone.head).rotation_difference(direction)
    bone.matrix=Matrix.LocRotScale(bone.head,rotation @ bone.matrix.to_quaternion(),Vector((1,1,1)))
    bpy.context.view_layer.update()


def solve_limb(bones, upper_name, lower_name, target, pole):
    upper=bones[upper_name];fore=bones[lower_name]
    shoulder=upper.head.copy()
    vec=target-shoulder;length=max(.01,min(vec.length,(upper.length+fore.length)*.98))
    direction=vec.normalized()
    along=(upper.length**2-fore.length**2+length**2)/(2*length)
    pole=(pole-direction*pole.dot(direction)).normalized()
    elbow=shoulder+direction*along+pole*math.sqrt(max(0,upper.length**2-along**2))
    _aim(upper,elbow)
    _aim(fore,shoulder+direction*length)


def _world_orientation(bone, rotation=None):
    basis=bone.bone.matrix_local.to_3x3().to_4x4()
    bone.matrix=Matrix.Translation(bone.head) @ (rotation or Matrix.Identity(4)) @ basis
    bpy.context.view_layer.update()


def finalize_pose(rig, fid, clip='idle', frame=0):
    """Bake clean end-effector targets, support hand and a planted lowest foot.

    No runtime IK dependency. Combat root X/Y is controlled exclusively by Godot.
    """
    bpy.context.view_layer.update()
    bones=rig.pose.bones
    active=clip in ['light_1','light_2','light_3','heavy','elemental','ultimate','down_punch','air_punch','sweep'] and frame in [6,10,12]
    prep=frame==4
    height=bones['hips'].head.z-bones['hips'].bone.head_local.z
    def arm(side,target):
        target=Vector(target)+Vector((0,0,height))
        solve_limb(bones,'upper_arm_'+side,'forearm_'+side,target,Vector((1 if side=='l' else -1,0,-.6)))
    if clip in ['idle','walk_forward','walk_back'] or frame in [0,24]:
        if fid=='kaze':
            arm('l',(.22,-.47,1.33));arm('r',(-.24,-.20,1.05))
        elif fid in ['ignis','tophia']:
            for side,sx in [('l',1),('r',-1)]:arm(side,(sx*.24,-.40,1.25 if fid=='ignis' else 1.24))
    if fid=='kaze' and active:
        if clip=='light_1':arm('r',(-.24,-.68,1.40))
        elif clip in ['light_2','elemental']:
            arm('r',(-.22,-.64,1.26));arm('l',(.22,-.64,1.47))
        elif clip=='ultimate':
            arm('r',(-.24,-.18,2.08));arm('l',(.24,-.18,2.08))
        if clip in ['light_3','heavy']:
            solve_limb(bones,'thigh_r','shin_r',Vector((-.16,-.81,1.05 if clip=='light_3' else 1.18)),Vector((0,-1,1)))
            _world_orientation(bones['foot_r'])
    elif fid=='ignis':
        if active and clip in ['light_1','light_2']:
            side='r' if clip=='light_1' else 'l'
            arm(side,(-.24 if side=='r' else .24,-.75,1.30))
            other='l' if side=='r' else 'r'
            arm(other,(.30 if other=='l' else -.30,-.03,1.02))
        if clip in ['heavy','light_3'] and (active or prep):
            for side,sx in [('l',1),('r',-1)]:arm(side,(sx*.065,-.54 if active else -.14,.72 if active else 2.05))
    elif fid=='tophia' and active:
        if clip=='light_1':arm('r',(-.24,-.65,1.34))
        elif clip=='light_2':arm('l',(.24,-.58,1.62))
        elif clip in ['heavy','elemental']:arm('r',(-.20,-.50,.76 if clip=='heavy' else .53))
        elif clip=='ultimate':arm('r',(-.24,-.65,1.40))
    if fid=='kaze' and clip not in ['knockdown','ko','get_up']:
        for side in ['l','r']:
            _world_orientation(bones['hand_'+side],Matrix.Rotation(math.pi,4,'Y'))
    if clip in ['victory','select'] and frame>=20:
        if fid=='tophia':
            arm('r',(-.16,-.22,1.70))
            _world_orientation(bones['hand_r'],Matrix.Rotation(math.pi,4,'Y'))
        elif fid=='kaze':
            arm('l',(.035,-.32,1.40));arm('r',(-.035,-.32,1.37))
        elif fid=='ignis':
            arm('r',(-.12,-.38,1.93))
        elif fid=='volt':
            _world_orientation(bones['cannon'],Matrix.Rotation(-math.pi/2,4,'X'))
    if fid=='tophia':
        for side in ['l','r']:
            hand=bones['hand_'+side]
            transform=(hand.matrix @ hand.bone.matrix_local.inverted()).to_3x3()
            for digit in ['index','middle','ring','pinky']:
                finger=bones['finger_'+digit+'_'+side]
                if clip in ['victory','select'] and frame>=20 and side=='r' and digit in ['index','middle']:
                    _aim(finger,finger.head+Vector((-.04 if digit=='index' else .04,-.005,.10)))
                else:
                    _aim(finger,finger.head+transform @ Vector((0,-.065,.02)))
    if fid=='volt' and clip not in ['ko','knockdown','get_up','victory','select']:
        # Lock barrel elevation while recoil travels through shoulders and hips.
        recoil = (.10 if clip in ['heavy','ultimate'] else .045) if active else 0.0
        arm('r',(-.27,-.52+recoil,1.26 if clip!='ultimate' else 1.18))
        _world_orientation(bones['cannon'])
        cannon=bones['cannon']
        solve_limb(bones,'upper_arm_l','forearm_l',cannon.head+Vector((.08,-.23,-.015)),Vector((.8,0,-1)))
    # Plant the lowest sole, calculated from the actual skinned foot vertices.
    # Jump and floor reactions deliberately retain their authored trajectories.
    if clip in ['jump_start','jump_air','jump_land','knockdown','ko','get_up','air_punch']:return
    mesh=next((o for o in rig.children if o.type=='MESH'),None)
    if not mesh:return
    foot_groups={g.index:g.name for g in mesh.vertex_groups if g.name.startswith('foot_')}
    lowest=100
    for v in mesh.data.vertices:
        for group in v.groups:
            if group.group in foot_groups:
                b=bones[foot_groups[group.group]]
                z=(b.matrix @ b.bone.matrix_local.inverted() @ v.co).z
                lowest=min(lowest,z)
    if lowest<99:
        root=bones['root']
        root.location += root.bone.matrix_local.to_3x3().inverted() @ Vector((0,0,-lowest+.012))
        bpy.context.view_layer.update()
