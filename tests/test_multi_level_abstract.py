from dataclasses import dataclass

import pytest

from serialite import (
    Errors,
    Failure,
    Success,
    UnknownClassError,
    abstract_serializable,
    serializable,
)


@abstract_serializable
@dataclass(frozen=True)
class Animal:
    name: str


@abstract_serializable
@dataclass(frozen=True)
class Pet(Animal):
    owner: str


@serializable
@dataclass(frozen=True)
class Dog(Pet):
    breed: str


@serializable
@dataclass(frozen=True)
class Cat(Pet):
    indoor: bool


@serializable
@dataclass(frozen=True)
class WildAnimal(Animal):
    habitat: str


@pytest.mark.parametrize(
    ("cls", "data", "value"),
    [
        (
            Animal,
            {"_type": "WildAnimal", "name": "Wolf", "habitat": "Forest"},
            WildAnimal(name="Wolf", habitat="Forest"),
        ),
        (
            Animal,
            {"_type": "Dog", "name": "Rex", "owner": "Alice", "breed": "Labrador"},
            Dog(name="Rex", owner="Alice", breed="Labrador"),
        ),
        (
            Animal,
            {"_type": "Cat", "name": "Whiskers", "owner": "Bob", "indoor": True},
            Cat(name="Whiskers", owner="Bob", indoor=True),
        ),
        (
            Pet,
            {"_type": "Dog", "name": "Rex", "owner": "Alice", "breed": "Labrador"},
            Dog(name="Rex", owner="Alice", breed="Labrador"),
        ),
    ],
)
def test_from_data(cls, data, value):
    assert cls.from_data(data) == Success(value)


@pytest.mark.parametrize(
    ("cls", "value", "data"),
    [
        (
            Animal,
            WildAnimal(name="Wolf", habitat="Forest"),
            {"_type": "WildAnimal", "name": "Wolf", "habitat": "Forest"},
        ),
        (
            Animal,
            Dog(name="Rex", owner="Alice", breed="Labrador"),
            {"_type": "Dog", "name": "Rex", "owner": "Alice", "breed": "Labrador"},
        ),
    ],
)
def test_to_data(cls, value, data):
    assert cls.to_data(value) == data


def test_subclass_serializers_contains_only_concrete_leaves():
    assert set(Animal.__subclass_serializers__.keys()) == {"Dog", "Cat", "WildAnimal"}


def test_unknown_type_lists_all_concrete_leaves():
    actual = Animal.from_data({"_type": "Fish", "name": "Nemo"})
    expected = Failure(
        Errors.one(
            UnknownClassError("Fish", ["Dog", "Cat", "WildAnimal"]),
            location=["_type"],
        )
    )
    assert actual == expected


def test_intermediate_rejects_sibling_subclass():
    actual = Pet.from_data({"_type": "WildAnimal", "name": "Wolf", "habitat": "Forest"})
    expected = Failure(
        Errors.one(
            UnknownClassError("WildAnimal", ["Dog", "Cat"]),
            location=["_type"],
        )
    )
    assert actual == expected
