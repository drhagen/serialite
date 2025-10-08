import pytest

from serialite import (
    Errors,
    Failure,
    IntegerSerializer,
    NonnegativeIntegerSerializer,
    PositiveIntegerSerializer,
    Success,
    ValidationError,
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
            Errors.one(ValidationError(f"Not a valid integer: {data!r}"))
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
        expected = Failure(
            Errors.one(ValidationError(f"Not a valid nonnegative integer: {data!r}"))
        )
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
        expected = Failure(Errors.one(ValidationError(f"Not a valid positive integer: {data!r}")))
        assert actual == expected

    @pytest.mark.parametrize("value", [12.5, -1, 0])
    def test_to_data_failure(self, value):
        with pytest.raises(ValueError):
            _ = positive_integer_serializer.to_data(value)
