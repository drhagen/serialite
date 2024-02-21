import pytest

from serialite import (
    DeserializationFailure,
    DeserializationSuccess,
    FloatSerializer,
    SetSerializer,
)

set_serializer = SetSerializer(FloatSerializer())


def test_valid_inputs():
    data = [12.3, 15.5, 16.0]
    value = {12.3, 15.5, 16.0}

    assert set_serializer.from_data(data) == DeserializationSuccess(value)
    assert sorted(set_serializer.to_data(value)) == sorted(data)


def test_from_data_failure_top_level():
    data = 12.5
    assert set_serializer.from_data(data) == DeserializationFailure("Not a valid list: 12.5")


def test_from_data_failure_element():
    data = ["str1", 15.5, "str2"]
    actual = set_serializer.from_data(data)
    expected_msg = {"0": "Not a valid float: 'str1'", "2": "Not a valid float: 'str2'"}
    assert actual == DeserializationFailure(expected_msg)


def test_from_data_failure_uniqueness():
    data = [12.3, 15.5, 16.0, 12.3]
    actual = set_serializer.from_data(data)
    expected_msg = {"3": "Duplicated value found: 12.3. Expected a list of unique values."}
    assert actual == DeserializationFailure(expected_msg)


def test_to_data_failure_top_level():
    with pytest.raises(ValueError):
        _ = set_serializer.to_data(12.5)


def test_to_data_failure_element():
    with pytest.raises(ValueError):
        _ = set_serializer.to_data({12.5, "a"})
