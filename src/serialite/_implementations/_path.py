__all__ = ["PathSerializer"]

from pathlib import Path

from .._base import Serializer
from .._result import Failure, Result, Success
from ._string import StringSerializer


class PathSerializer(Serializer):
    def from_data(self, data) -> Result[Path]:
        match StringSerializer().from_data(data):
            case Failure(error):
                return Failure(error)
            case Success(value):
                return Success(Path(value))

    def to_data(self, value):
        return value.as_posix()
