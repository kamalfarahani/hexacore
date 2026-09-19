from collections.abc import AsyncIterator, Callable, Iterator
from inspect import signature
from typing import Any

import pytest
from katharos.types import Result
from pydantic import BaseModel

from hexacore.invariant import invariant


def test_preserves_function_identity_metadata_and_does_not_execute() -> None:
    calls: list[BaseModel] = []

    def check(self: BaseModel) -> Result[Exception, None]:
        """Check the model."""
        calls.append(self)
        return Result.Success(None)

    original_signature = signature(check)
    original_annotations = check.__annotations__.copy()
    check.__dict__["custom_attribute"] = "retained"

    decorated = invariant(check)

    assert decorated is check
    assert decorated.__name__ == "check"
    assert decorated.__doc__ == "Check the model."
    assert decorated.__annotations__ == original_annotations
    assert signature(decorated) == original_signature
    assert decorated.__dict__["custom_attribute"] == "retained"
    assert decorated.__dict__["__model_invariant__"] is True
    assert calls == []


@pytest.mark.parametrize("failure", [False, True], ids=["success", "failure"])
def test_direct_calls_preserve_result_identity(failure: bool) -> None:
    result = Result.Failure(ValueError("invalid")) if failure else Result.Success(None)
    calls: list[BaseModel] = []

    class Model(BaseModel):
        @invariant
        def check(self) -> Result[ValueError, None]:
            calls.append(self)
            return result

    model = Model()
    assert calls == []
    assert model.check() is result
    assert calls == [model]


def test_accepts_positional_only_instance_parameter() -> None:
    class Model(BaseModel):
        @invariant
        def check(self, /) -> Result[Exception, None]:
            return Result.Success(None)

    assert Model().check() == Result.Success(None)


def test_repeated_decoration_preserves_function() -> None:
    def check(self: BaseModel) -> Result[Exception, None]:
        return Result.Success(None)

    assert invariant(invariant(check)) is check


class CallableObject:
    def __call__(self, model: BaseModel) -> Result[Exception, None]:
        return Result.Success(None)


class MethodContainer:
    def check(self) -> Result[Exception, None]:
        return Result.Success(None)


@pytest.mark.parametrize(
    "candidate",
    [
        None,
        42,
        len,
        CallableObject(),
        MethodContainer,
        MethodContainer().check,
        staticmethod(MethodContainer.check),
        classmethod(MethodContainer.check),
        property(MethodContainer.check),
    ],
    ids=[
        "none",
        "number",
        "builtin",
        "callable",
        "class",
        "bound-method",
        "staticmethod",
        "classmethod",
        "property",
    ],
)
def test_rejects_non_function_objects(candidate: Any) -> None:
    with pytest.raises(TypeError, match="^@invariant requires an instance method$"):
        invariant(candidate)


async def coroutine_check(self: BaseModel) -> Result[Exception, None]:
    return Result.Success(None)


def generator_check(self: BaseModel) -> Iterator[Result[Exception, None]]:
    yield Result.Success(None)


async def async_generator_check(
    self: BaseModel,
) -> AsyncIterator[Result[Exception, None]]:
    yield Result.Success(None)


@pytest.mark.parametrize(
    "candidate", [coroutine_check, generator_check, async_generator_check]
)
def test_rejects_asynchronous_and_generator_functions(candidate: Any) -> None:
    with pytest.raises(
        TypeError, match="^@invariant requires a synchronous, non-generator method$"
    ):
        invariant(candidate)
    assert "__model_invariant__" not in candidate.__dict__


@pytest.mark.parametrize(
    "candidate",
    [
        lambda: None,
        lambda self, extra: None,
        lambda self, extra=None: None,
        lambda *, self: None,
        lambda *args: None,
        lambda **kwargs: None,
        lambda self, *args: None,
        lambda self, **kwargs: None,
        lambda self, *, extra=None: None,
    ],
    ids=[
        "no-parameters",
        "extra-positional",
        "optional-positional",
        "keyword-only",
        "args-only",
        "kwargs-only",
        "extra-args",
        "extra-kwargs",
        "optional-keyword",
    ],
)
def test_rejects_invalid_signatures(candidate: Callable[..., Any]) -> None:
    with pytest.raises(
        TypeError, match="^@invariant methods must take only the model instance$"
    ):
        invariant(candidate)
    assert "__model_invariant__" not in candidate.__dict__
