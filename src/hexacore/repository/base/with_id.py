from abc import ABC, abstractmethod

from pydantic import BaseModel


class WithID[M: BaseModel](ABC):
    """Abstract base class for objects that carry an integer ID and an associated model.

    Type Args:
        M: A Pydantic BaseModel subtype representing the associated model.
    """

    @abstractmethod
    def get_id(self) -> int:
        """Returns the integer identifier of this object.

        Returns:
            The integer ID.

        Raises:
            NotImplementedError: If not implemented by a subclass.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_model(self) -> M:
        """Returns the model associated with this object.

        Returns:
            The associated model instance of type M.

        Raises:
            NotImplementedError: If not implemented by a subclass.
        """
        raise NotImplementedError()
