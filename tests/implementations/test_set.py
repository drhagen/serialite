import pytest

from serialite import (
    DuplicatedValueError,
    Errors,
    ExpectedFloatError,
    ExpectedListError,
    Failure,
    FloatSerializer,
    SetSerializer,
    Success,
)

set_serializer = SetSerializer(FloatSerializer())


def test_valid_inputs():
    data = [12.3, 15.5, 16.0]
    value = {12.3, 15.5, 16.0}

    assert set_serializer.from_data(data) == Success(value)
    assert sorted(set_serializer.to_data(value)) == sorted(data)


def test_from_data_failure_top_level():
    data = 12.5
    assert set_serializer.from_data(data) == Failure(Errors.one(ExpectedListError(data)))


def test_from_data_failure_element():
    data = ["str1", 15.5, "str2"]
    actual = set_serializer.from_data(data)
    expected = Errors()
    expected.add(ExpectedFloatError("str1"), location=[0])
    expected.add(ExpectedFloatError("str2"), location=[2])
    assert actual == Failure(expected)


def test_from_data_failure_uniqueness():
    data = [12.3, 15.5, 16.0, 12.3]
    actual = set_serializer.from_data(data)
    expected = Errors.one(
        DuplicatedValueError(12.3),
        location=[3],
    )
    assert actual == Failure(expected)


def test_to_data_failure_top_level():
    with pytest.raises(ValueError):
        _ = set_serializer.to_data(12.5)


def test_to_data_failure_element():
    with pytest.raises(ValueError):
        _ = set_serializer.to_data({12.5, "a"})


def test_duplicate_error_to_data_and_to_string():
    dup = DuplicatedValueError(12.3)
    assert dup.to_data() == {"duplicate": 12.3}
    assert str(dup) == "Expected a list of unique values, but got this duplicate 12.3"
