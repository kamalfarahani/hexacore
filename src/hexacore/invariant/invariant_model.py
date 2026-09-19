from inspect import isfunction
from typing import Self

from katharos.types import Result
from pydantic import BaseModel, ValidationError, model_validator
from pydantic_core import InitErrorDetails


class InvariantModel(BaseModel):
    """Model that checks marked invariants after successful field validation.

    Checks run in declaration order, visiting base classes in reverse MRO before
    subclasses. Overrides replace inherited checks and must be decorated again
    to participate. Validation collects all returned failures unless a check
    raises an exception or violates the Result return contract, which stops
    further checks immediately. Direct invariant calls retain their Result
    contract.

    Assignment validation is opt-in through Pydantic's validate_assignment
    configuration. model_construct bypasses validation, including invariants.
    """

    @model_validator(mode="after")
    def _check_model_invariants(self) -> Self:
        """Run effective invariant methods and return the validated model.

        Returns:
            This model when all invariant checks succeed.

        Raises:
            ValidationError: If any invariants return failures. Each failure is
                located at its method name. Non-ValueError exceptions are wrapped
                in ValueError with their original cause preserved.
            TypeError: If an invariant violates the Result return contract.
        """
        errors: list[tuple[str, Exception]] = []
        members: dict[str, object] = {}
        for base in reversed(type(self).__mro__):
            for name, member in vars(base).items():
                # An override belongs to the subclass's declaration order.
                members.pop(name, None)
                members[name] = member

        for name, member in members.items():
            if not isfunction(member) or not getattr(
                member, "__model_invariant__", False
            ):
                continue
            result = member(self)
            if not isinstance(result, Result):
                raise TypeError(f"Invariant {name} must return a Result")
            if result.is_failure():
                error = result.error
                if not isinstance(error, Exception):
                    raise TypeError(f"Invariant {name} must fail with an Exception")
                errors.append((name, error))
            elif result.value is not None:
                raise TypeError(f"Invariant {name} must return Success(None)")

        if errors:
            details: list[InitErrorDetails] = []
            for name, error in errors:
                if not isinstance(error, ValueError):
                    wrapped = ValueError(str(error))
                    wrapped.__cause__ = error
                    error = wrapped
                details.append(
                    InitErrorDetails(
                        type="value_error",
                        loc=(name,),
                        input=self,
                        ctx={"error": error},
                    )
                )
            raise ValidationError.from_exception_data(type(self).__name__, details)

        return self
