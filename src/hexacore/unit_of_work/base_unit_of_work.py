from abc import ABC, abstractmethod
from types import TracebackType
from typing import Self

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

    def __enter__(self) -> Self:
        """
        Enter the unit of work context manager.

        Returns:
            BaseUnitOfWork: The unit of work context manager.
        """
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """
        Exit the unit of work context manager.
        """
        self.done()

    @abstractmethod
    def start(self) -> None:
        """
        Prepare the unit of work for use.
        """
        raise NotImplementedError()

    def done(self) -> None:
        """
        Finish the unit of work and release any resources.
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
