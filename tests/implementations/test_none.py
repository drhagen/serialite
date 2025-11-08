import pytest

from serialite import (
    Errors,
    ExpectedNullError,
    Failure,
    NoneSerializer,
    Success,
)

none_serializer = NoneSerializer()


def test_valid_inputs():
    data = None

    assert none_serializer.from_data(data) == Success(data)
    assert none_serializer.to_data(data) == data


@pytest.mark.parametrize("data", ["none", False, {}])
def test_from_data_failure(data):
    data = "none"
    assert none_serializer.from_data(data) == Failure(Errors.one(ExpectedNullError(data)))


def test_to_data_failure():
    with pytest.raises(ValueError):
        _ = none_serializer.to_data(False)
