"""Abstract base repository interface."""

from abc import ABC, abstractmethod

from pydantic import BaseModel

from .db_promise import BaseDBPromise


class BaseRepository[M: BaseModel](ABC):
    """
    Base repository interface.
    """

    @abstractmethod
    def add(self, model: M) -> BaseDBPromise[M]:
        """
        Add a model to the repository.

        Args:
            model: The model to add.

        Returns:
            A promise that resolves to the added model.
        """
        raise NotImplementedError()

    @abstractmethod
    def get(self, id: int) -> BaseDBPromise[M]:
        """
        Get a model by its ID.

        Args:
            id: The ID of the model.

        Returns:
            A promise that resolves to the model with the given ID.
        """
        raise NotImplementedError()

    @abstractmethod
    def update(self, model: M, id: int) -> BaseDBPromise[M]:
        """
        Update a model in the repository.

        Args:
            model: The updated model data.
            id: The ID of the model to update.

        Returns:
            A promise that resolves to the updated model.
        """
        raise NotImplementedError()

    @abstractmethod
    def delete(self, id: int) -> BaseDBPromise[M]:
        """
        Delete a model from the repository.

        Args:
            id: The ID of the model to delete.

        Returns:
            A promise that resolves to the deleted model.
        """
        raise NotImplementedError()
