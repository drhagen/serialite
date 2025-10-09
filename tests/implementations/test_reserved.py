import pytest

from serialite import (
    Errors,
    Failure,
    ReservedSerializer,
    StringSerializer,
    Success,
    ValidationError,
)

reserved_serializer = ReservedSerializer(StringSerializer(), reserved={"false", "true"})


def test_valid_inputs():
    data = "foo"
    assert reserved_serializer.from_data(data) == Success(data)
    assert reserved_serializer.to_data(data) == data


def test_reserved_inputs():
    data = "true"
    assert reserved_serializer.from_data(data) == Failure(
        Errors.one(ValidationError("Reserved value: 'true'"))
    )


def test_to_data_failure():
    with pytest.raises(ValueError):
        _ = reserved_serializer.to_data("true")
