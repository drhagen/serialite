__all__ = ["is_openapi_component"]


def is_openapi_component(cls) -> bool:
    """Return whether this serializer should be treated as an OpenAPI component.

    This is used to determine whether FastAPI/Pydantic should generate
    schemas for this serializer.

    It treats Pydantic BaseModel subclasses as OpenAPI components, also.
    """
    from pydantic import BaseModel

    return getattr(cls, "is_openapi_component", False) or (
        isinstance(cls, type) and issubclass(cls, BaseModel)
    )
