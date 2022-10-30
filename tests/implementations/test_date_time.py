from datetime import datetime, timezone

import pytest

from serialite import DateTimeSerializer, DeserializationFailure, DeserializationSuccess

date_time_serializer = DateTimeSerializer()


def test_valid_inputs():
    data = "1969-07-20 20:17:40.000500+00:00"
    value = datetime(1969, 7, 20, 20, 17, 40, 500, timezone.utc)

    assert date_time_serializer.from_data(data) == DeserializationSuccess(value)
    assert date_time_serializer.to_data(value) == data


def test_terminal_z():
    data = "1969-07-20 20:17:40.000500Z"
    value = datetime(1969, 7, 20, 20, 17, 40, 500, timezone.utc)

    assert date_time_serializer.from_data(data) == DeserializationSuccess(value)


@pytest.mark.parametrize("data", [1969, "Hello World"])
def test_from_data_failure(data):
    assert date_time_serializer.from_data(data) == DeserializationFailure(
        f"Not a valid DateTime: {data!r}"
    )


def test_to_data_failure():
    with pytest.raises(ValueError):
        _ = date_time_serializer.to_data("1969")
