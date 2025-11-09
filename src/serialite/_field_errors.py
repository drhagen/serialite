__all__ = [
    "ConflictingFieldsError",
    "RequiredFieldError",
    "RequiredOneOfFieldsError",
    "RequiredTypeFieldError",
    "UnknownClassError",
    "UnknownFieldError",
]

from dataclasses import dataclass

from ._decorators import serializable


@serializable
@dataclass(frozen=True, slots=True)
class UnknownFieldError(Exception):
    field_name: str

    def __str__(self) -> str:
        return f"Expected valid field, but got {self.field_name!r}"


@serializable
@dataclass(frozen=True, slots=True)
class ConflictingFieldsError(Exception):
    field_name: str
    existing_fields: list[str]

    def __str__(self) -> str:
        return f"Expected {self.field_name!r} to be provided alone, but got conflicting fields {self.existing_fields!r}"


@serializable
@dataclass(frozen=True, slots=True)
class RequiredFieldError(Exception):
    field_name: str

    def __str__(self) -> str:
        return f"Expected field {self.field_name!r}, but did not receive it"


@serializable
@dataclass(frozen=True, slots=True)
class RequiredOneOfFieldsError(Exception):
    field_names: list[str]

    def __str__(self) -> str:
        return f"Expected one of the fields {self.field_names!r}, but did not receive any"


@serializable
@dataclass(frozen=True, slots=True)
class RequiredTypeFieldError(Exception):
    def __str__(self) -> str:
        return "Expected field '_type', but did not receive it"


@serializable
@dataclass(frozen=True, slots=True)
class UnknownClassError(Exception):
    type_name: str
    known_types: list[str]

    def __str__(self) -> str:
        return f"Expected one of the known types {self.known_types!r}, but got {self.type_name!r}"
