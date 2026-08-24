from collections.abc import Iterable, Iterator
from typing import cast, override

class Implicit_Mapping:

    def __init__(self, items: object):
        object.__setattr__(self, "_item", items)

    def _items(self) -> Iterable[object]:
        if isinstance(self._item, dict):
            return cast(Iterable[object], self._item.values())
        return self._item

    def __iter__(self):
        return iter(self._items())

    def __getattr__(self, name: str):
        #numpy and other packages may get a too eager with an __array_struct__ that just gets accepted all willy nilly. This ends here
        if name.startswith("__") and name.endswith("__"):
                raise AttributeError(name)

        return Implicit_Mapping(
            [getattr(item, name) for item in self._items()]
        )

    def flatten(self) -> Iterable[object]:
        def flatten_items(items: Iterable[object]) -> Iterable[object]:
            for item in items:
                if isinstance(item, (Implicit_Mapping, list, tuple)):
                    yield from flatten_items(item)
                else:
                    yield item

        return list(flatten_items(self._items()))

    @override
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

    @override
    def __repr__(self):
        return repr(list(self))

    @override
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
