__all__ = ["IntegerSerializer", "NonnegativeIntegerSerializer", "PositiveIntegerSerializer"]

from .._base import Serializer
from .._numeric_check import is_int
from .._result import DeserializationFailure, DeserializationResult, DeserializationSuccess


class IntegerSerializer(Serializer[int]):
    def from_data(self, data) -> DeserializationResult[int]:
        if isinstance(data, int):
            return DeserializationSuccess(data)
        else:
            return DeserializationFailure(f"Not a valid integer: {data!r}")

    def to_data(self, value: int):
        if not isinstance(value, int):
            raise ValueError(f"Not an int: {value!r}")
        return value

    def to_openapi_schema(self, refs: dict[Serializer, str], force: bool = False):
        return {"type": "integer"}


class NonnegativeIntegerSerializer(Serializer[int]):
    def from_data(self, data) -> DeserializationResult[int]:
        if is_int(data) and data >= 0:
            return DeserializationSuccess(data)
        else:
            return DeserializationFailure(f"Not a valid nonnegative integer: {data!r}")

    def to_data(self, value: int):
        if not is_int(value) or value < 0:
            raise ValueError(f"Not an nonnegative int: {value!r}")
        return value

    def to_openapi_schema(self, refs: dict[Serializer, str], force: bool = False):
        return {"type": "integer", "minimum": 0}


class PositiveIntegerSerializer(Serializer[int]):
    def from_data(self, data) -> DeserializationResult[int]:
        if is_int(data) and data > 0:
            return DeserializationSuccess(data)
        else:
            return DeserializationFailure(f"Not a valid positive integer: {data!r}")

    def to_data(self, value: int):
        if not is_int(value) or value <= 0:
            raise ValueError(f"Not an positive int: {value!r}")
        return value

    def to_openapi_schema(self, refs: dict[Serializer, str], force: bool = False):
        return {"type": "integer", "minimum": 1}
