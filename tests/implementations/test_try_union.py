from dataclasses import dataclass

import pytest

from serialite import (
    BooleanSerializer,
    Failure,
    FloatSerializer,
    IntegerSerializer,
    Success,
    TryUnionSerializer,
    serializable,
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


def test_child_components_uncollected():
    components = try_union_serializer.child_components()
    assert components == {}


def test_child_components_collected():
    @serializable
    @dataclass
    class Foo:
        bar: int

    @serializable
    @dataclass
    class Bar:
        baz: str

    try_union_foo_bar_serializer = TryUnionSerializer(Foo, Bar, IntegerSerializer())
    components = try_union_foo_bar_serializer.child_components()
    assert components == {"0": Foo, "1": Bar}


def test_to_openapi_schema():
    schema = try_union_serializer.to_openapi_schema()
    expected_schema = {"oneOf": [{"type": "number"}, {"type": "integer"}, {"type": "boolean"}]}
    assert schema == expected_schema
