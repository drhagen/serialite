import dataclasses
from dataclasses import dataclass

import pytest

from serialite import (
    Errors,
    Failure,
    PositiveIntegerSerializer,
    Success,
    ValidationError,
    abstract_serializable,
    field,
    serializable,
)


@serializable
@dataclass
class Basic:
    a: int
    b: str


@serializable
@dataclass(frozen=True)
class Frozen:
    a: int
    b: str


@abstract_serializable
@dataclass(frozen=True)
class Base:
    a: int


@serializable
@dataclass(frozen=True)
class Derived(Base):
    b: str


@pytest.mark.parametrize("cls", [Basic, Frozen, Derived])
def test_dataclass_basic(cls: type):
    value = cls(1, "foo")
    data = {"a": 1, "b": "foo"}

    assert value.to_data() == data
    assert cls.from_data(data) == Success(value)


@serializable
@dataclass(frozen=True)
class Default:
    a: int
    b: str = "bar"


@serializable
@dataclass(frozen=True)
class FieldDefault:
    a: int
    b: str = field(default="bar")


@serializable
@dataclass(frozen=True)
class FieldDefaultFactory:
    a: int
    b: str = field(default_factory=lambda: "bar")


@serializable
@dataclass(frozen=True)
class BuiltinFieldDefault:
    a: int
    b: str = dataclasses.field(default="bar")


@serializable
@dataclass(frozen=True)
class BuiltinFieldDefaultFactory:
    a: int
    b: str = dataclasses.field(default_factory=lambda: "bar")


@pytest.mark.parametrize(
    "cls",
    [Default, FieldDefault, FieldDefaultFactory, BuiltinFieldDefault, BuiltinFieldDefaultFactory],
)
def test_dataclass_field(cls: type):
    value_not_default = cls(1, "foo")
    value_implicit_default = cls(1)
    value_explicit_default = cls(1, "bar")
    data_not_default = {"a": 1, "b": "foo"}
    data_implicit_default = {"a": 1}
    data_explicit_default = {"a": 1, "b": "bar"}

    assert value_implicit_default == value_explicit_default

    assert value_not_default.to_data() == data_not_default
    assert value_implicit_default.to_data() == data_implicit_default
    assert value_explicit_default.to_data() == data_implicit_default

    assert cls.from_data(data_not_default) == Success(value_not_default)
    assert cls.from_data(data_implicit_default) == Success(value_implicit_default)
    assert cls.from_data(data_explicit_default) == Success(value_implicit_default)


def test_field_serializer_is_serializer():
    @serializable
    @dataclass(frozen=True)
    class Override:
        a: int = field(serializer=PositiveIntegerSerializer())
        b: str = "bar"

    value = Override(1)
    good_data = {"a": 1}
    bad_data = {"a": -1}

    assert value.to_data() == good_data
    assert Override.from_data(good_data) == Success(value)
    assert Override.from_data(bad_data) == Failure(
        Errors.one(ValidationError("Not a valid positive integer: -1"), location=["a"])
    )


def test_field_serializer_is_type():
    @serializable
    @dataclass(frozen=True)
    class IsType:
        a: int
        b: list = field(default_factory=list, serializer=list[str])

    value_default = IsType(1)
    value = IsType(1, ["a", "b"])

    data_default = {"a": 1}
    good_data = {"a": 1, "b": ["a", "b"]}
    bad_data = {"a": 1, "b": ["a", 2]}

    assert value_default.to_data() == data_default
    assert value.to_data() == good_data

    assert IsType.from_data(data_default) == Success(value_default)
    assert IsType.from_data(good_data) == Success(value)
    assert IsType.from_data(bad_data) == Failure(
        Errors.one(ValidationError("Not a valid string: 2"), location=["b", 1])
    )
