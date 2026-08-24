#!/usr/bin/env python

import bpy

from parser import SwissBUILDINGS3d_Parser

context: bpy.context

def read_some_data(context, filepath: str, use_some_setting: str):
    print("running read_some_data...")

    data = SwissBUILDINGS3d_Parser(filepath)

    # Would normally load the data here.
    print(data)

    return {'FINISHED'}


# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy.props import BoolProperty, EnumProperty, StringProperty
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper


class ImportSomeData(Operator, ImportHelper):
    """Load a SWISSBuildings file."""
    bl_idname: str = "import_gml.swissbuildings"  # important since its how bpy.ops.import_test.some_data is constructed  # pyright: ignore[reportUnusedVariable]
    bl_label: str = "Import SWISSBuildings data"  # pyright: ignore[reportUnusedVariable]

    # ImportHelper mix-in class uses this.
    filename_ext: str = ".gml"  # pyright: ignore[reportUnusedVariable]

    filter_glob: object = StringProperty (
        default="*.gml",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    use_setting: object = BoolProperty (
        name="Example Boolean",
        description="Example Tooltip",
        default=True,
    )

    type: object = EnumProperty (
        name="Example Enum",
        description="Choose between two items",
        items=(
            ('OPT_A', "First Option", "Description one"),
            ('OPT_B', "Second Option", "Description two"),
        ),
        default='OPT_A',
    )

    def execute(self, context):
        return read_some_data(context, self.filepath, self.use_setting)


# Only needed if you want to add into a dynamic menu.
def menu_func_import(self, context):
    self.layout.operator(ImportSomeData.bl_idname, text="SWISSBuildings (.gml)")


# Register and add to the "file selector" menu (required to use F3 search "Text Import Operator" for quick access).

def register():
    bpy.utils.register_class(ImportSomeData)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ImportSomeData)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()
    # Test call.
    #bpy.ops.import_test.some_data('INVOKE_DEFAULT')
