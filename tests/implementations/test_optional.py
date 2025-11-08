import pytest

from serialite import (
    Errors,
    ExpectedFloatError,
    Failure,
    FloatSerializer,
    OptionalSerializer,
    Success,
)

optional_serializer = OptionalSerializer(FloatSerializer())


@pytest.mark.parametrize("data", [12.5, None])
def test_valid_inputs(data):
    assert optional_serializer.from_data(data) == Success(data)
    assert optional_serializer.to_data(data) == data


def test_from_data_failure():
    data = "12.5"
    assert optional_serializer.from_data(data) == Failure(Errors.one(ExpectedFloatError("12.5")))


def test_to_data_failure():
    with pytest.raises(ValueError):
        _ = optional_serializer.to_data("12.5")
