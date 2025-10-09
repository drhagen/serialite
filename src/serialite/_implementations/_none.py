__all__ = ["NoneSerializer"]

from .._base import Serializer
from .._errors import Errors, ValidationError
from .._result import Failure, Success


class NoneSerializer(Serializer[None]):
    def from_data(self, data):
        if data is None:
            return Success(None)
        else:
            return Failure(Errors.one(ValidationError(f"Not a null: {data!r}")))

    def to_data(self, value: None):
        if value is not None:
            raise ValueError(f"Not an None: {value!r}")
        return value

    def to_openapi_schema(self, refs: dict[Serializer, str], force: bool = False):
        return {"nullable": True}
