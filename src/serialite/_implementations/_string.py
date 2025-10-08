__all__ = ["StringSerializer"]

import re

from .._base import Serializer
from .._errors import Errors, ValidationError
from .._result import Failure, Result, Success


class StringSerializer(Serializer[str]):
    def __init__(self, accept: str | None = None):
        self.accept = accept
        self.accept_regex = re.compile(accept) if accept is not None else None

    def from_data(self, data) -> Result[str]:
        if isinstance(data, str):
            if self.accept is None or self.accept_regex.fullmatch(data):
                return Success(data)
            else:
                return Failure(
                    Errors.one(ValidationError(f"Does not match regex r'{self.accept}': {data!r}"))
                )
        else:
            return Failure(Errors.one(ValidationError(f"Not a valid string: {data!r}")))

    def to_data(self, value: str):
        if not isinstance(value, str):
            raise ValueError(f"Not a string: {value!r}")
        if self.accept is not None and not self.accept_regex.fullmatch(value):
            raise ValueError(f"Does not match regex r'{self.accept}': {value!r}")
        return value

    def to_openapi_schema(self, refs: dict[Serializer, str], force: bool = False):
        return {"type": "string"}
