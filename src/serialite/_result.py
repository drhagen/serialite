from __future__ import annotations

__all__ = ["Failure", "Result", "Success"]

from returns import result

from ._errors import Errors

type Result[Output] = result.Result[Output, Errors]
Success = result.Success
Failure: type[result.Failure[Errors]] = result.Failure[Errors]
Failure = result.Failure
