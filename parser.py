#!/usr/bin/env python

from time import perf_counter as pfc
from typing import IO, Any, cast

import numpy as np

# etree is a compiled package that has no stubs shipped with it
from lxml import etree

try:
    from implicit_mapping import Implicit_Mapping
    from tooling import AABB_BoundingBox, Building, Version, nsl
except ImportError:
    from .implicit_mapping import Implicit_Mapping
    from .tooling import AABB_BoundingBox, Building, Version, nsl

class SwissBUILDINGS3d_Parser:
    """
    Parser Implementation for the SWISSBuildings3D dataset of swisstopo as an intermediate to blender
    """

    def __init__(self, _has_progress: bool, filepath: str | IO[bytes]) -> None:
        """
        Parses metadata and as a next step all the further data
        `Args`:
            - _has_progress:
                internal argument whether the system has tqdm available or not
            - filepath:
                A path to a citygml `.gml` file (may be absolute OR relative),
                or an open binary file-like object with the same content (e.g. a
                member of a zip archive), which is read fully during this call.
                Python filepath restrictions persist, spaces in paths may cause an error.
        """
        version: dict[str, Version]

        self._has_progress: bool = _has_progress

        self._root : etree.ElementBase

        # parse xml database
        self._root = (root := cast(etree.ElementBase, etree.parse(filepath).getroot()))

        # build a namespace. Using defined typing from dataset.
        self._ns: dict[str | None, str] | None = (ns := root.nsmap)

        # we now set our version, according to our ingested file
        self._version: dict[str, Version] = (version := {
            "swisstopo" : Version(root.findtext(nsl('gml:name', ns), default='').split(' ')[-1])
            # if needed, add more versions for tweaks performed by datasets and parse for them accordingly
        })


        self.building: dict[str, Building]
        self.buildings: Implicit_Mapping[Building]

        if Version("3.0") <= version["swisstopo"]:
            self.tiledata: dict[str, Any] = {  # pyright: ignore[reportExplicitAny]
                "set_info"          :   (_set_info := (
                                            root.find('.//' + nsl('gml:Envelope', ns))
                                        )),
                "coordinate_system" :   _set_info.attrib[nsl('srsName')] if _set_info is not None else '',
                "dimensions"        :   (_dimensions :=
                                            int(
                                                _set_info.attrib[nsl('srsDimension')]
                                            )
                                        if _set_info is not None else ''
                                        ),
                # float64: the envelope corners are LV95 magnitudes (~2.7e6 m), where a
                # float32 only resolves ~25cm steps. The tile center derived from them
                # becomes the world origin, so it must keep full precision.
                "lower_corner"      :   (_lower_corner := (
                                            np.asarray(
                                                _set_info.findtext(nsl('gml:lowerCorner', ns), default='')
                                                    .split(' '), dtype=np.float64
                                                ) if _set_info is not None else None
                                        )),
                "upper_corner"      :   (_upper_corner := (
                                            np.asarray(
                                                _set_info.findtext(nsl('gml:upperCorner', ns), default='')
                                                    .split(' '), dtype=np.float64
                                                ) if _set_info is not None else None
                                        )),
                "bounding_Box"      :   AABB_BoundingBox(_lower_corner, _upper_corner)
            }

    def parseBuildings(self):
        """
        Loads all buildings into a datastructure.
        """

        version = self._version
        root = self._root
        ns = self._ns

        if Version("3.0") <= version["swisstopo"]:

            buildings = root.findall(nsl('core:cityObjectMember', ns))

            source, start = (
                tqdm.tqdm(buildings, total=len(buildings), desc='Mapping buildings'), None
            ) if self._has_progress else (
                buildings, pfc()
            )

            self.building = {
                cast(str, _.find(nsl('bldg:Building', ns)).attrib[nsl('gml:id', ns)]) :  # pyright: ignore[reportOptionalMemberAccess]
                    Building(building=cast(etree.ElementBase, _), ns=ns, version=version["swisstopo"]) # pass object and namespace, generate all the surface patches data inside the class...
                for _ in source
            }

            print(f"Mapping done in {pfc()-start}s") if start else None
            self.buildings = Implicit_Mapping(self.building)


if __name__ == '__main__':

    import argparse
    try:
        import tqdm

        _has_progress = True
    except ImportError:
        _has_progress = False
        print(f"{ImportError}: tqdm not found, proceeding with just ordinary timing.")

    parser = argparse.ArgumentParser(
                        prog='Swisstopo SWISSBuildings GML parser',
                        description='DISCLAIMER: This importer is not associated with Swisstopo in any way, shape or form.')

    _ = parser.add_argument('-f', '--filename', required=True, help='requires a Swisstopo SWISSBuildings (or compatible) GML file.')

    args = parser.parse_args()

    # Testset
    hinterrhein = SwissBUILDINGS3d_Parser(_has_progress=_has_progress, filepath=cast(str,args.filename))
    hinterrhein.parseBuildings()
