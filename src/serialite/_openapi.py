__all__ = [
    "detect_collisions",
    "fix_openapi_refs",
    "is_openapi_component",
    "openapi_schema_name",
]

import weakref

from ._base import Serializable

try:
    from pydantic import BaseModel
except ImportError:

    class BaseModel:
        pass


_collision_names: set[str] = set()
_qualified_to_short: dict[str, str] = {}
_component_registry: weakref.WeakSet = weakref.WeakSet()


def register_component(serializable_class):
    """Register a class as an OpenAPI component for collision detection."""
    _component_registry.add(serializable_class)


def detect_collisions():
    """Scan all registered OpenAPI components and detect name collisions.

    Call this before generating OpenAPI schemas to enable module-qualified
    naming for types with the same class name in different modules.

    Also builds a mapping from qualified names to short names, used by
    fix_openapi_refs() to correct false-positive qualifications.
    """
    global _collision_names, _qualified_to_short

    all_components = set(_component_registry)
    all_components.update(_all_subclasses(Serializable))
    all_components.update(_all_subclasses(BaseModel))

    name_to_modules: dict[str, set[str]] = {}
    for component_class in all_components:
        name_to_modules.setdefault(component_class.__name__, set()).add(component_class.__module__)

    _collision_names = {name for name, modules in name_to_modules.items() if len(modules) > 1}

    _qualified_to_short = {}
    for component_class in all_components:
        if component_class.__name__ in _collision_names:
            qualified = (
                component_class.__module__.replace(".", "__") + "__" + component_class.__name__
            )
            _qualified_to_short[qualified] = component_class.__name__


def fix_openapi_refs(schema):
    """Fix $ref mismatches between serialite's qualified names and Pydantic's schema keys.

    When detect_collisions() marks a name as colliding, serialite generates
    module-qualified $refs (e.g. design__model__Dose). But Pydantic may or may
    not create a matching qualified schema key, depending on whether both
    modules' types actually appear in the API routes.

    Two cases:
    - Real collision (2+ qualified $refs point to the same short-name schema):
      copy the short-name schema under each qualified name and remove the
      short name if it is no longer referenced.
    - False positive (only 1 qualified $ref for a short-name schema):
      rewrite the qualified $ref back to the short name.

    Call this after get_openapi() returns the schema dict.
    """
    schemas = schema.get("components", {}).get("schemas", {})

    prefix = "#/components/schemas/"
    missing_qualified: dict[str, str] = {}

    def collect(obj):
        if isinstance(obj, dict):
            if "$ref" in obj:
                ref = obj["$ref"]
                if ref.startswith(prefix):
                    name = ref[len(prefix) :]
                    if name not in schemas and name in _qualified_to_short:
                        short = _qualified_to_short[name]
                        if short in schemas:
                            missing_qualified[name] = short
            for value in obj.values():
                collect(value)
        elif isinstance(obj, list):
            for item in obj:
                collect(item)

    collect(schema)

    short_to_qualified: dict[str, list[str]] = {}
    for qualified_name, short_name in missing_qualified.items():
        short_to_qualified.setdefault(short_name, []).append(qualified_name)

    real_collisions: set[str] = set()
    false_positives: dict[str, str] = {}
    for short_name, qualified_names in short_to_qualified.items():
        if len(qualified_names) >= 2:
            real_collisions.update(qualified_names)
            for qualified_name in qualified_names:
                schemas[qualified_name] = schemas[short_name].copy()
        else:
            false_positives[qualified_names[0]] = short_name

    if false_positives:

        def rewrite_refs(obj):
            if isinstance(obj, dict):
                if "$ref" in obj:
                    ref = obj["$ref"]
                    if ref.startswith(prefix):
                        name = ref[len(prefix) :]
                        if name in false_positives:
                            obj["$ref"] = prefix + false_positives[name]
                for value in obj.values():
                    rewrite_refs(value)
            elif isinstance(obj, list):
                for item in obj:
                    rewrite_refs(item)

        rewrite_refs(schema)

    if real_collisions:
        referenced_names: set[str] = set()

        def collect_refs(obj):
            if isinstance(obj, dict):
                if "$ref" in obj:
                    ref = obj["$ref"]
                    if ref.startswith(prefix):
                        referenced_names.add(ref[len(prefix) :])
                for value in obj.values():
                    collect_refs(value)
            elif isinstance(obj, list):
                for item in obj:
                    collect_refs(item)

        collect_refs(schema)

        for short_name in short_to_qualified:
            if len(short_to_qualified[short_name]) >= 2 and short_name not in referenced_names:
                del schemas[short_name]

    return schema


def openapi_schema_name(serializable_class):
    """Return the OpenAPI schema name, module-qualified if collision detected."""
    if serializable_class.__name__ in _collision_names:
        return (
            serializable_class.__module__.replace(".", "__") + "__" + serializable_class.__name__
        )
    return serializable_class.__name__


def is_openapi_component(serializer) -> bool:
    """Return whether this serializer should be treated as an OpenAPI component.

    This is used to determine whether FastAPI/Pydantic should generate
    schemas for this serializer.

    It treats Pydantic BaseModel subclasses as OpenAPI components, also.
    """

    return getattr(serializer, "is_openapi_component", False) or (
        isinstance(serializer, type) and issubclass(serializer, BaseModel)
    )


def _all_subclasses(base):
    result = set()
    work = list(base.__subclasses__())
    while work:
        subclass = work.pop()
        if subclass not in result:
            result.add(subclass)
            work.extend(subclass.__subclasses__())
    return result
