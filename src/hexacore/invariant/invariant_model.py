from inspect import isfunction
from typing import Any, Self, dataclass_transform

from katharos.types import Result
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    ValidationError,
    model_validator,
)
from pydantic_core import InitErrorDetails


@dataclass_transform(kw_only_default=True, field_specifiers=(Field, PrivateAttr))
class InvariantModel(BaseModel):
    """Model that checks marked invariants after successful field validation.

    Checks run in declaration order, visiting base classes in reverse MRO before
    subclasses. Overrides replace inherited checks and must be decorated again
    to participate. Validation collects all returned failures unless a check
    raises an exception or violates the Result return contract, which stops
    further checks immediately. Direct invariant calls retain their Result
    contract.

    Assignment validation is enabled by default, including invariant checks.
    Failed assignments restore the previous fields and assignment metadata.
    Restoration is shallow: in-place mutations and external side effects of
    validators or invariants are not undone.
    Subclasses inherit Pydantic configuration options and can override this
    default with ``validate_assignment=False`` in the class declaration.
    model_construct bypasses validation, including invariants.

    Examples:
        Declare Pydantic configuration options as class keywords::

            class Model(InvariantModel, frozen=True, extra="forbid"):
                value: int
    """

    model_config = ConfigDict(validate_assignment=True)

    def __setattr__(self, name: str, value: Any) -> None:
        """Assign an attribute, restoring model state if validation raises.

        Args:
            name: Attribute to assign.
            value: Proposed attribute value.
        """
        if name.startswith("_") or not type(self).model_config.get(
            "validate_assignment"
        ):
            super().__setattr__(name, value)
            return

        fields = self.__dict__.copy()
        fields_set = self.__pydantic_fields_set__.copy()
        extra = self.__pydantic_extra__
        extra = extra.copy() if extra is not None else None
        try:
            super().__setattr__(name, value)
        except Exception:
            object.__setattr__(self, "__dict__", fields)
            object.__setattr__(self, "__pydantic_fields_set__", fields_set)
            object.__setattr__(self, "__pydantic_extra__", extra)
            raise

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
