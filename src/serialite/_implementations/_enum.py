__all__ = ["EnumSerializer", "InvalidEnumValueError"]

from dataclasses import dataclass
from enum import Enum, IntEnum, StrEnum
from typing import Any, Literal

from .._base import Serializer
from .._decorators import serializable
from .._errors import Errors
from .._numeric_check import is_int
from .._result import Failure, Result, Success
from .._type_errors import ExpectedIntegerError, ExpectedStringError


class EnumSerializer[E: Enum](Serializer[E]):
    def __init__(self, enum_class: type[E], *, by: Literal["name", "value"] = "name"):
        if by not in ["name", "value"]:
            raise ValueError(f"Expected 'name' or 'value' for by, but got {by!r}")

        self.enum_class = enum_class
        self.by = by

    def from_data(self, data) -> Result[E]:
        if self.by == "name":
            return self._from_data_by_name(data)
        else:
            return self._from_data_by_value(data)

    def _from_data_by_name(self, data) -> Result[E]:
        if not isinstance(data, str):
            return Failure(Errors.one(ExpectedStringError(data)))

        try:
            return Success(self.enum_class[data])
        except KeyError:
            names = [m.name for m in self.enum_class]
            err = InvalidEnumValueError(self.enum_class.__name__, names, data)
            return Failure(Errors.one(err))

    def _from_data_by_value(self, data) -> Result[E]:
        if issubclass(self.enum_class, StrEnum):
            if not isinstance(data, str):
                return Failure(Errors.one(ExpectedStringError(data)))
        elif issubclass(self.enum_class, IntEnum):
            if not is_int(data):
                return Failure(Errors.one(ExpectedIntegerError(data)))

        try:
            return Success(self.enum_class(data))
        except ValueError:
            values = [m.value for m in self.enum_class]
            err = InvalidEnumValueError(self.enum_class.__name__, values, data)
            return Failure(Errors.one(err))

    def to_data(self, value: E):
        if not isinstance(value, self.enum_class):
            raise ValueError(f"Expected {self.enum_class.__name__}, got {type(value).__name__}")

        if self.by == "name":
            return value.name
        else:
            return value.value

    def to_openapi_schema(self, force: bool = False):
        if self.by == "name":
            return {"type": "string", "enum": [m.name for m in self.enum_class]}
        else:
            values = [m.value for m in self.enum_class]
            if all(isinstance(v, str) for v in values):
                return {"type": "string", "enum": values}
            elif all(is_int(v) for v in values):
                return {"type": "integer", "enum": values}
            else:
                return {"enum": values}


@serializable
@dataclass(frozen=True, slots=True)
class InvalidEnumValueError(Exception):
    enum_name: str
    values: list[Any]
    actual: Any

    def __str__(self) -> str:
        return f"Expected one of {self.values!r} for {self.enum_name}, but got {self.actual!r}"
