__all__ = ["FloatSerializer"]

from math import inf, isnan, nan
from typing import Any, Sequence

from .._base import Serializer
from .._numeric_check import is_real
from .._result import DeserializationFailure, DeserializationResult, DeserializationSuccess


class FloatSerializer(Serializer[float]):
    def __init__(
        self,
        nan_values: Sequence[Any] = (nan,),
        inf_values: Sequence[Any] = (inf,),
        neg_inf_values: Sequence[Any] = (-inf,),
    ):
        self.nan_values = nan_values
        self.inf_values = inf_values
        self.neg_inf_values = neg_inf_values

    def from_data(self, data) -> DeserializationResult[float]:
        if data in self.nan_values:
            return DeserializationSuccess(nan)
        elif data in self.inf_values:
            return DeserializationSuccess(inf)
        elif data in self.neg_inf_values:
            return DeserializationSuccess(-inf)
        elif is_real(data):
            return DeserializationSuccess(float(data))
        else:
            return DeserializationFailure(f"Not a valid float: {data!r}")

    def to_data(self, value: float):
        if not is_real(value):
            raise ValueError(f"Not a float: {value!r}")

        if isnan(value):
            return self.nan_values[0]
        elif value == inf:
            return self.inf_values[0]
        elif value == -inf:
            return self.neg_inf_values[0]
        else:
            return float(value)

    def to_openapi_schema(self, refs: dict[Serializer, str], force: bool = False):
        return {"type": "number"}
