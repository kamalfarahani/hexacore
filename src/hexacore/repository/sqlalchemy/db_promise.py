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
        error: The error that occurred, or ``None`` if no error occurred.
    """

    with_id: SQLAlchemyWithID[M] | None
    error: Exception | None

    def __init__(
        self,
        with_id: SQLAlchemyWithID[M] | None,
        error: Exception | None = None,
    ) -> None:
        """
        Initialize the promise.

        Args:
            with_id: The ``SQLAlchemyWithID`` wrapper, or ``None`` if the
                entity was not found.
            error: The error that occurred, or ``None`` if no error occurred.
        """
        self.with_id = with_id
        self.error = error

    @property
    def value(self) -> Result[Exception, M]:
        """
        Get the value of the promise.

        Returns:
            The domain model in a ``Result``, or an ``Exception`` failure
            if the entity was not found or an error occurred.
        """
        if self.with_id is None:
            return Result[Exception, M].Failure(
                self.error or NotFoundError("Value not found in the database")
            )

        return Result[Exception, M].Success(self.with_id.get_model())

    @property
    def result(self) -> Result[Exception, SQLAlchemyWithID[M]]:
        """
        Get the result of the promise.

        Returns:
            The ``SQLAlchemyWithID`` wrapper in a ``Result``, or an ``Exception``
            failure if the entity was not found or an error occurred.
        """
        if self.error:
            return Result[Exception, SQLAlchemyWithID[M]].Failure(self.error)

        if self.with_id is None:
            return Result[Exception, SQLAlchemyWithID[M]].Failure(
                NotFoundError("Value not found in the database")
            )

        try:
            if self.with_id.get_id() is None:
                return Result[Exception, SQLAlchemyWithID[M]].Failure(
                    PromiseNotReadyError("DBPromise is not ready")
                )
        except Exception as e:
            return Result[Exception, SQLAlchemyWithID[M]].Failure(e)

        return Result[Exception, SQLAlchemyWithID[M]].Success(self.with_id)
