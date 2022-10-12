__all__ = ["StableSet"]

from collections.abc import Iterable, Set
from typing import TypeVar

Element = TypeVar("Element", covariant=True)


class StableSet(Set[Element]):
    """An immutable set with stable iteration order."""

    def __init__(self, *items: Element):
        self._elements = {item: None for item in items}

    def __contains__(self, item: Element):
        return item in self._elements.keys()

    def __iter__(self):
        return iter(self._elements.keys())

    def __len__(self):
        return len(self._elements)

    def __or__(self, other: Iterable[Element]):
        return StableSet(*self._elements.keys(), *other)

    def __ror__(self, other: Iterable[Element]):
        return StableSet(*other, *self._elements.keys())

    def __and__(self, other: Iterable[Element]):
        return StableSet(*(element for element in self._elements.keys() if element in other))

    def __rand__(self, other: Iterable[Element]):
        return StableSet(*(element for element in other if element in self._elements))

    def __xor__(self, other: Iterable[Element]):
        return StableSet(
            *(element for element in self._elements.keys() if element not in other),
            *(element for element in other if element not in self._elements),
        )

    def __rxor__(self, other: Iterable[Element]):
        return StableSet(
            *(element for element in other if element not in self._elements),
            *(element for element in self._elements.keys() if element not in other),
        )

    def __sub__(self, other: Iterable[Element]):
        return StableSet(*(element for element in self._elements.keys() if element not in other))

    def __repr__(self):
        return f"StableSet({', '.join(map(repr, self._elements))})"
