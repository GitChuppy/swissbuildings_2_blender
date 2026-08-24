#!/usr/bin/env python

from time import perf_counter as pfc

import numpy as np

# etree is a compiled package that has no stubs shipped with it
from lxml import etree

from tooling import AABB_BoundingBox, Building, Version, nsl
from implicit_mapping import Implicit_Mapping


class SwissBUILDINGS3d_Parser:
    """
    Parser Implementation for the SWISSBuildings3D dataset of swisstopo as an intermediate to blender
    """
    version: dict[str, Version]

    def __init__(self, filepath: str) -> None:
        """
        Parses metadata and as a next step all the further data
        `Args`:
            - filepath:
                A path to a citygml `.gml` file.
                May be absolute OR relative.
                Python filepath restrictions persist, spaces in paths may cause an error.
        """

        # parse xml database
        self._root = (root := etree.parse(filepath).getroot())

        # build a namespace. Using defined typing from dataset.
        self._ns: dict[str | None, str] = (ns := root.nsmap)

        # we now set our version, according to our ingested file
        self._version: dict = (version := {
            "swisstopo" : Version(root.find(nsl('gml:name', ns)).text.split(" ")[-1])
            # if needed, add more versions for tweaks performed by datasets and parse for them accordingly
        })

        if Version("3.0") <= version["swisstopo"]:
            self.tiledata: dict = {
                "set_info"          :   (_set_info := (
                                            root.find(nsl('gml:boundedBy', ns))
                                            .find(nsl('gml:Envelope', ns))
                                        )),
                "coordinate_system" :   _set_info.attrib[nsl('srsName')],                "dimensions"        :   (_dimensions := int(_set_info.attrib[nsl('srsDimension')])),
                "lower_corner"      :   (_lower_corner := (
                                            np.array(
                                                _set_info.find(nsl('gml:lowerCorner', ns))
                                                        .text.split(' '), dtype=np.float32
                                                )
                                        )),
                "upper_corner"      :   (_upper_corner := (
                                            np.array(
                                                _set_info.find(nsl('gml:upperCorner', ns))
                                                        .text.split(' '), dtype=np.float32
                                                )
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

            self.building: dict[str, Building]

            if has_progress:
                self.building = {
                    _.find(nsl('bldg:Building', ns)).attrib[nsl('gml:id', ns)] : Building(building=_, ns=ns, version=version["swisstopo"]) # pass object and namespace, generate all the surface patches data inside the class...
                    for _ in tqdm.tqdm(buildings, total=len(buildings), desc='Mapping buildings')
                }
            else:
                start = pfc()
                self.building = {
                    _.find(nsl('bldg:Building', ns)).attrib[nsl('gml:id', ns)] : Building(building=_, ns=ns, version=version["swisstopo"]) # pass object and namespace, generate all the surface patches data inside the class...
                    for _ in buildings
                }
                print(f"Mapping done in {pfc()-start}s")
            self.buildings = Implicit_Mapping(self.building)



if __name__ == '__main__':

    import argparse
    try:
        import tqdm

        has_progress = True
    except ImportError:
        print(f"{ImportError}: progressing without.")

    parser = argparse.ArgumentParser(
                        prog='Swisstopo SWISSBuildings GML parser',
                        description='DISCLAIMER: This importer is not associated with Swisstopo in any way, shape or form.')

    parser.add_argument('-f', '--filename', required=True, help='requires a Swisstopo SWISSBuildings (or compatible) GML file.')

    args = parser.parse_args()

    # Testset
    hinterrhein = SwissBUILDINGS3d_Parser(filepath=args.filename)
    hinterrhein.parseBuildings()
