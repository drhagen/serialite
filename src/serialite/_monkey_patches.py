from __future__ import annotations

__all__ = [
    "monkey_patch_pydantic_subclasscheck",
    "monkey_patch_pydantic_v2_get_flat_models_from_model",
]

from ._stable_set import StableSet


def __subclasscheck__(cls: type, sub: type) -> bool:  # noqa: N807
    from pydantic import BaseModel

    if cls is BaseModel and hasattr(sub, "_is_pydantic_base_model"):
        # To minimize the blast radius, only change how subclassing works on
        # exactly BaseModel. Hypothetical subtypes of BaseModel will not be
        # affected by this method.
        return sub._is_pydantic_base_model
    else:
        return super(type(BaseModel), cls).__subclasscheck__(sub)


def monkey_patch_pydantic_subclasscheck() -> None:
    # Pydantic and FastAPI make extensive use of issubclass(cls, BaseModel).
    # To implement a Pydantic interface, it is not enough to duck type the key
    # methods. The call to issubclass must be intercepted and rewritten.
    # Fortunately, BaseModel has its own metaclass, so we can attach a new
    # definition of __subclasscheck__ to it that will cause
    # issubclass(cls, BaseModel) to return the value of _is_pydantic_base_model
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


def monkey_patch_pydantic_v2_get_flat_models_from_model() -> None:
    # For Pydantic v2 / FastAPI compatibility, we need to monkey patch the
    # function that collects all models from a root model.

    try:
        from fastapi._compat import v2
        from fastapi._compat.v2 import TypeModelSet
        from fastapi._compat.v2 import (
            get_flat_models_from_model as original_get_flat_models_from_model,
        )
    except ImportError:
        pass
    else:
        from typing import Union

        def get_flat_models_from_model(
            model: type, known_models: Union[TypeModelSet, None] = None
        ) -> TypeModelSet:
            if hasattr(model, "collect_openapi_models"):
                if known_models is None:
                    known_models = set()

                new_models = model.collect_openapi_models(StableSet())

                # Mutate known_models to include all collected models
                # This is important because the caller expects known_models to be updated
                known_models.update(new_models)

                return known_models
            else:
                return original_get_flat_models_from_model(model, known_models)

        v2.get_flat_models_from_model = get_flat_models_from_model
