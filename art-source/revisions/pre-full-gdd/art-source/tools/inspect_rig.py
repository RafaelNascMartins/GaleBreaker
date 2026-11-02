import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
for fid in ['kaze','ignis','tophia','volt']:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/f'art-source/characters/{fid}/{fid}.blend'))
    rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
    for track in rig.animation_data.nla_tracks:track.mute=True
    for action_name in ['idle','light_1','heavy']:
        action=bpy.data.actions[action_name]
        rig.animation_data.action=action
        rig.animation_data.action_slot=action.slots[0]
        bpy.context.scene.frame_set(8)
        print('POSE',fid,action_name,json.dumps({n:[list(rig.pose.bones[n].head),list(rig.pose.bones[n].tail)] for n in ['head','upper_arm_r','forearm_r','hand_r','thigh_r','shin_r','foot_r','cannon']}))
