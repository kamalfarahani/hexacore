from collections.abc import Callable
from inspect import (
    Parameter,
    isasyncgenfunction,
    iscoroutinefunction,
    isfunction,
    isgeneratorfunction,
    signature,
)

from katharos.types import Result
from pydantic import BaseModel


def invariant[M: BaseModel, E: Exception](
    method: Callable[[M], Result[E, None]],
) -> Callable[[M], Result[E, None]]:
    """Mark an instance method for automatic validation on InvariantModel.

    The method remains unchanged, so direct calls still return a Result.
    Apply this decorator to synchronous, non-generator methods taking only the
    model instance. Checks must not mutate the model.

    Args:
        method: Check returning Success(None) or Failure containing an exception.

    Returns:
        The original method marked as an invariant.

    Raises:
        TypeError: If the decorated object is not a synchronous, non-generator
            instance method taking only the model instance.
    """
    if not isfunction(method):
        raise TypeError("@invariant requires an instance method")
    if (
        iscoroutinefunction(method)
        or isgeneratorfunction(method)
        or isasyncgenfunction(method)
    ):
        raise TypeError("@invariant requires a synchronous, non-generator method")
    parameters = list(signature(method).parameters.values())
    if len(parameters) != 1 or parameters[0].kind not in (
        Parameter.POSITIONAL_ONLY,
        Parameter.POSITIONAL_OR_KEYWORD,
    ):
        raise TypeError("@invariant methods must take only the model instance")
    method.__dict__["__model_invariant__"] = True
    return method
