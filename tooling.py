#!/usr/bin/python


import numpy as np
from lxml import etree  # pyright: ignore[reportAttributeAccessIssue]
from numpy.typing import NDArray


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

    def __init__(self, corner1: NDArray[np.float32], corner2: NDArray[np.float32]) -> None:
        self._corner1: NDArray[np.float32] = corner1
        self._corner2: NDArray[np.float32] = corner2
        self.update()

    def update(self) -> None:
        self.center: NDArray[np.float32] = (np.add(self._corner1, self._corner2)*0.5).astype(np.float32)

    # getter and setters to make sure updating the AABB updates associated data
    @property
    def corner1(self):
        return self._corner1

    @corner1.setter
    def corner1(self, value):
        self._corner1 = value
        self.update()

    @property
    def corner2(self):
        return self._corner2

    @corner2.setter
    def corner2(self, value):
        self._corner2 = value
        self.update()

class Implicit_Mapping:
    __slots__ = ("_item",)

    def __init__(self, items):
        object.__setattr__(self, "_item", items)

    def _items(self):
        if hasattr(self._item, "values"):
            return self._item.values()
        return self._item

    def __iter__(self):
        return iter(self._items())

    def __getattr__(self, name):
        #numpy and other packages may get a too eager with an __array_struct__ that just gets accepted all willy nilly. This ends here
        if name.startswith("__") and name.endswith("__"):
                raise AttributeError(name)

        return Implicit_Mapping(
            [getattr(item, name) for item in self._items()]
        )

    def flatten(self):
        def flatten_items(items):
            for item in items:
                if isinstance(item, (Implicit_Mapping, list, tuple)):
                    yield from flatten_items(item)
                else:
                    yield item

        return list(flatten_items(self._items()))

    def __setattr__(self, name, value):
        items = list(self._items())

        if isinstance(value, Implicit_Mapping):
            values = list(value._items())

            if len(items) != len(values):
                raise ValueError(
                    f"Cannot assign {len(values)} values to {len(items)} items"
                )

            for item, item_value in zip(items, values):
                setattr(item, name, item_value)

        else:
            for item in items:
                setattr(item, name, value)

    def __repr__(self):
        return repr(list(self))

    def __str__(self):
        return str(list(self))

    def __add__(self, other):
        return Implicit_Mapping(
            [item + other for item in self._items()]
        )

    def __sub__(self, other):
        return Implicit_Mapping(
            [item - other for item in self._items()]
        )

    def __mul__(self, other):
        return Implicit_Mapping(
            [item * other for item in self._items()]
        )

    def __truediv__(self, other):
        return Implicit_Mapping(
            [item / other for item in self._items()]
        )

class Building:

    class Surface:

        class Polygon:

            class Vertex:

                def __init__(self, version: Version, vertices: NDArray[np.float32]) -> None:

                    if Version("3.0") <= version:
                        # Ensure we have exactly 3 coordinates, padding with 0.0 if necessary
                        self._coords: NDArray[np.float32] = np.asarray((vertices + [0.0, 0.0, 0.0])[:3], dtype=np.float32)

                # --- Individual Coordinates ---
                @property
                def x(self) -> np.float32:
                    return self._coords[0]

                @x.setter
                def x(self, value: np.float32) -> None:
                    self._coords[0] = value

                @property
                def y(self) -> np.float32:
                    return self._coords[1]

                @y.setter
                def y(self, value: np.float32) -> None:
                    self._coords[1] = value

                @property
                def z(self) -> np.float32:
                    return self._coords[2]

                @z.setter
                def z(self, value: np.float32) -> None:
                    self._coords[2] = value

                # --- Composed Coordinates (Bidirectional) ---
                @property
                def xy(self) -> NDArray[np.float32]:
                    return np.asarray((self._coords[0], self._coords[1]), dtype=np.float32)

                @xy.setter
                def xy(self, value: NDArray[np.float32]) -> None:
                    self._coords[0], self._coords[1] = value

                @property
                def yz(self) -> NDArray[np.float32]:
                    return np.asarray((self._coords[1], self._coords[2]), dtype=np.float32)

                @yz.setter
                def yz(self, value: NDArray[np.float32]) -> None:
                    self._coords[1], self._coords[2] = value

                @property
                def xz(self) -> NDArray[np.float32]:
                    return np.asarray((self._coords[0], self._coords[2]), dtype=np.float32)

                @xz.setter
                def xz(self, value: NDArray[np.float32]) -> None:
                    self._coords[0], self._coords[2] = value

                @property
                def xyz(self) -> NDArray[np.float32]:
                    return np.asarray(self._coords, dtype=np.float32)

                @xyz.setter
                def xyz(self, value: NDArray[np.float32]) -> None:
                    self._coords[:] = value # Update list in place

            # end Vertex
            vertex: list[Vertex]
            vertices: Implicit_Mapping

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
                        self.Vertex(version=version, vertices=np.asarray(vertices, dtype=np.float32))
                        for vertices in _arr_vertex_ring[:-1]
                    ]

                self.vertices = Implicit_Mapping(self.vertex)

        # end Polygon

        face: dict[str, Polygon]
        faces: Implicit_Mapping

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

            self.faces = Implicit_Mapping(self.face)
            # end Surface

    component: dict[str, Surface]

    bounding_box: AABB_BoundingBox

    def __init__(self, building: etree._Element, ns: dict[str | None, str], version: Version) -> None:

        self.component = {}
        self.components = Implicit_Mapping(self.component)

        if Version("3.0") <= version:

            for ground_type in ('GroundSurface', 'WallSurface', 'RoofSurface', 'lod2Solid'):
                surface = building.findall('.//' + nsl(f"bldg:{ground_type}"   ,ns))
                if surface:
                    self.component[ground_type] = self.Surface(surface, ns=ns, version=version)

            vertices = np.asarray(self.components.faces.vertices.xyz.flatten(), dtype=np.float32).reshape((-1,3))
            self.bounding_box = AABB_BoundingBox(corner1=np.min(vertices, axis=0),
                                                 corner2=np.max(vertices, axis=0))

            self.components.faces.vertices.xyz -= self.bounding_box.center

# end Building

# functions
def nsl(identifier: str, namespace: dict | None = None) -> str:
    """
    Tiny helper function: lxml doesnt allow for the namespace resolution of indices / keys (see `.attrib[]` modifier).
    This function essentially emulates this, if only for a generic expression.
    WARNING: Will ignore special prefixes like `.//`. If this is required, add them seperately before the nsl expression using the `+` operator.
    """

    if ':' not in identifier:
        return identifier
    else:
        if namespace is None:
            raise ValueError('namespace dictionary required for identifiers with a colon (:)')
        prefix, local = identifier.split(':')
        return "{" + f"{namespace[prefix]}" + "}" + f"{local}"
