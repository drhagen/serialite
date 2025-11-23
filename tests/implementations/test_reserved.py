from dataclasses import dataclass

import pytest

from serialite import (
    Errors,
    Failure,
    ReservedSerializer,
    ReservedValueError,
    StringSerializer,
    Success,
    serializable,
)

reserved_serializer = ReservedSerializer(StringSerializer(), reserved={"false", "true"})


def test_valid_inputs():
    data = "foo"
    assert reserved_serializer.from_data(data) == Success(data)
    assert reserved_serializer.to_data(data) == data


def test_reserved_inputs():
    data = "true"
    assert reserved_serializer.from_data(data) == Failure(Errors.one(ReservedValueError("true")))


def test_to_data_failure():
    with pytest.raises(ValueError):
        _ = reserved_serializer.to_data("true")


def test_reserved_value_error_to_data_and_to_string():
    r = ReservedValueError("null")
    assert r.to_data() == {"actual": "null"}
    assert str(r) == "This is a reserved value: 'null'"


def test_child_components_uncollected():
    components = reserved_serializer.child_components()
    assert components == {}


def test_child_components_collected():
    @serializable
    @dataclass
    class Foo:
        bar: int

    reserved_foo_serializer = ReservedSerializer(Foo, reserved=set())
    components = reserved_foo_serializer.child_components()
    assert components == {"internal": Foo}


def test_to_openapi_schema():
    schema = reserved_serializer.to_openapi_schema()
    expected_schema = {"type": "string"}
    assert schema == expected_schema
