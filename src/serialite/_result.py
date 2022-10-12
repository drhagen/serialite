from __future__ import annotations

__all__ = [
    "DeserializationError",
    "DeserializationResult",
    "DeserializationFailure",
    "DeserializationSuccess",
]

from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, NoReturn, TypeVar

Output = TypeVar("Output")


class DeserializationError(Exception):
    """Default exception raised by DeserializationResult.or_die."""

    def __init__(self, error):
        super().__init__(error)
        self.error = error

    def __str__(self):
        return repr(self.error)

    def __repr__(self):
        return f"DeserializationError({self.error!r})"


class DeserializationResult(Generic[Output]):
    """Abstract base class for return value of `Serializer.from_data`."""

    @abstractmethod
    def or_die(self, exception: Exception | type[Exception] = DeserializationError) -> Output:
        """Return value or raise exception.

        If this is a `DeserializationSuccess`, return the value. If this is a
        `DeserializationFailure`, raise an exception. The error may be supplied.
        If the exception is an instance of `BaseException`, it is simply raised.
        Otherwise, it is called with the contents of `self.error` and then
        raised. By default, a `DeserializationError` is constructed and raised.
        """


@dataclass(frozen=True)
class DeserializationFailure(DeserializationResult[NoReturn]):
    """Container for error indicating failure to deserialize.

    This is returned whenever `Serializer.from_data` fails. The `error`
    parameter must be JSON serializable so that it can be returned in an HTTP
    response.
    """

    error: Any

    def or_die(self, exception: Exception | type[Exception] = DeserializationError) -> NoReturn:
        if isinstance(exception, Exception):
            # Simply raise a fully formed exception
            raise exception
        else:
            # Pass error structure to an exception class or other callable
            raise exception(self.error)


@dataclass(frozen=True)
class DeserializationSuccess(Generic[Output], DeserializationResult[Output]):
    """Container for deserialized value.

    This is returned whenever `Serializer.from_data` succeeds. The `value`
    parameter can be any Python object.
    """

    value: Output

    def or_die(self, exception: Exception | type[Exception] = DeserializationError) -> Output:
        return self.value
