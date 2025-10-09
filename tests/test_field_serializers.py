from uuid import UUID

import pytest

from serialite import (
    AccessPermissions,
    Errors,
    Failure,
    FieldsSerializer,
    MultiField,
    SingleField,
    Success,
    UuidSerializer,
    ValidationError,
    empty_default,
    serializer,
)


@pytest.mark.parametrize(
    "fields_serializer",
    [
        FieldsSerializer(myField=UUID),
        FieldsSerializer(myField=UuidSerializer()),
        FieldsSerializer(myField=SingleField(UUID)),
        FieldsSerializer(myField=SingleField(UuidSerializer())),
    ],
)
def test_single_field(fields_serializer):
    data = {"myField": "00112233-4455-6677-8899-aabbccddeeff"}
    value = {"myField": UUID("00112233-4455-6677-8899-aabbccddeeff")}

    assert fields_serializer.from_data(data) == Success(value)
    assert fields_serializer.to_data(value) == data


@pytest.mark.parametrize(
    "fields_serializer",
    [
        FieldsSerializer(myField=MultiField({"a": UUID})),
        FieldsSerializer(myField=MultiField({"a": UUID, "b": str})),
        FieldsSerializer(myField=MultiField({"b": str, "a": UUID}, to_data="a")),
        FieldsSerializer(myField=MultiField({"a": UuidSerializer()})),
    ],
)
def test_multi_field(fields_serializer):
    data = {"a": "00112233-4455-6677-8899-aabbccddeeff"}
    value = {"myField": UUID("00112233-4455-6677-8899-aabbccddeeff")}

    assert fields_serializer.from_data(data) == Success(value)
    assert fields_serializer.to_data(value) == data


@pytest.mark.parametrize(
    "fields_serializer",
    [
        FieldsSerializer(myField=SingleField(str, default="Pirate")),
        FieldsSerializer(myField=MultiField({"a": str, "b": int}, default="Pirate")),
    ],
)
def test_default_value(fields_serializer):
    data = {}
    value = {"myField": "Pirate"}

    assert fields_serializer.from_data(data) == Success(value)
    assert fields_serializer.to_data(value) == data


def test_from_data_not_dict():
    fields_serializer = FieldsSerializer()
    assert fields_serializer.from_data(1) == Failure(
        Errors.one(ValidationError("Not a dictionary: 1"))
    )


@pytest.mark.parametrize(
    "fields_serializer",
    [
        FieldsSerializer(a=int),
        FieldsSerializer(myField=MultiField({"b": str, "a": int})),
    ],
)
def test_from_data_deserialization_failure(fields_serializer):
    data = {"a": "2.5"}
    assert fields_serializer.from_data(data) == Failure(
        Errors.one(ValidationError("Not a valid integer: '2.5'"), location=["a"])
    )


def test_from_data_invalid_field():
    fields_serializer = FieldsSerializer(myField=str)
    assert fields_serializer.from_data({"c": 1, "myField": "Hello"}) == Failure(
        Errors.one(ValidationError("This field is invalid."), location=["c"])
    )


def test_from_data_invalid_field_allowed():
    fields_serializer = FieldsSerializer(myField=str)
    assert fields_serializer.from_data({"c": 1, "myField": "Hello"}, allow_unused=True) == Success(
        {"myField": "Hello"}
    )


def test_from_data_multi_field_repeated_fields():
    fields_serializer = FieldsSerializer(a=MultiField({"b": int, "c": str}))
    expected = Errors.one(
        ValidationError(
            "This field cannot be provided because these fields are already provided: b"
        ),
        location=["c"],
    )
    assert fields_serializer.from_data({"b": 2, "c": "Boom"}) == Failure(expected)


@pytest.mark.parametrize(
    "fields_serializer",
    [
        FieldsSerializer(myField=SingleField(UUID, default=empty_default)),
        FieldsSerializer(myField=MultiField({"myField": UUID, "alt": str}, default=empty_default)),
    ],
)
def test_from_data_default_value_empty_default(fields_serializer):
    data = {}
    value = {}
    assert fields_serializer.from_data(data) == Success(value)


def test_from_data_no_default_single_field():
    fields_serializer = FieldsSerializer(myField=SingleField(str))
    data = {}
    assert fields_serializer.from_data(data) == Failure(
        Errors.one(ValidationError("This field is required."), location=["myField"])
    )


def test_from_data_no_default_multi_field():
    fields_serializer = FieldsSerializer(myField=MultiField({"a": str, "b": int}))
    data = {}
    assert fields_serializer.from_data(data) == Failure(
        Errors.one(ValidationError("One of these fields is required: a, b"), location=["myField"])
    )


def test_from_data_field_not_writable():
    data = {"b": "Hiding"}

    fields_serializer = FieldsSerializer(
        myField=MultiField({"a": int, "b": str}, access=AccessPermissions.read_only)
    )
    assert fields_serializer.from_data(data) == Failure(
        Errors.one(ValidationError("This field is invalid."), location=["b"])
    )

    fields_serializer = FieldsSerializer(b=SingleField(str, access=AccessPermissions.read_only))
    assert fields_serializer.from_data(data, allow_unused=True) == Success({})


def test_to_data_default_value_no_hiding():
    value = {"myField": "Pirate"}

    fields_serializer = FieldsSerializer(
        myField=SingleField(str, default="Pirate", hide_default=False)
    )
    assert fields_serializer.to_data(value) == value

    fields_serializer = FieldsSerializer(
        myField=MultiField({"a": str, "b": int}, default="Pirate", hide_default=False)
    )
    assert fields_serializer.to_data(value) == {"a": "Pirate"}


def test_to_data_multi_field_use_to_data():
    fields_serializer = FieldsSerializer(myField=MultiField({"a": int, "b": str}))
    value = {"myField": 2}
    assert fields_serializer.to_data(value) == {"a": 2}

    fields_serializer = FieldsSerializer(myField=MultiField({"a": int, "b": str}, to_data="b"))
    value = {"myField": "3"}
    assert fields_serializer.to_data(value) == {"b": "3"}


def test_to_data_source_object():
    class TempObject:
        def __init__(self, a, b):
            self.a = a
            self.b = b

    fields_serializer = FieldsSerializer(a=int, b=str)
    actual = fields_serializer.to_data(TempObject(3, "Hello"), source="object")
    expected = {"a": 3, "b": "Hello"}
    assert actual == expected


def test_to_data_source_invalid():
    fields_serializer = FieldsSerializer(a=int)
    with pytest.raises(ValueError):
        _ = fields_serializer.to_data({"a": 1}, source="integer")


def test_to_data_field_not_readable():
    fields_serializer = FieldsSerializer(
        a=int, b=SingleField(serializer(str), access=AccessPermissions.write_only)
    )
    value = {"a": 3, "b": "Hiding"}
    expected = {"a": 3}  # Do not serialize b
    actual = fields_serializer.to_data(value)
    assert actual == expected


def test_empty_input():
    fields_serializer = FieldsSerializer()

    assert fields_serializer.from_data({}) == Success({})
    assert fields_serializer.to_data({}) == {}
