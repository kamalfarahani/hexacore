"""SQLAlchemy implementation of the database promise pattern."""

from katharos.ds import Result
from pydantic import BaseModel

from hexacore.repository.base import BaseDBPromise
from hexacore.repository.exceptions import NotFoundError, PromiseNotReadyError

from .with_id import SQLAlchemyWithID


class SQLAlchemyDBPromise[M: BaseModel](BaseDBPromise[M]):
    """
    SQLAlchemy implementation of the database promise pattern.

    Wraps a ``SQLAlchemyWithID`` and provides deferred access to the
    persisted entity.  Generic over ``M``, a ``BaseModel`` subtype
    representing the domain model.

    Attributes:
        with_id: The ``SQLAlchemyWithID`` wrapper, or ``None`` if the entity
            was not found.
    """

    with_id: SQLAlchemyWithID[M] | None

    def __init__(
        self,
        with_id: SQLAlchemyWithID[M] | None,
    ) -> None:
        """
        Initialize the promise.

        Args:
            with_id: The ``SQLAlchemyWithID`` wrapper, or ``None`` if the
                entity was not found.
        """
        self.with_id = with_id

    @property
    def value(self) -> Result[NotFoundError, M]:
        """
        Get the value of the promise.

        Returns:
            The domain model in a ``Result``, or a ``NotFoundError`` failure
            if the entity was not found.
        """
        if self.with_id is None:
            return Result[NotFoundError, M].Failure(
                NotFoundError("Value not found in the database")
            )

        return Result[NotFoundError, M].Success(self.with_id.get_model())

    @property
    def ready(self) -> bool:
        """
        Check if the promise is ready.

        Returns:
            ``True`` if the entity has a database-assigned ID, ``False``
            otherwise.
        """
        if self.with_id is None:
            return False

        if self.with_id.get_id() is not None:
            return True

        return False

    @property
    def result(self) -> Result[PromiseNotReadyError, SQLAlchemyWithID[M]]:
        """
        Get the result of the promise.

        Returns:
            The ``SQLAlchemyWithID`` wrapper in a ``Result``, or a
            ``PromiseNotReadyError`` failure if the promise is not ready.
        """
        if not self.ready:
            return Result[PromiseNotReadyError, SQLAlchemyWithID[M]].Failure(
                PromiseNotReadyError("DBPromise is not ready")
            )

        # this is safe because we checked ready above, this line is only for type checker
        assert self.with_id is not None

        return Result[PromiseNotReadyError, SQLAlchemyWithID[M]].Success(self.with_id)
