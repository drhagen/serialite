__all__ = ["ArraySerializer"]

from typing import Generic, TypeVar

import numpy as np

from .._base import Serializer
from .._dispatcher import serializer
from .._result import DeserializationFailure, DeserializationResult, DeserializationSuccess
from .._stable_set import StableSet
from ._list import ListSerializer

Element = TypeVar("Element")


class ArraySerializer(Generic[Element], Serializer[np.ndarray]):
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

    def from_data(self, data) -> DeserializationResult[np.ndarray]:
        elements = self.list_serializer.from_data(data)

        if isinstance(elements, DeserializationFailure):
            return elements
        else:
            return DeserializationSuccess(np.array(elements.value, dtype=self.dtype))

    def to_data(self, value: np.ndarray):
        if not isinstance(value, np.ndarray):
            raise ValueError(f"Not an array: {value!r}")

        return self.list_serializer.to_data(value.tolist())

    def collect_openapi_models(
        self, parent_models: StableSet[Serializer]
    ) -> StableSet[Serializer]:
        return self.element_serializer.collect_openapi_models(parent_models)

    def to_openapi_schema(self, refs: dict[Serializer, str], force: bool = False):
        return {"type": "array", "items": self.element_serializer.to_openapi_schema(refs)}
