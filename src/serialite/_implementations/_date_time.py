__all__ = ["DateTimeSerializer"]

from datetime import datetime

from .._base import Serializer
from .._errors import Errors, ValidationError
from .._result import Failure, Result, Success


class DateTimeSerializer(Serializer[datetime]):
    def from_data(self, data) -> Result[datetime]:
        if isinstance(data, str):
            if data.endswith("Z"):
                # Python does not handle the terminal "Z"
                # https://github.com/python/cpython/issues/80010
                sanitized_data = data[:-1] + "+00:00"
            else:
                sanitized_data = data
            try:
                value = datetime.fromisoformat(sanitized_data)
            except ValueError:
                return Failure(Errors.one(ValidationError(f"Not a valid DateTime: {data!r}")))
            else:
                return Success(value)
        else:
            return Failure(Errors.one(ValidationError(f"Not a valid DateTime: {data!r}")))

    def to_data(self, value):
        if not isinstance(value, datetime):
            raise ValueError(f"Not a DateTime: {value!r}")
        return value.isoformat(sep=" ")

    def to_openapi_schema(self, refs: dict[Serializer, str], force: bool = False):
        return {"type": "string", "format": "date-time"}
