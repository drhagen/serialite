import pytest

from serialite import Errors, Failure, LiteralSerializer, Success, ValidationError

literal_serializer = LiteralSerializer("none", 1, 2, 3)


@pytest.mark.parametrize("data", ["none", 2])
def test_valid_inputs(data):
    assert literal_serializer.from_data(data) == Success(data)
    assert literal_serializer.to_data(data) == data


def test_invalid_input():
    data = "invalid"

    assert literal_serializer.from_data(data) == Failure(
        Errors.one(ValidationError("Not one of ['none', 1, 2, 3]: 'invalid'"))
    )
    with pytest.raises(ValueError):
        _ = literal_serializer.to_data(data)
