from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Tuple, Union
from uuid import UUID

import pytest

from serialite import DeserializationSuccess, serializer


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
        (Dict[int, float], [[11, 11.5], [22, 22.8]], {11: 11.5, 22: 22.8}),
        (dict[int, float], [[11, 11.5], [22, 22.8]], {11: 11.5, 22: 22.8}),
    ],
)
def test_dispatch(data_type, data, value):
    this_serializer = serializer(data_type)

    assert this_serializer.from_data(data) == DeserializationSuccess(value)
    assert this_serializer.to_data(value) == data


@pytest.mark.parametrize("type", [Optional[int], int | None])
def test_dispatch_optional(type):
    optional_serializer = serializer(type)

    assert optional_serializer.from_data(1).or_die() == 1
    assert optional_serializer.to_data(1) == 1
    assert optional_serializer.from_data(None).or_die() is None
    assert optional_serializer.to_data(None) is None


@pytest.mark.parametrize("type", [Union[str, int], str | int])
def test_dispatch_union(type):
    union_serializer = serializer(type)

    assert union_serializer.from_data(1).or_die() == 1
    assert union_serializer.to_data(1) == 1
    assert union_serializer.from_data("a").or_die() == "a"
    assert union_serializer.to_data("a") == "a"


def test_dispatch_literal():
    literal_serializer = serializer(Literal["none", 1, 2, 3])

    assert literal_serializer.from_data("none").or_die() == "none"
    assert literal_serializer.to_data(1) == 1
    assert literal_serializer.from_data(2).or_die() == 2
    assert literal_serializer.to_data(3) == 3


def test_dispatch_any():
    any_serializer = serializer(Any)

    assert any_serializer.from_data(1).or_die() == 1
    assert any_serializer.from_data("any string").or_die() == "any string"
    assert any_serializer.from_data({"a": 1}).or_die() == {"a": 1}


def test_dispatch_type_alias():
    type Scale = Literal["log", "linear"]

    scale_serializer = serializer(Scale)
    assert scale_serializer.from_data("log").or_die() == "log"
    assert scale_serializer.from_data("linear").or_die() == "linear"
    assert scale_serializer.to_data("log") == "log"
    assert scale_serializer.to_data("linear") == "linear"
