import pytest

from serialite import DeserializationFailure, DeserializationSuccess, NoneSerializer

none_serializer = NoneSerializer()


def test_valid_inputs():
    data = None

    assert none_serializer.from_data(data) == DeserializationSuccess(data)
    assert none_serializer.to_data(data) == data


@pytest.mark.parametrize("data", ["none", False, {}])
def test_from_data_failure(data):
    data = "none"
    assert none_serializer.from_data(data) == DeserializationFailure(f"Not a null: {data!r}")


def test_to_data_failure():
    with pytest.raises(ValueError):
        _ = none_serializer.to_data(False)
