__all__ = ["LiteralSerializer"]

from .._base import Serializer
from .._numeric_check import is_int, is_real
from .._result import DeserializationFailure, DeserializationSuccess


class LiteralSerializer(Serializer):
    def __init__(self, *possibilities):
        self.possibilities = possibilities

    def from_data(self, data):
        if data in self.possibilities:
            return DeserializationSuccess(data)
        else:
            return DeserializationFailure(f"Not one of {list(self.possibilities)!r}: {data!r}")

    def to_data(self, value):
        if value not in self.possibilities:
            raise ValueError(f"Not one of {list(self.possibilities)!r}: {value!r}")

        return value

    def to_openapi_schema(self, refs: dict[Serializer, str], force: bool = False):
        if all(isinstance(x, str) for x in self.possibilities):
            return {"type": "string", "enum": self.possibilities}
        elif all(is_int(x) for x in self.possibilities):
            return {"type": "integer", "enum": self.possibilities}
        elif all(is_real(x) for x in self.possibilities):
            return {"type": "number", "enum": self.possibilities}
        else:
            return {"enum": self.possibilities}
