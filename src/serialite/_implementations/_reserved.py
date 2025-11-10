__all__ = ["ReservedSerializer", "ReservedValueError"]

from collections.abc import Set
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from .._base import Serializer
from .._decorators import serializable
from .._errors import Errors
from .._result import Failure, Result, Success
from .._stable_set import StableSet

Element = TypeVar("Element")


class ReservedSerializer(Generic[Element], Serializer[Element]):
    def __init__(self, internal_serializer: Serializer[Element], *, reserved: Set[Element]):
        self.internal_serializer = internal_serializer
        self.reserved = reserved

    def from_data(self, data) -> Result[Element]:
        match self.internal_serializer.from_data(data):
            case Failure(error):
                return Failure(error)
            case Success(value):
                if value in self.reserved:
                    return Failure(Errors.one(ReservedValueError(value)))
                return Success(value)

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


@serializable
@dataclass(frozen=True, slots=True)
class ReservedValueError(Exception):
    actual: Any

    def __str__(self) -> str:
        return f"This is a reserved value: {self.actual!r}"
