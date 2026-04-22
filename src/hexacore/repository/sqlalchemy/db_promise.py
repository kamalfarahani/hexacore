from hexacore.repository.base import BaseDBPromise
from hexacore.repository.exceptions import NotFoundError, PromiseNotReadyError

from .model_orm import ModelORM


class SQLAlchemyDBPromise[T](BaseDBPromise[T]):
    """
    A SQLAlchemy implementation of the database promise pattern.

    This class wraps a domain model value and its corresponding ORM object,
    providing a way to track whether the object has been persisted to the database.
    """

    model_orm: ModelORM[T] | None

    def __init__(
        self,
        model_orm: ModelORM[T] | None,
    ) -> None:
        """
        Initialize the promise.

        Args:
            model_orm (ModelORM[T] | None): The corresponding ORM object, if available.
        """
        self.model_orm = model_orm

    @property
    def value(self) -> T:
        """
        Get the value of the promise.

        Returns:
            T: The value of the promise.

        Raises:
            NotFoundError: If the value is not found in the database.
        """
        if self.model_orm is None:
            raise NotFoundError("Value not found in the database")

        return self.model_orm.model

    @property
    def ready(self) -> bool:
        """
        Check if the promise is ready.

        Returns:
            bool: True if the promise is ready, False otherwise.
        """
        if self.model_orm is None:
            return False

        if self.model_orm.id is not None:
            return True

        return False

    @property
    def result(self) -> ModelORM[T]:
        """
        Get the result of the promise.

        Returns:
            Result[PromiseNotReadyError, CustomBase]: The result of the promise.
        """
        if not self.ready:
            raise PromiseNotReadyError("DBPromise is not ready")

        # this is safe because we checked ready above, this line is only for type checker
        assert self.model_orm is not None

        return self.model_orm
