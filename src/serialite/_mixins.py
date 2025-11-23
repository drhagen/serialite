__all__ = ["AbstractSerializableMixin", "SerializableMixin"]

from typing import Any, ClassVar

from ._base import Serializable
from ._descriptors import classproperty
from ._errors import Errors
from ._fields_serializer import FieldsSerializer, no_default
from ._result import Failure, Success


class SerializableMixin(Serializable):
    """A mixin to make simple classes serializable.

    This mixin inspects an abstract `__fields_serializer__` to provide an
    implementation for `Serializable`.
    """

    __fields_serializer__: ClassVar[FieldsSerializer]

    @classmethod
    def from_data(cls, data):
        match cls.__fields_serializer__.from_data(data):
            case Failure(error):
                return Failure(error)
            case Success(value):
                return Success(cls(**value))

    def to_data(self):
        return self.__fields_serializer__.to_data(self, source="object")

    @classmethod
    def to_openapi_schema(cls, force: bool = False):
        if force:
            schema = cls.__fields_serializer__.to_openapi_schema()

            if hasattr(cls, "__subclass_serializers__"):
                # It is not possible in OpenAPI to have the discriminator field
                # only in places where the base class is expected (that is,
                # where it is needed), so we have to say that it is accepted for
                # the subclass, even though it is not. This works as long as no
                # place in the API accepts just a concrete class.

                discriminator_field = {"_type": {"type": "string", "enum": [cls.__name__]}}
                schema = schema | {"properties": discriminator_field | schema["properties"]}

            return schema
        else:
            return {"$ref": f"#/$defs/{cls.__name__}"}

    @classproperty
    def model_fields(cls) -> dict[str, Any]:
        """Build Pydantic FieldInfo objects from __fields_serializer__.

        This allows Pydantic's get_flat_models_from_model to discover
        nested Serializable types.
        """
        from pydantic.fields import FieldInfo
        from pydantic_core import PydanticUndefined

        if not hasattr(cls, "__fields_serializer__"):
            return {}

        fields = {}
        # Get type annotations from the class
        annotations = getattr(cls, "__annotations__", {})

        for name, field in cls.__fields_serializer__.object_field_serializers.items():
            # Try to get the annotation from __annotations__ first
            if name in annotations:
                annotation = annotations[name]
            # If the serializer is itself a type (e.g. a Serializable class),
            # use that as the annotation
            elif isinstance(field.serializer, type):
                annotation = field.serializer
            # Otherwise fall back to Any
            else:
                annotation = Any

            # Determine the default value
            if field.default is no_default:
                default = PydanticUndefined
            else:
                default = field.default

            # Create a FieldInfo for this field
            fields[name] = FieldInfo(
                annotation=annotation,
                default=default,
            )

        return fields


class AbstractSerializableMixin(Serializable):
    """Provides Serializable for abstract base classes.

    This mixin inspects an abstract `__subclass_serializers__` to provide an
    implementation for `Serializable`.

    This provides a standard way to serialize instances of an abstract base
    class. The concrete classes must be `Serializable`; that is, they have
    their own implementation of `from_data` and `to_data` for serializing and
    deserializing instances of themselves. The concrete classes must also
    deserialize from and serialize to a dictionary. This is important because
    `to_data` of this mixin will add the key "_type" to the dictionary
    containing the name of the subclass. Likewise, `from_data` of this mixin
    will look for the key "_type" to determine which subclass to dispatch the
    remainder of the dictionary to.
    """

    __subclass_serializers__: ClassVar[dict[str, Serializable]]

    @classmethod
    def from_data(cls, data):
        try:
            type_name = data["_type"]
        except KeyError:
            from ._field_errors import RequiredTypeFieldError

            return Failure(Errors.one(RequiredTypeFieldError(), location=["_type"]))
        except TypeError:
            # Import locally to avoid circular import at module import time
            from ._type_errors import ExpectedDictionaryError

            return Failure(Errors.one(ExpectedDictionaryError(data)))

        # The rest of data
        subclass_data = {key: value for key, value in data.items() if key != "_type"}

        subclass = cls.__subclass_serializers__.get(type_name)
        if subclass is None:
            from ._field_errors import UnknownClassError

            return Failure(
                Errors.one(
                    UnknownClassError(type_name, list(cls.__subclass_serializers__.keys())),
                    location=["_type"],
                )
            )
        else:
            return subclass.from_data(subclass_data)

    @classmethod
    def to_data(cls, value):
        if not isinstance(value, cls):
            raise TypeError(f"Expected instance of {cls}, but got {value}")

        if value.to_data == cls.to_data:
            raise TypeError(
                "Recursion in AbstractSerializableMixin.to_data detected while processing"
                f" {value}.This likely do to a failure to implement to_data on {type(value)}"
            )

        return {"_type": value.__class__.__name__} | value.to_data()

    @classmethod
    def to_openapi_schema(cls, force: bool = False):
        if force:
            return {
                "type": "object",
                "discriminator": {"propertyName": "_type"},
                "oneOf": [
                    subclass.to_openapi_schema()
                    for subclass in cls.__subclass_serializers__.values()
                ],
            }
        else:
            return {"$ref": f"#/$defs/{cls.__name__}"}

    @classproperty
    def model_fields(cls) -> dict[str, Any]:
        """Build Pydantic FieldInfo objects from __subclass_serializers__.

        For abstract classes, we create a discriminated union field that
        references all the subclasses. This allows Pydantic to discover
        all subclasses.
        """
        from typing import Union

        from pydantic.fields import FieldInfo

        if not hasattr(cls, "__subclass_serializers__"):
            return {}

        # Create a Union type of all subclasses
        subclass_types = list(cls.__subclass_serializers__.values())
        if not subclass_types:
            return {}

        # For a discriminated union, we need a field for the discriminator
        # and the value can be any of the subclasses
        if len(subclass_types) == 1:
            union_type = subclass_types[0]
        else:
            union_type = Union[tuple(subclass_types)]

        # Return a synthetic field that represents the discriminated union
        # The _type field is the discriminator, but we model this as a single
        # field that can be any of the subclasses
        return {
            "_value": FieldInfo(
                annotation=union_type,
                default=...,  # Required field
            )
        }
