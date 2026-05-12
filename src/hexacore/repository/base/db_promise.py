"""Abstract database promise interface."""

from abc import ABC, abstractmethod

from katharos.ds import Result
from pydantic import BaseModel

from hexacore.repository.exceptions import PromiseNotReadyError

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
    def value(self) -> Result[Exception, M]:
        """
        Get the value of the promise.

        Returns:
            The domain model wrapped in a ``Result``, or an ``Exception``
            failure if the entity was not found or an error occurred.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def result(self) -> Result[Exception, WithID[M]]:
        """
        Get the result of the promise.

        Returns:
            The ``WithID`` wrapper in a ``Result``, or an ``Exception``
            failure if the entity was not found or an error occurred.
        """
        raise NotImplementedError()
