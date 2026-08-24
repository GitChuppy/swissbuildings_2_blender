from collections.abc import Iterable, Iterator
from typing import Any, cast, override


class Implicit_Mapping[T_Item]:

    _item: list[T_Item] | dict[str, T_Item]  # pyright: ignore[reportUninitializedInstanceVariable]

    def __init__(self, items: list[T_Item] | dict[str, T_Item]) -> None:
        object.__setattr__(self, "_item", items)

    def _items(self) -> Iterable[T_Item]:
        if isinstance(self._item, dict):
            return self._item.values()
        return self._item

    def __iter__(self) -> Iterator[T_Item]:
        return iter(self._items())

    def __getattr__(self, name: str) -> Implicit_Mapping[object]:
        #numpy and other packages may get a too eager with an __array_struct__ that just gets accepted all willy nilly. This ends here
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)

        return Implicit_Mapping(
            [cast(object, getattr(item, name)) for item in self._items()]
        )

    def flatten(self) -> list[object]:
        def flatten_items(items: Iterable[object]) -> Iterator[object]:
            for item in items:
                if isinstance(item, (Implicit_Mapping, list, tuple)):
                    yield from flatten_items(cast(Iterable[object], item))
                else:
                    yield item

        return list(flatten_items(self._items()))

    @override
    def __setattr__(self, name: str, value: object) -> None:
        items = list(self._items())

        if isinstance(value, Implicit_Mapping):
            mapping = cast(Implicit_Mapping[object], value)
            values = list(mapping._items())

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
    def __repr__(self) -> str:
        return repr(list(self))

    @override
    def __str__(self) -> str:
        return str(list(self))

    def __add__(self, other: Any) -> Implicit_Mapping[Any]:  # pyright: ignore[reportAny,reportExplicitAny]
        return Implicit_Mapping(
            [item + other for item in self._items()]
        )

    def __sub__(self, other: Any) -> Implicit_Mapping[Any]:  # pyright: ignore[reportAny,reportExplicitAny]
        return Implicit_Mapping(
            [item - other for item in self._items()]
        )

    def __mul__(self, other: Any) -> Implicit_Mapping[Any]:  # pyright: ignore[reportAny,reportExplicitAny]
        return Implicit_Mapping(
            [item * other for item in self._items()]
        )

    def __truediv__(self, other: Any) -> Implicit_Mapping[Any]:  # pyright: ignore[reportAny,reportExplicitAny]
        return Implicit_Mapping(
            [item / other for item in self._items()]
        )
