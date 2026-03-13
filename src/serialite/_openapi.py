__all__ = ["is_openapi_component"]

try:
    from pydantic import BaseModel
except ImportError:

    class BaseModel:
        pass


def is_openapi_component(serializer) -> bool:
    """Return whether this serializer should be treated as an OpenAPI component.

    This is used to determine whether FastAPI/Pydantic should generate
    schemas for this serializer.

    It treats Pydantic BaseModel subclasses as OpenAPI components, also.
    """

    return getattr(serializer, "is_openapi_component", False) or (
        isinstance(serializer, type) and issubclass(serializer, BaseModel)
    )
