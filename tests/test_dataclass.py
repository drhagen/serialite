import dataclasses
from dataclasses import dataclass

import pytest

from serialite import (
    Errors,
    ExpectedStringError,
    Failure,
    IntegerOutOfRangeError,
    PositiveIntegerSerializer,
    Success,
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


def test_serializable_empty_parentheses():
    @serializable()
    @dataclass(frozen=True)
    class EmptyParens:
        a: int
        b: str = "x"

    assert EmptyParens(1).to_data() == {"a": 1}
    assert EmptyParens.from_data({"a": 1}) == Success(EmptyParens(1))


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
        Errors.one(IntegerOutOfRangeError(actual=-1, minimum=1), location=["a"])
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
        Errors.one(ExpectedStringError(2), location=["b", 1])
    )


def test_hide_default_false():
    @serializable(hide_default=False)
    @dataclass(frozen=True)
    class Defaults:
        a: int
        b: str = "x"
        c: list[int] = dataclasses.field(default_factory=list)
        d: int | None = None

    data = Defaults(1).to_data()
    assert data == {"a": 1, "b": "x", "c": [], "d": None}
    assert Defaults.from_data(data) == Success(Defaults(1))


def test_hide_default_false_with_field_serializer():
    @serializable(hide_default=False)
    @dataclass(frozen=True)
    class WithFieldSerializer:
        a: int = field(default=1, serializer=PositiveIntegerSerializer())

    assert WithFieldSerializer().to_data() == {"a": 1}


def test_hide_default_false_fills_missing_fields():
    @serializable(hide_default=False)
    @dataclass(frozen=True)
    class Defaults:
        a: int
        b: str = "x"

    assert Defaults.from_data({"a": 1}) == Success(Defaults(1))


def test_field_hide_default_false():
    @serializable
    @dataclass(frozen=True)
    class FieldShown:
        a: int
        b: str = field(default="x", hide_default=False)
        c: list[int] = field(default_factory=list, hide_default=False)
        d: str = "y"

    data = FieldShown(1).to_data()
    assert data == {"a": 1, "b": "x", "c": []}
    assert FieldShown.from_data(data) == Success(FieldShown(1))


def test_field_hide_default_true_overrides_decorator():
    @serializable(hide_default=False)
    @dataclass(frozen=True)
    class FieldHidden:
        a: int
        b: str = field(default="x", hide_default=True)
        c: str = "y"

    data = FieldHidden(1).to_data()
    assert data == {"a": 1, "c": "y"}
    assert FieldHidden.from_data(data) == Success(FieldHidden(1))


def test_field_hide_default_true_overrides_decorator_with_factory():
    @serializable(hide_default=False)
    @dataclass(frozen=True)
    class FactoryHidden:
        a: int
        b: list[int] = field(default_factory=list, hide_default=True)

    data = FactoryHidden(1).to_data()
    assert data == {"a": 1}
    assert FactoryHidden.from_data(data) == Success(FactoryHidden(1))

    non_default = FactoryHidden(1, [2, 3])
    assert non_default.to_data() == {"a": 1, "b": [2, 3]}
    assert FactoryHidden.from_data(non_default.to_data()) == Success(non_default)


def test_field_without_hide_default_uses_decorator():
    @serializable(hide_default=False)
    @dataclass(frozen=True)
    class FieldInherits:
        a: int = field(default=1, serializer=PositiveIntegerSerializer())

    assert FieldInherits().to_data() == {"a": 1}
