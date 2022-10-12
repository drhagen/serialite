import pytest

from serialite import DeserializationFailure, DeserializationSuccess, StringSerializer

string_serializer = StringSerializer()
regex_serializer = StringSerializer(r"[a-zA-Z]+")


def test_valid_inputs():
    data = "Hello World"

    assert string_serializer.from_data(data) == DeserializationSuccess(data)
    assert string_serializer.to_data(data) == data


def test_from_data_failure():
    data = 12.5
    assert string_serializer.from_data(data) == DeserializationFailure("Not a valid string: 12.5")


def test_to_data_failure():
    with pytest.raises(ValueError):
        _ = string_serializer.to_data(12.5)


def test_regex():
    assert regex_serializer.from_data("foo") == DeserializationSuccess("foo")
    assert regex_serializer.to_data("foo") == "foo"
    assert regex_serializer.from_data("foo ") == DeserializationFailure(
        "Does not match regex r'[a-zA-Z]+': 'foo '"
    )
    assert regex_serializer.from_data(" foo") == DeserializationFailure(
        "Does not match regex r'[a-zA-Z]+': ' foo'"
    )
    with pytest.raises(ValueError):
        _ = regex_serializer.to_data("foo*")
