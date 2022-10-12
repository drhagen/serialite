__all__ = ["PathSerializer"]

from pathlib import Path

from .._base import Serializer
from .._result import DeserializationFailure, DeserializationResult, DeserializationSuccess
from ._string import StringSerializer


class PathSerializer(Serializer):
    def from_data(self, data) -> DeserializationResult:
        path_or_error = StringSerializer().from_data(data)

        if isinstance(path_or_error, DeserializationFailure):
            return path_or_error
        else:
            path = path_or_error.or_die()

            return DeserializationSuccess(Path(path))

    def to_data(self, value):
        return value.as_posix()
