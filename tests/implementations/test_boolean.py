import pytest

from serialite import BooleanSerializer, Errors, Failure, Success, ValidationError

boolean_serializer = BooleanSerializer()


@pytest.mark.parametrize("data", [True, False])
def test_valid_inputs(data):
    assert boolean_serializer.from_data(data) == Success(data)
    assert boolean_serializer.to_data(data) == data


@pytest.mark.parametrize("data", ["maybe", "true"])
def test_from_data_failure(data):
    actual = boolean_serializer.from_data(data)
    expected = Failure(Errors.one(ValidationError(f"Not a valid boolean: {data!r}")))
    assert actual == expected


def test_to_data_failure():
    with pytest.raises(ValueError):
        _ = boolean_serializer.to_data("true")
