from __future__ import annotations

__all__ = [
    "FieldsSerializer",
    "AccessPermissions",
    "FieldsSerializerField",
    "SingleField",
    "MultiField",
    "no_default",
    "empty_default",
]

from collections.abc import Mapping
from enum import Enum, auto
from typing import Any

from ._base import Serializer
from ._result import DeserializationFailure, DeserializationResult, DeserializationSuccess
from ._stable_set import StableSet

# A sentinel object to indicate that a default is not available,
# so an error should be raised if the item is not found
no_default = object()

# A sentinel object to indicate that a default is not necessary,
# so the associated field should remain blank
empty_default = object()


class AccessPermissions(Enum):
    read_write = auto()
    read_only = auto()
    write_only = auto()

    def readable(self):
        return self == AccessPermissions.read_write or self == AccessPermissions.read_only

    def writeable(self):
        return self == AccessPermissions.read_write or self == AccessPermissions.write_only


class FieldsSerializerField:
    def __init__(
        self,
        *,
        default: Any = no_default,
        hide_default: bool = True,
        access: AccessPermissions = AccessPermissions.read_write,
    ):
        """Abstract base class for arguments to FieldsSerializer.

        Subclasses of this algebraic data type serve a single purpose in
        fulfilling the `object_field_serializers` argument of
        `FieldsSerializer`.
        """
        self.default = default
        self.hide_default = hide_default
        self.access = access

    @property
    def readable(self):
        return self.access.readable()

    @property
    def writable(self):
        return self.access.writeable()


class SingleField(FieldsSerializerField):
    def __init__(
        self,
        serializer: Serializer | Any,
        *,
        default: Any = no_default,
        hide_default: bool = True,
        access: AccessPermissions = AccessPermissions.read_write,
    ):
        """A field serializer with a direct data field to object field mapping.

        This is only useful as an argument to `FieldsSerializer`. It represents
        a field where the name of the field in the data is the same as the name
        of the field on the object.

        `serializer` is either a `serialite.Serializer` or an object which can
        be passed to `serialite.serializer` to obtain one.

        `default` controls what happens if the data does not provide a value for
        this field. If it is the sentinel `no_default`, then a failure is
        generated. If it is the sentinel `empty_default`, then no value for this
        field is given. If it is any other value, then that value is given for
        this field.

        If `hide_default` is `True`, when serializing, if the serialized value
        equals `default`, then the field is omitted from the serialized data.

        If `access` is `read_write`, the field is used when both deserializing
        and serializing. If it is `read_only`, the field is only used when
        serializing. If it is `write_only`, the field is only used when
        deserializing.
        """
        from . import serializer as lookup_serializer

        if not isinstance(serializer, Serializer):
            serializer = lookup_serializer(serializer)

        super().__init__(default=default, hide_default=hide_default, access=access)
        self.serializer = serializer


class MultiField(FieldsSerializerField):
    def __init__(
        self,
        serializers: dict[str, Serializer | Any],
        *,
        default: Any = no_default,
        hide_default: bool = True,
        access: AccessPermissions = AccessPermissions.read_write,
        to_data: str = None,  # noqa: RUF013
    ):
        """A field serializer with a direct data field to object field mapping.

        This is only useful as an argument to `FieldsSerializer`. It represents
        a field where there are multiple data fields that can map to a single
        object field. The name of the data field controls which serializer is
        applied. Multiple data fields being satisfied results in a failure.

        Each value in `serializers` is either a `serialite.Serializer` or an
        object which can be passed to `serialite.serializer` to obtain one.

        `default` controls what happens if the data does not provide a value for
        this field. If it is the sentinel `no_default`, then a failure is
        generated. If it is the sentinel `empty_default`, then no value for this
        field is given. If it is any other value, then that value is given for
        this field.

        If `hide_default` is `True`, when serializing, if the serialized value
        equals `default`, then the field is omitted from the serialized data.

        If `access` is `read_write`, the field is used when both deserializing
        and serializing. If it is `read_only`, the field is only used when
        serializing. If it is `write_only`, the field is only used when
        deserializing.

        `to_data` determines which serializer is used when serializing to data.
        If this is not provided, then the first serializer in `serializers` is
        used.
        """
        from . import serializer

        cleaned_field_serializers = {}
        for name, field in serializers.items():
            # Serializers can be instances or subclasses of base class Serializer
            if (
                isinstance(field, Serializer)
                or isinstance(field, type)
                and issubclass(field, Serializer)
            ):
                cleaned_field_serializers[name] = field
            else:
                cleaned_field_serializers[name] = serializer(field)

        if to_data is None:
            to_data = next(iter(serializers.keys()))

        super().__init__(default=default, hide_default=hide_default, access=access)
        self.serializers = cleaned_field_serializers
        self.to_data = to_data


class FieldsSerializer(Mapping):
    # Implement mapping so that __fields_serializer__ of a base class can be **kwarg
    # into a subclass

    def __init__(self, **object_field_serializers: FieldsSerializerField | Serializer | Any):
        from . import serializer

        # Raw serializers are wrapped in `SingleField`s,
        # other objects get a lookup for their serializer
        cleaned_object_field_serializers = {}
        for name, field in object_field_serializers.items():
            if isinstance(field, FieldsSerializerField):
                cleaned_object_field_serializers[name] = field
            elif (
                isinstance(field, Serializer)
                or isinstance(field, type)
                and issubclass(field, Serializer)
            ):
                cleaned_object_field_serializers[name] = SingleField(field)
            else:
                cleaned_object_field_serializers[name] = SingleField(serializer(field))

        self.object_field_serializers = cleaned_object_field_serializers

        data_field_deserializers = {}
        data_name_to_object_name = {}
        for object_field_name, field_serializer in self.object_field_serializers.items():
            if isinstance(field_serializer, SingleField):
                if object_field_name in data_field_deserializers:
                    raise ValueError(
                        f"Data field name appears multiple times: {object_field_name}"
                    )
                data_field_deserializers[object_field_name] = field_serializer.serializer
                data_name_to_object_name[object_field_name] = object_field_name
            elif isinstance(field_serializer, MultiField):
                for data_field_name, serializer in field_serializer.serializers.items():
                    if data_field_name in data_field_deserializers:
                        raise ValueError(
                            f"Data field name appears multiple times: {object_field_name}"
                        )
                    data_field_deserializers[data_field_name] = serializer
                    data_name_to_object_name[data_field_name] = object_field_name

        # Mapping of data field name to deserializer.
        # Because of `MultiField`s, there may be legal data fields that are not keys of
        # `self.serializers`. This collects all the possible field names with their associated
        # `Serializer`s.
        self.data_field_deserializers = data_field_deserializers

        # Mapping of each data field name to its object field name.
        # `MultiField`s allow for the data field name to be different from the object field name to
        # which it maps. This provides the mapping from data field name to object field name.
        self.data_name_to_object_name = data_name_to_object_name

    def from_data(self, data: dict[str, Any], *, allow_unused=False) -> DeserializationResult:
        """Deserialize fields from a dictionary.

        Complex objects are usually serialized as a dictionary, where each key
        of the dictionary is an object of a particular type. This function
        performs the following tasks required to deserialize such an object:

        (1) Check that the data is actually a dictionary.
        (2) Check that the keys in the data map to an object field.
            (a) If a field is missing, a default value may be supplied.
            (b) If there are extra keys in the data, this is a failure unless
                `allow_unused` is True
        (3) Run the deserializer for each field.

        This returns either (1) a `DeserializationSuccess` containing a
        dictionary with the same keys as `self.object_field_serializers` but the
        values have been replaced by the deserialized values of deserialized
        fields or (2) a `DeserializationFailure` containing a dictionary with
        the subset of keys from `self.object_field_serializers` whose
        deserializers failed and values containing the deserialization errors.

        If `format` is `"data"`, then the fields of the data are themselves data
        and `from_data` of each field serializer will be used. If `format` is
        `"string"`, then the fields of the data are still in string form and
        `from_string` of each serializer will be used. The former is for typical
        JSON data, while the latter is for query parameters.
        """
        # Return early if the data isn't even a dict
        if not isinstance(data, dict):
            return DeserializationFailure(f"Not a dictionary: {data!r}")

        values = {}
        errors = {}

        # Check that all data fields are valid, that all values are valid,
        # and map data fields to object fields
        for key, value in data.items():
            if (
                key not in self.data_name_to_object_name
                or not self.object_field_serializers[self.data_name_to_object_name[key]].writable
            ):
                # This data field name is not understood
                if not allow_unused:
                    # Fail it
                    errors[key] = "This field is invalid."
                else:
                    # Quietly ignore it
                    pass
            else:
                # This data field maps to an object field
                object_field_name = self.data_name_to_object_name[key]
                if object_field_name in values:
                    # If this object field is already filled, it must have been
                    # filled under a different data field name in the same
                    # MultiField serializer field. Find the data field name
                    # already used and report this field cannot be used as long
                    # as the first one is also used.
                    multi_field = self.object_field_serializers[object_field_name]
                    preexisting_keys = [
                        field_key
                        for field_key in multi_field.serializers.keys()
                        if field_key in data and field_key != key
                    ]
                    errors[key] = (
                        "This field cannot be provided because these fields are already provided: "
                        + ", ".join(preexisting_keys)
                    )
                else:
                    error_or_value = self.data_field_deserializers[key].from_data(value)

                    if isinstance(error_or_value, DeserializationFailure):
                        errors[key] = error_or_value.error

                        # Mark this object field as handled so that an additional error is not
                        # generated
                        values[object_field_name] = None
                    else:
                        values[object_field_name] = error_or_value.value

        # Check that object fields have been created, defaulted, or ignored
        for object_field_name, serializer_field in self.object_field_serializers.items():
            if object_field_name not in values and serializer_field.writable:
                if serializer_field.default is no_default:
                    # This field is required
                    if isinstance(serializer_field, SingleField):
                        errors[object_field_name] = "This field is required."
                    elif isinstance(serializer_field, MultiField):
                        error_message = "One of these fields is required: " + ", ".join(
                            serializer_field.serializers.keys()
                        )
                        errors[object_field_name] = error_message
                    else:
                        raise TypeError(
                            f"Expected FieldsSerializerField, not {type(serializer_field)}"
                        )
                elif serializer_field.default is empty_default:
                    # This field can be ignored
                    pass
                else:
                    # This field has a default value
                    values[object_field_name] = serializer_field.default

        if len(errors) > 0:
            return DeserializationFailure(errors)
        else:
            return DeserializationSuccess(values)

    def to_data(self, values, *, source="dictionary"):
        """Serialize fields to a dictionary.

        For each item in `self.object_field_serializers`, the item in `values`
        with the corresponding key is extracted, its serializer is run, and the
        serialized value is put into the return dictionary.
        """
        data = {}
        for object_field_name, serializer_field in self.object_field_serializers.items():
            if not serializer_field.readable:
                # This field is not serialized
                continue

            if source == "dictionary":
                value = values[object_field_name]
            elif source == "object":
                value = getattr(values, object_field_name)
            else:
                raise ValueError(
                    f"Input argument source must be 'dictionary' or 'object' not {source!r}"
                )

            if (
                serializer_field.hide_default
                and serializer_field.default is not no_default
                and serializer_field.default is not empty_default
                and value == serializer_field.default
            ):
                # Do not serialize the value if it equals the default
                continue

            if isinstance(serializer_field, SingleField):
                serializer = serializer_field.serializer
                data_field_name = object_field_name
            elif isinstance(serializer_field, MultiField):
                serializer = serializer_field.serializers[serializer_field.to_data]
                data_field_name = serializer_field.to_data
            else:
                raise TypeError(f"Expected FieldsSerializerField, not {type(serializer_field)}")

            data[data_field_name] = serializer.to_data(value)

        return data

    def collect_openapi_models(
        self, parent_models: StableSet[Serializer]
    ) -> StableSet[Serializer]:
        models = StableSet()
        for serializer in self.data_field_deserializers.values():
            models |= serializer.collect_openapi_models(parent_models)
        return models

    def to_openapi_schema(self, refs: dict[Serializer, str]) -> dict[str, Any]:
        required = []
        properties = {}
        for name, field in self.object_field_serializers.items():
            if isinstance(field, SingleField):
                property = field.serializer.to_openapi_schema(refs)

                if field.default is not no_default and field.default is not None:
                    # OpenAPI generator 5 crashes if the default is null
                    property["default"] = field.serializer.to_data(field.default)
                else:
                    required.append(name)

                properties[name] = property
            else:
                raise NotImplementedError()

        return {
            "type": "object",
            "required": required,
            "properties": properties,
        }

    def __iter__(self):
        yield from self.object_field_serializers.keys()

    def __getitem__(self, item):
        return self.object_field_serializers[item]

    def __len__(self):
        return len(self.object_field_serializers)
