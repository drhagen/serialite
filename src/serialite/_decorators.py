__all__ = ["serializable", "abstract_serializable"]

import dataclasses
from dataclasses import MISSING
from functools import wraps
from typing import get_type_hints

from ._base import Serializable, Serializer
from ._descriptors import classproperty
from ._fields_serializer import FieldsSerializer, SingleField, no_default
from ._mixins import AbstractSerializableMixin, SerializableMixin

# Allow commented out code in this file because it is important documentation
# ruff: noqa: ERA001


# Inspired by https://stackoverflow.com/a/14412901/1485877
def flexible_decorator(dec):
    """A decorator decorator to allow it to be used with or without parameters.

    Decorate a decorator like this:

    @decorator
    def multiply(f, factor=2):
        # Multiply a function's return value by some factor
        @wraps(f)
        def wrap(*args, **kwargs):
            return factor * f(*args, **kwargs)
        return wrap

    Then use the decorator in any of the following ways:

    @multiply
    def f1(x, y):
        return x + y

    @multiply(3)
    def f2(x, y):
        return x * y

    @multiply(factor=5)
    def f3(x, y):
        return x - y

    assert f1(2, 3) == (2 + 3) * 2
    assert f2(2, 5) == (2 * 5) * 3
    assert f3(8, 1) == (8 - 1) * 5

    Note that this technique will fail if the decorator can be parameterized
    with a single positional argument that is callable.
    """

    @wraps(dec)
    def new_dec(*args, **kwargs):
        if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
            # Bare decorated function
            return dec(args[0])
        else:
            # Decorator called with arguments
            return lambda f: dec(f, *args, **kwargs)

    return new_dec


def infer_fields_serializer(cls):
    from . import serializer

    if "__fields_serializer__" in cls.__dict__:
        raise TypeError(
            "Cannot apply serializable decorator to a class that already defines"
            " __fields_serializer__. Remove __fields_serializer__ so that serializable can add it"
            " or inherit from SerializableMixin to use the __fields_serializer__ that is already"
            " defined."
        )

    if dataclasses.is_dataclass(cls):
        # The field serializers and default values are inferred from the dataclass fields.
        # If available, the serializer on the dataclass field takes priority
        fields = dataclasses.fields(cls)
        types = get_type_hints(cls)

        serializer_fields = {}
        for field in fields:
            maybe_serializer = field.metadata.get("serializer", MISSING)
            if maybe_serializer is not MISSING:
                field_serializer = maybe_serializer
            else:
                field_serializer = serializer(types[field.name])

            maybe_default = field.default
            maybe_factory_default = field.default_factory
            if maybe_default is MISSING and maybe_factory_default is MISSING:
                # Recast to our sentinel for no default
                field_default = no_default
            elif maybe_default is not MISSING:
                field_default = maybe_default
            elif maybe_factory_default is not MISSING:
                field_default = maybe_factory_default()

            serializer_fields[field.name] = SingleField(field_serializer, default=field_default)

        cls.__fields_serializer__ = FieldsSerializer(**serializer_fields)
    else:
        raise TypeError("The serializable decorator can only be applied to dataclasses.")


@flexible_decorator
def serializable(cls):
    """Decorator that provides Serializable interface.

    This decorator can be applied to a dataclass. It inserts `SerializableMixin`
    at the front of the list of base classes and generates a reasonable
    `__fields_serializer__` class attribute from the dataclass fields.
    """
    infer_fields_serializer(cls)

    new_bases = (SerializableMixin, *cls.__bases__)
    try:
        # Try to mutate the bases of the class in place.
        # This will fail if the only base is `object`.
        cls.__bases__ = new_bases
        cls.__init_subclass__()
    except TypeError:
        # If that fails, create a new class with the same name
        # This breaks any descriptors--in particular, cached_property--so do not use this technique
        # cls = type(cls.__name__, (SerializableMixin,) + cls.__bases__, dict(cls.__dict__))

        # Add the appropriate methods directly to the class
        # Only supply implementation if it was not supplied in class
        # Get the canonical implementations from Serializable and SerializableMixin.
        # Get the method from the __dict__ and not from attribute access so that
        # we get the unbound methods rather than the bound ones.
        if "from_data" not in cls.__dict__:
            cls.from_data = SerializableMixin.__dict__["from_data"]

        if "to_data" not in cls.__dict__:
            cls.to_data = SerializableMixin.__dict__["to_data"]

        if "collect_openapi_models" not in cls.__dict__:
            cls.collect_openapi_models = SerializableMixin.__dict__["collect_openapi_models"]

        if "to_openapi_schema" not in cls.__dict__:
            cls.to_openapi_schema = SerializableMixin.__dict__["to_openapi_schema"]

        if "_is_pydantic_base_model" not in cls.__dict__:
            cls._is_pydantic_base_model = Serializable.__dict__["_is_pydantic_base_model"]

        if "validate" not in cls.__dict__:
            cls.validate = Serializable.__dict__["validate"]

        if "__get_validators__" not in cls.__dict__:
            cls.__get_validators__ = Serializable.__dict__["__get_validators__"]

        if "__config__" not in cls.__dict__:
            cls.__config__ = Serializable.__dict__["__config__"]

        if "dict" not in cls.__dict__:
            cls.dict = Serializable.__dict__["dict"]

        if "__processed__" not in cls.__dict__:
            cls.__processed__ = Serializable.__dict__["__processed__"]

    return cls


@classproperty
def __subclass_serializers__(cls) -> dict[str, Serializer]:  # noqa: N807
    return {subclass.__name__: subclass for subclass in cls.__subclasses__()}


def infer_subclass_serializers(cls):
    if "__subclass_serializers__" in cls.__dict__:
        raise TypeError(
            "Cannot apply abstract_serializable decorator to a class that already defines"
            " __subclass_serializers__. Remove __subclass_serializers__ so that"
            " abstract_serializable can add it or inherit from AbstractSerializableMixin to use"
            " the __subclass_serializers__ that is already defined."
        )

    cls.__subclass_serializers__ = __subclass_serializers__


@flexible_decorator
def abstract_serializable(cls):
    """Decorator that provides AbstractSerializableMixin interface.

    This decorator can be applied to an abstract class. It inserts
    `AbstractSerializableMixin` at the front of the list of base classes and
    generates a reasonable `__subclass_serializers__` class property.
    """
    infer_subclass_serializers(cls)

    new_bases = (AbstractSerializableMixin, *cls.__bases__)
    try:
        # Try to mutate the bases of the class in place.
        # This will fail if the only base is `object`.
        cls.__bases__ = new_bases
        cls.__init_subclass__()
    except TypeError:
        # If that fails, create a new class with the same name
        # This breaks any descriptors--in particular, cached_property--so do not use this technique
        # cls = type(
        #     cls.__name__,
        #     (AbstractSerializableMixin,) + cls.__bases__, dict(cls.__dict__),
        # )

        # Do the same thing as serializable, but use AbstractSerializableMixin
        # instead of SerializableMixin.
        if "from_data" not in cls.__dict__:
            cls.from_data = AbstractSerializableMixin.__dict__["from_data"]

        if "to_data" not in cls.__dict__:
            cls.to_data = AbstractSerializableMixin.__dict__["to_data"]

        if "__subclass_serializers__" not in cls.__dict__:
            cls.__subclass_serializers__ = AbstractSerializableMixin.__dict__[
                "__subclass_serializers__"
            ]

        if "collect_openapi_models" not in cls.__dict__:
            cls.collect_openapi_models = AbstractSerializableMixin.__dict__[
                "collect_openapi_models"
            ]

        if "to_openapi_schema" not in cls.__dict__:
            cls.to_openapi_schema = AbstractSerializableMixin.__dict__["to_openapi_schema"]

        if "_is_pydantic_base_model" not in cls.__dict__:
            cls._is_pydantic_base_model = Serializable.__dict__["_is_pydantic_base_model"]

        if "validate" not in cls.__dict__:
            cls.validate = Serializable.__dict__["validate"]

        if "__get_validators__" not in cls.__dict__:
            cls.__get_validators__ = Serializable.__dict__["__get_validators__"]

        if "__config__" not in cls.__dict__:
            cls.__config__ = Serializable.__dict__["__config__"]

        if "dict" not in cls.__dict__:
            cls.dict = Serializable.__dict__["dict"]

        if "__processed__" not in cls.__dict__:
            cls.__processed__ = Serializable.__dict__["__processed__"]

    return cls
