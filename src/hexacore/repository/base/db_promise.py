"""Abstract database promise interface."""

from abc import ABC, abstractmethod

from katharos.ds import Result
from pydantic import BaseModel

from hexacore.repository.exceptions import NotFoundError, PromiseNotReadyError

from .with_id import WithID


class BaseDBPromise[M: BaseModel](ABC):
    """
    Abstract database promise interface.

    Represents a deferred database action whose result may not be available
    until after the current transaction is committed.  Generic over ``M``, a
    ``BaseModel`` subtype representing the domain model.
    """

    @property
    @abstractmethod
    def value(self) -> Result[NotFoundError, M]:
        """
        Get the value of the promise.

        Returns:
            The domain model wrapped in a ``Result``, or a ``NotFoundError``
            failure if the entity was not found.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def ready(self) -> bool:
        """
        Check if the promise is ready.

        Returns:
            ``True`` if the database has assigned an ID, ``False`` otherwise.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def result(self) -> Result[PromiseNotReadyError, WithID[M]]:
        """
        Get the result of the promise.

        Returns:
            The ``WithID`` wrapper in a ``Result``, or a ``PromiseNotReadyError``
            failure if the promise is not yet ready.
        """
        raise NotImplementedError()
