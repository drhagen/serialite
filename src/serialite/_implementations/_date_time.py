__all__ = ["DateTimeSerializer"]

from datetime import datetime

from .._base import Serializer
from .._result import DeserializationFailure, DeserializationResult, DeserializationSuccess


class DateTimeSerializer(Serializer[datetime]):
    def from_data(self, data) -> DeserializationResult[datetime]:
        if isinstance(data, str):
            try:
                value = datetime.fromisoformat(data)
            except ValueError:
                return DeserializationFailure(f"Not a valid DateTime: {data!r}")
            else:
                return DeserializationSuccess(value)
        else:
            return DeserializationFailure(f"Not a valid DateTime: {data!r}")

    def to_data(self, value):
        if not isinstance(value, datetime):
            raise ValueError(f"Not a DateTime: {value!r}")
        return value.isoformat(sep=" ")

    def to_openapi_schema(self, refs: dict[Serializer, str], force: bool = False):
        return {"type": "string", "format": "date-time"}
