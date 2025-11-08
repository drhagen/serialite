import pytest

from serialite import (
    Errors,
    ExpectedIntegerError,
    Failure,
    IntegerOutOfRangeError,
    IntegerSerializer,
    NonnegativeIntegerSerializer,
    PositiveIntegerSerializer,
    Success,
)

integer_serializer = IntegerSerializer()


class TestIntegerSerializer:
    @pytest.mark.parametrize("data", [12, -15])
    def test_valid_inputs(self, data):
        assert integer_serializer.from_data(data) == Success(data)
        assert integer_serializer.to_data(data) == data

    @pytest.mark.parametrize("data", ["12", 3.5])
    def test_from_data_failure(self, data):
        assert integer_serializer.from_data(data) == Failure(
            Errors.one(ExpectedIntegerError(data))
        )

    def test_to_data_failure(self):
        with pytest.raises(ValueError):
            _ = integer_serializer.to_data(13.5)


nonnegative_integer_serializer = NonnegativeIntegerSerializer()


class TestNonnegativeIntegerSerializer:
    @pytest.mark.parametrize("data", [15, 0])
    def test_valid_inputs(self, data):
        assert nonnegative_integer_serializer.from_data(data) == Success(data)
        assert nonnegative_integer_serializer.to_data(data) == data

    @pytest.mark.parametrize("data", [12.5, -1, "10"])
    def test_from_data_failure(self, data):
        actual = nonnegative_integer_serializer.from_data(data)
        if not isinstance(data, int):
            expected = Failure(Errors.one(ExpectedIntegerError(data)))
        else:
            expected = Failure(Errors.one(IntegerOutOfRangeError(actual=data, minimum=0)))

        assert actual == expected

    @pytest.mark.parametrize("value", [12.5, -1])
    def test_to_data_failure(self, value):
        with pytest.raises(ValueError):
            _ = nonnegative_integer_serializer.to_data(value)


positive_integer_serializer = PositiveIntegerSerializer()


class TestPositiveIntegerSerializer:
    def test_valid_inputs(self):
        data = 15

        assert positive_integer_serializer.from_data(data) == Success(data)
        assert positive_integer_serializer.to_data(data) == data

    @pytest.mark.parametrize("data", [12.5, -1, 0])
    def test_from_data_failure(self, data):
        actual = positive_integer_serializer.from_data(data)
        if not isinstance(data, int):
            expected = Failure(Errors.one(ExpectedIntegerError(data)))
        else:
            expected = Failure(Errors.one(IntegerOutOfRangeError(actual=data, minimum=1)))

        assert actual == expected

    @pytest.mark.parametrize("value", [12.5, -1, 0])
    def test_to_data_failure(self, value):
        with pytest.raises(ValueError):
            _ = positive_integer_serializer.to_data(value)
