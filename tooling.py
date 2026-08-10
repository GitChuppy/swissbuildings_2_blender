#!/usr/bin/python


import numpy as np
from lxml import etree  # pyright: ignore[reportAttributeAccessIssue]


# classes
class Version:
    def __init__(self, str_version: str) -> None:
        try:
            arr_version = [int(_) for _ in str_version.split('.')]
        except ValueError:
            raise ValueError("version string cannot be empty")

        self.major  = arr_version[0]
        self.minor  = arr_version[1] if len(arr_version) > 1 else 0
        self.hotfix = arr_version[2] if len(arr_version) > 2 else 0
        self._raw   = f"{self.major}.{self.minor}.{self.hotfix}"

    def __lt__(self, other) -> bool:
        return (
            self.major,
            self.minor,
            self.hotfix
        ) < (
            other.major,
            other.minor,
            other.hotfix
        )
    def __gt__(self, other) -> bool:
        return (
            self.major,
            self.minor,
            self.hotfix
        ) > (
            other.major,
            other.minor,
            other.hotfix
        )
    def __le__(self, other) -> bool:
        return not(self.__gt__(other))
    def __ge__(self, other) -> bool:
        return not(self.__lt__(other))
    def __eq__(self, other) -> bool:
        return  (
            self.major,
            self.minor,
            self.hotfix
        ) == (
            other.major,
            other.minor,
            other.hotfix
        )
    def __ne__(self, other) -> bool:
        return not(self.__eq__(other))

# testing framework
#case_alpha = Version("1.2.3")
#case_beta  = Version("3.4")
#case_gamma = Version("")

#print(case_alpha == Version("1.2.3"))
#print(Version("1") == Version("1.0.0"))
#print(Version("2") < Version("0.9.9"))

class AABB_BoundingBox:

    def __init__(self, corner1, corner2) -> None:
        self._corner1 = corner1
        self._corner2 = corner2
        self.update()

    def update(self) -> None:
        self.center = (self.corner1+self.corner2)*0.5

    # getter and setters to make sure updating the AABB updates associated data
    @property
    def corner1(self):
        return self._corner1

    @corner1.setter
    def corner1(self, value):
        self.corner1 = value
        self.update()

    @property
    def corner2(self):
        return self._corner2

    @corner2.setter
    def corner2(self, value):
        self.corner2 = value
        self.update()

class Building:

    class Surface:

        class Polygon:

            class Vertex:

                def __init__(self, version: Version, vertices: list[float]) -> None:

                    if Version("3.0") <= version:
                        # Ensure we have exactly 3 coordinates, padding with 0.0 if necessary
                        self._coords: list[float] = (vertices + [0.0, 0.0, 0.0])[:3]

                        # --- Individual Coordinates ---
                        @property
                        def x(self) -> float:
                            return self._coords[0]

                        @x.setter
                        def x(self, value: float) -> None:
                            self._coords[0] = value

                        @property
                        def y(self) -> float:
                            return self._coords[1]

                        @y.setter
                        def y(self, value: float) -> None:
                            self._coords[1] = value

                        @property
                        def z(self) -> float:
                            return self._coords[2]

                        @z.setter
                        def z(self, value: float) -> None:
                            self._coords[2] = value

                        # --- Composed Coordinates (Bidirectional) ---
                        @property
                        def xy(self) -> tuple[float, float]:
                            return (self._coords[0], self._coords[1])

                        @xy.setter
                        def xy(self, value: tuple[float, float]) -> None:
                            self._coords[0], self._coords[1] = value

                        @property
                        def yz(self) -> tuple[float, float]:
                            return (self._coords[1], self._coords[2])

                        @yz.setter
                        def yz(self, value: tuple[float, float]) -> None:
                            self._coords[1], self._coords[2] = value

                        @property
                        def xz(self) -> tuple[float, float]:
                            return (self._coords[0], self._coords[2])

                        @xz.setter
                        def xz(self, value: tuple[float, float]) -> None:
                            self._coords[0], self._coords[2] = value

                        @property
                        def xyz(self) -> tuple[float, float, float]:
                            return tuple(self._coords)

                        @xyz.setter
                        def xyz(self, value: tuple[float, float, float]) -> None:
                            self._coords[:] = value # Update list in place

                        # --- Optional: Expose the raw list if needed ---
                        @property
                        def coords(self) -> list[float]:
                            return self._coords

            # end Vertex
            vertex: list[Vertex]

            def __init__(self, polygon: etree._Element, ns: dict[str | None, str], version: Version, dimension: int = 3) -> None:

                _arr_vertex_ring: np.ndarray = np.array(polygon.split(), dtype=np.float32)

                # TODO: Add line position of XML document to error messages
                len_arr_vertex_ring = len(_arr_vertex_ring)
                if len_arr_vertex_ring % dimension != 0:
                    raise IndexError("Amount of vertecies is mangled: Make sure every vertex contains a x, y AND z component.")
                elif len_arr_vertex_ring < dimension*3:
                    raise IndexError("Polygon need atleast 3 vertices")
                elif _arr_vertex_ring[:dimension].all() != _arr_vertex_ring[-dimension:].all():
                    raise ValueError("The last vertex needs to be coinciding with the first vertex")
                else:
                    _arr_vertex_ring = _arr_vertex_ring.reshape((-1, dimension))

                    self.vertex = [
                        self.Vertex(version=version, vertices=vertices)
                        for vertices in _arr_vertex_ring[:-1]
                    ]

        # end Polygon

        face: dict[str, Polygon]

        def __init__(self, surfaces: list[etree._Element], ns: dict[str | None, str], version: Version) -> None:

            if Version("3.0") <= version:
                self.face = {
                            patch.attrib[nsl('gml:id', ns)]: self.Polygon(
                                polygon=patch.find('.//' + nsl('gml:posList', ns)).text,
                                ns=ns,
                                version=version
                            )
                            for surface in surfaces
                            for patch in surface.findall('.//' + nsl('gml:Polygon', ns))
                        }
            # end Surface

    component: dict[str, Surface]

    def __init__(self, building: etree._Element, ns: dict[str | None, str], version: Version) -> None:

        self.component = {}

        if Version("3.0") <= version:
            self.component['GroundSurface']  = self.Surface(building.findall('.//' + nsl('bldg:GroundSurface'   ,ns)), ns=ns, version=version)
            self.component['WallSurface']    = self.Surface(building.findall('.//' + nsl('bldg:WallSurface'     ,ns)), ns=ns, version=version)
            self.component['RoofSurface']    = self.Surface(building.findall('.//' + nsl('bldg:RoofSurface'     ,ns)), ns=ns, version=version)

# end Building

# functions
def nsl(identifier: str, namespace: dict | None = None) -> str:

    if ':' not in identifier:
        return identifier
    else:
        if namespace is None:
            raise ValueError('namespace dictionary required for identifiers with a colon (:)')
        prefix, local = identifier.split(':')
        return "{" + f"{namespace[prefix]}" + "}" + f"{local}"
