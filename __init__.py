#!/usr/bin/env python

import math
import os
import zipfile
from contextlib import contextmanager
from typing import Any

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
    angle: float = 30.0,
) -> None:
    """
    Creates one mesh object holding the polygons of `surface`, built around 0,0,0 with bmesh,
    then places the object at `center` inside `collection`.
    All faces are smooth-shaded; edges whose angle between the adjacent faces is less than
    `angle` degrees are marked sharp instead of separating the faces.
    """
    bm = bmesh.new()
    try:
        for face_id, polygon in surface.face.items():
            try:
                verts = [bm.verts.new(tuple(float(c) for c in vertex.xyz)) for vertex in polygon.vertices]
                _ = bm.faces.new(verts)
            except (ValueError, RuntimeError) as error:
                raise ImportError(f"surface patch malformed '{face_id}' of '{name}': {error}")

        bmesh.ops.remove_doubles(bm, verts = bm.verts, use_connected=False, dist=0.0)
        bmesh.ops.recalc_face_normals(bm)
        # Smooth-shade all faces (bmesh-level, avoids bpy.ops context overhead and undo dirtying).
        for face in bm.faces:
            face.smooth = True
        # Mark edges with an angle below `angle` degrees as sharp edges; the faces stay connected.
        limit = math.radians(angle)
        for edge in bm.edges:
            if len(edge.link_faces) == 2:
                if edge.calc_face_angle() >= limit:
                    edge.smooth = False
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


@contextmanager
def _gml_source(filepath: str):
    """
    Opens the GML content behind `filepath`, fully in memory: plain files pass through
    as a path, zip archives are read from their single .gml member (decompressed in
    RAM, nothing is written to disk).
    TODO(perf): eventually stream the parsed coordinates straight into GPU buffers
    (VRAM), skipping the CPU-resident float64 tree and the bmesh round-trip.
    """
    if not zipfile.is_zipfile(filepath):
        yield filepath
        return
    with zipfile.ZipFile(filepath) as archive:
        members = [name for name in archive.namelist() if name.lower().endswith(".gml")]
        if len(members) != 1:
            raise ValueError(f"Expected exactly one .gml file in zip '{filepath}', found {len(members)}.")
        yield archive.open(members[0])


def import_swissbuildings(context: bpy.types.Context, filepath: str) -> set[str]:
    """
    Imports the SWISSBuildings citygml file at `filepath` into the scene:
    one root collection (named after the file) containing one collection per building,
    each with a separate mesh object for its wall, roof and ground surfaces.
    Importing the same file again replaces the contents of the previous root collection.
    `filepath` may be a plain .gml file or a .zip archive containing a single .gml
    file; the archive is decompressed in RAM, nothing is written to disk.

    Geometry is placed relative to the tile's bounding-box center instead of raw LV95
    coordinates: Blender stores meshes and object transforms in float32, which at LV95
    magnitudes (~2.7e6 m) only resolves ~10-25cm steps. Relative to the tile center the
    same values keep sub-millimeter precision.
    Only x/y are shifted this way; z keeps its absolute LV95 height so all imported
    tiles share the same height datum.
    """
    with _gml_source(filepath) as source:
        data = SwissBUILDINGS3d_Parser(False, source)
        data.parseBuildings()

    buildings: dict[str, Building] | None = getattr(data, "building", None)
    if not buildings:
        raise ValueError(f"No buildings found in '{filepath}' (requires dataset version >= 3.0).")

    tiledata: dict[str, Any] | None = getattr(data, "tiledata", None)  # pyright: ignore[reportExplicitAny]
    if tiledata is None:
        raise ValueError(f"No tile bounding box found in '{filepath}' (requires dataset version >= 3.0).")
    tile_center = np.asarray(tiledata["bounding_Box"].center, dtype=np.float64)

    # Only the horizontal (x/y) position is corrected for the tile offset; height is kept
    # absolute: the envelope's z range is just this tile's min/max height, not a datum, so
    # subtracting it would sink the tile to an arbitrary height. Keeping z absolute means
    # every tile shares the LV95 height system (m above HÖH).
    tile_origin = np.asarray([tile_center[0], tile_center[1], 0.0], dtype=np.float64)

    # The first tile imported into this scene defines the world origin: the ground point
    # below its bounding-box center maps to (0, 0, 0). Later tiles are offset by the same
    # anchor (each from its own bounding box), so multiple tiles land in their correct
    # relative position.
    # To re-anchor the scene on a different tile, delete context.scene["swissbuildings_world_origin"]
    # and import that tile.
    world_origin: NDArray[np.float64] = context.scene.get("swissbuildings_world_origin")
    if world_origin is None:
        world_origin = tile_origin
        context.scene["swissbuildings_world_origin"] = list(world_origin)
    else:
        world_origin = np.asarray(world_origin, dtype=np.float64)

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
                # Absolute LV95 building center, shifted in x/y so the tile center sits at the
                # world origin; z keeps the absolute height.
                empty.location = tuple(float(c) for c in (building.bounding_box.center - world_origin))
                empty.show_in_front = True
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
        default="*.gml;*.zip",
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
