__all__ = ["JsonSerializer"]

from typing import Any

from .._base import Serializer
from .._result import DeserializationResult, DeserializationSuccess


class JsonSerializer(Serializer[Any]):
    """Serializer for any valid JSON object.

    By definition, the data is already valid JSON, so `from_data` and `to_data`
    merely return their inputs.
    """

    def from_data(self, data) -> DeserializationResult[Any]:
        return DeserializationSuccess(data)

    def to_data(self, value: Any):
        return value
