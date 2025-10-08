__all__ = ["BooleanSerializer"]

from .._base import Serializer
from .._errors import Errors, ValidationError
from .._result import Failure, Result, Success


class BooleanSerializer(Serializer[bool]):
    def from_data(self, data) -> Result[bool]:
        if isinstance(data, bool):
            return Success(data)
        else:
            return Failure(Errors.one(ValidationError(f"Not a valid boolean: {data!r}")))

    def to_data(self, value: bool):
        if not isinstance(value, bool):
            raise ValueError(f"Not an bool: {value!r}")
        return value

    def to_openapi_schema(self, refs: dict[Serializer, str], force: bool = False):
        return {"type": "boolean"}
