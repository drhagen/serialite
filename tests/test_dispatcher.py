from datetime import datetime
from typing import Any, Dict, List, Literal, NewType, Optional, Tuple, Union
from uuid import UUID

import pytest

from serialite import (
    Errors,
    Failure,
    Serializable,
    StringSerializer,
    Success,
    ValidationError,
    serializer,
)


@pytest.mark.parametrize(
    ("data_type", "data", "value"),
    [
        (bool, True, True),
        (int, 3, 3),
        (float, 2.5, 2.5),
        (str, "a", "a"),
        (datetime, "2018-06-28 03:18:53", datetime(2018, 6, 28, 3, 18, 53)),
        (
            UUID,
            "00112233-4455-6677-8899-aabbccddeeff",
            UUID("00112233-4455-6677-8899-aabbccddeeff"),
        ),
        (List[int], [11, 22, 33], [11, 22, 33]),
        (List[str], ["a", "b"], ["a", "b"]),
        (list[str], ["a", "b"], ["a", "b"]),
        (Tuple[int, str], [5, "a"], (5, "a")),
        (tuple[int, str], [5, "a"], (5, "a")),
        (Dict[str, int], {"a": 11, "b": 22}, {"a": 11, "b": 22}),
        (dict[str, int], {"a": 11, "b": 22}, {"a": 11, "b": 22}),
    ],
)
def test_dispatch(data_type, data, value):
    this_serializer = serializer(data_type)

    assert this_serializer.from_data(data) == Success(value)
    assert this_serializer.to_data(value) == data


@pytest.mark.parametrize("type", [Optional[int], int | None])
def test_dispatch_optional(type):
    optional_serializer = serializer(type)

    assert optional_serializer.from_data(1) == Success(1)
    assert optional_serializer.to_data(1) == 1
    assert optional_serializer.from_data(None) == Success(None)
    assert optional_serializer.to_data(None) is None


@pytest.mark.parametrize("type", [Union[str, int], str | int])
def test_dispatch_union(type):
    union_serializer = serializer(type)

    assert union_serializer.from_data(1) == Success(1)
    assert union_serializer.to_data(1) == 1
    assert union_serializer.from_data("a") == Success("a")
    assert union_serializer.to_data("a") == "a"


def test_dispatch_literal():
    literal_serializer = serializer(Literal["none", 1, 2, 3])

    assert literal_serializer.from_data("none") == Success("none")
    assert literal_serializer.to_data(1) == 1
    assert literal_serializer.from_data(2) == Success(2)
    assert literal_serializer.to_data(3) == 3


def test_dispatch_any():
    any_serializer = serializer(Any)

    assert any_serializer.from_data(1) == Success(1)
    assert any_serializer.from_data("any string") == Success("any string")
    assert any_serializer.from_data({"a": 1}) == Success({"a": 1})


def test_dispatch_type_alias():
    type Scale = Literal["log", "linear"]

    scale_serializer = serializer(Scale)
    assert scale_serializer.from_data("log") == Success("log")
    assert scale_serializer.from_data("linear") == Success("linear")
    assert scale_serializer.to_data("log") == "log"
    assert scale_serializer.to_data("linear") == "linear"


def test_dispatch_newtype():
    UserId = NewType("UserId", int)

    user_id = UserId(42)
    user_id_serializer = serializer(UserId)
    assert user_id_serializer.from_data(42) == Success(user_id)
    assert user_id_serializer.to_data(user_id) == 42


def test_dispatch_nested_newtype():
    UserId = NewType("UserId", int)
    ProUserId = NewType("ProUserId", UserId)

    pro_user_id = ProUserId(42)
    pro_user_id_serializer = serializer(ProUserId)
    assert pro_user_id_serializer.from_data(42) == Success(pro_user_id)
    assert pro_user_id_serializer.to_data(pro_user_id) == 42


def test_dispatch_dict_with_newtype_str_key():
    Key = NewType("Key", str)

    dict_serializer = serializer(dict[Key, int])
    assert dict_serializer.from_data({"a": 1, "b": 2}) == Success({"a": 1, "b": 2})
    assert dict_serializer.to_data({"a": 1, "b": 2}) == {"a": 1, "b": 2}


def test_dispatch_dict_with_nested_newtype_str_key():
    Key = NewType("Key", str)
    NestedKey = NewType("NestedKey", Key)

    dict_serializer = serializer(dict[NestedKey, int])
    assert dict_serializer.from_data({"a": 1, "b": 2}) == Success({"a": 1, "b": 2})
    assert dict_serializer.to_data({"a": 1, "b": 2}) == {"a": 1, "b": 2}


def test_dispatch_dict_with_type_alias_str_key():
    type Key = str

    dict_serializer = serializer(dict[Key, int])
    assert dict_serializer.from_data({"a": 1, "b": 2}) == Success({"a": 1, "b": 2})
    assert dict_serializer.to_data({"a": 1, "b": 2}) == {"a": 1, "b": 2}


def test_dispatch_dict_with_nested_type_alias_str_key():
    type Key = str
    type NestedKey = Key

    dict_serializer = serializer(dict[NestedKey, int])
    assert dict_serializer.from_data({"a": 1, "b": 2}) == Success({"a": 1, "b": 2})
    assert dict_serializer.to_data({"a": 1, "b": 2}) == {"a": 1, "b": 2}


def test_dispatch_serializable_subclass_of_registered_type():
    class Tag(str, Serializable):
        @classmethod
        def from_data(cls, data):
            if not isinstance(data, str) or not data.startswith("tag:"):
                return Failure(Errors.one(ValidationError(f"Not a tag: {data!r}")))
            return Success(cls(data))

        def to_data(self):
            return str(self)

    tag_serializer = serializer(Tag)
    assert tag_serializer is Tag  # the class is its own serializer

    # Recovering a Tag (not a plain str) proves Tag.from_data/to_data run.
    assert isinstance(tag_serializer.from_data("tag:x").unwrap(), Tag)
    assert tag_serializer.to_data(Tag("tag:x")) == "tag:x"

    # A plain string is accepted by the builtin StringSerializer but must be
    # rejected here, proving Tag.from_data runs rather than StringSerializer.
    assert isinstance(tag_serializer.from_data("plain"), Failure)


def test_dispatch_explicit_registration_overrides_serializable_subclass():
    class Widget(str, Serializable):
        pass

    override = StringSerializer()
    serializer.register(Widget, lambda cls: override)

    assert serializer(Widget) is override


def test_dispatch_generic_serializable_subclass_of_registered_type():
    class TypedList[T](list, Serializable):
        @classmethod
        def from_data(cls, data):
            if not isinstance(data, list):
                return Failure(Errors.one(ValidationError(f"Not a list: {data!r}")))
            return Success(cls(data))

        def to_data(self):
            return list(self)

    typed_list_serializer = serializer(TypedList[int])

    # The builtin list serializer would yield a plain list. Recovering a
    # TypedList proves TypedList.from_data runs instead of ListSerializer.
    parsed = typed_list_serializer.from_data([1, 2, 3])
    assert isinstance(parsed.unwrap(), TypedList)
    assert typed_list_serializer.to_data(TypedList([1, 2, 3])) == [1, 2, 3]


def test_dispatch_generic_serializable_subclass_without_registered_base():
    class Box[T](Serializable):
        def __init__(self, value):
            self.value = value

        @classmethod
        def from_data(cls, data):
            return Success(cls(data["value"]))

        def to_data(self):
            return {"value": self.value}

    # Unlike TypedList (whose origin subclasses the registered list), Box's
    # origin has no registered serializer. This covers the plain generic path.
    box_serializer = serializer(Box[int])
    assert box_serializer.from_data({"value": 7}).unwrap().value == 7
    assert box_serializer.to_data(Box(7)) == {"value": 7}
