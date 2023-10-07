import bpy
import math
from . types.mtn import Mtn, BoneMotion, Keyframe

POSEDATA_PREFIX = 'pose.bones["%s"].'


def invalid_active_object(self, context):
    self.layout.label(text='You need to select the bon_root object to export animation')


def missing_action(self, context):
    self.layout.label(text='No action for active armature. Nothing to export')


def create_mtn(arm_obj, act, model_name):
    pose_bones = [bone for bone in arm_obj.pose.bones if 'bon_rest' in bone]
    curves_map = {bone.name: [] for bone in pose_bones}

    for curve in act.fcurves:
        if 'pose.bones' not in curve.data_path:
            continue

        bone_name = curve.data_path.split('"')[1]
        if bone_name in curves_map:
            curves_map[bone_name].append(curve)

    bone_motions = []

    for b, bone in enumerate(pose_bones):
        keyframes = []

        path_prefix = POSEDATA_PREFIX % bone.name
        key_types_map = {
            path_prefix + '["Bon Scale"]': 0,
            path_prefix + 'location': 3,
            path_prefix + 'rotation_euler': 6,
            path_prefix + 'scale': 9
        }

        for curve in curves_map[bone.name]:
            key_type = key_types_map.get(curve.data_path)
            if key_type is None:
                continue

            for kp in curve.keyframe_points:
                time, val2 = kp.co
                if kp.interpolation != 'BEZIER':
                    val1 = 0.0
                else:
                    angle = math.asin(kp.handle_right[1] - val2)
                    val1 = math.tan(angle)

                keyframes.append(Keyframe(int(time), key_type + curve.array_index, val1, val2))

        keyframes.sort(key=lambda kf: (kf.key_type, kf.time))
        bone_motions.append(BoneMotion(b, keyframes))

    return Mtn(model_name, 0, bone_motions)


def save(context, filepath, use_big_endian):
    arm_obj = context.view_layer.objects.active
    if not arm_obj or type(arm_obj.data) != bpy.types.Armature or 'bon_model_name' not in arm_obj:
        context.window_manager.popup_menu(invalid_active_object, title='Error', icon='ERROR')
        return {'CANCELLED'}

    act = None
    animation_data = arm_obj.animation_data
    if animation_data:
        act = animation_data.action

    if not act:
        context.window_manager.popup_menu(missing_action, title='Error', icon='ERROR')
        return {'CANCELLED'}

    endian = '>' if use_big_endian else '<'
    mtn = create_mtn(arm_obj, act, arm_obj.get('bon_model_name'))
    mtn.duration = int(context.scene.frame_end)
    mtn.save(filepath, endian)

    return {'FINISHED'}
