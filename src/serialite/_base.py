from __future__ import annotations

__all__ = ["Serializer", "Serializable"]

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from ._descriptors import classproperty
from ._result import DeserializationFailure, DeserializationResult
from ._stable_set import StableSet

if TYPE_CHECKING:
    from pydantic.typing import AbstractSetIntStr, MappingIntStrAny

Output = TypeVar("Output")
SerializableOutput = TypeVar("SerializableOutput", bound="Serializable")


class Serializer(Generic[Output]):
    """Serialize and deserialize a particular object."""

    @abstractmethod
    def from_data(self, data: Any) -> DeserializationResult[Output]:
        """Deserialize an object from data."""
        raise NotImplementedError()

    @abstractmethod
    def to_data(self, value: Output) -> Any:
        """Serialize an object to data."""
        raise NotImplementedError()

    def collect_openapi_models(
        self, parent_models: StableSet[Serializer]
    ) -> StableSet[Serializer]:
        """Collect the set of OpenAPI models required for this Serializer.

        `Serializer`s that represent models should return a set containing
        themselves.

        `Serializer`s with child `Serializer`s that may be models should add
        themselves to `parent_models` and pass that to all children's
        `collect_openapi_models` method. The parent `Serializer` and all models
        received from children should be combined and returned.

        The default is to return no models.
        """
        return StableSet()

    def to_openapi_schema(self, refs: dict[Serializer, str], force: bool = False) -> Any:
        """Generate the OpenAPI schema representation for this class.

        Each serializer should check if its fully qualified name exists in
        `refs` and return a '$ref', unless `force` is true, in which case it
        should return its full schema, but not pass `force` to its child
        serializers.

        The default is no schema.
        """
        return {}


class Serializable(Serializer[SerializableOutput]):
    """Classes that serialize instances of themselves."""

    # There is no way to indicate in Python's type system that
    # type[Serializable] is an instance of Serializer. So these signatures
    # appear inconsistent with the base class.
    @classmethod
    @abstractmethod
    def from_data(cls, data: Any) -> DeserializationResult[Output]:
        pass

    @abstractmethod
    def to_data(self: SerializableOutput) -> Any:
        pass

    @classmethod
    def collect_openapi_models(cls, parent_models: StableSet[Serializer]) -> StableSet[Serializer]:
        return StableSet()

    @classmethod
    def to_openapi_schema(cls, refs: dict[Serializer, str], force: bool = False) -> Any:
        return {}

    # All attributes and methods below this point are for Pydantic
    # compatibility. These methods along with the appropriate monkey patching
    # allow all Serialite Serializables to be used as Pydantic BaseModels.

    # This flag is used by the issubclass(_, BaseModel) monkey patch to identify
    # classes that claim to be subclasses of BaseModel.
    _is_pydantic_base_model = True

    # This flag protects dataclasses from conversion
    __processed__ = True

    @classmethod
    def validate(cls, value: Any, values, field, config):
        # This is the canonical name for the main Pydantic validator. It does
        # not have to have this name as long as it is returned by
        # __get_validators__.

        # FastAPI passes in both data to be parsed and instances of the object
        # itself for some reason. Politely return the object if we get an
        # instance of this class.
        if isinstance(value, cls):
            return value

        result = cls.from_data(value)

        if isinstance(result, DeserializationFailure):
            # Must raise ValueError, TypeError, or AssertionError for Pydantic
            # to catch it. Or we could construct a Pydantic ValidationError.
            # https://pydantic-docs.helpmanual.io/usage/validators/
            raise ValueError(result.error)
        else:
            return result.or_die()

    @classmethod
    def __get_validators__(cls):
        # FastAPI uses pydantic.fields.ModelField to convert a type hint into a
        # Pydantic parser. ModelField relies on this field to get the parser.
        # The call chain is here: APIRoute > get_dependant > get_param_field >
        # create_response_field > ModelField > prepare > populate_validators >
        # __get_validators__

        yield cls.validate

    @classproperty
    def __config__(cls):
        # FastAPI accesses this attribute in a few places. It does not matter.
        try:
            from pydantic import BaseConfig

            return BaseConfig
        except ImportError:
            # Protect against auto-documentation programs trying to get all
            # properties.
            return None

    def dict(
        self,
        include: AbstractSetIntStr | MappingIntStrAny = None,
        exclude: AbstractSetIntStr | MappingIntStrAny = None,
        by_alias: bool = False,
        skip_defaults: bool = None,  # noqa: RUF013
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ):
        # FastAPI and Pydantic can only serialize instances of the validator,
        # which is why dict is implemented on Serializable instead of plain Serializer.
        # Serialite Serializers simply cannot be passed directly to FastAPI.

        data = self.to_data()
        if exclude is not None:
            data = {key: value for key, value in data.items() if key not in exclude}

        if hasattr(self, "__subclass_serializers__"):
            # Pydantic has no concept of algebraic data types. It does not use
            # the field to determine how to serialize an object. It purely asks
            # the object itself how it should be serialized via the dict
            # method. This implementation of dict assumes that anytime a
            # subclass of an abstract serializable is serialized, it was
            # supposed to be serialized with the abstract serializer, not the
            # concrete class. This is not a good assumption, but Pydantic is not
            # expressive enough to have two serializers for the same object.
            return {"_type": self.__class__.__name__} | data
        else:
            return data
