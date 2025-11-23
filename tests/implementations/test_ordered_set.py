import pytest

try:
    from ordered_set import OrderedSet
except ImportError:
    pytest.skip("ordered-set not available", allow_module_level=True)

from dataclasses import dataclass

from serialite import (
    DuplicatedValueError,
    Errors,
    ExpectedFloatError,
    ExpectedListError,
    Failure,
    FloatSerializer,
    OrderedSetSerializer,
    Success,
    serializable,
)

ordered_set_serializer = OrderedSetSerializer(FloatSerializer())


def test_valid_inputs():
    data = [12.3, 15.5, 16.0]
    value = OrderedSet([12.3, 15.5, 16.0])

    assert ordered_set_serializer.from_data(data) == Success(value)
    assert ordered_set_serializer.to_data(value) == data


def test_from_data_failure_top_level():
    data = 12.5
    assert ordered_set_serializer.from_data(data) == Failure(Errors.one(ExpectedListError(data)))


def test_from_data_failure_element():
    data = ["str1", 15.5, "str2"]
    actual = ordered_set_serializer.from_data(data)
    expected = Errors()
    expected.add(ExpectedFloatError("str1"), location=[0])
    expected.add(ExpectedFloatError("str2"), location=[2])
    assert actual == Failure(expected)


def test_from_data_failure_uniqueness():
    data = [12.3, 15.5, 16.0, 12.3]
    actual = ordered_set_serializer.from_data(data)
    expected = Errors()
    expected.add(DuplicatedValueError(12.3), location=[3])
    assert actual == Failure(expected)


def test_to_data_failure_top_level():
    with pytest.raises(ValueError):
        _ = ordered_set_serializer.to_data(12.5)


def test_to_data_failure_element():
    with pytest.raises(ValueError):
        _ = ordered_set_serializer.to_data(OrderedSet([12.5, "a"]))


def test_child_components_uncollected():
    components = ordered_set_serializer.child_components()
    assert components == {}


def test_child_components_collected():
    @serializable
    @dataclass
    class Foo:
        bar: int

    ordered_set_foo_serializer = OrderedSetSerializer(Foo)
    components = ordered_set_foo_serializer.child_components()
    assert components == {"element": Foo}


def test_to_openapi_schema():
    schema = ordered_set_serializer.to_openapi_schema()
    expected_schema = {"type": "array", "items": {"type": "number"}}
    assert schema == expected_schema
