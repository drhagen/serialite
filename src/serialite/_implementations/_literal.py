__all__ = ["LiteralSerializer", "UnknownValueError"]

from dataclasses import dataclass
from typing import Any

from .._base import Serializer
from .._decorators import serializable
from .._errors import Errors
from .._numeric_check import is_int, is_real
from .._result import Failure, Success


class LiteralSerializer(Serializer):
    def __init__(self, *possibilities):
        self.possibilities = possibilities

    def from_data(self, data):
        if data in self.possibilities:
            return Success(data)
        else:
            return Failure(Errors.one(UnknownValueError(list(self.possibilities), data)))

    def to_data(self, value):
        if value not in self.possibilities:
            raise ValueError(f"Not one of {list(self.possibilities)!r}: {value!r}")

        return value

    def to_openapi_schema(self, force: bool = False):
        possibilities = list(self.possibilities)

        if all(isinstance(x, str) for x in possibilities):
            return {"type": "string", "enum": possibilities}
        elif all(is_int(x) for x in possibilities):
            return {"type": "integer", "enum": possibilities}
        elif all(is_real(x) for x in possibilities):
            return {"type": "number", "enum": possibilities}
        else:
            return {"enum": possibilities}


@serializable
@dataclass(frozen=True, slots=True)
class UnknownValueError(Exception):
    possibilities: list[Any]
    actual: Any

    def __str__(self) -> str:
        return f"Expected one of {self.possibilities!r}, but got {self.actual!r}"
