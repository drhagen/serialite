import pytest

from serialite import (
    Errors,
    Failure,
    FloatSerializer,
    StringSerializer,
    Success,
    TupleSerializer,
    ValidationError,
)

tuple_serializer = TupleSerializer(FloatSerializer(), StringSerializer())


def test_valid_inputs():
    data = [12.3, "foo"]
    value = tuple(data)

    assert tuple_serializer.from_data(data) == Success(value)
    assert tuple_serializer.to_data(value) == data


def test_from_data_failure_wrong_type():
    data = 12.5
    assert tuple_serializer.from_data(data) == Failure(
        Errors.one(ValidationError("Not a valid list: 12.5"))
    )


def test_from_data_failure_wrong_length():
    data = [12.5]
    assert tuple_serializer.from_data(data) == Failure(
        Errors.one(ValidationError("Has 1 elements, not 2: [12.5]"))
    )


def test_from_data_failure_element():
    data = ["12.3", "str2"]
    actual = tuple_serializer.from_data(data)
    expected = Errors.one(ValidationError("Not a valid float: '12.3'"), location=[0])
    assert actual == Failure(expected)


def test_to_data_failure_wrong_type():
    with pytest.raises(ValueError):
        _ = tuple_serializer.to_data(12.5)


def test_to_data_failure_wrong_length():
    with pytest.raises(ValueError):
        _ = tuple_serializer.to_data([12.3, "str2", "str3"])


def test_to_data_failure_element():
    with pytest.raises(ValueError):
        _ = tuple_serializer.to_data(["12.5", "a"])
