from abc import ABC, abstractmethod
from typing import Protocol

from pydantic import BaseModel


class WithID(Protocol):
    """
    Protocol for objects that have an ID.
    """

    def get_id(self) -> int: ...


class BaseDBPromise[M: BaseModel](ABC):
    """
    Base database promise interface.
    This interface is used to represent an action for the database that can be executed later.
    """

    @property
    @abstractmethod
    def value(self) -> M:
        """
        Get the value of the promise.

        Returns:
            M: The value of the promise.

        Raises:
            NotFoundError: If the value is not found in the database.
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
    def result(self) -> WithID:
        """
        Get the result of the promise.

        Returns:
            WithID: The result of the promise.

        Raises:
            PromiseNotReadyError: If the promise is not ready yet.
        """
        raise NotImplementedError()
