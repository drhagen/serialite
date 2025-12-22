from __future__ import annotations

__all__ = ["ErrorElement", "Errors", "ValidationError", "ValidationExceptionGroup", "raise_errors"]

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, NoReturn, Self, TypedDict


@dataclass(frozen=True, slots=True)
class ValidationError(Exception):
    """A simple exception wrapper.

    It is best practice to define a specific exception for each error case.
    However, this may be used when no specific exception type is available.

    Attributes:
        message: The error message.
    """

    message: str

    def __str__(self) -> str:
        return self.message


@dataclass(frozen=True, slots=True, init=False)
class ValidationExceptionGroup(ExceptionGroup):
    """An ExceptionGroup raised by Errors.raise_on_errors.

    This exception wraps multiple validation errors, maintaining the location
    context for each error through the `ErrorElement` structure. It is an
    immutable, non-empty mirror of the `Errors` data structure.

    Attributes:
        errors: A tuple of `ErrorElement` objects.
    """

    errors: tuple[ErrorElement, ...]

    def __new__(cls, errors: Sequence[ErrorElement]) -> Self:
        message = "Validation errors"
        exceptions = [error.error for error in errors]
        return ExceptionGroup.__new__(cls, message, exceptions)

    def __init__(self, errors: Sequence[ErrorElement]) -> None:
        object.__setattr__(self, "errors", tuple(errors))


class ErrorData(TypedDict):
    """The serialized form of an `ErrorElement`.

    This exists purely for type hinting.
    """

    location: tuple[str | int, ...]
    type: str
    message: str
    context: Any | None


@dataclass(frozen=True, slots=True)
class ErrorElement:
    """An individual error with its location in the data structure.

    The user should not construct this directly, but use `Errors.add` or
    `Errors.one` instead.

    Attributes:
        error: The error that occurred. If this is a `Serializable`, it will
            be serialized when the `Errors` object is serialized.
        location: The location in the data structure where the error occurred.
    """

    error: Exception
    location: tuple[str | int, ...] = field(kw_only=False)

    def to_data(self) -> ErrorData:
        return {
            "location": list(self.location),
            "type": type(self.error).__name__,
            "message": str(self.error),
            "context": self.error.to_data() if hasattr(self.error, "to_data") else None,
        }


@dataclass(slots=True)
class Errors:
    """A collection of errors that occurred during deserialization.

    This is a mutable object for accumulating validation errors that are found
    and their locations in the data structure. The constructor should not be
    used directly, but rather the static method `Errors.one` or the instance
    methods `add` and `extend`.

    Attributes:
        errors: The list of `ErrorElement` objects.
    """

    errors: list[ErrorElement] = field(default_factory=list)

    @staticmethod
    def one(error: Exception, *, location: Sequence[str | int] = ()) -> Errors:
        """Construct and return a new `Errors` object containing a single
        `ErrorElement`.

        This is a convenience constructor intended for places where a
        single-error `Errors` value is needed and `add` would be inconvenient.

        Args:
            error: The error that occurred. If this is a `Serializable`, it will
                be serialized when the `Errors` object is serialized.
            location: The location in the data structure where the error
                occurred.
        """
        return Errors([ErrorElement(error, location=tuple(location))])

    def is_empty(self) -> bool:
        """Check if there are any errors.

        Returns:
            bool: True if there are no errors, False otherwise.
        """
        return len(self.errors) == 0

    def raise_on_errors(self) -> None:
        """Raise an exception if there are any errors.

        Raises:
            ValidationExceptionGroup: If there are errors, raises a
                ValidationExceptionGroup containing all the errors with
                their location information preserved.
        """
        if not self.is_empty():
            raise ValidationExceptionGroup(self.errors)

    def add(self, error: Exception, *, location: Sequence[str | int] = ()) -> None:
        """Add an error with its location in the data structure.

        This mutates the `Errors` object, constructing and appending a single
        `ErrorElement` to the list of errors.

        Args:
            error: The error that occurred. If this is a `Serializable`, it will
                be serialized when the `Errors` object is serialized.
            location: The location in the data structure where the error
                occurred.
        """
        self.errors.append(ErrorElement(error, location=tuple(location)))

    def extend(self, other: Errors, *, location: Sequence[str | int] = ()) -> None:
        """Extend this `Errors` object with another.

        This mutates the `Errors` object by fetching every error from `other`
        and adding it to `self`. The location of each error in `other` is
        prefixed with the provided `location`.

        Args:
            other: The other `Errors` object from which to fetch errors.
            location: The location prefix to add to each error in `other`.
        """
        for error in other.errors:
            self.errors.append(
                ErrorElement(error.error, location=tuple(location) + error.location)
            )

    def to_data(self) -> list[ErrorData]:
        """Convert to a data structure suitable for serialization.

        Returns:
            A list of `dict`s, each with three keys:
                "location": The location unchanged
                "type": The name of the class of the error
                "message": `str` of the error
                "context": Serialization of the error
        """
        return [element.to_data() for element in self.errors]


def raise_errors(errors: Errors) -> NoReturn:
    """Raise the errors contained in an Errors object.

    This is intended as a utility for use in the `Result.alt` method to raise an
    exception on `Failure`. Only non-empty `Errors` should be in the `Failure`.
    This function will raise a `ValueError` if applied to an empty `Errors`
    object.
    """
    errors.raise_on_errors()
    raise ValueError("Expected Errors object with at least one error, but it was empty.")
