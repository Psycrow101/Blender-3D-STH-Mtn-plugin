import bpy
import math
from os import path
from . types.mtn import Mtn
from . import_sth_bon import find_bon_nodes


def invalid_active_object(self, context):
    self.layout.label(text='You need to select the bon_root object to import animation')


def create_keyframe(curve, frame, val, tangent):
    curve.keyframe_points.add(1)
    kf = curve.keyframe_points[-1]

    angle = math.atan(tangent)
    handle_x, handle_y = math.cos(angle), math.sin(angle)

    kf.co = frame, val
    kf.interpolation = 'BEZIER'
    kf.handle_left_type = 'ALIGNED'
    kf.handle_right_type = 'ALIGNED'
    kf.handle_left = frame - handle_x, val - handle_y
    kf.handle_right = frame + handle_x, val + handle_y


# TODO: one action
def create_animation(node_objects, mtn: Mtn):
    for m in mtn.bone_motions:
        node_obj = node_objects[m.bone_id]
        act = bpy.data.actions.new('action') # TODO: rename
        curves = [act.fcurves.new(data_path='scale', index=i) for i in range(3)]
        curves += [act.fcurves.new(data_path='location', index=i) for i in range(3)]
        curves += [act.fcurves.new(data_path='rotation_euler', index=i) for i in range(3)]
        curves += [act.fcurves.new(data_path='scale_w', index=i) for i in range(3)]

        for kf in m.keyframes:
            create_keyframe(curves[kf.key_type], kf.time, kf.val2, kf.val1)

        node_obj.animation_data_create().action = act


def load(context, filepath):
    root_obj = context.view_layer.objects.active
    if not root_obj or root_obj.get('bon_model_name') is None:
        context.window_manager.popup_menu(invalid_active_object, title='Error', icon='ERROR')
        return {'CANCELLED'}

    node_objects = find_bon_nodes(root_obj)

    mtn = Mtn.load(filepath)
    create_animation(node_objects, mtn)
    context.scene.frame_start = 0
    context.scene.frame_end = mtn.duration

    return {'FINISHED'}
