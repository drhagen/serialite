from dataclasses import dataclass

import pytest

from serialite import (
    Errors,
    ExpectedDictionaryError,
    ExpectedFloatError,
    Failure,
    FloatSerializer,
    RawDictSerializer,
    ReservedSerializer,
    ReservedValueError,
    StringSerializer,
    Success,
    serializable,
)

raw_dict_serializer = RawDictSerializer(FloatSerializer())
raw_dict_serializer_with_key = RawDictSerializer(
    key_serializer=ReservedSerializer(StringSerializer(), reserved={"null"}),
    value_serializer=FloatSerializer(),
)


def test_valid_inputs():
    data = {"a": 12.3, "b": 15.5, "c": 16.0}

    assert raw_dict_serializer.from_data(data) == Success(data)
    assert raw_dict_serializer.to_data(data) == data


def test_from_data_failure_not_a_dict():
    data = 12.5
    assert raw_dict_serializer.from_data(data) == Failure(
        Errors.one(ExpectedDictionaryError(data))
    )


def test_from_data_failure_value():
    data = {"a": "str1", "b": 15.5, "c": "str2"}
    actual = raw_dict_serializer.from_data(data)
    expected = Errors()
    expected.add(ExpectedFloatError("str1"), location=["a"])
    expected.add(ExpectedFloatError("str2"), location=["c"])
    assert actual == Failure(expected)


def test_to_data_failure():
    with pytest.raises(ValueError):
        _ = raw_dict_serializer.to_data(12.3)


def test_key_serializer_valid_inputs():
    data = {"a": 12.3, "b": 15.5, "c": 16.0}

    assert raw_dict_serializer_with_key.from_data(data) == Success(data)
    assert raw_dict_serializer_with_key.to_data(data) == data


def test_key_serializer_bad_inputs():
    data = {"a": 12.3, "null": 15.5, "c": 16.0}
    assert raw_dict_serializer_with_key.from_data(data) == Failure(
        Errors.one(ReservedValueError("null"), location=["null"])
    )
    with pytest.raises(ValueError):
        _ = raw_dict_serializer_with_key.to_data(data)


def test_error_to_data_and_to_string():
    e = ExpectedDictionaryError(["a", 12.3])
    assert e.to_data() == {"actual": ["a", 12.3]}
    assert str(e) == "Expected dictionary, but got ['a', 12.3]"


def test_child_components_uncollected():
    components = raw_dict_serializer.child_components()
    assert components == {}


def test_child_components_collected():
    @serializable
    @dataclass
    class Foo:
        bar: int

    raw_dict_foo_serializer = RawDictSerializer(Foo)
    components = raw_dict_foo_serializer.child_components()
    assert components == {"value": Foo}


def test_to_openapi_schema():
    schema = raw_dict_serializer.to_openapi_schema()
    expected_schema = {"type": "object", "additionalProperties": {"type": "number"}}
    assert schema == expected_schema
