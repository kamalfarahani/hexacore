"""WithID abstract interface for entities carrying a database ID."""

from abc import ABC, abstractmethod

from pydantic import BaseModel


class WithID[M: BaseModel](ABC):
    """
    Abstract base class for objects that carry an integer ID and an associated model.

    Generic over ``M``, a ``BaseModel`` subtype representing the associated
    domain model.
    """

    @abstractmethod
    def get_id(self) -> int | None:
        """
        Returns the integer identifier of this object.

        Returns:
            The identifier or None if not set.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_model(self) -> M:
        """
        Returns the model associated with this object.

        Returns:
            The model instance of type M.
        """
        raise NotImplementedError()
