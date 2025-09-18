__all__ = ["serializer"]

from abc import get_cache_token
from datetime import datetime
from pathlib import Path
from types import GenericAlias, UnionType
from typing import Any, Literal, TypeAliasType, TypeVar, Union, get_origin
from uuid import UUID

from ._base import Serializer

Output = TypeVar("Output")


def subclassdispatch(func):
    """Single dispatch based on the subclass of the first argument.

    This is a modified version of `functools.singledispatch` that dispatches on
    whether or not the first argument is a subtype of the registered type.

    It is a decorator of a generic function `func`.

    ```
    @subclassdispatch
    def my_func(cls: type):
        print('Default implementation')
    ```

    This imbues `func` with the `func.register` decorator, which can be used to
    register methods of the generic function for a particular type.

    ```
    @my_func.register(list)
    def my_func_for_int(cls):
        print('list was received')
    ```

    If `func` is called with a type `cls` (not an instance of a type, an actual
    type object itself), then the body of the method that is registered with a
    subtype of `cls` (including `cls` itself) will be run. If no supertype of
    `cls` is registered, then the body of the generic function is run.

    This will only work as the dispatcher for `serializer` as the `Union`,
    `Optional`, `Literal`, and `Any` types are hardcoded to dispatch to their
    respective serializers because the `issubclass` function does not work on
    them. This decorator cannot be used outside of this module.
    """
    from functools import _find_impl, update_wrapper
    from types import MappingProxyType
    from typing import _GenericAlias
    from weakref import WeakKeyDictionary

    registry = {}
    dispatch_cache = WeakKeyDictionary()
    cache_token = None

    def dispatch(cls: type):
        """generic_func.dispatch(cls) -> <function implementation>

        Runs the dispatch algorithm to return the best available implementation
        for the given `cls` registered on `generic_func`
        """
        nonlocal cache_token
        if cache_token is not None:
            current_token = get_cache_token()
            if cache_token != current_token:
                dispatch_cache.clear()
                cache_token = current_token

        if isinstance(cls, TypeAliasType):
            # Hash is not defined on TypeAliasType, so it cannot be used in WeakKeyDictionary
            return type_alias_type_serializer

        origin = get_origin(cls)
        if origin in {Union, UnionType}:
            # issubclass does not work on Union and Optional
            # WeakKeyDictionary does not work on UnionType
            # must bypass the dispatcher
            if len(cls.__args__) == 2 and cls.__args__[1] is type(None):
                # Optional is just a Union with NoneType in the second argument
                return optional_serializer
            else:
                # This is the standard Union
                return union_serializer

        try:
            impl = dispatch_cache[cls]
        except KeyError:
            try:
                impl = registry[cls]
            except KeyError:
                if isinstance(cls, GenericAlias) or issubclass(cls.__class__, _GenericAlias):
                    # issubclass does not work on Generic types since Python 3.7.0;
                    # must extract the base class and dispatch on that
                    if origin is Literal:
                        # issubclass does not work on Literal either
                        impl = literal_serializer
                    else:
                        # This is the standard Generic class
                        impl = _find_impl(origin, registry)
                elif cls is Any:
                    # issubclass does not work on Any; must directly inject this
                    impl = any_serializer
                else:
                    impl = _find_impl(cls, registry)
            dispatch_cache[cls] = impl
        return impl

    def register(cls, func=None):
        """generic_func.register(cls, func) -> func

        Registers a new implementation for the given *cls* on a *generic_func*.
        """
        nonlocal cache_token
        if func is None:
            return lambda f: register(cls, f)
        registry[cls] = func
        if cache_token is None and hasattr(cls, "__abstractmethods__"):
            cache_token = get_cache_token()
        dispatch_cache.clear()
        return func

    def wrapper(*args, **kw):
        # This differs from functools.singledispatch by using args[0] rather than args[0].__class__
        return dispatch(args[0])(*args, **kw)

    registry[object] = func
    wrapper.register = register
    wrapper.dispatch = dispatch
    wrapper.registry = MappingProxyType(registry)
    wrapper._clear_cache = dispatch_cache.clear
    update_wrapper(wrapper, func)
    return wrapper


# Classes we control can have from_data and to_data methods on them. External
# classes need to have a Serializer defined for them. By default we duck type
# and assume that the appropriate methods are already defined on the class.


@subclassdispatch
def serializer(cls: type[Output]) -> Serializer[Output]:
    """Given a class, return a serializer of instances of that class."""
    return cls


@serializer.register(type(None))
def none_serializer(cls):
    from ._implementations import NoneSerializer

    return NoneSerializer()


@serializer.register(bool)
def boolean_serializer(cls):
    from ._implementations import BooleanSerializer

    return BooleanSerializer()


@serializer.register(int)
def integer_serializer(cls):
    from ._implementations import IntegerSerializer

    return IntegerSerializer()


@serializer.register(float)
def float_serializer(cls):
    from ._implementations import FloatSerializer

    return FloatSerializer()


@serializer.register(str)
def string_serializer(cls):
    from ._implementations import StringSerializer

    return StringSerializer()


@serializer.register(datetime)
def datetime_serializer(cls):
    from ._implementations import DateTimeSerializer

    return DateTimeSerializer()


@serializer.register(UUID)
def uuid_serializer(cls):
    from ._implementations import UuidSerializer

    return UuidSerializer()


@serializer.register(list)
def list_serializer(cls):
    from ._implementations import ListSerializer

    return ListSerializer(serializer(cls.__args__[0]))


@serializer.register(set)
def set_serializer(cls):
    from ._implementations import SetSerializer

    return SetSerializer(serializer(cls.__args__[0]))


@serializer.register(tuple)
def tuple_serializer(cls):
    from ._implementations import TupleSerializer

    return TupleSerializer(*(serializer(arg) for arg in cls.__args__))


@serializer.register(dict)
def dict_serializer(cls):
    from ._implementations import OrderedDictSerializer, RawDictSerializer

    if cls.__args__[0] is str:
        return RawDictSerializer(serializer(cls.__args__[1]))
    else:
        return OrderedDictSerializer(serializer(cls.__args__[0]), serializer(cls.__args__[1]))


@serializer.register(Path)
def path_serializer(cls):
    from ._implementations import PathSerializer

    return PathSerializer()


# Union disables subclassing so Optional cannot be used to dispatch
# @serializer.register(Optional)
def optional_serializer(cls):
    from ._implementations import OptionalSerializer

    return OptionalSerializer(serializer(cls.__args__[0]))


# Union disables subclassing so it cannot be used to dispatch
# @serializer.register(Union)
def union_serializer(cls):
    from ._implementations import TryUnionSerializer

    return TryUnionSerializer(*[serializer(type_arg) for type_arg in cls.__args__])


# @serializer.register(Literal)
def literal_serializer(cls):
    from ._implementations import LiteralSerializer

    return LiteralSerializer(*cls.__args__)


# @serializer.register(Any)
def any_serializer(cls):
    from ._implementations import JsonSerializer

    return JsonSerializer()


# TypeAliasType does not implement hashing so it cannot be used to dispatch
# @serializer.register(TypeAliasType)
def type_alias_type_serializer(cls):
    return serializer(cls.__value__)


try:
    import numpy as np
except ImportError:
    pass
else:

    @serializer.register(np.ndarray)
    def array_serializer(cls):
        from ._implementations import ArraySerializer

        return ArraySerializer(dtype=float)


try:
    from ordered_set import OrderedSet
except ImportError:
    pass
else:

    @serializer.register(OrderedSet)
    def ordered_set_serializer(cls):
        from ._implementations import OrderedSetSerializer

        return OrderedSetSerializer(serializer(cls.__args__[0]))
