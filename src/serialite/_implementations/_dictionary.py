__all__ = ["OrderedDictSerializer", "RawDictSerializer"]

from collections import OrderedDict
from typing import Generic, TypeVar

from .._base import Serializer
from .._result import DeserializationFailure, DeserializationResult, DeserializationSuccess
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

    def from_data(self, data) -> DeserializationResult[dict[Key, Value]]:
        # Return early if the data isn't even a list
        if not isinstance(data, list):
            return DeserializationFailure(f"Not a valid list: {data!r}")

        # Validate keys first, so that errors in values can be better formatted
        errors = {}
        keys = []
        for i, item in enumerate(data):
            if not isinstance(item, (list, tuple)) or len(item) != 2:
                errors[str(i)] = f"Not a valid length-2 list: {item!r}"
            else:
                value_or_error = self.key_serializer.from_data(item[0])
                if isinstance(value_or_error, DeserializationFailure):
                    errors[str(i)] = value_or_error.error
                else:
                    keys.append(value_or_error.value)

        if len(errors) > 0:
            return DeserializationFailure(errors)

        # Validate values, including the key in errors to help identify the location of the failure
        errors = {}
        values = []
        for i, item in enumerate(data):
            value_or_error = self.value_serializer.from_data(item[1])
            if isinstance(value_or_error, DeserializationFailure):
                errors[str(keys[i])] = value_or_error.error
            else:
                values.append((keys[i], value_or_error.value))

        if len(errors) > 0:
            return DeserializationFailure(errors)
        else:
            return DeserializationSuccess(OrderedDict(values))

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

    def from_data(self, data) -> DeserializationResult[dict[str, Value]]:
        # Return early if the data isn't even a dict
        if not isinstance(data, dict):
            return DeserializationFailure(f"Not a valid dict: {data!r}")

        # Validate keys and values
        # Include the key in errors to help identify the location of the failure
        errors = {}
        values = {}
        for key, value in data.items():
            key_or_error = self.key_serializer.from_data(key)
            if isinstance(key_or_error, DeserializationFailure):
                errors[key] = key_or_error.error
                continue
            else:
                output_key = key_or_error.value

            value_or_error = self.value_serializer.from_data(value)
            if isinstance(value_or_error, DeserializationFailure):
                # Use original keys for errors
                errors[key] = value_or_error.error
            else:
                # Use deserialized keys for values
                values[output_key] = value_or_error.value

        if len(errors) > 0:
            return DeserializationFailure(errors)
        else:
            return DeserializationSuccess(values)

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
