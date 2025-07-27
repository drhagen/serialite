__all__ = ["TupleSerializer"]

from typing import Generic
from typing_extensions import TypeVarTuple, Unpack

from .._base import Serializer
from .._result import DeserializationFailure, DeserializationResult, DeserializationSuccess
from .._stable_set import StableSet

TupleArguments = TypeVarTuple("TupleArguments")

try:
    from numpy import ndarray
except ImportError:
    # Class that will never pass an isinstance check
    class ndarray:  # noqa: N801
        pass


class TupleSerializer(Generic[Unpack[TupleArguments]], Serializer[tuple[Unpack[TupleArguments]]]):
    def __init__(self, *element_serializers: Unpack[TupleArguments]):
        self.element_serializers = element_serializers

    def from_data(self, data) -> DeserializationResult[tuple[Unpack[TupleArguments]]]:
        # Return early if the data isn't even a list
        if not isinstance(data, list):
            return DeserializationFailure(f"Not a valid list: {data!r}")

        # Return early if the list is not the correct length
        if len(data) != len(self.element_serializers):
            return DeserializationFailure(
                f"Has {len(data)} elements, not {len(self.element_serializers)}: {data!r}"
            )

        # Validate values
        errors = {}
        values = []
        for i, (item, serializer) in enumerate(zip(data, self.element_serializers, strict=True)):
            value_or_error = serializer.from_data(item)
            if isinstance(value_or_error, DeserializationFailure):
                errors[str(i)] = value_or_error.error
            else:
                values.append(value_or_error.value)

        if len(errors) > 0:
            return DeserializationFailure(errors)
        else:
            return DeserializationSuccess(tuple(values))

    def to_data(self, value: tuple[Unpack[TupleArguments]]):
        # Accept an ndarray or list for ergonomics
        if not isinstance(value, (tuple, list, ndarray)):
            raise ValueError(f"Not a tuple: {value!r}")
        if len(value) != len(self.element_serializers):
            raise ValueError(
                f"Has {len(value)} elements, not {len(self.element_serializers)}: {value}"
            )

        return [
            serializer.to_data(item)
            for item, serializer in zip(value, self.element_serializers, strict=True)
        ]

    def collect_openapi_models(
        self, parent_models: StableSet[Serializer]
    ) -> StableSet[Serializer]:
        models = StableSet()
        for serializer in self.element_serializers:
            models |= serializer.collect_openapi_models(parent_models)
        return models

    def to_openapi_schema(self, refs: dict[Serializer, str], force: bool = False):
        n = len(self.element_serializers)
        return {
            "type": "array",
            "prefixItems": [
                serializer.to_openapi_schema(refs) for serializer in self.element_serializers
            ],
            "minItems": n,
            "maxItems": n,
        }
