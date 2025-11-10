from dataclasses import dataclass

from serialite import Errors, ValidationError
from serialite._decorators import serializable


def test_is_empty():
    e = Errors()
    assert e.is_empty()
    e.add(ValidationError("An error"))
    assert not e.is_empty()


def test_one_creates_single_error():
    e = Errors.one(ValidationError("Something went wrong"))
    assert not e.is_empty()
    assert e == Errors.one(ValidationError("Something went wrong"))


def test_add_single_equals_one():
    e = Errors()
    e.add(ValidationError("Single error"))
    assert not e.is_empty()
    assert e == Errors.one(ValidationError("Single error"))


def test_extend_prefixes_location():
    child = Errors.one(ValidationError("error"), location=["child"])
    parent = Errors()
    parent.extend(child, location=["parent"])

    expected = Errors()
    expected.add(ValidationError("error"), location=["parent", "child"])

    assert parent == expected


def test_to_data():
    @serializable
    @dataclass
    class MatchError(Exception):
        expected: str
        actual: str

        def __str__(self):
            return f"Expected {self.expected}, got {self.actual}"

    e2 = Errors()
    e2.add(MatchError(expected="foo", actual="bar"), location=["x"])
    e2.add(MatchError(expected="baz", actual="qux"), location=[1])
    actual = e2.to_data()
    assert actual == [
        {
            "location": ["x"],
            "type": "MatchError",
            "message": "Expected foo, got bar",
            "context": {"expected": "foo", "actual": "bar"},
        },
        {
            "location": [1],
            "type": "MatchError",
            "message": "Expected baz, got qux",
            "context": {"expected": "baz", "actual": "qux"},
        },
    ]


def test_to_data_unserializable():
    e = Errors()
    e.add(ValueError("Something went wrong"))
    actual = e.to_data()
    assert actual == [
        {"location": [], "type": "ValueError", "message": "Something went wrong", "context": None}
    ]


def test_to_data_validation_error():
    e = Errors()
    e.add(ValidationError("Not allowed"))
    actual = e.to_data()
    assert actual == [
        {"location": [], "type": "ValidationError", "message": "Not allowed", "context": None}
    ]
