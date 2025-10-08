from collections import OrderedDict

import pytest

from serialite import (
    Errors,
    Failure,
    FloatSerializer,
    OrderedDictSerializer,
    StringSerializer,
    Success,
    ValidationError,
)

ordered_dict_serializer = OrderedDictSerializer(StringSerializer(), FloatSerializer())


def test_valid_inputs():
    # from_data: Accepts list of list or tuple (with 2 elements in each)
    data = [["A", 12.3], ["B", 15.5], ["C", 16.0]]
    value = OrderedDict([("A", 12.3), ("B", 15.5), ("C", 16.0)])

    assert ordered_dict_serializer.from_data(data) == Success(value)
    assert ordered_dict_serializer.to_data(value) == data


def test_from_data_failure_not_a_list():
    data = {"A": 12.3, "B": 15.5}
    actual = ordered_dict_serializer.from_data(data)
    assert actual == Failure(
        Errors.one(ValidationError("Not a valid list: {'A': 12.3, 'B': 15.5}"))
    )


def test_from_data_failure_keys():
    # 2- Deserializing keys generates failures
    data = [[True, 12.3], ["B", 15.5], [1, 16.0]]
    actual = ordered_dict_serializer.from_data(data)
    expected = Errors()
    expected.add(ValidationError("Not a valid string: True"), location=[0])
    expected.add(ValidationError("Not a valid string: 1"), location=[2])
    assert actual == Failure(expected)


def test_from_data_failure_values():
    data = [["A", "12.3"], ["B", 15.5], ["C", False]]
    actual = ordered_dict_serializer.from_data(data)
    expected = Errors()
    expected.add(ValidationError("Not a valid float: '12.3'"), location=["A"])
    expected.add(ValidationError("Not a valid float: False"), location=["C"])
    assert actual == Failure(expected)


def test_from_data_failure_items():
    data = [["A", 12.3], ["B", 15.5, 18.9], ["C", 16.0]]
    actual = ordered_dict_serializer.from_data(data)
    expected = Errors.one(
        ValidationError("Not a valid length-2 list: ['B', 15.5, 18.9]"), location=[1]
    )
    assert actual == Failure(expected)


def test_to_data_failure():
    with pytest.raises(ValueError):
        _ = ordered_dict_serializer.to_data([12.34, 15.5])
