from __future__ import annotations

__all__ = ["Serializable", "Serializer"]

from abc import abstractmethod
from typing import Any

from ._descriptors import classproperty
from ._result import Failure, Result, Success


class Serializer[Output]:
    """Serialize and deserialize a particular object."""

    @abstractmethod
    def from_data(self, data: Any) -> Result[Output]:
        """Deserialize an object from data."""
        raise NotImplementedError()

    @abstractmethod
    def to_data(self, value: Output) -> Any:
        """Serialize an object to data."""
        raise NotImplementedError()

    # Flag indicating whether this serializer represents an OpenAPI component
    # (a model that should appear in the components/schemas section)
    is_openapi_component: bool = False

    def child_components(self) -> dict[str, type[Serializer]]:
        """Return child serializers that are OpenAPI components.

        This method should return the immediate child serializers that are also
        OpenAPI components.
        """
        return {}

    def to_openapi_schema(self, force: bool = False) -> Any:
        """Generate the OpenAPI schema representation for this class.

        If `force` is False and this serializer represents a component, it
        should return a '$ref'. If `force` is True, it should return its full
        schema, but not pass `force` to its child serializers.

        The default is no schema.
        """
        return {}


class Serializable[SerializableOutput](Serializer[SerializableOutput]):
    """Classes that serialize instances of themselves."""

    # There is no way to indicate in Python's type system that
    # type[Serializable] is an instance of Serializer. So these signatures
    # appear inconsistent with the base class.
    @classmethod
    @abstractmethod
    def from_data(cls, data: Any) -> Result[SerializableOutput]:
        pass

    @abstractmethod
    def to_data(self: SerializableOutput) -> Any:
        pass

    @classmethod
    def child_components(cls) -> dict[str, type[Serializable]]:
        return {}

    @classmethod
    def to_openapi_schema(cls, force: bool = False) -> Any:
        return {}

    # All attributes and methods below this point are for Pydantic v2
    # compatibility. These methods allow all Serialite Serializables to be used
    # as type annotations in FastAPI. The full Pydantic interface is not
    # implemented, only that which is necessary for FastAPI to work.

    # This flag protects dataclasses from conversion
    __processed__ = True

    @classmethod
    def _pydantic_validate(cls, value: Any) -> SerializableOutput:
        # FastAPI passes in both data to be parsed and instances of the object
        if isinstance(value, cls):
            return value

        match cls.from_data(value):
            case Failure(errors):
                # Convert Serialite Errors to Pydantic ValidationError
                # This preserves as much error information as possible
                # (location, type, message, context), making errors look like
                # native Pydantic validation errors
                from pydantic_core import PydanticCustomError
                from pydantic_core import ValidationError as PydanticValidationError

                line_errors = []
                for element in errors.errors:
                    # Create a PydanticCustomError from the Serialite error
                    serialite_error = element.error
                    pydantic_custom_error = PydanticCustomError(
                        type(serialite_error).__name__,
                        str(serialite_error),
                        serialite_error.to_data() if hasattr(serialite_error, "to_data") else {},
                    )

                    line_errors.append(
                        {
                            "type": pydantic_custom_error,
                            "loc": element.location,
                        }
                    )

                raise PydanticValidationError.from_exception_data(
                    title=cls.__name__,
                    line_errors=line_errors,
                )
            case Success(validated_value):
                return validated_value

    @classmethod
    def _pydantic_serialize(cls, value: Any) -> Any:
        return cls.to_data(value)

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler):
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
    def __get_pydantic_json_schema__(cls, core_schema_obj, handler):
        # Pydantic v2 uses __get_pydantic_json_schema__ to generate OpenAPI
        # schemas. We return the full schema here (force=True).
        return cls.to_openapi_schema(force=True)

    @classproperty
    def model_fields(cls):
        # FastAPI invokes this to collect all the components. We only fill in
        # enough information for that purpose and even hack it for additional
        # purposes.
        from pydantic.fields import FieldInfo

        # Get child components from the class
        components = cls.child_components()

        # Build FieldInfo objects for each component
        fields: dict[str, FieldInfo] = {}
        for name, component_cls in components.items():
            fields[name] = FieldInfo(annotation=component_cls)

        return fields

    @classproperty
    def model_config(cls):
        # A place where Pydantic puts various metadata and options. Serialite
        # is not configurable in this way, so return a default configuration.
        from pydantic import ConfigDict

        return ConfigDict()

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
