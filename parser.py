#!/usr/bin/python


from typing import ClassVar

import numpy as np

# etree is a compiled package that has no stubs shipped with it
from lxml import etree  # pyright: ignore[reportAttributeAccessIssue]

from tooling import AABB_BoundingBox, Version


class SwissBUILDINGS3d_Parser:

    version: ClassVar = {}

    def __init__(self, filepath: str) -> None:

        # parse xml database
        root = etree.parse(filepath).getroot()

        # build a namespace. Using defined typing from dataset.
        ns = root.nsmap

        # we now set our version, according to our ingested file
        version = {
            "parser" : Version(root.find('gml:name', ns).text.split(" ")[-1])
        }

        # here be version handling and indexing
        if Version("3.0") <= version["parser"]:

            metadata = {
                "coordinate_system" :   (
                                        root.find('gml:boundedBy', ns)
                                            .find('gml:Envelope', ns)
                                            .attrib['srsName']
                                        ),
                "dimensions"        :   (_dimensions := int(
                                        root.find('gml:boundedBy', ns)
                                            .find('gml:Envelope', ns)
                                            .attrib['srsDimension']
                                        )),
                "lower_corner"      :   (_lower_corner := (
                                            np.array(
                                                root.find('gml:boundedBy', ns)
                                                    .find('gml:Envelope', ns)
                                                    .find('gml:lowerCorner', ns)
                                                    .text.split(' '), dtype=np.float32
                                                )
                                        )),
                "upper_corner"      :   (_upper_corner := (
                                            np.array(
                                                root.find('gml:boundedBy', ns)
                                                    .find('gml:Envelope', ns)
                                                    .find('gml:upperCorner', ns)
                                                    .text.split(' '), dtype=np.float32
                                                )
                                        )),
                "boundingBox"       :   AABB_BoundingBox(_lower_corner, _upper_corner)
            }

            print("Working with: " + root.find('gml:name', ns).text)
            # 1. fetch metadata
            print(metadata['boundingBox'].center)

            # 2. collect layer(s), like rooftop, walls and floors

            # 3. generate an index of metadata

            # 4. create hints for object types in an array

            # 5. create arrays for the amount of objects, note down line position start and end in xml

            # 6. dispatch worker threads to parse, transform, categorize and store into a sqlite database (TODO: prepare sematic layout for objects, and their table in sqlite)

            # 7. close sqlite db


    def transfer (self) -> int:
        return 0


hinterrhein = SwissBUILDINGS3d_Parser(filepath="demo_Hinterrhein.gml")
print("finished")
