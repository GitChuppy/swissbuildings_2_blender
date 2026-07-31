#!/usr/bin/python


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
        ) < (
            other.major,
            other.minor,
            other.hotfix
        )
    def __le__(self, other) -> bool:
        return not(self.__lt__(other))
    def __ge__(self, other) -> bool:
        return not(self.__gt__(other))
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

"""# testing framework
case_alpha = Version("1.2.3")
case_beta  = Version("3.4")
case_gamma = Version("")

print(case_alpha == Version("1.2.3"))
print(Version("1") == Version("1.0.0"))
print(Version("2") < Version("0.9.9"))
"""

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

# functions
def ns_lookup(identifier: str, namespace: dict | None = None) -> str:

    if ':' not in identifier:
        return identifier
    else:
        if namespace is None:
            raise ValueError('namespace dictionary required for identifiers with a colon (:)')
        prefix, local = identifier.split(':')
        return "{" + f"{namespace[prefix]}" + "}" + f"{local}"
