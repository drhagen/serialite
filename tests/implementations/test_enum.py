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

DATE = datetime(2024, 1, 1, 12, 0, 0)


def serializer_from_enum(enum) -> EnumSerializer:
    return EnumSerializer(enum)


def serializer_from_enum_member(enum_member) -> EnumSerializer:
    return serializer_from_enum(type(enum_member))


class Color(Enum):
    RED = "red"
    GREEN = "green"


class Priority(IntEnum):
    LOW = 1
    HIGH = auto()


class Status(StrEnum):
    ACTIVE = "active"
    INACTIVE = auto()


class CaseInsensitiveStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            for member in cls:
                if member.value.lower() == value.lower():
                    return member
        return None


class MixedEnum(Enum):
    STRING = "hello"
    NUMBER = 42
    DATE = DATE


@pytest.mark.parametrize(
    ("enum_member", "value"),
    [
        (Color.RED, "red"),
        (Color.GREEN, "green"),
        (Priority.LOW, 1),
        (Priority.HIGH, 2),
        (Status.ACTIVE, "active"),
        (Status.INACTIVE, "inactive"),
        (MixedEnum.STRING, "hello"),
        (MixedEnum.NUMBER, 42),
        (MixedEnum.DATE, DATE),
    ],
)
def test_valid_inputs(enum_member, value):
    serializer = serializer_from_enum_member(enum_member)
    assert serializer.from_data(value) == Success(enum_member)
    assert serializer.to_data(enum_member) == value


@pytest.mark.parametrize(
    ("enum", "data", "expected"),
    [
        (Priority, "1", ExpectedIntegerError("1")),
        (Priority, True, ExpectedIntegerError(True)),
        (Status, 123, ExpectedStringError(123)),
    ],
)
def test_wrong_type(enum, data, expected):
    serializer = serializer_from_enum(enum)
    assert serializer.from_data(data) == Failure(Errors.one(expected))


@pytest.mark.parametrize(
    ("data", "enum"),
    [("invalid", Color), (99, Priority), ("invalid", Status), ("invalid", CaseInsensitiveStatus)],
)
def test_invalid_value(data, enum):
    serializer = serializer_from_enum(enum)
    values = [m.value for m in enum]
    enum_name = enum.__name__

    expected = Failure(Errors.one(InvalidEnumValueError(enum_name, values, data)))
    assert serializer.from_data(data) == expected


def test_to_data_invalid():
    serializer = serializer_from_enum(Color)

    with pytest.raises(ValueError):
        serializer.to_data("invalid")


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ("AcTiVe", CaseInsensitiveStatus.ACTIVE),
        ("active", CaseInsensitiveStatus.ACTIVE),
        ("INACTIVE", CaseInsensitiveStatus.INACTIVE),
    ],
)
def test_missing_method(data, expected):
    serializer = serializer_from_enum(CaseInsensitiveStatus)
    assert serializer.from_data(data) == Success(expected)


def test_invalid_enum_value_error_string():
    e = InvalidEnumValueError("Color", ["red", "green"], "invalid")
    assert e.to_data() == {
        "enum_name": "Color",
        "values": ["red", "green"],
        "actual": "invalid",
    }
    assert str(e) == "Expected one of ['red', 'green'] for Color, but got 'invalid'"


@pytest.mark.parametrize(
    ("enum", "expected"),
    [
        (Color, {"type": "string", "enum": ["red", "green"]}),
        (Priority, {"type": "integer", "enum": [1, 2]}),
        (Status, {"type": "string", "enum": ["active", "inactive"]}),
        (MixedEnum, {"enum": ["hello", 42, DATE]}),
    ],
)
def test_to_openapi_schema(enum, expected):
    serializer = serializer_from_enum(enum)
    assert serializer.to_openapi_schema() == expected
