from __future__ import annotations

__all__ = ["monkey_patch_pydantic_subclasscheck"]


def __subclasscheck__(cls: type, sub: type) -> bool:  # noqa: N807
    from pydantic import BaseModel

    if cls is BaseModel and hasattr(sub, "is_openapi_component"):
        # To minimize the blast radius, only change how subclassing works on
        # exactly BaseModel. Hypothetical subtypes of BaseModel will not be
        # affected by this method.
        return sub.is_openapi_component
    else:
        return super(type(BaseModel), cls).__subclasscheck__(sub)


def monkey_patch_pydantic_subclasscheck() -> None:
    # Pydantic and FastAPI make extensive use of issubclass(cls, BaseModel).
    # To implement a Pydantic interface, it is not enough to duck type the key
    # methods. The call to issubclass must be intercepted and rewritten.
    # Fortunately, BaseModel has its own metaclass, so we can attach a new
    # definition of __subclasscheck__ to it that will cause
    # issubclass(cls, BaseModel) to return the value of is_openapi_component
    # if it exists. We cannot look for __get_validators__ because some non-Base
    # Model classes in Pydantic have this method and FastAPI treats them very
    # differently.

    try:
        from pydantic import BaseModel
    except ImportError:
        pass
    else:
        metaclass = type(BaseModel)
        metaclass.__subclasscheck__ = __subclasscheck__
