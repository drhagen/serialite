import pytest

from serialite import (
    DeserializationError,
    DeserializationFailure,
    DeserializationSuccess,
    Serializer,
)


class TestDeserializationError:
    def test_constructor(self):
        obj = DeserializationError("error msg")
        assert obj.error == "error msg"

    def test_str(self):
        obj = DeserializationError("error msg")
        assert str(obj) == "'error msg'"

    def test_repr(self):
        obj = DeserializationError("error msg")
        assert repr(obj) == "DeserializationError('error msg')"


class TestDeserializationFailure:
    def test_constructor(self):
        error = "Should be integer"
        actual = DeserializationFailure(error)
        assert actual.error == error

    def test_or_die(self):
        error = "Should be integer"
        obj = DeserializationFailure(error)
        with pytest.raises(DeserializationError):
            obj.or_die()

    def test_or_die_custom(self):
        error = "Should be integer"
        obj = DeserializationFailure(error)
        with pytest.raises(TypeError):
            obj.or_die(TypeError("Custom message"))


class TestDeserializationSuccess:
    def test_constructor(self):
        value = "pass"
        actual = DeserializationSuccess(value)
        assert actual.value == value

    def test_or_die(self):
        value = "my value"
        obj = DeserializationSuccess(value)
        actual = obj.or_die()
        assert actual == value


class NoneSerializer(Serializer):
    @staticmethod
    def from_data(data):
        if data is None:
            return DeserializationSuccess(None)
        else:
            return DeserializationFailure(f"Not None: {data!r}")

    @staticmethod
    def to_data(value):
        if value is None:
            return None
        else:
            raise TypeError("Value must be None.")
