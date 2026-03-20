from __future__ import annotations

__all__ = ["monkey_patch_pydantic_subclasscheck"]

from typing import Any


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


def __instancecheck__(cls: type, instance: Any) -> bool:  # noqa: N807
    from pydantic import BaseModel

    if cls is BaseModel and hasattr(instance, "is_openapi_component"):
        # To minimize the blast radius, only change how isinstance works on
        # exactly BaseModel. Hypothetical subtypes of BaseModel will not be
        # affected by this method.
        return instance.is_openapi_component
    else:
        return super(type(BaseModel), cls).__instancecheck__(instance)


def monkey_patch_pydantic_instancecheck() -> None:
    # FastAPI also makes use of isinstance(obj, BaseModel) in
    # fastapi.encoders.jsonable_encoder. We need to patch __instancecheck__
    # using the same process for the same reasons. Normally, __instancecheck__
    # calls __subclasscheck__, but Pydantic overrode the default behavior in
    # order to work around a Python bug.
    # https://github.com/samuelcolvin/pydantic/pull/4081

    try:
        from pydantic import BaseModel
    except ImportError:
        pass
    else:
        metaclass = type(BaseModel)
        metaclass.__instancecheck__ = __instancecheck__
