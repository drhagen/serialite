import pytest

try:
    import numpy as np
except ImportError:
    pytest.skip("NumPy not available", allow_module_level=True)

from serialite import (
    ArraySerializer,
    DeserializationFailure,
    DeserializationSuccess,
    IntegerSerializer,
    serializer,
)

array_serializer = ArraySerializer(dtype=int)


class TestArraySerializer:
    @pytest.mark.parametrize(
        "serializer_obj", [ArraySerializer(dtype=int), ArraySerializer(IntegerSerializer())]
    )
    def test_valid_inputs(self, serializer_obj):
        data = [12, 15, 18]
        value = np.asarray(data, dtype=int)

        actual = serializer_obj.from_data(data)
        assert isinstance(actual, DeserializationSuccess)
        np.testing.assert_equal(actual.or_die(), value)

        assert serializer_obj.to_data(value) == data

    def test_from_data_failure(self):
        data = ["str1", 15, "str2"]
        actual = array_serializer.from_data(data)
        expected_msg = {"0": "Not a valid integer: 'str1'", "2": "Not a valid integer: 'str2'"}
        assert actual == DeserializationFailure(expected_msg)

    def test_to_data_failure_not_array(self):
        with pytest.raises(ValueError):
            _ = array_serializer.to_data(3)

    def test_to_data_failure_bad_element(self):
        with pytest.raises(ValueError):
            _ = array_serializer.to_data([12, 15, 18])


def test_dispatch_np_array():
    data = [1.1, 2.2, 3.3, 4.4]
    value = np.asarray([1.1, 2.2, 3.3, 4.4])
    array_serializer = serializer(np.ndarray)

    np.testing.assert_equal(array_serializer.from_data(data).or_die(), value)
    assert array_serializer.to_data(value) == data
