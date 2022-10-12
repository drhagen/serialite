import pytest

from serialite import (
    DeserializationFailure,
    DeserializationSuccess,
    FloatSerializer,
    ListSerializer,
)

list_serializer = ListSerializer(FloatSerializer())


def test_valid_inputs():
    data = [12.3, 15.5, 16.0]

    assert list_serializer.from_data(data) == DeserializationSuccess(data)
    assert list_serializer.to_data(data) == data


def test_from_data_failure_top_level():
    data = 12.5
    assert list_serializer.from_data(data) == DeserializationFailure("Not a valid list: 12.5")


def test_from_data_failure_element():
    data = ["str1", 15.5, "str2"]
    actual = list_serializer.from_data(data)
    expected_msg = {"0": "Not a valid float: 'str1'", "2": "Not a valid float: 'str2'"}
    assert actual == DeserializationFailure(expected_msg)


def test_to_data_failure_top_level():
    with pytest.raises(ValueError):
        _ = list_serializer.to_data(12.5)


def test_to_data_failure_element():
    with pytest.raises(ValueError):
        _ = list_serializer.to_data([12.5, "a"])
