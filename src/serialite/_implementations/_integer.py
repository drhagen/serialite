__all__ = [
    "IntegerOutOfRangeError",
    "IntegerSerializer",
    "NonnegativeIntegerSerializer",
    "PositiveIntegerSerializer",
]

from dataclasses import dataclass

from .._base import Serializer
from .._decorators import serializable
from .._errors import Errors
from .._numeric_check import is_int
from .._result import Failure, Result, Success
from .._type_errors import ExpectedIntegerError


class IntegerSerializer(Serializer[int]):
    def from_data(self, data) -> Result[int]:
        if isinstance(data, int):
            return Success(data)
        else:
            return Failure(Errors.one(ExpectedIntegerError(data)))

    def to_data(self, value: int):
        if not isinstance(value, int):
            raise ValueError(f"Not an int: {value!r}")
        return value

    def to_openapi_schema(self, refs: dict[Serializer, str], force: bool = False):
        return {"type": "integer"}


class NonnegativeIntegerSerializer(Serializer[int]):
    def from_data(self, data) -> Result[int]:
        if not is_int(data):
            return Failure(Errors.one(ExpectedIntegerError(data)))

        if data >= 0:
            return Success(data)
        else:
            return Failure(Errors.one(IntegerOutOfRangeError(actual=int(data), minimum=0)))

    def to_data(self, value: int):
        if not is_int(value) or value < 0:
            raise ValueError(f"Not an nonnegative int: {value!r}")
        return value

    def to_openapi_schema(self, refs: dict[Serializer, str], force: bool = False):
        return {"type": "integer", "minimum": 0}


class PositiveIntegerSerializer(Serializer[int]):
    def from_data(self, data) -> Result[int]:
        if not is_int(data):
            return Failure(Errors.one(ExpectedIntegerError(data)))

        if data > 0:
            return Success(data)
        else:
            return Failure(Errors.one(IntegerOutOfRangeError(actual=int(data), minimum=1)))

    def to_data(self, value: int):
        if not is_int(value) or value <= 0:
            raise ValueError(f"Not an positive int: {value!r}")
        return value

    def to_openapi_schema(self, refs: dict[Serializer, str], force: bool = False):
        return {"type": "integer", "minimum": 1}


@serializable
@dataclass(frozen=True, slots=True)
class IntegerOutOfRangeError(Exception):
    """Raised when an integer is outside the expected range.

    Either minimum or maximum must be provided.

    Attributes:
        actual: The integer that was provided.
        minimum: Minimum bound, inclusive.
        maximum: Maximum bound, inclusive.
    """

    actual: int
    minimum: int | None = None
    maximum: int | None = None

    def __post_init__(self):
        if self.minimum is None and self.maximum is None:
            raise ValueError("Either minimum or maximum must be provided.")

    def __str__(self) -> str:
        if self.minimum is not None and self.maximum is not None:
            return (
                f"Expected integer from {self.minimum} to {self.maximum}, but got {self.actual!r}"
            )
        elif self.minimum is not None:
            return f"Expected integer greater than or equal to {self.minimum}, but got {self.actual!r}"
        elif self.maximum is not None:
            return (
                f"Expected integer less than or equal to {self.maximum}, but got {self.actual!r}"
            )
        else:
            raise NotImplementedError()
