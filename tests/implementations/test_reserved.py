import pytest

from serialite import (
    DeserializationFailure,
    DeserializationSuccess,
    ReservedSerializer,
    StringSerializer,
)

reserved_serializer = ReservedSerializer(StringSerializer(), reserved={"false", "true"})


def test_valid_inputs():
    data = "foo"
    assert reserved_serializer.from_data(data) == DeserializationSuccess(data)
    assert reserved_serializer.to_data(data) == data


def test_reserved_inputs():
    data = "true"
    assert reserved_serializer.from_data(data) == DeserializationFailure("Reserved value: 'true'")


def test_to_data_failure():
    with pytest.raises(ValueError):
        _ = reserved_serializer.to_data("true")
