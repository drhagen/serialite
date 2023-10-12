from math import inf, nan

import pytest

from serialite import DeserializationFailure, DeserializationSuccess, FloatSerializer

float_serializer = FloatSerializer()


@pytest.mark.parametrize("data", [12, 15.34])
def test_valid_inputs(data):
    actual = float_serializer.from_data(data)
    expected = DeserializationSuccess(data)
    assert actual == expected
    assert isinstance(actual.or_die(), float)  # Verify actual result is a float (not int)
    assert float_serializer.to_data(data) == data


@pytest.mark.parametrize(("data", "value"), [("nan", nan), ("inf", inf), ("-inf", -inf)])
def test_nonfinite_inputs(data, value):
    nonfinite_float_serializer = FloatSerializer(
        nan_values=("nan",), inf_values=("inf",), neg_inf_values=("-inf",)
    )

    assert nonfinite_float_serializer.from_data(data) == DeserializationSuccess(value)
    assert nonfinite_float_serializer.to_data(value) == data


def test_from_data_failure():
    data = "12.5"
    assert float_serializer.from_data(data) == DeserializationFailure("Not a valid float: '12.5'")


def test_to_data_failure():
    with pytest.raises(ValueError):
        _ = float_serializer.to_data("12.5")
