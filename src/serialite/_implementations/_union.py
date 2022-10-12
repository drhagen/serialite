__all__ = ["TryUnionSerializer", "OptionalSerializer"]

from typing import Generic, TypeVar

from .._base import Serializer
from .._result import DeserializationFailure, DeserializationResult, DeserializationSuccess
from .._stable_set import StableSet

Element = TypeVar("Element")


class TryUnionSerializer(Serializer):
    def __init__(self, *serializers: Serializer):
        self.serializers = serializers

    def from_data(self, data):
        # Try each possibility and return the first value that succeeds,
        # otherwise return both errors
        errors = {}
        for serializer in self.serializers:
            value_or_error = serializer.from_data(data)
            if isinstance(value_or_error, DeserializationSuccess):
                return value_or_error
            else:
                errors[str(serializer)] = value_or_error.error

        return DeserializationFailure(errors)

    def to_data(self, value):
        # Try each possibility. It should not be possible for both to fail.
        errors = []
        for serializer in self.serializers:
            try:
                return serializer.to_data(value)
            except Exception as e:
                errors.append(e)

        raise ValueError(
            "All available serializers failed: " + ", ".join(map(str, self.serializers)), errors
        )

    def collect_openapi_models(
        self, parent_models: StableSet[Serializer]
    ) -> StableSet[Serializer]:
        models = StableSet()
        for serializer in self.serializers:
            models |= serializer.collect_openapi_models(parent_models)
        return models

    def to_openapi_schema(self, refs: dict[Serializer, str], force: bool = False):
        return {
            "oneOf": [serializer.to_openapi_schema(refs) for serializer in self.serializers],
        }


class OptionalSerializer(Generic[Element], Serializer[Element | None]):
    def __init__(self, element_serializer: Serializer[Element]):
        self.element_serializer = element_serializer

    def from_data(self, data) -> DeserializationResult[Element | None]:
        if data is None:
            return DeserializationSuccess(None)
        else:
            return self.element_serializer.from_data(data)

    def to_data(self, value: Element | None):
        if value is None:
            return None
        else:
            return self.element_serializer.to_data(value)

    def collect_openapi_models(
        self, parent_models: StableSet[Serializer]
    ) -> StableSet[Serializer]:
        return self.element_serializer.collect_openapi_models(parent_models)

    def to_openapi_schema(self, refs: dict[Serializer, str], force: bool = False):
        return self.element_serializer.to_openapi_schema(refs) | {"nullable": True}
