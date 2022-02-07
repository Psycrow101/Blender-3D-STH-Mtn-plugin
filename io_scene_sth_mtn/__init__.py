import bpy
from bpy.props import (
        StringProperty,
        BoolProperty,
        )
from bpy_extras.io_utils import (
        ImportHelper,
        ExportHelper,
        )

bl_info = {
    "name": "Shadow the Hedgehog Animation",
    "author": "Psycrow",
    "version": (0, 0, 3),
    "blender": (2, 81, 0),
    "location": "File > Import-Export",
    "description": "Import / Export Shadow the Hedgehog Animation (.bon, .mtn, .STHanim)",
    "warning": "",
    "wiki_url": "",
    "support": 'COMMUNITY',
    "category": "Import-Export"
}

if "bpy" in locals():
    import importlib
    if "import_sth_mtn" in locals():
        importlib.reload(import_sth_mtn)
    if "import_sth_bon" in locals():
        importlib.reload(import_sth_bon)
    if "export_sth_mtn" in locals():
        importlib.reload(export_sth_mtn)


class ImportSTHBon(bpy.types.Operator, ImportHelper):
    bl_idname = "import_scene.sth_bon"
    bl_label = "Import Shadow the Hedgehog Bones"
    bl_options = {'PRESET', 'UNDO'}

    filter_glob: StringProperty(default="*.bon", options={'HIDDEN'})
    filename_ext = ".bon"

    def execute(self, context):
        from . import import_sth_bon

        keywords = self.as_keywords(ignore=("filter_glob",
                                            ))

        return import_sth_bon.load(context, **keywords)


class ImportSTHMtn(bpy.types.Operator, ImportHelper):
    bl_idname = "import_scene.sth_mtn"
    bl_label = "Import Shadow the Hedgehog Animation"
    bl_options = {'PRESET', 'UNDO'}

    filter_glob: StringProperty(default="*.mtn;*.STHanim", options={'HIDDEN'})
    filename_ext = ".mtn"

    bake_action: BoolProperty(
        name="Bake action",
        description="Bake animation to an armature",
        default=True,
    )

    def execute(self, context):
        from . import import_sth_mtn

        keywords = self.as_keywords(ignore=("filter_glob",
                                            ))

        return import_sth_mtn.load(context, **keywords)


class ExportSTHMtn(bpy.types.Operator, ExportHelper):
    bl_idname = "export_scene.sth_mtn"
    bl_label = "Export Shadow the Hedgehog Animation"
    bl_options = {'PRESET'}

    filter_glob: StringProperty(default="*.mtn;*.STHanim", options={'HIDDEN'})
    filename_ext = ".mtn"

    use_big_endian: BoolProperty(
        name="Big Endian",
        description="Big Endian",
        default=False,
    )

    def execute(self, context):
        from . import export_sth_mtn

        keywords = self.as_keywords(ignore=("filter_glob",
                                            ))

        return export_sth_mtn.save(context, keywords['filepath'], keywords['use_big_endian'])


def menu_func_import_bon(self, context):
    self.layout.operator(ImportSTHBon.bl_idname,
                         text="Shadow the Hedgehog Bones (.bon)")


def menu_func_import_mtn(self, context):
    self.layout.operator(ImportSTHMtn.bl_idname,
                         text="Shadow the Hedgehog Animation (.mtn, .STHanim)")


def menu_func_export_mtn(self, context):
    self.layout.operator(ExportSTHMtn.bl_idname,
                         text="Shadow the Hedgehog Animation (.mtn, .STHanim)")


classes = (
    ImportSTHBon,
    ImportSTHMtn,
    ExportSTHMtn,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import_bon)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import_mtn)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export_mtn)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import_bon)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import_mtn)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export_mtn)

    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
