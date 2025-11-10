__all__ = ["TupleLengthError", "TupleSerializer"]

from dataclasses import dataclass
from typing import Any, Generic
from typing_extensions import TypeVarTuple, Unpack

from .._base import Serializer
from .._decorators import serializable
from .._errors import Errors
from .._result import Failure, Result, Success
from .._stable_set import StableSet
from .._type_errors import ExpectedListError

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

    def from_data(self, data) -> Result[tuple[Unpack[TupleArguments]]]:
        # Return early if the data isn't even a list
        if not isinstance(data, list):
            return Failure(Errors.one(ExpectedListError(data)))

        # Return early if the list is not the correct length
        if len(data) != len(self.element_serializers):
            return Failure(
                Errors.one(TupleLengthError(len(data), len(self.element_serializers), data))
            )

        # Validate values
        errors = Errors()
        values = []
        for i, (item, serializer) in enumerate(zip(data, self.element_serializers, strict=True)):
            match serializer.from_data(item):
                case Failure(error):
                    errors.extend(error, location=[i])
                case Success(value):
                    values.append(value)

        if not errors.is_empty():
            return Failure(errors)
        else:
            return Success(tuple(values))

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


@serializable
@dataclass(frozen=True, slots=True)
class TupleLengthError(Exception):
    actual_length: int
    expected_length: int
    actual: list[Any]

    def __str__(self) -> str:
        return f"Expected tuple of length {self.expected_length}, but got length {len(self.actual)} tuple {self.actual!r}"
