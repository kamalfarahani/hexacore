from abc import ABC, abstractmethod

from katharos.ds import Result
from pydantic import BaseModel

from hexacore.repository.exceptions import NotFoundError, PromiseNotReadyError

from .with_id import WithID


class BaseDBPromise[M: BaseModel](ABC):
    """
    Base database promise interface.
    This interface is used to represent an action for the database that can be executed later.
    """

    @property
    @abstractmethod
    def value(self) -> Result[NotFoundError, M]:
        """
        Get the value of the promise.

        Returns:
            Result[NotFoundError, M]: The value of the promise, or an error if not found.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def ready(self) -> bool:
        """
        Check if the promise is ready.

        Returns:
            bool: True if the promise is ready, False otherwise.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def result(self) -> Result[PromiseNotReadyError, WithID[M]]:
        """
        Get the result of the promise.

        Returns:
            Result[PromiseNotReadyError, WithID[M]]: The result of the promise,
                or an error if the promise is not ready.
        """
        raise NotImplementedError()
