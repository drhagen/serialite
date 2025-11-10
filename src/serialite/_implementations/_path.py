__all__ = ["PathSerializer"]

from pathlib import Path

from .._base import Serializer
from .._errors import Errors
from .._result import Failure, Result, Success
from .._type_errors import ExpectedStringError


class PathSerializer(Serializer):
    def from_data(self, data) -> Result[Path]:
        if not isinstance(data, str):
            return Failure(Errors.one(ExpectedStringError(data)))

        return Success(Path(data))

    def to_data(self, value):
        if not isinstance(value, Path):
            raise ValueError(f"Not a Path: {value!r}")
        return value.as_posix()
