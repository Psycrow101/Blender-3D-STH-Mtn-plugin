import bpy
from mathutils import Matrix, Vector
from . types.bon import Bon


def invalid_active_object(self, context):
    self.layout.label(text='You need to select the armature to attach BON')


def trans_matrix(v):
    return Matrix.Translation(v)


def scale_matrix(v):
    mat = Matrix.Identity(4)
    mat[0][0], mat[1][1], mat[2][2] = v[0], v[1], v[2]
    return mat


def rotate_matrix(e):
    rot = e.to_quaternion()
    return rot.to_matrix().to_4x4()


def find_bon_nodes(root_obj):
    def append_children(p):
        node_objects.append(p)
        for ch in p.children:
            append_children(ch)

    node_objects = []
    for child in root_obj.children:
        append_children(child)

    return node_objects


def attach_bon(context, arm_obj, bon: Bon, apply_bone_names):
    collection = bpy.data.collections.new(bon.model_name + '.bon')
    context.scene.collection.children.link(collection)

    root_obj = bpy.data.objects.new('bon_root', None)
    root_obj.location = Vector((0, -bon.root_offset, 0))
    root_obj.parent = arm_obj
    collection.objects.link(root_obj)

    tags_map = {}
    for b in bon.bones:
        for bone in arm_obj.data.bones:
             if bone['bone_id'] == b.tag:
                tags_map[b.tag] = bone
                if apply_bone_names:
                    bone.name = b.name
                break

    node_objects = [bpy.data.objects.new(b.name, None) for b in bon.bones]
    nodes_map = {}
    for i, b in enumerate(bon.bones):
        nodes_map[b.tag] = node_objects[i]

    for b in bon.bones:
        node_obj = nodes_map[b.tag]
        node_obj.matrix_local = trans_matrix(b.pos) @ rotate_matrix(b.rot) @ scale_matrix(b.scale)
        if b.parent:
            node_obj.parent = nodes_map[b.parent.tag]
        else:
            node_obj.parent = root_obj

        collection.objects.link(node_obj)
        node_obj.show_in_front = True

        bone = tags_map.get(b.tag)
        if bone:
            c = arm_obj.pose.bones[bone.name].constraints.new('COPY_TRANSFORMS')
            c.target = node_obj

    return root_obj


def load(context, filepath, *, apply_bone_names):
    arm_obj = context.view_layer.objects.active
    if not arm_obj or type(arm_obj.data) != bpy.types.Armature:
        context.window_manager.popup_menu(invalid_active_object, title='Error', icon='ERROR')
        return {'CANCELLED'}

    bon = Bon.load(filepath)
    bon.find_bone_parents()

    bpy.ops.object.mode_set(mode='OBJECT')
    root_obj = attach_bon(context, arm_obj, bon, apply_bone_names)
    root_obj['bon_model_name'] = bon.model_name
    context.view_layer.objects.active = root_obj

    return {'FINISHED'}
