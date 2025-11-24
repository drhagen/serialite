__all__ = ["ListSerializer"]

from .._base import Serializer
from .._errors import Errors
from .._openapi import is_openapi_component
from .._result import Failure, Result, Success
from .._type_errors import ExpectedListError

try:
    from numpy import ndarray
except ImportError:
    # Class that will never pass an isinstance check
    class ndarray:  # noqa: N801
        pass


class ListSerializer[Element](Serializer[list[Element]]):
    def __init__(self, element_serializer: Serializer[Element]):
        self.element_serializer = element_serializer

    def from_data(self, data) -> Result[list[Element]]:
        # Return early if the data isn't even a list
        if not isinstance(data, list):
            return Failure(Errors.one(ExpectedListError(data)))

        # Validate values
        errors = Errors()
        values = []
        for i, value in enumerate(data):
            match self.element_serializer.from_data(value):
                case Failure(error):
                    errors.extend(error, location=[i])
                case Success(value):
                    values.append(value)

        if not errors.is_empty():
            return Failure(errors)
        else:
            return Success(values)

    def to_data(self, value: list[Element]):
        # Accept an ndarray also for ergonomics
        if not isinstance(value, (list, ndarray)):
            raise ValueError(f"Not a list: {value!r}")

        return [self.element_serializer.to_data(item) for item in value]

    def child_components(self):
        if is_openapi_component(self.element_serializer):
            return {"element": self.element_serializer}
        else:
            return {}

    def to_openapi_schema(self, force: bool = False):
        return {"type": "array", "items": self.element_serializer.to_openapi_schema()}
