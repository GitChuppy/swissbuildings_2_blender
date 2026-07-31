#!/usr/bin/python


from typing import ClassVar

import numpy as np

# etree is a compiled package that has no stubs shipped with it
from lxml import etree  # pyright: ignore[reportAttributeAccessIssue]

from tooling import AABB_BoundingBox, Version
from tooling import ns_lookup as nsl


class SwissBUILDINGS3d_Parser:

    version: ClassVar = {}

    def __init__(self, filepath: str) -> None:

        # parse xml database
        root = etree.parse(filepath).getroot()

        # build a namespace. Using defined typing from dataset.
        ns: dict = root.nsmap

        # we now set our version, according to our ingested file
        version: dict = {
            "parser" : Version(root.find(nsl('gml:name', ns)).text.split(" ")[-1])
        }

        if Version("3.0") <= version["parser"]:

            metadata: dict = {
                "set_info"          :   (_set_info := (
                                            root.find(nsl('gml:boundedBy', ns))
                                            .find(nsl('gml:Envelope', ns))
                                        )),
                "coordinate_system" :   _set_info.attrib[nsl('srsName')],
                # currently not used but still collected
                "dimensions"        :   (_dimensions := int(_set_info.attrib[nsl('srsDimension')])),
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

            print("Working with: " + root.find(nsl('gml:name', ns)).text)
            set_data = root.findall(nsl('core:cityObjectMember', ns))
            # 1. collect layer(s), like rooftop, walls and floors
            # (in this version, roof surfaces can be stand-alone)
            print([_.find(nsl('bldg:Building', ns)).attrib[nsl('gml:id', ns)] for _ in set_data])

            # 2. generate an index of metadata

            # 3. create hints for object types in an array

            # 4. create arrays for the amount of objects, note down line position start and end in xml

            # 5. dispatch worker threads to parse, transform, categorize and store into a sqlite database (TODO: prepare sematic layout for objects, and their table in sqlite)

            # 6. close sqlite db


    def transfer (self) -> int:
        return 0


hinterrhein = SwissBUILDINGS3d_Parser(filepath="demo_Hinterrhein.gml")
print("finished")
