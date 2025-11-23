from dataclasses import dataclass

import pytest

from serialite import serializable

try:
    import numpy as np
except ImportError:
    pytest.skip("NumPy not available", allow_module_level=True)

from serialite import (
    ArraySerializer,
    Errors,
    ExpectedIntegerError,
    Failure,
    IntegerSerializer,
    Success,
    serializer,
)

array_serializer = ArraySerializer(dtype=int)


@pytest.mark.parametrize(
    "serializer_obj", [ArraySerializer(dtype=int), ArraySerializer(IntegerSerializer())]
)
def test_valid_inputs(serializer_obj):
    data = [12, 15, 18]
    value = np.asarray(data, dtype=int)
    actual = serializer_obj.from_data(data)
    assert isinstance(actual, Success)
    np.testing.assert_equal(actual.unwrap(), value)

    assert serializer_obj.to_data(value) == data


def test_from_data_failure():
    data = ["str1", 15, "str2"]
    actual = array_serializer.from_data(data)
    expected = Errors()
    expected.add(ExpectedIntegerError("str1"), location=[0])
    expected.add(ExpectedIntegerError("str2"), location=[2])
    assert actual == Failure(expected)


def test_to_data_failure_not_array():
    with pytest.raises(ValueError):
        _ = array_serializer.to_data(3)


def test_to_data_failure_bad_element():
    with pytest.raises(ValueError):
        _ = array_serializer.to_data([12, 15, 18])


def test_child_components_uncollected():
    components = array_serializer.child_components()
    assert components == {}


def test_child_components_collected():
    @serializable
    @dataclass
    class Foo:
        bar: int

    array_foo_serializer = ArraySerializer(Foo)
    components = array_foo_serializer.child_components()
    assert components == {"element": Foo}


def test_to_openapi_schema():
    schema = array_serializer.to_openapi_schema()
    expected_schema = {
        "type": "array",
        "items": {"type": "integer"},
    }
    assert schema == expected_schema


def test_dispatch_np_array():
    data = [1.1, 2.2, 3.3, 4.4]
    value = np.asarray([1.1, 2.2, 3.3, 4.4])
    array_serializer = serializer(np.ndarray)

    np.testing.assert_equal(array_serializer.from_data(data).unwrap(), value)
    assert array_serializer.to_data(value) == data
