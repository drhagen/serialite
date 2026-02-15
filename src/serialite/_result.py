from __future__ import annotations

__all__ = ["Failure", "Result", "Success"]

from typing import TYPE_CHECKING

from returns import result

from ._errors import Errors

if TYPE_CHECKING:
    # TODO: remove this when https://github.com/astral-sh/ty/issues/136 is resolved
    # See https://github.com/astral-sh/ty/issues/2788
    class Result[Output]:
        def unwrap(self) -> Output: ...
else:
    type Result[Output] = result.Result[Output, Errors]

Success = result.Success
Failure: type[result.Failure[Errors]] = result.Failure[Errors]
Failure = result.Failure
