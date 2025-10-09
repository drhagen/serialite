import pytest

from serialite import (
    BooleanSerializer,
    Failure,
    FloatSerializer,
    IntegerSerializer,
    Success,
    TryUnionSerializer,
)

try_union_serializer = TryUnionSerializer(
    FloatSerializer(), IntegerSerializer(), BooleanSerializer()
)


@pytest.mark.parametrize("data", [True, 12, 13.5])
def test_valid_inputs(data):
    assert try_union_serializer.from_data(data) == Success(data)
    assert try_union_serializer.to_data(data) == data


def test_from_data_failure():
    # The error message is too complex to bother verifying
    data = "Hello!"
    actual = try_union_serializer.from_data(data)
    assert isinstance(actual, Failure)


def test_to_data_failure():
    with pytest.raises(ValueError):
        _ = try_union_serializer.to_data("invalid")
