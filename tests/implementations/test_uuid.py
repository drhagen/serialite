from uuid import UUID

import pytest

from serialite import DeserializationFailure, DeserializationSuccess, UuidSerializer

uuid_serializer = UuidSerializer()


def test_valid_inputs():
    data = "00112233-4455-6677-8899-aabbccddeeff"
    value = UUID(data)

    assert uuid_serializer.from_data(data) == DeserializationSuccess(value)
    assert uuid_serializer.to_data(value) == data


@pytest.mark.parametrize("data", [12.5, "Hello World"])
def test_from_data_failure(data):
    assert uuid_serializer.from_data(data) == DeserializationFailure(f"Not a valid UUID: {data!r}")


def test_to_data_failure():
    with pytest.raises(ValueError):
        # string instead of UUID object
        _ = uuid_serializer.to_data("00112233-4455-6677-8899-aabbccddeeff")
