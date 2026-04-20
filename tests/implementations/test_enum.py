from datetime import datetime
from enum import Enum, IntEnum, StrEnum, auto

import pytest

from serialite import (
    EnumSerializer,
    Errors,
    ExpectedIntegerError,
    ExpectedStringError,
    Failure,
    InvalidEnumValueError,
    Success,
)


class Color(Enum):
    RED = "red"
    GREEN = "green"


class Priority(IntEnum):
    LOW = 1
    HIGH = auto()


class Status(StrEnum):
    ACTIVE = "active"
    INACTIVE = auto()


class AutoEnum(Enum):
    A = auto()
    B = auto()


DATE = datetime(2024, 1, 1, 12, 0, 0)


class MixedEnum(Enum):
    STRING = "hello"
    NUMBER = 42
    DATE = DATE


# By name (default)
@pytest.mark.parametrize(
    ("enum_class", "name", "member"),
    [
        (Color, "RED", Color.RED),
        (Color, "GREEN", Color.GREEN),
        (Priority, "LOW", Priority.LOW),
        (Priority, "HIGH", Priority.HIGH),
        (Status, "ACTIVE", Status.ACTIVE),
        (Status, "INACTIVE", Status.INACTIVE),
        (AutoEnum, "A", AutoEnum.A),
        (AutoEnum, "B", AutoEnum.B),
        (MixedEnum, "STRING", MixedEnum.STRING),
        (MixedEnum, "DATE", MixedEnum.DATE),
    ],
)
def test_by_name(enum_class, name, member):
    s = EnumSerializer(enum_class)
    assert s.from_data(name) == Success(member)
    assert s.to_data(member) == name


@pytest.mark.parametrize("data", [123, True, None, ["a"]])
def test_by_name_rejects_non_string_data(data):
    s = EnumSerializer(Color)
    expected = ExpectedStringError(data)
    assert s.from_data(data) == Failure(Errors.one(expected))


def test_by_name_rejects_unknown_name():
    s = EnumSerializer(Color)
    expected = InvalidEnumValueError("Color", ["RED", "GREEN"], "BLUE")
    assert s.from_data("BLUE") == Failure(Errors.one(expected))


def test_by_name_to_data_raises_on_non_member():
    s = EnumSerializer(Color)
    with pytest.raises(ValueError):
        s.to_data("RED")


@pytest.mark.parametrize(
    ("enum_class", "expected"),
    [
        (Color, {"type": "string", "enum": ["RED", "GREEN"]}),
        (Priority, {"type": "string", "enum": ["LOW", "HIGH"]}),
        (Status, {"type": "string", "enum": ["ACTIVE", "INACTIVE"]}),
        (AutoEnum, {"type": "string", "enum": ["A", "B"]}),
        (MixedEnum, {"type": "string", "enum": ["STRING", "NUMBER", "DATE"]}),
    ],
)
def test_by_name_openapi_schema(enum_class, expected):
    s = EnumSerializer(enum_class)
    assert s.to_openapi_schema() == expected


# By value
@pytest.mark.parametrize(
    ("enum_class", "value", "member"),
    [
        (Color, "red", Color.RED),
        (Color, "green", Color.GREEN),
        (Priority, 1, Priority.LOW),
        (Priority, 2, Priority.HIGH),
        (Status, "active", Status.ACTIVE),
        (Status, "inactive", Status.INACTIVE),
        (MixedEnum, "hello", MixedEnum.STRING),
        (MixedEnum, 42, MixedEnum.NUMBER),
        (MixedEnum, DATE, MixedEnum.DATE),
    ],
)
def test_by_value(enum_class, value, member):
    s = EnumSerializer(enum_class, by="value")
    assert s.from_data(value) == Success(member)
    assert s.to_data(member) == value


@pytest.mark.parametrize(
    ("enum_class", "data", "expected"),
    [
        (Priority, "1", ExpectedIntegerError("1")),
        (Priority, True, ExpectedIntegerError(True)),
        (Status, 123, ExpectedStringError(123)),
    ],
)
def test_by_value_rejects_wrong_type(enum_class, data, expected):
    s = EnumSerializer(enum_class, by="value")
    assert s.from_data(data) == Failure(Errors.one(expected))


def test_by_value_rejects_unknown_value():
    s = EnumSerializer(Color, by="value")
    expected = InvalidEnumValueError("Color", ["red", "green"], "blue")
    assert s.from_data("blue") == Failure(Errors.one(expected))


def test_by_value_to_data_raises_on_non_member():
    s = EnumSerializer(Color, by="value")
    with pytest.raises(ValueError):
        s.to_data("red")


@pytest.mark.parametrize(
    ("enum_class", "expected"),
    [
        (Color, {"type": "string", "enum": ["red", "green"]}),
        (Priority, {"type": "integer", "enum": [1, 2]}),
        (Status, {"type": "string", "enum": ["active", "inactive"]}),
        (MixedEnum, {"enum": ["hello", 42, DATE]}),
    ],
)
def test_by_value_openapi_schema(enum_class, expected):
    s = EnumSerializer(enum_class, by="value")
    assert s.to_openapi_schema() == expected


# Error
def test_invalid_enum_value_error():
    error = InvalidEnumValueError("Color", ["RED", "GREEN"], "BLUE")
    assert error.to_data() == {
        "enum_name": "Color",
        "values": ["RED", "GREEN"],
        "actual": "BLUE",
    }
    assert str(error) == "Expected one of ['RED', 'GREEN'] for Color, but got 'BLUE'"
