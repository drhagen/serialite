from dataclasses import dataclass

import pytest

from serialite import (
    Errors,
    ExpectedFloatError,
    Failure,
    FloatSerializer,
    OptionalSerializer,
    Success,
    serializable,
)

optional_serializer = OptionalSerializer(FloatSerializer())


@pytest.mark.parametrize("data", [12.5, None])
def test_valid_inputs(data):
    assert optional_serializer.from_data(data) == Success(data)
    assert optional_serializer.to_data(data) == data


def test_from_data_failure():
    data = "12.5"
    assert optional_serializer.from_data(data) == Failure(Errors.one(ExpectedFloatError("12.5")))


def test_to_data_failure():
    with pytest.raises(ValueError):
        _ = optional_serializer.to_data("12.5")


def test_child_components_uncollected():
    components = optional_serializer.child_components()
    assert components == {}


def test_child_components_collected():
    @serializable
    @dataclass
    class Foo:
        bar: int

    optional_foo_serializer = OptionalSerializer(Foo)
    components = optional_foo_serializer.child_components()
    assert components == {"element": Foo}


def test_to_openapi_schema():
    schema = optional_serializer.to_openapi_schema()
    expected_schema = {"type": "number", "nullable": True}
    assert schema == expected_schema
