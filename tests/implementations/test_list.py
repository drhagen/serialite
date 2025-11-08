import pytest

from serialite import (
    Errors,
    ExpectedFloatError,
    Failure,
    FloatSerializer,
    ListSerializer,
    Success,
    ValidationError,
)

list_serializer = ListSerializer(FloatSerializer())


def test_valid_inputs():
    data = [12.3, 15.5, 16.0]

    assert list_serializer.from_data(data) == Success(data)
    assert list_serializer.to_data(data) == data


def test_from_data_failure_top_level():
    data = 12.5
    assert list_serializer.from_data(data) == Failure(
        Errors.one(ValidationError("Not a valid list: 12.5"))
    )


def test_from_data_failure_element():
    data = ["str1", 15.5, "str2"]
    actual = list_serializer.from_data(data)
    expected = Errors()
    expected.add(ExpectedFloatError("str1"), location=[0])
    expected.add(ExpectedFloatError("str2"), location=[2])
    assert actual == Failure(expected)


def test_to_data_failure_top_level():
    with pytest.raises(ValueError):
        _ = list_serializer.to_data(12.5)


def test_to_data_failure_element():
    with pytest.raises(ValueError):
        _ = list_serializer.to_data([12.5, "a"])
