__all__ = ["ReservedSerializer"]

from collections.abc import Set
from typing import Generic, TypeVar

from .._base import Serializer
from .._result import DeserializationFailure, DeserializationResult
from .._stable_set import StableSet

Element = TypeVar("Element")


class ReservedSerializer(Generic[Element], Serializer[Element]):
    def __init__(self, internal_serializer: Serializer[Element], *, reserved: Set[Element]):
        self.internal_serializer = internal_serializer
        self.reserved = reserved

    def from_data(self, data) -> DeserializationResult[Element]:
        result = self.internal_serializer.from_data(data)

        if isinstance(result, DeserializationFailure):
            return result
        elif result.value in self.reserved:
            return DeserializationFailure(f"Reserved value: {result.value!r}")
        else:
            return result

    def to_data(self, value):
        if value in self.reserved:
            raise ValueError(f"Reserved value: {value}")

        return self.internal_serializer.to_data(value)

    def collect_openapi_models(
        self, parent_models: StableSet[Serializer]
    ) -> StableSet[Serializer]:
        return self.internal_serializer.collect_openapi_models(parent_models)

    def to_openapi_schema(self, refs: dict[Serializer, str], force: bool = False):
        return self.internal_serializer.to_openapi_schema(refs)
