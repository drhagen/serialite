__all__ = ["OrderedDictSerializer", "RawDictSerializer"]

from collections import OrderedDict
from typing import Generic, TypeVar

from .._base import Serializer
from .._errors import Errors, ValidationError
from .._result import Failure, Result, Success
from .._stable_set import StableSet
from ._string import StringSerializer

Key = TypeVar("Key")
Value = TypeVar("Value")


class OrderedDictSerializer(Generic[Key, Value], Serializer[dict[Key, Value]]):
    """Serializing a dictionary as a list of entries.

    The fields of a JSON object is inherently unordered. Also, the keys cannot
    be anything except strings. If retaining the order of a dictionary is
    desired or allowing a key other than a string is required, this serializer
    can be used. It is represented as a JSON list (which is ordered) or
    2-element lists, where the first element is the key and the second element
    is the value.
    """

    def __init__(self, key_serializer: Serializer[Key], value_serializer: Serializer[Value]):
        self.key_serializer = key_serializer
        self.value_serializer = value_serializer

    def from_data(self, data) -> Result[dict[Key, Value]]:
        # Return early if the data isn't even a list
        if not isinstance(data, list):
            return Failure(Errors.one(ValidationError(f"Not a valid list: {data!r}")))

        # Validate keys first, so that errors in values can be better formatted
        errors = Errors()
        keys = []
        for i, item in enumerate(data):
            if not isinstance(item, (list, tuple)) or len(item) != 2:
                errors.add(ValidationError(f"Not a valid length-2 list: {item!r}"), location=[i])
            else:
                match self.key_serializer.from_data(item[0]):
                    case Failure(error):
                        errors.extend(error, location=[i])
                    case Success(value):
                        keys.append(value)

        if not errors.is_empty():
            return Failure(errors)

        # Validate values, including the key in errors to help identify the location of the failure
        errors = Errors()
        values = []
        for i, item in enumerate(data):
            match self.value_serializer.from_data(item[1]):
                case Failure(error):
                    errors.extend(error, location=[keys[i]])
                case Success(value):
                    values.append((keys[i], value))

        if not errors.is_empty():
            return Failure(errors)
        else:
            return Success(OrderedDict(values))

    def to_data(self, value: dict[Key, Value]):
        if not isinstance(value, dict):
            raise ValueError(f"Not an dict: {value!r}")

        return [
            [self.key_serializer.to_data(key), self.value_serializer.to_data(value)]
            for key, value in value.items()
        ]


class RawDictSerializer(Generic[Value], Serializer[dict[str, Value]]):
    """Serializing a dictionary to a dictionary rather than a list of tuples.

    OpenAPI does not understand tuples and therefore cannot capture the
    definition of an ordered dictionary as given by `OrderedDictSerializer`.
    `RawDictSerializer` can be used to serialize dictionaries when the key is a
    string and order is unimportant and a type that is understood by OpenAPI is
    important.
    """

    def __init__(
        self,
        value_serializer: Serializer[Value],
        *,
        key_serializer: Serializer[str] = StringSerializer(),  # noqa: B008
    ):
        self.value_serializer = value_serializer
        self.key_serializer = key_serializer

    def from_data(self, data) -> Result[dict[str, Value]]:
        # Return early if the data isn't even a dict
        if not isinstance(data, dict):
            return Failure(Errors.one(ValidationError(f"Not a valid dict: {data!r}")))

        # Validate keys and values
        # Include the key in errors to help identify the location of the failure
        errors = Errors()
        values = {}
        for key, value in data.items():
            match self.key_serializer.from_data(key):
                case Failure(error):
                    errors.extend(error, location=[key])
                    continue
                case Success(parsed_key):
                    pass

            match self.value_serializer.from_data(value):
                case Failure(error):
                    errors.extend(error, location=[key])
                case Success(parsed_value):
                    values[parsed_key] = parsed_value

        if not errors.is_empty():
            return Failure(errors)
        else:
            return Success(values)

    def to_data(self, value: dict[str, Value]):
        if not isinstance(value, dict):
            raise ValueError(f"Not an dict: {value!r}")

        return {
            self.key_serializer.to_data(key): self.value_serializer.to_data(value)
            for key, value in value.items()
        }

    def collect_openapi_models(
        self, parent_models: StableSet[Serializer]
    ) -> StableSet[Serializer]:
        return self.value_serializer.collect_openapi_models(parent_models)

    def to_openapi_schema(self, refs: dict[Serializer, str], force: bool = False):
        return {
            "type": "object",
            "additionalProperties": self.value_serializer.to_openapi_schema(refs),
        }
