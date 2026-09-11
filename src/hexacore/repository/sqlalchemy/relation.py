"""Execute relation mutations through subclass-provided SQLAlchemy handlers."""

from abc import abstractmethod
from collections.abc import Callable, Mapping

from katharos.types import Result
from sqlalchemy.orm import Session

from hexacore.relation import BaseRelation, BaseRelationMutation
from hexacore.repository.base import BaseRelationRepository
from hexacore.repository.exceptions import UnsupportedMutationError


class SQLAlchemyRelationRepository[R: BaseRelation](BaseRelationRepository[R]):
    """Dispatch relation mutations using a caller-owned SQLAlchemy session.

    Execution preserves the collector and does not manage transactions.
    The caller must roll back if a handler fails after earlier mutations
    have already been applied.
    """

    def __init__(self, session: Session) -> None:
        """Initialize the repository.

        Args:
            session: Session used by handlers and managed by the caller.
        """
        self._session = session

    @property
    def session(self) -> Session:
        """The caller-owned session available to mutation handlers."""
        return self._session

    @property
    @abstractmethod
    def mutation_handlers(
        self,
    ) -> Mapping[type[BaseRelationMutation], Callable[..., None]]:
        """Mutation classes mapped to bound handlers accepting one mutation.

        The first registered class in a mutation's method resolution order
        wins, allowing unparameterized registrations for generic mutations.
        """
        ...

    def execute_mutations(self, relation: R) -> Result[UnsupportedMutationError, None]:
        """Validate and execute a snapshot of pending mutations in order.

        Handler exceptions propagate immediately and stop the batch. Pending
        mutations are preserved on both success and failure.

        Args:
            relation: Collector whose mutations should be applied.

        Returns:
            Success containing None after executing the batch, or failure
            containing an unsupported-mutation error without invoking handlers.
        """
        mutations = tuple(relation.mutations)
        handlers = dict(self.mutation_handlers)
        pending: list[tuple[Callable[..., None], BaseRelationMutation]] = []
        for mutation in mutations:
            for mutation_type in type(mutation).__mro__:
                handler = handlers.get(mutation_type)
                if handler is not None:
                    pending.append((handler, mutation))
                    break
            else:
                return Result.Failure(
                    UnsupportedMutationError(
                        f"Unsupported mutation type: {type(mutation).__qualname__}"
                    )
                )

        for handler, mutation in pending:
            handler(mutation)
        return Result.Success(None)
