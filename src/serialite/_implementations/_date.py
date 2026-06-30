__all__ = ["DateSerializer", "InvalidDateError"]

from dataclasses import dataclass
from datetime import date, datetime

from .._base import Serializer, SerializerToRef
from .._decorators import serializable
from .._errors import Errors
from .._result import Failure, Result, Success
from .._type_errors import ExpectedStringError


class DateSerializer(Serializer[date]):
    def from_data(self, data) -> Result[date]:
        if isinstance(data, str):
            # date.fromisoformat accepts only YYYY-MM-DD, rejecting strings that
            # carry a time component.
            try:
                value = date.fromisoformat(data)
            except ValueError:
                return Failure(Errors.one(InvalidDateError(data)))
            else:
                return Success(value)
        else:
            return Failure(Errors.one(ExpectedStringError(data)))

    def to_data(self, value):
        # datetime is a subclass of date, so isinstance(value, date) alone would
        # accept a datetime and serialize it with a time component. Exclude it
        # explicitly.
        if not isinstance(value, date) or isinstance(value, datetime):
            raise ValueError(f"Not a Date: {value!r}")
        return value.isoformat()

    def to_openapi_schema(self, serializer_to_ref: SerializerToRef, *, force: bool = False):
        return {"type": "string", "format": "date"}


@serializable
@dataclass(frozen=True, slots=True)
class InvalidDateError(Exception):
    actual: str

    def __str__(self) -> str:
        return f"Expected Date, but got {self.actual!r}"
