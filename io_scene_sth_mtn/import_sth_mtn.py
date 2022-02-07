import bpy
import math
from os import path
from . types.mtn import Mtn
from . import_sth_bon import find_bon_nodes

POSEDATA_PREFIX = 'pose.bones["%s"].'


def invalid_active_object(self, context):
    self.layout.label(text='You need to select the bon_root object to import animation')


def add_pose_keyframe(curves, frame, values):
    for i, c in enumerate(curves):
        c.keyframe_points.add(1)
        c.keyframe_points[-1].co = frame, values[i]
        c.keyframe_points[-1].interpolation = 'LINEAR'


def add_node_keyframe(curve, frame, val, tangent):
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


def create_baked_action(context, arm_obj):
    act = bpy.data.actions.new('baked_action')
    curves = ([], [], [])

    for bone in arm_obj.pose.bones:
        g = act.groups.new(name=bone.name)
        cl = [act.fcurves.new(data_path=(POSEDATA_PREFIX % bone.name) + 'location', index=i) for i in range(3)]
        cr = [act.fcurves.new(data_path=(POSEDATA_PREFIX % bone.name) + 'rotation_quaternion', index=i) for i in range(4)]
        cs = [act.fcurves.new(data_path=(POSEDATA_PREFIX % bone.name) + 'scale', index=i) for i in range(3)]

        for c in cl:
            c.group = g

        for c in cr:
            c.group = g

        for c in cs:
            c.group = g

        curves[0].append(cl)
        curves[1].append(cr)
        curves[2].append(cs)
        bone.rotation_mode = 'QUATERNION'

    old_frame = context.scene.frame_current
    frame_start = context.scene.frame_start
    frame_end = context.scene.frame_end

    last_trans = [[None, None, None] for b in range(len(arm_obj.pose.bones))]

    for frame in range(frame_start, frame_end + 1):
        context.scene.frame_set(frame)
        for b, bone in enumerate(arm_obj.pose.bones):
            arm_bone = arm_obj.data.bones[bone.name]
            mat, local_mat = bone.matrix, arm_bone.matrix_local
            if bone.parent:
                mat = bone.parent.matrix.inverted_safe() @ mat
                local_mat = arm_bone.parent.matrix_local.inverted_safe() @ local_mat

            trans_mat = local_mat.inverted_safe() @ mat
            trans = trans_mat.to_translation(), trans_mat.to_quaternion(), trans_mat.to_scale()

            for t in range(3):
                val = trans[t]
                if val != last_trans[b][t] or frame == frame_end:
                    add_pose_keyframe(curves[t][b], frame, val)
                    last_trans[b][t] = val

    context.scene.frame_set(old_frame)
    return act


def create_node_actions(mtn: Mtn):
    actions = {}
    for m in mtn.bone_motions:
        act = bpy.data.actions.new('action')
        curves = [act.fcurves.new(data_path='scale', index=i) for i in range(3)]
        curves += [act.fcurves.new(data_path='location', index=i) for i in range(3)]
        curves += [act.fcurves.new(data_path='rotation_euler', index=i) for i in range(3)]
        curves += [act.fcurves.new(data_path='scale_w', index=i) for i in range(3)]

        for kf in m.keyframes:
            add_node_keyframe(curves[kf.key_type], kf.time, kf.val2, kf.val1)

        actions[m.bone_id] = act

    return actions


def load(context, filepath, *, bake_action):
    root_obj = context.view_layer.objects.active
    if not root_obj or root_obj.get('bon_model_name') is None:
        context.window_manager.popup_menu(invalid_active_object, title='Error', icon='ERROR')
        return {'CANCELLED'}

    filename = path.basename(filepath)
    mtn = Mtn.load(filepath)
    node_objects = find_bon_nodes(root_obj)
    node_actions = create_node_actions(mtn)
    context.scene.frame_start = 0
    context.scene.frame_end = mtn.duration

    for bone_id, act in node_actions.items():
        act.name = '%s_NODE_%d' % (filename, bone_id)
        node_objects[bone_id].animation_data_create().action = act

    if bake_action:
        arm_obj = root_obj.parent
        act = create_baked_action(context, arm_obj)
        act.name = filename
        arm_obj.animation_data_create().action = act


    return {'FINISHED'}
