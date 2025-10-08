from math import inf, isnan, nan

import pytest

from serialite import Errors, Failure, FloatSerializer, Success, ValidationError

float_serializer = FloatSerializer()


def float_equal(a, b):
    if isnan(a) and isnan(b):
        return True
    else:
        return a == b


@pytest.mark.parametrize("data", [12, 15.34])
def test_valid_inputs(data):
    actual = float_serializer.from_data(data)
    expected = Success(data)
    assert actual == expected
    assert isinstance(actual.unwrap(), float)  # Verify actual result is a float (not int)
    assert float_serializer.to_data(data) == data


@pytest.mark.parametrize(("data", "value"), [("nan", nan), ("inf", inf), ("-inf", -inf)])
def test_nonfinite_inputs(data, value):
    nonfinite_float_serializer = FloatSerializer(
        nan_values=("nan",), inf_values=("inf",), neg_inf_values=("-inf",)
    )

    # Do not use equality because Success(nan) != Success(nan)
    actual = nonfinite_float_serializer.from_data(data)
    assert isinstance(actual, Success)
    assert float_equal(actual.unwrap(), value)
    assert nonfinite_float_serializer.to_data(value) == data


def test_from_data_failure():
    data = "12.5"
    assert float_serializer.from_data(data) == Failure(
        Errors.one(ValidationError("Not a valid float: '12.5'"))
    )


def test_to_data_failure():
    with pytest.raises(ValueError):
        _ = float_serializer.to_data("12.5")
