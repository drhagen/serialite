from __future__ import annotations

__all__ = ["Serializable", "Serializer"]

from abc import abstractmethod
from typing import Any, Generic, TypeVar

from ._descriptors import classproperty
from ._result import Failure, Result, Success
from ._stable_set import StableSet

Output = TypeVar("Output")
SerializableOutput = TypeVar("SerializableOutput", bound="Serializable")


class Serializer(Generic[Output]):
    """Serialize and deserialize a particular object."""

    @abstractmethod
    def from_data(self, data: Any) -> Result[Output]:
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

    def to_openapi_schema(self, force: bool = False) -> Any:
        """Generate the OpenAPI schema representation for this class.

        If `force` is False and this serializer represents a model, it should
        return a '$ref'. If `force` is True, it should return its full schema,
        but not pass `force` to its child serializers.

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
    def from_data(cls, data: Any) -> Result[Output]:
        pass

    @abstractmethod
    def to_data(self: SerializableOutput) -> Any:
        pass

    @classmethod
    def collect_openapi_models(cls, parent_models: StableSet[Serializer]) -> StableSet[Serializer]:
        return StableSet()

    @classmethod
    def to_openapi_schema(cls, force: bool = False) -> Any:
        return {}

    # All attributes and methods below this point are for Pydantic v2
    # compatibility. These methods allow all Serialite Serializables to be used
    # as type annotations in FastAPI. The full Pydantic interface is not
    # implemented, only that which is necessary for FastAPI to work.

    # This flag is used by the issubclass(_, BaseModel) monkey patch to identify
    # classes that claim to be subclasses of BaseModel.
    _is_pydantic_base_model = True

    # This flag protects dataclasses from conversion
    __processed__ = True

    @classmethod
    def _pydantic_validate(cls, value: Any) -> SerializableOutput:
        # FastAPI passes in both data to be parsed and instances of the object
        if isinstance(value, cls):
            return value

        match cls.from_data(value):
            case Failure(error):
                # Must raise ValueError, TypeError, or AssertionError for
                # Pydantic to catch it. Or we could construct a Pydantic
                # ValidationError.
                # https://docs.pydantic.dev/latest/concepts/validators/
                raise ValueError(error)
            case Success(validated_value):
                return validated_value

    @classmethod
    def _pydantic_serialize(cls, value: Any) -> Any:
        return cls.to_data(value)

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, _handler):
        # Pydantic v2 uses __get_pydantic_core_schema__ to package custom
        # validation and serialization.
        from pydantic_core import core_schema

        return core_schema.no_info_plain_validator_function(
            cls._pydantic_validate,
            ref=f"{cls.__module__}.{cls.__name__}",
            serialization=core_schema.plain_serializer_function_ser_schema(
                cls._pydantic_serialize
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(cls, _core_schema_obj, _handler):
        # Pydantic v2 uses __get_pydantic_json_schema__ to generate OpenAPI
        # schemas.

        # Models are collected via the monkey-patched
        # get_flat_models_from_model, but they are not used here. The refs must
        # be consistently generated.
        return cls.to_openapi_schema(force=True)

    @classproperty
    def model_config(cls):
        # A place where Pydantic puts various metadata and options. Serialite
        # is not configurable in this way, so return a default configuration.
        from pydantic import ConfigDict

        return ConfigDict()

    @classproperty
    def model_fields(cls):
        # FastAPI expects model_fields for OpenAPI schema generation
        # Return an empty dict since our schema is handled through
        # __get_pydantic_core_schema__
        return {}

    def model_dump(
        self,
        *,
        mode: str = "python",
        include: Any = None,
        exclude: Any = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool = True,
    ):
        # FastAPI does not call this function, but it does require that it be
        # here.
        raise NotImplementedError()
