from __future__ import annotations

__all__ = ["field"]

import dataclasses
from collections.abc import Callable, Mapping
from dataclasses import _MISSING_TYPE, MISSING
from typing import Any, Literal, overload

from ._base import Serializer

# Overload signatures based on typeshed's dataclasses.field stub.
# They let type checkers preserve the declared field type instead of collapsing it to Field.


# default provided
@overload
def field[T](
    *,
    default: T,
    default_factory: Literal[_MISSING_TYPE.MISSING] = ...,
    serializer: Serializer[T] = ...,
    init: bool = ...,
    repr: bool = ...,
    hash: bool | None = ...,
    compare: bool = ...,
    metadata: Mapping[Any, Any] | None = ...,
    kw_only: bool = ...,
) -> T: ...


# default_factory provided
@overload
def field[T](
    *,
    default: Literal[_MISSING_TYPE.MISSING] = ...,
    default_factory: Callable[[], T] = ...,
    serializer: Serializer[T] = ...,
    init: bool = ...,
    repr: bool = ...,
    hash: bool | None = ...,
    compare: bool = ...,
    metadata: Mapping[Any, Any] | None = ...,
    kw_only: bool = ...,
) -> T: ...


# neither default nor default_factory
@overload
def field[T](
    *,
    default: Literal[_MISSING_TYPE.MISSING] = ...,
    default_factory: Literal[_MISSING_TYPE.MISSING] = ...,
    serializer: Serializer[T] = ...,
    init: bool = ...,
    repr: bool = ...,
    hash: bool | None = ...,
    compare: bool = ...,
    metadata: Mapping[Any, Any] | None = ...,
    kw_only: bool = ...,
) -> Any: ...


def field(
    *,
    default=MISSING,
    default_factory=MISSING,
    serializer=MISSING,
    init=True,
    repr=True,
    hash=None,
    compare=True,
    metadata=None,
    kw_only=MISSING,
):
    serializer_metadata = (metadata if metadata is not None else {}) | {"serializer": serializer}
    return dataclasses.field(
        default=default,
        default_factory=default_factory,
        init=init,
        repr=repr,
        hash=hash,
        compare=compare,
        metadata=serializer_metadata,
        kw_only=kw_only,
    )
