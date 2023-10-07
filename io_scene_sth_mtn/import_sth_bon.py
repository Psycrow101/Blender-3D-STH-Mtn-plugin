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


def create_edit_bone(arm, name):
    edit_node = arm.edit_bones.new(name)
    edit_node.head = (0, 0, 0)
    edit_node.tail = (0, 0, 0.05)
    return edit_node


def create_constraint(trans_type, bone, target, subtarget):
    constraint = bone.constraints.new(trans_type)
    constraint.target = target
    constraint.subtarget = subtarget
    return constraint


def create_scale_driver(trans_type, bone, target_arm, target_name, node_name, index):
    driver = bone.driver_add('scale', index).driver
    driver.expression = 'scl / div'

    variable = driver.variables.new()
    variable.name = 'scl'
    variable.type = 'TRANSFORMS'

    target = variable.targets[0]
    target.id = target_arm
    target.bone_target = target_name
    target.transform_type = trans_type
    target.transform_space = 'LOCAL_SPACE'

    variable = driver.variables.new()
    variable.name = 'div'
    variable.type = 'SINGLE_PROP'

    target = variable.targets[0]
    target.id_type = 'OBJECT'
    target.id = target_arm
    target.data_path = f'pose.bones["{node_name}"]["Bon Scale"][{index}]'

    return driver


def attach_bon(context, arm_obj, bon: Bon, apply_bone_names):
    collection = bpy.data.collections.new(bon.model_name + '.bon')
    context.scene.collection.children.link(collection)

    tags_map = {}
    for b in bon.bones:
        for bone in arm_obj.data.bones:
             if bone['bone_id'] == b.tag:
                if apply_bone_names:
                    bone.name = b.name
                tags_map[b.tag] = bone.name
                break

    root_arm = bpy.data.armatures.new('bon_root')

    root_obj = bpy.data.objects.new(collection.name, root_arm)
    root_obj.location = Vector((0, -bon.root_offset, 0))
    root_obj.parent = arm_obj
    root_obj.show_in_front = True
    collection.objects.link(root_obj)

    # Create edit bones
    context.view_layer.objects.active = root_obj
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)

    names_map = {}
    for b in bon.bones:
        edit_node = create_edit_bone(root_arm, b.name)
        node_name = edit_node.name
        socket_name = None
        if b.parent:
            socket_name = node_name + '_socket'
            create_edit_bone(root_arm, socket_name)
        names_map[b.tag] = (node_name, socket_name)

    # Set parents
    for b in bon.bones:
        if not b.parent:
            continue

        node_name, socket_name = names_map[b.tag]
        edit_node = root_arm.edit_bones[node_name]
        socket_node = root_arm.edit_bones[socket_name]

        edit_node.parent = socket_node

        parent_name = names_map[b.parent.tag][1]
        if parent_name is not None:
            socket_node.parent = root_arm.edit_bones[parent_name]

    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

    # Set rest pose and drivers
    for b in bon.bones:
        node_name, socket_name = names_map[b.tag]

        pose_node = root_obj.pose.bones[node_name]
        pose_node.rotation_mode = 'XYZ'

        matrix = trans_matrix(b.pos) @ rotate_matrix(b.rot) @ scale_matrix(b.scale)
        if pose_node.parent:
            matrix = pose_node.parent.matrix @ matrix

        pose_node.matrix = matrix
        pose_node['Bon Scale'] = Vector((1.0, 1.0, 1.0))
        pose_node['bon_rest'] = matrix.copy()

        if socket_name is not None:
            root_obj.data.bones[socket_name].hide = True

            socket_node = root_obj.pose.bones[socket_name]
            socket_node.rotation_mode = 'XYZ'

            for i in range(3):
                socket_node.lock_location[i] = True
                socket_node.lock_rotation[i] = True

            target_name = names_map[b.parent.tag][0]

            create_constraint('COPY_LOCATION', socket_node, root_obj, target_name)
            create_constraint('COPY_ROTATION', socket_node, root_obj, target_name)

            create_scale_driver('SCALE_X', socket_node, root_obj, target_name, node_name, 0)
            create_scale_driver('SCALE_Y', socket_node, root_obj, target_name, node_name, 1)
            create_scale_driver('SCALE_Z', socket_node, root_obj, target_name, node_name, 2)

        bone_name = tags_map.get(b.tag)
        if bone_name is not None:
            create_constraint('COPY_TRANSFORMS', arm_obj.pose.bones[bone_name], root_obj, node_name)

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

    return {'FINISHED'}
