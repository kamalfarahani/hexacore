from abc import ABC, abstractmethod
from types import TracebackType

from pydantic import BaseModel

from hexacore.repository import BaseRepository


class BaseUnitOfWork[M: BaseModel](ABC):
    """
    Base unit of work interface.
    """

    @property
    @abstractmethod
    def repository(self) -> BaseRepository[M]:
        """
        Get the repository.
        """
        raise NotImplementedError()

    @abstractmethod
    def __enter__(self) -> "BaseUnitOfWork":
        """
        Enter the unit of work context manager.

        Returns:
            BaseUnitOfWork: The unit of work context manager.
        """
        raise NotImplementedError()

    @abstractmethod
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """
        Exit the unit of work context manager.
        """
        raise NotImplementedError()

    @abstractmethod
    def commit(self) -> None:
        """
        Commit the transaction.
        """
        raise NotImplementedError()

    @abstractmethod
    def rollback(self) -> None:
        """
        Rollback the transaction.
        """
        raise NotImplementedError()
