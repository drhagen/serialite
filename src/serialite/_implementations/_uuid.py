__all__ = ["InvalidUuidError", "UuidSerializer"]

from dataclasses import dataclass
from uuid import UUID

from .._base import Serializer
from .._decorators import serializable
from .._errors import Errors
from .._result import Failure, Result, Success
from .._type_errors import ExpectedStringError


class UuidSerializer(Serializer[UUID]):
    def from_data(self, data) -> Result[UUID]:
        if isinstance(data, str):
            try:
                value = UUID(data)
            except Exception:
                return Failure(Errors.one(InvalidUuidError(data)))
            else:
                return Success(value)
        else:
            return Failure(Errors.one(ExpectedStringError(data)))

    def to_data(self, value: UUID):
        if not isinstance(value, UUID):
            raise ValueError(f"Not a UUID: {value!r}")
        return str(value)

    def to_openapi_schema(self, refs: dict[Serializer, str], force: bool = False):
        return {"type": "string", "format": "uuid"}


@serializable
@dataclass(frozen=True, slots=True)
class InvalidUuidError(Exception):
    actual: str

    def __str__(self) -> str:
        return f"Expected UUID, but got {self.actual!r}"
