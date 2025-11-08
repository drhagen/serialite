__all__ = ["BooleanSerializer", "ExpectedBooleanError"]

from dataclasses import dataclass

from .._base import Serializer
from .._decorators import serializable
from .._errors import Errors
from .._result import Failure, Result, Success


class BooleanSerializer(Serializer[bool]):
    def from_data(self, data) -> Result[bool]:
        if isinstance(data, bool):
            return Success(data)
        else:
            return Failure(Errors.one(ExpectedBooleanError(data)))

    def to_data(self, value: bool):
        if not isinstance(value, bool):
            raise ValueError(f"Not an bool: {value!r}")
        return value

    def to_openapi_schema(self, refs: dict[Serializer, str], force: bool = False):
        return {"type": "boolean"}


@serializable
@dataclass(frozen=True, slots=True)
class ExpectedBooleanError(Exception):
    actual: object

    def __str__(self) -> str:
        return f"Expected boolean, but got {self.actual!r}"
