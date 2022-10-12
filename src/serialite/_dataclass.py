__all__ = ["field"]

import dataclasses
from dataclasses import MISSING, Field

from ._base import Serializer


def field(
    *,
    default=MISSING,
    default_factory=MISSING,
    serializer: Serializer | type = MISSING,
    init: bool = True,
    repr: bool = True,
    hash: bool | None = None,
    compare: bool = True,
    metadata: dict | None = None,
    kw_only: bool = MISSING,
) -> Field:
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
