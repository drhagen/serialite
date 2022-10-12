__all__ = ["ListSerializer"]

from typing import Generic, TypeVar

from .._base import Serializer
from .._result import DeserializationFailure, DeserializationResult, DeserializationSuccess
from .._stable_set import StableSet

Element = TypeVar("Element")

try:
    from numpy import ndarray
except ImportError:
    # Class that will never pass an isinstance check
    class ndarray:  # noqa: N801
        pass


class ListSerializer(Generic[Element], Serializer[list[Element]]):
    def __init__(self, element_serializer: Serializer[Element]):
        self.element_serializer = element_serializer

    def from_data(self, data) -> DeserializationResult[list[Element]]:
        # Return early if the data isn't even a list
        if not isinstance(data, list):
            return DeserializationFailure(f"Not a valid list: {data!r}")

        # Validate values
        errors = {}
        values = []
        for i, value in enumerate(data):
            value_or_error = self.element_serializer.from_data(value)
            if isinstance(value_or_error, DeserializationFailure):
                errors[str(i)] = value_or_error.error
            else:
                values.append(value_or_error.value)

        if len(errors) > 0:
            return DeserializationFailure(errors)
        else:
            return DeserializationSuccess(values)

    def to_data(self, value: list[Element]):
        # Accept an ndarray also for ergonomics
        if not isinstance(value, (list, ndarray)):
            raise ValueError(f"Not a list: {value!r}")

        return [self.element_serializer.to_data(item) for item in value]

    def collect_openapi_models(
        self, parent_models: StableSet[Serializer]
    ) -> StableSet[Serializer]:
        return self.element_serializer.collect_openapi_models(parent_models)

    def to_openapi_schema(self, refs: dict[Serializer, str], force: bool = False):
        return {"type": "array", "items": self.element_serializer.to_openapi_schema(refs)}
