__all__ = ["DuplicatedValueError", "SetSerializer"]

from dataclasses import dataclass
from typing import Any

from .._base import Serializer
from .._decorators import serializable
from .._errors import Errors
from .._openapi import is_openapi_component
from .._result import Failure, Result, Success
from .._type_errors import ExpectedListError


class SetSerializer[Element](Serializer[set[Element]]):
    def __init__(self, element_serializer: Serializer[Element]):
        self.element_serializer = element_serializer

    def from_data(self, data) -> Result[set[Element]]:
        # Return early if the data isn't even a list
        if not isinstance(data, list):
            return Failure(Errors.one(ExpectedListError(data)))

        # Validate values
        errors = Errors()
        values = set()
        for i, value in enumerate(data):
            match self.element_serializer.from_data(value):
                case Failure(error):
                    errors.extend(error, location=[i])
                case Success(value):
                    if value in values:
                        errors.add(DuplicatedValueError(value), location=[i])
                    else:
                        values.add(value)

        if not errors.is_empty():
            return Failure(errors)
        else:
            return Success(values)

    def to_data(self, value: set[Element]):
        if not isinstance(value, set):
            raise ValueError(f"Not a set: {value!r}")

        return [self.element_serializer.to_data(item) for item in value]

    def child_components(self):
        if is_openapi_component(self.element_serializer):
            return {"element": self.element_serializer}
        else:
            return {}

    def to_openapi_schema(self, force: bool = False):
        return {"type": "array", "items": self.element_serializer.to_openapi_schema()}


@serializable
@dataclass(frozen=True, slots=True)
class DuplicatedValueError(Exception):
    duplicate: Any

    def __str__(self) -> str:
        return f"Expected a list of unique values, but got this duplicate {self.duplicate!r}"
