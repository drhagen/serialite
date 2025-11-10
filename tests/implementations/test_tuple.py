import pytest

from serialite import (
    Errors,
    ExpectedFloatError,
    ExpectedListError,
    Failure,
    FloatSerializer,
    StringSerializer,
    Success,
    TupleLengthError,
    TupleSerializer,
)

tuple_serializer = TupleSerializer(FloatSerializer(), StringSerializer())


def test_valid_inputs():
    data = [12.3, "foo"]
    value = tuple(data)

    assert tuple_serializer.from_data(data) == Success(value)
    assert tuple_serializer.to_data(value) == data


def test_from_data_failure_wrong_type():
    data = 12.5
    assert tuple_serializer.from_data(data) == Failure(Errors.one(ExpectedListError(data)))


def test_from_data_failure_wrong_length():
    data = [12.5]
    assert tuple_serializer.from_data(data) == Failure(Errors.one(TupleLengthError(1, 2, [12.5])))


def test_from_data_failure_element():
    data = ["12.3", "str2"]
    actual = tuple_serializer.from_data(data)
    expected = Errors.one(ExpectedFloatError("12.3"), location=[0])
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


def test_tuple_length_error_to_data_and_to_string():
    e = TupleLengthError(1, 2, [12.5])
    assert e.to_data() == {"actual_length": 1, "expected_length": 2, "actual": [12.5]}
    assert str(e) == "Expected tuple of length 2, but got length 1 tuple [12.5]"
