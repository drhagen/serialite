__all__ = ["RegexMismatchError", "StringSerializer"]

import re
from dataclasses import dataclass

from .._base import Serializer
from .._decorators import serializable
from .._errors import Errors
from .._result import Failure, Result, Success
from .._type_errors import ExpectedStringError


class StringSerializer(Serializer[str]):
    def __init__(self, accept: str | None = None):
        self.accept = accept
        self.accept_regex = re.compile(accept) if accept is not None else None

    def from_data(self, data) -> Result[str]:
        if isinstance(data, str):
            if self.accept is None or self.accept_regex.fullmatch(data):
                return Success(data)
            else:
                return Failure(Errors.one(RegexMismatchError(self.accept, data)))
        else:
            return Failure(Errors.one(ExpectedStringError(data)))

    def to_data(self, value: str):
        if not isinstance(value, str):
            raise ValueError(f"Not a string: {value!r}")
        if self.accept is not None and not self.accept_regex.fullmatch(value):
            raise ValueError(f"Does not match regex r'{self.accept}': {value!r}")
        return value

    def to_openapi_schema(self, refs: dict[Serializer, str], force: bool = False):
        return {"type": "string"}


@serializable
@dataclass(frozen=True, slots=True)
class RegexMismatchError(Exception):
    pattern: str
    actual: str

    def __str__(self) -> str:
        return f"Expected string matching {self.pattern!r}, but got {self.actual!r}"
