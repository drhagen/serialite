import pytest

from serialite import (
    Errors,
    ExpectedStringError,
    Failure,
    RegexMismatchError,
    StringSerializer,
    Success,
)

string_serializer = StringSerializer()
regex_serializer = StringSerializer(r"[a-zA-Z]+")


def test_valid_inputs():
    data = "Hello World"

    assert string_serializer.from_data(data) == Success(data)
    assert string_serializer.to_data(data) == data


def test_from_data_failure():
    data = 12.5
    assert string_serializer.from_data(data) == Failure(Errors.one(ExpectedStringError(data)))


def test_to_data_failure():
    with pytest.raises(ValueError):
        _ = string_serializer.to_data(12.5)


def test_regex():
    assert regex_serializer.from_data("foo") == Success("foo")
    assert regex_serializer.to_data("foo") == "foo"
    assert regex_serializer.from_data("foo ") == Failure(
        Errors.one(RegexMismatchError(r"[a-zA-Z]+", "foo "))
    )
    assert regex_serializer.from_data(" foo") == Failure(
        Errors.one(RegexMismatchError(r"[a-zA-Z]+", " foo"))
    )
    with pytest.raises(ValueError):
        _ = regex_serializer.to_data("foo*")


def test_error_to_data_and_to_string():
    err = ExpectedStringError(1)
    assert err.to_data() == {"actual": 1}
    assert str(err) == "Expected string, but got 1"


def test_regex_error_to_data_and_to_string():
    regex_err = RegexMismatchError(r"[a-zA-Z]+", " foo")
    assert regex_err.to_data() == {"pattern": r"[a-zA-Z]+", "actual": " foo"}
    assert str(regex_err) == "Expected string matching '[a-zA-Z]+', but got ' foo'"
