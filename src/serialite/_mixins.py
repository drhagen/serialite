__all__ = ["SerializableMixin", "AbstractSerializableMixin"]

from typing import ClassVar

from ._base import Serializable, Serializer
from ._fields_serializer import FieldsSerializer
from ._result import DeserializationFailure, DeserializationSuccess
from ._stable_set import StableSet


class SerializableMixin(Serializable):
    """A mixin to make simple classes serializable.

    This mixin inspects an abstract `__fields_serializer__` to provide an
    implementation for `Serializable`.
    """

    __fields_serializer__: ClassVar[FieldsSerializer]

    @classmethod
    def from_data(cls, data):
        value_or_error = cls.__fields_serializer__.from_data(data)

        if isinstance(value_or_error, DeserializationFailure):
            return value_or_error
        else:
            return DeserializationSuccess(cls(**value_or_error.value))

    def to_data(self):
        return self.__fields_serializer__.to_data(self, source="object")

    @classmethod
    def collect_openapi_models(cls, parent_models: StableSet[Serializer]) -> StableSet[Serializer]:
        # Every class that uses AbstractSerializableMixin gets put into the OpenAPI models.
        if cls not in parent_models:
            this_set = StableSet(cls)
            parent_models |= this_set
            return this_set | cls.__fields_serializer__.collect_openapi_models(parent_models)

    @classmethod
    def to_openapi_schema(cls, refs: dict[Serializer, str], force: bool = False):
        if force or cls not in refs:
            schema = cls.__fields_serializer__.to_openapi_schema(refs)

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
            return refs[cls]


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
            return DeserializationFailure({"_type": "This field is required."})
        except TypeError:
            return DeserializationFailure(f"Not a dictionary: {data!r}")

        # The rest of data
        subclass_data = {key: value for key, value in data.items() if key != "_type"}

        subclass = cls.__subclass_serializers__.get(type_name)
        if subclass is None:
            return DeserializationFailure({"_type": f"Class not found: {type_name!r}"})
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
    def collect_openapi_models(cls, parent_models: StableSet[Serializer]) -> StableSet[Serializer]:
        # Every class that uses AbstractSerializableMixin gets put into the OpenAPI models.
        if cls not in parent_models:
            this_set = StableSet(cls)
            parent_models |= this_set
            models = StableSet()
            for subclass in cls.__subclass_serializers__.values():
                models |= subclass.collect_openapi_models(parent_models)
            return this_set | models
        else:
            return StableSet()

    @classmethod
    def to_openapi_schema(cls, refs: dict[Serializer, str], force: bool = False):
        if force or cls not in refs:
            return {
                "type": "object",
                "discriminator": {"propertyName": "_type"},
                "oneOf": [
                    subclass.to_openapi_schema(refs)
                    for subclass in cls.__subclass_serializers__.values()
                ],
            }
        else:
            return refs[cls]
