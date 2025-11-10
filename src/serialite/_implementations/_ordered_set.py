__all__ = ["OrderedSetSerializer"]

from typing import Generic, TypeVar

from ordered_set import OrderedSet

from .._base import Serializer
from .._errors import Errors
from .._result import Failure, Result, Success
from .._stable_set import StableSet
from .._type_errors import ExpectedListError
from ._set import DuplicatedValueError

Element = TypeVar("Element")


class OrderedSetSerializer(Generic[Element], Serializer[OrderedSet[Element]]):
    def __init__(self, element_serializer: Serializer[Element]):
        self.element_serializer = element_serializer

    def from_data(self, data) -> Result[OrderedSet[Element]]:
        # Return early if the data isn't even a list
        if not isinstance(data, list):
            return Failure(Errors.one(ExpectedListError(data)))

        # Validate values
        errors = Errors()
        values = OrderedSet()
        for i, value in enumerate(data):
            match self.element_serializer.from_data(value):
                case Failure(error):
                    errors.extend(error, location=[i])
                case Success(value):
                    if value in values:
                        errors.add(DuplicatedValueError(value), location=[i])
                    else:
                        values.add(value)

        if not errors.is_empty():
            return Failure(errors)
        else:
            return Success(values)

    def to_data(self, value: OrderedSet[Element]):
        if not isinstance(value, OrderedSet):
            raise ValueError(f"Not an OrderedSet: {value!r}")

        return [self.element_serializer.to_data(item) for item in value]

    def collect_openapi_models(
        self, parent_models: StableSet[Serializer]
    ) -> StableSet[Serializer]:
        return self.element_serializer.collect_openapi_models(parent_models)

    def to_openapi_schema(self, refs: dict[Serializer, str], force: bool = False):
        return {"type": "array", "items": self.element_serializer.to_openapi_schema(refs)}
