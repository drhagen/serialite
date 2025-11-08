from collections import OrderedDict

import pytest

from serialite import (
    Errors,
    ExpectedFloatError,
    ExpectedLength2ListError,
    ExpectedListError,
    ExpectedStringError,
    Failure,
    FloatSerializer,
    OrderedDictSerializer,
    StringSerializer,
    Success,
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
    assert actual == Failure(Errors.one(ExpectedListError(data)))


def test_from_data_failure_keys():
    # 2- Deserializing keys generates failures
    data = [[True, 12.3], ["B", 15.5], [1, 16.0]]
    actual = ordered_dict_serializer.from_data(data)
    expected = Errors()
    expected.add(ExpectedStringError(True), location=[0, 0])
    expected.add(ExpectedStringError(1), location=[2, 0])
    assert actual == Failure(expected)


def test_from_data_failure_values():
    data = [["A", "12.3"], ["B", 15.5], ["C", False]]
    actual = ordered_dict_serializer.from_data(data)
    expected = Errors()
    expected.add(ExpectedFloatError("12.3"), location=[0, 1])
    expected.add(ExpectedFloatError(False), location=[2, 1])
    assert actual == Failure(expected)


def test_from_data_failure_items():
    data = [["A", 12.3], ["B", 15.5, 18.9], ["C", 16.0]]
    actual = ordered_dict_serializer.from_data(data)
    assert actual == Failure(Errors.one(ExpectedLength2ListError(["B", 15.5, 18.9]), location=[1]))


def test_to_data_failure():
    with pytest.raises(ValueError):
        _ = ordered_dict_serializer.to_data([12.34, 15.5])
