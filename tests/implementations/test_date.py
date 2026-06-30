from datetime import date, datetime

import pytest

from serialite import (
    DateSerializer,
    DateTimeSerializer,
    Errors,
    ExpectedStringError,
    Failure,
    InvalidDateError,
    Success,
    serializer,
)

date_serializer = DateSerializer()


def test_valid_inputs():
    data = "1969-07-20"
    value = date(1969, 7, 20)

    assert date_serializer.from_data(data) == Success(value)
    assert date_serializer.to_data(value) == data


def test_from_data_failure_non_string():
    data = 1969
    assert date_serializer.from_data(data) == Failure(Errors.one(ExpectedStringError(data)))


def test_from_data_failure_invalid_string():
    data = "Hello World"
    assert date_serializer.from_data(data) == Failure(Errors.one(InvalidDateError(data)))


def test_from_data_rejects_datetime_string():
    data = "1969-07-20 20:17:40"
    assert date_serializer.from_data(data) == Failure(Errors.one(InvalidDateError(data)))


def test_to_data_failure():
    with pytest.raises(ValueError):
        _ = date_serializer.to_data("1969")


def test_to_data_rejects_datetime():
    with pytest.raises(ValueError):
        _ = date_serializer.to_data(datetime(1969, 7, 20, 20, 17, 40))


def test_date_error_to_data_and_to_string():
    e = InvalidDateError("Hello World")
    assert e.to_data() == {"actual": "Hello World"}
    assert str(e) == "Expected Date, but got 'Hello World'"


def test_to_openapi_schema():
    schema = date_serializer.to_openapi_schema(lambda _: {})
    expected_schema = {"type": "string", "format": "date"}
    assert schema == expected_schema


def test_dispatch_keeps_date_and_datetime_distinct():
    assert isinstance(serializer(date), DateSerializer)
    assert isinstance(serializer(datetime), DateTimeSerializer)
