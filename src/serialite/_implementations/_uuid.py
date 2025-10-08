__all__ = ["UuidSerializer"]

from uuid import UUID

from .._base import Serializer
from .._errors import Errors, ValidationError
from .._result import Failure, Result, Success


class UuidSerializer(Serializer[UUID]):
    def from_data(self, data) -> Result[UUID]:
        if isinstance(data, str):
            try:
                value = UUID(data)
            except Exception:
                return Failure(Errors.one(ValidationError(f"Not a valid UUID: {data!r}")))
            else:
                return Success(value)
        else:
            return Failure(Errors.one(ValidationError(f"Not a valid UUID: {data!r}")))

    def to_data(self, value: UUID):
        if not isinstance(value, UUID):
            raise ValueError(f"Not a UUID: {value!r}")
        return str(value)

    def to_openapi_schema(self, refs: dict[Serializer, str], force: bool = False):
        return {"type": "string", "format": "uuid"}
