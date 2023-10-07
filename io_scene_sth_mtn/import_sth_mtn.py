import bpy
import math
from mathutils import Vector
from os import path
from . types.mtn import Mtn

POSEDATA_PREFIX = 'pose.bones["%s"].'


def invalid_active_object(self, context):
    self.layout.label(text='You need to select the bon_root object to import animation')


def add_pose_keyframe(curves, frame, values):
    for i, c in enumerate(curves):
        c.keyframe_points.add(1)
        c.keyframe_points[-1].co = frame, values[i]
        c.keyframe_points[-1].interpolation = 'LINEAR'


def add_mtn_keyframe(curve, frame, val, tangent):
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


# TODO: socket scale
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


def create_mtn_action(root_obj, mtn: Mtn):
    act = bpy.data.actions.new('action')

    pose_bones = [bone for bone in root_obj.pose.bones if 'bon_rest' in bone]

    for b, bone in enumerate(pose_bones):
        bone.rotation_mode = 'XYZ'
        bone['Bon Scale'] = Vector((1.0, 1.0, 1.0))
        bone.matrix = bone['bon_rest'].copy()

        curves = [act.fcurves.new(data_path=(POSEDATA_PREFIX % bone.name) + '["Bon Scale"]', index=i) for i in range(3)]
        curves += [act.fcurves.new(data_path=(POSEDATA_PREFIX % bone.name) + 'location', index=i) for i in range(3)]
        curves += [act.fcurves.new(data_path=(POSEDATA_PREFIX % bone.name) + 'rotation_euler', index=i) for i in range(3)]
        curves += [act.fcurves.new(data_path=(POSEDATA_PREFIX % bone.name) + 'scale', index=i) for i in range(3)]

        group = act.groups.new(name=bone.name)
        for c in curves:
            c.group = group

        for kf in mtn.bone_motions[b].keyframes:
            add_mtn_keyframe(curves[kf.key_type], kf.time, kf.val2, kf.val1)

    return act


def load(context, filepath, *, bake_action):
    root_obj = context.view_layer.objects.active
    if not root_obj or type(root_obj.data) != bpy.types.Armature or 'bon_model_name' not in root_obj:
        context.window_manager.popup_menu(invalid_active_object, title='Error', icon='ERROR')
        return {'CANCELLED'}

    animation_data = root_obj.animation_data
    if not animation_data:
        animation_data = root_obj.animation_data_create()

    filename = path.basename(filepath)
    mtn = Mtn.load(filepath)
    act = create_mtn_action(root_obj, mtn)
    act.name = filename
    animation_data.action = act

    context.scene.frame_start = 0
    context.scene.frame_end = mtn.duration

    if bake_action:
        arm_obj = root_obj.parent
        act = create_baked_action(context, arm_obj)
        act.name = filename
        arm_obj.animation_data_create().action = act


    return {'FINISHED'}
