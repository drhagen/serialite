from dataclasses import dataclass

import pytest

from serialite import (
    FieldsSerializer,
    SerializableMixin,
    Success,
    abstract_serializable,
    serializable,
)

# Allow commented-out code in this file for the hierarchy diagram
# ruff: noqa: ERA001


# Hierarchy under test:
#
# Base  (abstract, slots=True)
# ├── AbstractMiddle  (abstract, slots=True)
# │   ├── SlotsConcrete  (@serializable, slots=True)
# │   │   └── SlotsConcreteChild  (@serializable, slots=True)
# │   └── NoSlotsConcrete  (@serializable, no slots)
# ├── ManualConcrete  (hand-written from_data, no dataclass)
# ├── MixinConcrete  (SerializableMixin, __fields_serializer__)
# └── SlotsManualConcrete  (@dataclass(slots=True), hand-written from_data)
@abstract_serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class Base:
    pass


@abstract_serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class AbstractMiddle(Base):
    pass


@serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class SlotsConcrete(AbstractMiddle):
    x: int


@serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class SlotsConcreteChild(SlotsConcrete):
    y: str


@serializable
@dataclass(frozen=True, kw_only=True)
class NoSlotsConcrete(AbstractMiddle):
    z: float


class ManualConcrete(Base):
    @classmethod
    def from_data(cls, data):
        return Success(cls())

    def to_data(self):
        return {}


class MixinConcrete(SerializableMixin, Base):
    __fields_serializer__ = FieldsSerializer(value=int)

    def __init__(self, value: int):
        self.value = value


@dataclass(frozen=True, slots=True)
class SlotsManualConcrete(Base):
    w: int

    @classmethod
    def from_data(cls, data):
        return Success(cls(w=data["w"]))

    def to_data(self):
        return {"w": self.w}


def test_base_discovers_all_concrete():
    assert set(Base.__subclass_serializers__.keys()) == {
        "SlotsConcrete",
        "SlotsConcreteChild",
        "NoSlotsConcrete",
        "ManualConcrete",
        "MixinConcrete",
        "SlotsManualConcrete",
    }


def test_abstract_intermediate_discovers_own_subtree():
    assert set(AbstractMiddle.__subclass_serializers__.keys()) == {
        "SlotsConcrete",
        "SlotsConcreteChild",
        "NoSlotsConcrete",
    }


@pytest.mark.parametrize(
    ("name", "expected_cls"),
    [
        ("SlotsConcrete", SlotsConcrete),
        ("SlotsConcreteChild", SlotsConcreteChild),
        ("NoSlotsConcrete", NoSlotsConcrete),
        ("ManualConcrete", ManualConcrete),
        ("MixinConcrete", MixinConcrete),
        ("SlotsManualConcrete", SlotsManualConcrete),
    ],
)
def test_discovered_class_is_replacement_not_original(name, expected_cls):
    assert Base.__subclass_serializers__[name] is expected_cls


def test_original_class_with_class_body_from_data_is_skipped():
    all_subs = list(Base.__subclasses__())  # prevent GC

    original = next(
        (
            s
            for s in all_subs
            if s.__name__ == "SlotsManualConcrete" and "__slots__" not in vars(s)
        ),
        None,
    )
    assert original is not None, "Original class must exist for this test to be valid"
    assert "from_data" in original.__dict__
    assert Base.__subclass_serializers__["SlotsManualConcrete"] is not original
