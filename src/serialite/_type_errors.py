__all__ = [
    "ExpectedBooleanError",
    "ExpectedDictionaryError",
    "ExpectedFloatError",
    "ExpectedIntegerError",
    "ExpectedListError",
    "ExpectedNullError",
    "ExpectedStringError",
]

from dataclasses import dataclass
from typing import Any

from ._decorators import serializable


@serializable
@dataclass(frozen=True, slots=True)
class ExpectedStringError(Exception):
    actual: Any

    def __str__(self) -> str:
        return f"Expected string, but got {self.actual!r}"


@serializable
@dataclass(frozen=True, slots=True)
class ExpectedIntegerError(Exception):
    actual: Any

    def __str__(self) -> str:
        return f"Expected integer, but got {self.actual!r}"


@serializable
@dataclass(frozen=True, slots=True)
class ExpectedFloatError(Exception):
    actual: Any

    def __str__(self) -> str:
        return f"Expected float, but got {self.actual!r}"


@serializable
@dataclass(frozen=True, slots=True)
class ExpectedBooleanError(Exception):
    actual: Any

    def __str__(self) -> str:
        return f"Expected boolean, but got {self.actual!r}"


@serializable
@dataclass(frozen=True, slots=True)
class ExpectedListError(Exception):
    actual: Any

    def __str__(self) -> str:
        return f"Expected list, but got {self.actual!r}"


@serializable
@dataclass(frozen=True, slots=True)
class ExpectedDictionaryError(Exception):
    actual: Any

    def __str__(self) -> str:
        return f"Expected dictionary, but got {self.actual!r}"


@serializable
@dataclass(frozen=True, slots=True)
class ExpectedNullError(Exception):
    actual: Any

    def __str__(self) -> str:
        return f"Expected null, but got {self.actual!r}"
