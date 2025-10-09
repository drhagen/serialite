from pathlib import Path

import pytest

from serialite import Errors, Failure, PathSerializer, Success, ValidationError

path_serializer = PathSerializer()


def test_valid_inputs():
    data = "a/b/c.txt"
    value = Path(data)

    assert path_serializer.from_data(data) == Success(value)
    assert path_serializer.to_data(value) == value.as_posix()


@pytest.mark.parametrize("data", [12.5, None, 123])
def test_from_data_failure(data):
    assert path_serializer.from_data(data) == Failure(
        Errors.one(ValidationError(f"Not a valid string: {data!r}"))
    )


def test_to_data_failure():
    # to_data expects a pathlib.Path instance
    with pytest.raises(ValueError):
        _ = path_serializer.to_data("a/b/c.txt")
