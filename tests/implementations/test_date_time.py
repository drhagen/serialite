from datetime import datetime, timezone

import pytest

from serialite import (
    DateTimeSerializer,
    Errors,
    ExpectedStringError,
    Failure,
    InvalidDateTimeError,
    Success,
)

date_time_serializer = DateTimeSerializer()


def test_valid_inputs():
    data = "1969-07-20 20:17:40.000500+00:00"
    value = datetime(1969, 7, 20, 20, 17, 40, 500, timezone.utc)

    assert date_time_serializer.from_data(data) == Success(value)
    assert date_time_serializer.to_data(value) == data


def test_terminal_z():
    data = "1969-07-20 20:17:40.000500Z"
    value = datetime(1969, 7, 20, 20, 17, 40, 500, timezone.utc)

    assert date_time_serializer.from_data(data) == Success(value)


def test_from_data_failure_non_string():
    data = 1969
    assert date_time_serializer.from_data(data) == Failure(Errors.one(ExpectedStringError(data)))


def test_from_data_failure_invalid_string():
    data = "Hello World"
    assert date_time_serializer.from_data(data) == Failure(Errors.one(InvalidDateTimeError(data)))


def test_to_data_failure():
    with pytest.raises(ValueError):
        _ = date_time_serializer.to_data("1969")
