__all__ = ["UuidSerializer"]

from uuid import UUID

from .._base import Serializer
from .._result import DeserializationFailure, DeserializationResult, DeserializationSuccess


class UuidSerializer(Serializer[UUID]):
    def from_data(self, data) -> DeserializationResult[UUID]:
        if isinstance(data, str):
            try:
                value = UUID(data)
            except Exception:
                return DeserializationFailure(f"Not a valid UUID: {data!r}")
            else:
                return DeserializationSuccess(value)
        else:
            return DeserializationFailure(f"Not a valid UUID: {data!r}")

    def to_data(self, value: UUID):
        if not isinstance(value, UUID):
            raise ValueError(f"Not a UUID: {value!r}")
        return str(value)

    def to_openapi_schema(self, refs: dict[Serializer, str], force: bool = False):
        return {"type": "string", "format": "uuid"}
