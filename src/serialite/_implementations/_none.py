__all__ = ["NoneSerializer"]

from pydantic.json_schema import GenerateJsonSchema

from .._base import Serializer
from .._errors import Errors
from .._result import Failure, Success
from .._type_errors import ExpectedNullError


class NoneSerializer(Serializer[None]):
    def from_data(self, data):
        if data is None:
            return Success(None)
        else:
            return Failure(Errors.one(ExpectedNullError(data)))

    def to_data(self, value: None):
        if value is not None:
            raise ValueError(f"Not an None: {value!r}")
        return value

    def to_openapi_schema(
        self, force: bool = False, json_schema_generator: GenerateJsonSchema | None = None
    ):
        return {"nullable": True}
