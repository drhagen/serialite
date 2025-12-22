from dataclasses import dataclass

import pytest

from serialite import (
    ErrorElement,
    Errors,
    ExpectedFloatError,
    ValidationError,
    ValidationExceptionGroup,
    raise_errors,
    serializable,
    serializer,
)


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


def test_raise_on_errors_empty():
    e = Errors()
    result = e.raise_on_errors()
    assert result is None


def test_raise_on_errors_catchable_as_single_error():
    e = Errors()
    e.add(ValidationError("Invalid value"), location=["field1"])

    with pytest.raises(ValidationExceptionGroup) as exc_info:
        e.raise_on_errors()

    assert exc_info.value == ValidationExceptionGroup(
        (
            ErrorElement(
                ValidationError("Invalid value"),
                location=("field1",),
            ),
        )
    )


def test_raise_on_errors_catchable_as_exception_group():
    e = Errors()
    e.add(ValueError("Invalid value"))
    e.add(TypeError("Wrong type"))

    caught_value_error = False
    caught_type_error = False

    try:
        e.raise_on_errors()
    except* ValueError as err:
        caught_value_error = True
        assert err.exceptions[0].args[0] == "Invalid value"  # noqa: PT017
    except* TypeError as err:
        caught_type_error = True
        assert err.exceptions[0].args[0] == "Wrong type"  # noqa: PT017

    assert caught_value_error
    assert caught_type_error


def test_raise_errors_in_alt():
    failure = serializer(float).from_data("not a float")

    with pytest.raises(ValidationExceptionGroup) as exc_info:
        _ = failure.alt(raise_errors)

    assert exc_info.value == ValidationExceptionGroup(
        (
            ErrorElement(
                ExpectedFloatError(actual="not a float"),
                location=(),
            ),
        )
    )


def test_raise_errors_on_empty():
    with pytest.raises(ValueError):
        raise_errors(Errors())
