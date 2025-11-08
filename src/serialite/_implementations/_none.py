__all__ = ["ExpectedNoneError", "NoneSerializer"]

from dataclasses import dataclass
from typing import Any

from .._base import Serializer
from .._decorators import serializable
from .._errors import Errors
from .._result import Failure, Success


class NoneSerializer(Serializer[None]):
    def from_data(self, data):
        if data is None:
            return Success(None)
        else:
            return Failure(Errors.one(ExpectedNoneError(data)))

    def to_data(self, value: None):
        if value is not None:
            raise ValueError(f"Not an None: {value!r}")
        return value

    def to_openapi_schema(self, refs: dict[Serializer, str], force: bool = False):
        return {"nullable": True}


@serializable
@dataclass(frozen=True, slots=True)
class ExpectedNoneError(Exception):
    actual: Any

    def __str__(self) -> str:
        return f"Expected null, but got {self.actual!r}"
