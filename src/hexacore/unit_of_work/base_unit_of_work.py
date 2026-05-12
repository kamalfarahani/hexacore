"""Abstract unit-of-work interface."""

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
        The repository for the model type managed by this unit of work.

        Returns:
            The repository instance.
        """
        raise NotImplementedError()

    def __enter__(self) -> Self:
        """
        Enter the unit of work context manager.

        Returns:
            This unit of work instance.
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
        """Prepare the unit of work for use."""
        raise NotImplementedError()

    def done(self) -> None:
        """Finish the unit of work and release any resources."""
        raise NotImplementedError()

    @abstractmethod
    def commit(self) -> None:
        """Flush all pending changes and commit the current transaction."""
        raise NotImplementedError()

    @abstractmethod
    def rollback(self) -> None:
        """Discard all pending changes by rolling back the current transaction."""
        raise NotImplementedError()
