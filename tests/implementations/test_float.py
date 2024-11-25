from math import inf, isnan, nan

import pytest

from serialite import DeserializationFailure, DeserializationSuccess, FloatSerializer

float_serializer = FloatSerializer()


def float_equal(a, b):
    if isnan(a) and isnan(b):
        return True
    else:
        return a == b


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

    # Do not use equality because DeserializationSuccess(nan) != DeserializationSuccess(nan)
    actual = nonfinite_float_serializer.from_data(data)
    assert isinstance(actual, DeserializationSuccess)
    assert float_equal(actual.or_die(), value)
    assert nonfinite_float_serializer.to_data(value) == data


def test_from_data_failure():
    data = "12.5"
    assert float_serializer.from_data(data) == DeserializationFailure("Not a valid float: '12.5'")


def test_to_data_failure():
    with pytest.raises(ValueError):
        _ = float_serializer.to_data("12.5")
