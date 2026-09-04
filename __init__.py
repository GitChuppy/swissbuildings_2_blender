#!/usr/bin/env python

import os

import bmesh
import bpy
from bpy.ops import collection
import numpy as np
from bpy.props import StringProperty
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper
from numpy.typing import NDArray

try:
    from parser import SwissBUILDINGS3d_Parser
    from tooling import Building
except ImportError:
    from .parser import SwissBUILDINGS3d_Parser
    from .tooling import Building

# The building components imported as mesh objects: one mesh object per building and component.
# Note that 'lod2Solid' is deliberately not imported; extend this tuple to add more.
SURFACE_TYPES: tuple[str, ...] = ("WallSurface", "RoofSurface", "GroundSurface")


def _child_collection(parent: bpy.types.Collection, name: str) -> bpy.types.Collection:
    """
    Returns the child collection `name` of `parent`, creating and linking it if it does not exist yet.
    """
    child = next((c for c in parent.children if c.name == name), None)
    if child is None:
        child = bpy.data.collections.new(name)
        parent.children.link(child)
    return child


def _purge_collection(collection: bpy.types.Collection) -> None:
    """
    Recursively removes all objects and child collections of `collection` (and its descendants) from the blend file.
    """
    for child in list(collection.children):
        _purge_collection(child)
        collection.children.unlink(child)
        bpy.data.collections.remove(child)
    for obj in list(collection.objects):
        bpy.data.objects.remove(obj)


def _create_surface_mesh(
    parent: bpy.types.Object,
    name: str,
    surface: Building.Surface,
    internal_collection: bpy.types.Collection,
) -> None:
    """
    Creates one mesh object holding the polygons of `surface`, built around 0,0,0 with bmesh,
    then places the object at `center` inside `collection`.
    """
    bm = bmesh.new()
    try:
        for face_id, polygon in surface.face.items():
            try:
                verts = [bm.verts.new(tuple(float(c) for c in vertex.xyz)) for vertex in polygon.vertices]
                _ = bm.faces.new(verts)
            except (ValueError, RuntimeError) as error:
                raise ImportError(f"surface patch malformed '{face_id}' of '{name}': {error}")

        bmesh.ops.remove_doubles(bm, verts = bm.verts, use_connected = False, dist=0.0)
        bmesh.ops.recalc_face_normals(bm)
        mesh = bpy.data.meshes.new(name)
        bm.to_mesh(mesh)
    finally:
        bm.free()

    if not mesh.vertices:
        bpy.data.meshes.remove(mesh)
        return

    obj = bpy.data.objects.new(name, mesh)
    internal_collection.objects.link(obj)
    obj.parent = parent


def import_swissbuildings(context: bpy.types.Context, filepath: str) -> set[str]:
    """
    Imports the SWISSBuildings citygml file at `filepath` into the scene:
    one root collection (named after the file) containing one collection per building,
    each with a separate mesh object for its wall, roof and ground surfaces.
    Importing the same file again replaces the contents of the previous root collection.
    """
    data = SwissBUILDINGS3d_Parser(False, filepath)
    data.parseBuildings()

    buildings: dict[str, Building] | None = getattr(data, "building", None)
    if not buildings:
        raise ValueError(f"No buildings found in '{filepath}' (requires dataset version >= 3.0).")

    root_collection = _child_collection(
        context.scene.collection,
        os.path.splitext(os.path.basename(filepath))[0],
    )
    _purge_collection(root_collection)

    total_meshes = sum(
        1
        for building in buildings.values()
        for surface_type in SURFACE_TYPES
        if surface_type in building.component
    )

    window_manager = context.window_manager
    window_manager.progress_begin(0, total_meshes)
    try:
        meshes_created = 0
        buildings_created = 0
        for building_id, building in buildings.items():
            building_collection: bpy.types.Collection | None = None
            for surface_type in SURFACE_TYPES:
                surface = building.component.get(surface_type)
                if surface is None:
                    continue
                if building_collection is None:
                    building_collection = _child_collection(root_collection, building_id)
                    empty = bpy.data.objects.new(building_id, None)
                    building_collection.objects.link(empty)
                    buildings_created += 1
                _create_surface_mesh(
                    parent=empty,
                    name=f"{building_id}_{surface_type}",
                    surface=surface,
                    internal_collection=building_collection,
                )
                empty.location = tuple(float(c) for c in building.bounding_box.center)
                meshes_created += 1
                window_manager.progress_update(meshes_created)
    finally:
        window_manager.progress_end()

    print(f"Imported {buildings_created} buildings from {filepath}")
    return {'FINISHED'}


# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
class ImportSwissBuildings(Operator, ImportHelper):
    """Load a SWISSBuildings file."""
    bl_idname: str = "import_gml.swissbuildings"  # important since its how bpy.ops.import_gml.swissbuildings is constructed  # pyright: ignore[reportUnusedVariable]
    bl_label: str = "Import SWISSBuildings data"  # pyright: ignore[reportUnusedVariable]

    # ImportHelper mix-in class uses this.
    filename_ext: str = ".gml"  # pyright: ignore[reportUnusedVariable]

    filter_glob: object = StringProperty(
        default="*.gml",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context):
        return import_swissbuildings(context, self.filepath)


# Only needed if you want to add into a dynamic menu.
def menu_func_import(self, context):
    self.layout.operator(ImportSwissBuildings.bl_idname, text="SWISSBuildings (.gml)")


# Register and add to the "file selector" menu (required to use F3 search "Text Import Operator" for quick access).

def register():
    bpy.utils.register_class(ImportSwissBuildings)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ImportSwissBuildings)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()
    # Test call.
    #bpy.ops.import_gml.swissbuildings('INVOKE_DEFAULT')
