from dataclasses import dataclass

from serialite import abstract_serializable, serializable

garbage_collection_protection = []


@abstract_serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class Package:
    pass


@abstract_serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class PyPiPackage(Package):
    extras: list[str] | None = None


@serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class PyPiVersionPackage(PyPiPackage):
    version: str


@serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class PyPiPinnedPackage(PyPiVersionPackage):
    hash: str


@serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class CondaPackage(Package):
    version: str


# @dataclass(slots=True) creates a new class, leaving the original in
# __subclasses__() as a ghost. Hold strong references so ghosts survive GC
# and actually exercise the ghost-skipping logic.
garbage_collection_protection = [
    Package,
    PyPiPackage,
    PyPiVersionPackage,
    PyPiPinnedPackage,
    CondaPackage,
]


def test_subclass_serializers_contains_exactly_all_concrete():
    assert set(Package.__subclass_serializers__.keys()) == {
        "PyPiVersionPackage",
        "PyPiPinnedPackage",
        "CondaPackage",
    }
