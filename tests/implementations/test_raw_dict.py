import pytest

from serialite import (
    DeserializationFailure,
    DeserializationSuccess,
    FloatSerializer,
    RawDictSerializer,
    ReservedSerializer,
    StringSerializer,
)

raw_dict_serializer = RawDictSerializer(FloatSerializer())
raw_dict_serializer_with_key = RawDictSerializer(
    key_serializer=ReservedSerializer(StringSerializer(), reserved={"null"}),
    value_serializer=FloatSerializer(),
)


def test_valid_inputs():
    data = {"a": 12.3, "b": 15.5, "c": 16.0}

    assert raw_dict_serializer.from_data(data) == DeserializationSuccess(data)
    assert raw_dict_serializer.to_data(data) == data


def test_from_data_failure_not_a_dict():
    data = 12.5
    assert raw_dict_serializer.from_data(data) == DeserializationFailure("Not a valid dict: 12.5")


def test_from_data_failure_value():
    data = {"a": "str1", "b": 15.5, "c": "str2"}
    actual = raw_dict_serializer.from_data(data)
    expected_msg = {"a": "Not a valid float: 'str1'", "c": "Not a valid float: 'str2'"}
    assert actual == DeserializationFailure(expected_msg)


def test_to_data_failure():
    with pytest.raises(ValueError):
        _ = raw_dict_serializer.to_data(12.3)


def test_key_serializer_valid_inputs():
    data = {"a": 12.3, "b": 15.5, "c": 16.0}

    assert raw_dict_serializer_with_key.from_data(data) == DeserializationSuccess(data)
    assert raw_dict_serializer_with_key.to_data(data) == data


def test_key_serializer_bad_inputs():
    data = {"a": 12.3, "null": 15.5, "c": 16.0}

    assert raw_dict_serializer_with_key.from_data(data) == DeserializationFailure(
        {"null": "Reserved value: 'null'"}
    )
    with pytest.raises(ValueError):
        _ = raw_dict_serializer_with_key.to_data(data)
