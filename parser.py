#!/usr/bin/python

import numpy as np

# etree is a compiled package that has no stubs shipped with it
from lxml import etree  # pyright: ignore[reportAttributeAccessIssue]

from tooling import AABB_BoundingBox, Building, Version, nsl


class SwissBUILDINGS3d_Parser:

    version: dict[str, Version]

    def __init__(self, filepath: str) -> None:

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
                "boundingBox"       :   AABB_BoundingBox(_lower_corner, _upper_corner)
            }

    def parseBuildings(self):
        """
        Loads all buildings into a datastructure.
        """
        version = self._version
        root = self._root
        ns = self._ns

        if Version("3.0") <= version["swisstopo"]:
            self.buildings: dict[str, Building] = {
                _.find(nsl('bldg:Building', ns)).attrib[nsl('gml:id', ns)] : Building(building=_, ns=ns, version=version["swisstopo"]) # pass object and namespace, generate all the surface patches data inside the class...
                for _ in root.findall(nsl('core:cityObjectMember', ns))
            }

    def transfer (self) -> int:
        return 0

if __name__ == '__main__':
    # Testset
    hinterrhein = SwissBUILDINGS3d_Parser(filepath="demo_Hinterrhein.gml")
    hinterrhein.parseBuildings()
    #print(list(list(hinterrhein.buildings.values())[_].component for _ in range(20)))
    print("finished")
