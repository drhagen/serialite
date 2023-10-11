from abc import abstractmethod
from dataclasses import dataclass

from serialite import (
    AbstractSerializableMixin,
    DeserializationFailure,
    DeserializationSuccess,
    serializable,
)


class DataAbstractSerializableClass(AbstractSerializableMixin):
    __subclass_serializers__ = {}

    @abstractmethod
    def get_value(self):
        raise NotImplementedError()


# Subclass A: implements from_data and to_data
# This class does not have @serializable decorator by design
class DataSubClassSerializableA(DataAbstractSerializableClass):
    value: float

    @classmethod
    def from_data(cls, data):
        return DeserializationSuccess(data["value"])

    @classmethod
    def to_data(cls, value):
        return {"value": value}

    def get_value(self):
        return self.value


DataSubClassSerializableA.__subclass_serializers__["DataSubClassSerializableA"] = (
    DataSubClassSerializableA
)


def test_from_data_valid():
    data = {"_type": "DataSubClassSerializableA", "value": 2.4}
    assert DataAbstractSerializableClass.from_data(data) == DeserializationSuccess(2.4)


def test_from_data_no_type():
    data = {"value": 2.4}
    actual = DataAbstractSerializableClass.from_data(data)
    expected = DeserializationFailure({"_type": "This field is required."})
    assert actual == expected


def test_from_data_not_a_dict():
    data = "Boom"
    actual = DataAbstractSerializableClass.from_data(data)
    expected = DeserializationFailure("Not a dictionary: 'Boom'")
    assert actual == expected


def test_from_data_not_a_subclass():
    data = {"_type": "NotThere", "value": 2.4}
    actual = DataAbstractSerializableClass.from_data(data)
    expected = DeserializationFailure({"_type": "Class not found: 'NotThere'"})
    assert actual == expected


# Base class with serializable decorator
@serializable
@dataclass(frozen=True)
class DataSerializableClass:
    dimension: int
    value: float
    name: str
    outputs: dict[str, float]


def test_valid_inputs():
    data = {"dimension": 3, "value": 5.6, "name": "macrophage", "outputs": {"a": 1.2, "b": 3.4}}
    value = DataSerializableClass(3, 5.6, "macrophage", {"a": 1.2, "b": 3.4})

    assert DataSerializableClass.from_data(data) == DeserializationSuccess(value)
    assert DataSerializableClass.to_data(value) == data


def test_from_data_failure():
    # Missing required field: name
    data = {"dimension": 3, "value": 5.6, "outputs": {"a": 1.2, "b": 3.4}}
    assert DataSerializableClass.from_data(data) == DeserializationFailure(
        {"name": "This field is required."}
    )

    # Deserialization failure
    data = {"dimension": 3, "value": 5.6, "name": "macrophage", "outputs": "Boom"}
    assert DataSerializableClass.from_data(data) == DeserializationFailure(
        {"outputs": "Not a valid dict: 'Boom'"}
    )
