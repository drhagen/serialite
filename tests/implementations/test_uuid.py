from uuid import UUID

import pytest

from serialite import (
    Errors,
    ExpectedStringError,
    Failure,
    InvalidUuidError,
    Success,
    UuidSerializer,
)

uuid_serializer = UuidSerializer()


def test_valid_inputs():
    data = "00112233-4455-6677-8899-aabbccddeeff"
    value = UUID(data)

    assert uuid_serializer.from_data(data) == Success(value)
    assert uuid_serializer.to_data(value) == data


def test_from_data_failure_non_string():
    data = 12.5
    assert uuid_serializer.from_data(data) == Failure(Errors.one(ExpectedStringError(data)))


def test_from_data_failure_invalid_string():
    data = "Hello World"
    assert uuid_serializer.from_data(data) == Failure(Errors.one(InvalidUuidError(data)))


def test_to_data_failure():
    with pytest.raises(ValueError):
        # string instead of UUID object
        _ = uuid_serializer.to_data("00112233-4455-6677-8899-aabbccddeeff")


def test_uuid_error_to_data_and_to_string():
    e = InvalidUuidError("Hello World")
    assert e.to_data() == {"actual": "Hello World"}
    assert str(e) == "Expected UUID, but got 'Hello World'"
