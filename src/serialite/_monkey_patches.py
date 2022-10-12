from __future__ import annotations

__all__ = [
    "monkey_patch_pydantic_subclasscheck",
    "monkey_patch_pydantic_instancecheck",
    "monkey_patch_fastapi_create_cloned_field",
    "monkey_patch_pydantic_get_flat_models_from_model",
    "monkey_patch_pydantic_model_type_schema",
]

from typing import TYPE_CHECKING, Any

from ._stable_set import StableSet

if TYPE_CHECKING:
    from pydantic import BaseModel
    from pydantic.fields import ModelField
    from pydantic.schema import TypeModelOrEnum, TypeModelSet


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


def __instancecheck__(cls: type, instance: Any) -> bool:  # noqa: N807
    from pydantic import BaseModel

    if cls is BaseModel and hasattr(instance, "_is_pydantic_base_model"):
        # To minimize the blast radius, only change how isinstance works on
        # exactly BaseModel. Hypothetical subtypes of BaseModel will not be
        # affected by this method.
        return instance._is_pydantic_base_model
    else:
        return super(type(BaseModel), cls).__instancecheck__(instance)


def monkey_patch_pydantic_instancecheck() -> None:
    # Pydantic and FastAPI also make extensive use of
    # isinstance(obj, BaseModel). We need to patch __instancecheck__ using the
    # same process for the same reasons. Normally, __instancecheck__ calls
    # __subclasscheck__, but Pydantic overrode the default behavior in order to
    # work around a Python bug.
    # https://github.com/samuelcolvin/pydantic/pull/4081

    try:
        from pydantic import BaseModel
    except ImportError:
        pass
    else:
        metaclass = type(BaseModel)
        metaclass.__instancecheck__ = __instancecheck__


def monkey_patch_fastapi_create_cloned_field() -> None:
    # To work around a misfeature in Pydantic, FastAPI clones every
    # Pydantic class that it receives. This breaks Serialite's
    # AbstractSerializableMixin because the cloned abstract serializer now has
    # no subclasses. The function that does the cloning is monkey patched to
    # simply pass Serialite classes through without modification.

    try:
        from fastapi import routing, utils
        from fastapi.utils import create_cloned_field as original_create_cloned_field
    except ImportError:
        pass
    else:

        def create_cloned_field(
            field: ModelField,
            *,
            cloned_types: dict[type[BaseModel], type[BaseModel]] | None = None,
        ):
            original_type = field.type_
            if hasattr(original_type, "to_data"):
                return field
            else:
                return original_create_cloned_field(field, cloned_types=cloned_types)

        utils.create_cloned_field = create_cloned_field
        routing.create_cloned_field = create_cloned_field


def monkey_patch_pydantic_get_flat_models_from_model() -> None:
    # Just like Serialite, Pydantic collects all the models by traversing the
    # models it already has. It is cleaner to let Serialite do its own traversal
    # by monkey patching pydantic.schema.get_flat_models_from_model to intercept
    # Serialite classes.

    try:
        from pydantic import schema
        from pydantic.schema import (
            get_flat_models_from_model as original_get_flat_models_from_model,
        )
    except ImportError:
        pass
    else:

        def get_flat_models_from_model(
            model: type[BaseModel], known_models: TypeModelSet = None
        ) -> TypeModelSet:
            if hasattr(model, "collect_openapi_models"):
                if known_models is None:
                    known_models = StableSet()

                new_models = model.collect_openapi_models(StableSet())

                return known_models | new_models
            else:
                return original_get_flat_models_from_model(model, known_models)

        schema.get_flat_models_from_model = get_flat_models_from_model


def monkey_patch_pydantic_model_type_schema() -> None:
    # Just like Serialite, Pydantic takes all the models it found and generates
    # the schema for each one using references where appropriate. It does not
    # use the .schema method, but the model_type_schema function instead. It is
    # cleaner to intercept Serialite classes passed to this function.

    try:
        from pydantic import schema
        from pydantic.schema import model_type_schema as original_model_type_schema
    except ImportError:
        pass
    else:

        def model_type_schema(
            model: type[BaseModel],
            *,
            by_alias: bool,
            model_name_map: dict[TypeModelOrEnum, str],
            ref_template: str,
            ref_prefix: str | None = None,
            known_models: TypeModelSet,
        ) -> tuple[dict[str, Any], dict[str, Any], set[str]]:
            if ref_template is None:
                from pydantic.schema import default_ref_template

                ref_template = default_ref_template

            if hasattr(model, "to_openapi_schema"):
                if ref_prefix is None:
                    ref_prefix = "#/definitions/"

                refs = {
                    model: {"$ref": ref_prefix + name} for model, name in model_name_map.items()
                }

                # For inexplicable reasons, Pydantic requires that all the
                # definitions of sub models need to be returned right now.
                models = model.collect_openapi_models(StableSet())

                definitions = {
                    model.__name__: model.to_openapi_schema(refs, force=True) for model in models
                }

                return model.to_openapi_schema(refs, force=True), definitions, models
            else:
                return original_model_type_schema(
                    model,
                    by_alias=by_alias,
                    model_name_map=model_name_map,
                    ref_prefix=ref_prefix,
                    ref_template=ref_template,
                    known_models=known_models,
                )

        schema.model_type_schema = model_type_schema
