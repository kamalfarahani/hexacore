from katharos.ds import Result
from pydantic import BaseModel

from hexacore.repository.base import BaseDBPromise
from hexacore.repository.exceptions import NotFoundError, PromiseNotReadyError

from .with_id import SQLAlchemyWithID


class SQLAlchemyDBPromise[M: BaseModel](BaseDBPromise[M]):
    """
    SQLAlchemy implementation of the database promise pattern.

    This class wraps a SQLAlchemy ORM model through SQLAlchemyWithID and provides
    a way to track whether the object has been persisted to the database. It implements
    lazy loading and deferred access to database entities.

    Type Args:
        M: A Pydantic BaseModel subtype representing the domain model.

    Attributes:
        with_id: The SQLAlchemy WithID wrapper containing the ORM model, or None if not found.
    """

    with_id: SQLAlchemyWithID[M] | None

    def __init__(
        self,
        with_id: SQLAlchemyWithID[M] | None,
    ) -> None:
        """
        Initialize the promise.

        Args:
            with_id: The SQLAlchemy WithID wrapper containing the ORM model, or None if not found.
        """
        self.with_id = with_id

    @property
    def value(self) -> Result[NotFoundError, M]:
        """
        Get the value of the promise.

        Returns:
            Result[NotFoundError, M]: The value of the promise.
        """
        if self.with_id is None:
            return Result[NotFoundError, M].Failure(
                NotFoundError("Value not found in the database")
            )

        return Result[NotFoundError, M].Success(self.with_id.model_orm.model)

    @property
    def ready(self) -> bool:
        """
        Check if the promise is ready.

        Returns:
            bool: True if the promise is ready, False otherwise.
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
            Result[PromiseNotReadyError, SQLAlchemyWithID[M]]: The result of the promise.
        """
        if not self.ready:
            return Result[PromiseNotReadyError, SQLAlchemyWithID[M]].Failure(
                PromiseNotReadyError("DBPromise is not ready")
            )

        # this is safe because we checked ready above, this line is only for type checker
        assert self.with_id is not None

        return Result[PromiseNotReadyError, SQLAlchemyWithID[M]].Success(self.with_id)
