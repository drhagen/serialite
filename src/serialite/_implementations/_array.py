__all__ = ["ArraySerializer"]

import numpy as np

from .._base import Serializer
from .._dispatcher import serializer
from .._openapi import is_openapi_component
from .._result import Failure, Result, Success
from ._list import ListSerializer


class ArraySerializer[Element](Serializer[np.ndarray]):
    def __init__(
        self,
        element_serializer: Serializer[Element] | None = None,
        dtype: type[Element] | None = None,
    ):
        if element_serializer is None and dtype is None:
            raise TypeError("Either element_serializer or dtype must be specified.")

        if element_serializer is None:
            element_serializer = serializer(dtype)

        self.list_serializer = ListSerializer(element_serializer)
        self.element_serializer = element_serializer
        self.dtype = dtype

    def from_data(self, data) -> Result[np.ndarray]:
        match self.list_serializer.from_data(data):
            case Failure(error):
                return Failure(error)
            case Success(value):
                return Success(np.array(value, dtype=self.dtype))

    def to_data(self, value: np.ndarray):
        if not isinstance(value, np.ndarray):
            raise ValueError(f"Not an array: {value!r}")

        return self.list_serializer.to_data(value.tolist())

    def child_components(self):
        if is_openapi_component(self.element_serializer):
            return {"element": self.element_serializer}
        else:
            return {}

    def to_openapi_schema(self, force: bool = False):
        return {"type": "array", "items": self.element_serializer.to_openapi_schema()}
