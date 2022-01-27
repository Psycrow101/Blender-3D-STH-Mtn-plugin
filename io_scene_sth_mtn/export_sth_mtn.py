import bpy
import math
from . types.mtn import Mtn, BoneMotion, Keyframe
from . import_sth_bon import find_bon_nodes


def invalid_active_object(self, context):
    self.layout.label(text='You need to select the bon_root object to export animation')


def create_mtn(root_obj, model_name):
    key_types_map = {'scale': 0, 'location': 3, 'rotation_euler': 6, 'scale_w': 9}
    bone_motions = []

    node_objects = find_bon_nodes(root_obj)
    for bone_id, node_obj in enumerate(node_objects):
        keyframes = []
        act = node_obj.animation_data.action
        for curve in act.fcurves:
            key_type = key_types_map.get(curve.data_path)
            if key_type is None or (bone_id == 0 and key_type == 0):
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
        bone_motions.append(BoneMotion(bone_id, keyframes))

    return Mtn(model_name, 0, bone_motions)


def save(context, filepath, use_big_endian):
    root_obj = context.view_layer.objects.active
    if not root_obj or root_obj.get('bon_model_name') is None:
        context.window_manager.popup_menu(invalid_active_object, title='Error', icon='ERROR')
        return {'CANCELLED'}

    endian = '>' if use_big_endian else '<'
    mtn = create_mtn(root_obj, root_obj.get('bon_model_name'))
    mtn.duration = int(context.scene.frame_end)
    mtn.save(filepath, endian)

    return {'FINISHED'}
