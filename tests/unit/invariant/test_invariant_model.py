from typing import Any

import pytest
from katharos.types import Result
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

from hexacore.invariant import InvariantModel, invariant


def test_model_without_invariants_validates_fields() -> None:
    class Model(InvariantModel):
        value: int

    assert InvariantModel().model_dump() == {}
    assert Model(value="3").model_dump() == {"value": 3}
    with pytest.raises(ValidationError) as caught:
        Model(value="invalid")
    assert caught.value.errors()[0]["loc"] == ("value",)


@pytest.mark.parametrize("entrypoint", ["init", "python", "json"])
@pytest.mark.parametrize("valid", [False, True], ids=["failure", "success"])
def test_validation_entrypoints_run_after_field_validation(
    entrypoint: str, valid: bool
) -> None:
    seen: list[tuple[int, int]] = []

    class Model(InvariantModel):
        value: int
        limit: int = 10

        @field_validator("value")
        @classmethod
        def double(cls, value: int) -> int:
            return value * 2

        @invariant
        def below_limit(self) -> Result[ValueError, None]:
            seen.append((self.value, self.limit))
            if self.value > self.limit:
                return Result.Failure(ValueError("exceeds limit"))
            return Result.Success(None)

    raw = "5" if valid else "6"

    def validate() -> Model:
        if entrypoint == "init":
            return Model(value=raw)
        if entrypoint == "python":
            return Model.model_validate({"value": raw})
        return Model.model_validate_json('{"value": "' + raw + '"}')

    if valid:
        model = validate()
        assert model.model_dump() == {"value": 10, "limit": 10}
    else:
        with pytest.raises(ValidationError) as caught:
            validate()
        assert caught.value.errors()[0]["loc"] == ("below_limit",)
    assert seen == [(int(raw) * 2, 10)]


@pytest.mark.parametrize("data", [{}, {"value": "invalid"}], ids=["missing", "invalid"])
def test_field_errors_prevent_invariants(data: dict[str, Any]) -> None:
    calls: list[str] = []

    class Model(InvariantModel):
        value: int

        @invariant
        def check(self) -> Result[Exception, None]:
            calls.append("check")
            return Result.Success(None)

    with pytest.raises(ValidationError) as caught:
        Model.model_validate(data)
    assert caught.value.errors()[0]["loc"] == ("value",)
    assert calls == []


def test_collects_failures_in_order_and_preserves_error_details() -> None:
    calls: list[str] = []
    models: list[InvariantModel] = []
    first_error = ValueError("first failure")
    second_error = RuntimeError("second failure")

    class Model(InvariantModel):
        value: int

        @invariant
        def z_first(self) -> Result[ValueError, None]:
            calls.append("first")
            models.append(self)
            return Result.Failure(first_error)

        @invariant
        def successful(self) -> Result[Exception, None]:
            calls.append("success")
            return Result.Success(None)

        @invariant
        def a_last(self) -> Result[RuntimeError, None]:
            calls.append("last")
            return Result.Failure(second_error)

    with pytest.raises(ValidationError) as caught:
        Model(value=7)

    assert calls == ["first", "success", "last"]
    assert caught.value.title == "Model"
    assert caught.value.error_count() == 2
    first, second = caught.value.errors(include_url=False)
    assert first == {
        "type": "value_error",
        "loc": ("z_first",),
        "msg": "Value error, first failure",
        "input": models[0],
        "ctx": {"error": first_error},
    }
    assert first["input"] is models[0]
    assert first["ctx"]["error"] is first_error
    assert second["type"] == "value_error"
    assert second["loc"] == ("a_last",)
    assert second["msg"] == "Value error, second failure"
    assert second["input"] is models[0]
    wrapped = second["ctx"]["error"]
    assert isinstance(wrapped, ValueError)
    assert str(wrapped) == str(second_error)
    assert wrapped.__cause__ is second_error


class CustomValueError(ValueError):
    pass


@pytest.mark.parametrize(
    "error",
    [
        ValueError("invalid"),
        CustomValueError("invalid"),
        TypeError("invalid"),
        RuntimeError("invalid"),
        Exception("invalid"),
    ],
)
def test_returned_exceptions_are_validation_errors(error: Exception) -> None:
    class Model(InvariantModel):
        @invariant
        def check(self) -> Result[Exception, None]:
            return Result.Failure(error)

    with pytest.raises(ValidationError) as caught:
        Model()
    detail = caught.value.errors()[0]
    assert detail["loc"] == ("check",)
    contextual_error = detail["ctx"]["error"]
    if isinstance(error, ValueError):
        assert contextual_error is error
    else:
        assert type(contextual_error) is ValueError
        assert contextual_error.__cause__ is error


@pytest.mark.parametrize("earlier_failure", [False, True])
@pytest.mark.parametrize(
    ("result", "message"),
    [
        (None, "must return a Result"),
        (False, "must return a Result"),
        (0, "must return a Result"),
        (object(), "must return a Result"),
        (Result.Success(False), "must return Success(None)"),
        (Result.Success(0), "must return Success(None)"),
        (Result.Success(""), "must return Success(None)"),
        (Result.Success([]), "must return Success(None)"),
        (Result.Success(ValueError("success payload")), "must return Success(None)"),
        (Result.Failure(BaseException("invalid")), "must fail with an Exception"),
        (Result.Failure(KeyboardInterrupt()), "must fail with an Exception"),
        (Result.Failure(SystemExit()), "must fail with an Exception"),
    ],
    ids=[
        "none",
        "bool",
        "int",
        "object",
        "success-false",
        "success-zero",
        "success-empty-string",
        "success-empty-list",
        "success-exception",
        "base-exception",
        "keyboard-interrupt",
        "system-exit",
    ],
)
def test_contract_violations_stop_checks(
    result: Any, message: str, earlier_failure: bool
) -> None:
    calls: list[str] = []

    class Model(InvariantModel):
        @invariant
        def first(self) -> Result[ValueError, None]:
            calls.append("first")
            return (
                Result.Failure(ValueError("earlier"))
                if earlier_failure
                else Result.Success(None)
            )

        @invariant
        def invalid(self) -> Any:
            calls.append("invalid")
            return result

        @invariant
        def last(self) -> Result[Exception, None]:
            calls.append("last")
            return Result.Success(None)

    with pytest.raises(TypeError) as caught:
        Model()
    assert str(caught.value) == f"Invariant invalid {message}"
    assert calls == ["first", "invalid"]


@pytest.mark.parametrize("earlier_failure", [False, True])
@pytest.mark.parametrize(
    "error",
    [
        ValueError("raised"),
        AssertionError("raised"),
        TypeError("raised"),
        RuntimeError("raised"),
    ],
)
def test_raised_exceptions_stop_checks(error: Exception, earlier_failure: bool) -> None:
    calls: list[str] = []

    class Model(InvariantModel):
        @invariant
        def first(self) -> Result[ValueError, None]:
            calls.append("first")
            return (
                Result.Failure(ValueError("earlier"))
                if earlier_failure
                else Result.Success(None)
            )

        @invariant
        def raises(self) -> Result[Exception, None]:
            calls.append("raises")
            raise error

        @invariant
        def last(self) -> Result[Exception, None]:
            calls.append("last")
            return Result.Success(None)

    if isinstance(error, (ValueError, AssertionError)):
        with pytest.raises(ValidationError) as caught:
            Model()
        assert caught.value.error_count() == 1
        detail = caught.value.errors()[0]
        assert detail["loc"] == ()
        assert detail["ctx"]["error"] is error
        assert detail["type"] == (
            "value_error" if isinstance(error, ValueError) else "assertion_error"
        )
    else:
        with pytest.raises(type(error)) as propagated:
            Model()
        assert propagated.value is error
    assert calls == ["first", "raises"]


def test_nested_model_failure_includes_field_path() -> None:
    class Child(InvariantModel):
        @invariant
        def check(self) -> Result[ValueError, None]:
            return Result.Failure(ValueError("invalid child"))

    class Parent(BaseModel):
        child: Child

    with pytest.raises(ValidationError) as caught:
        Parent.model_validate({"child": {}})
    assert caught.value.errors()[0]["loc"] == ("child", "check")


@pytest.mark.parametrize("validate_assignment", [False, True])
def test_assignment_validation_is_opt_in(validate_assignment: bool) -> None:
    calls: list[int] = []

    class Model(InvariantModel):
        model_config = (
            ConfigDict(validate_assignment=True)
            if validate_assignment
            else ConfigDict()
        )
        value: int

        @invariant
        def positive(self) -> Result[ValueError, None]:
            calls.append(self.value)
            return (
                Result.Success(None)
                if self.value > 0
                else Result.Failure(ValueError("must be positive"))
            )

    model = Model(value=1)
    model.value = 2
    if validate_assignment:
        with pytest.raises(ValidationError) as caught:
            model.value = 0
        assert caught.value.errors()[0]["loc"] == ("positive",)
        assert calls == [1, 2, 0]
    else:
        model.value = 0
        assert calls == [1]
    assert model.value == 0


def test_assignment_field_error_prevents_invariants_and_preserves_value() -> None:
    calls: list[int] = []

    class Model(InvariantModel):
        model_config = ConfigDict(validate_assignment=True)
        value: int

        @invariant
        def check(self) -> Result[Exception, None]:
            calls.append(self.value)
            return Result.Success(None)

    model = Model(value=1)
    with pytest.raises(ValidationError) as caught:
        model.value = "invalid"  # type: ignore[assignment]
    assert caught.value.errors()[0]["loc"] == ("value",)
    assert calls == [1]
    assert model.value == 1


def test_construct_bypasses_validation_and_direct_call_returns_original_result() -> (
    None
):
    calls: list[InvariantModel] = []
    failure = Result.Failure(ValueError("invalid"))

    class Model(InvariantModel):
        value: int

        @invariant
        def check(self) -> Result[ValueError, None]:
            calls.append(self)
            return failure

    model = Model.model_construct(value="unvalidated")
    assert calls == []
    assert model.value == "unvalidated"
    assert model.check() is failure
    assert calls == [model]
