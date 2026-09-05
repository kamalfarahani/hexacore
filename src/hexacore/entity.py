from abc import ABC, abstractmethod


class Entity[I](ABC):
    """
    Base class for all entities in the system.
    """

    @property
    @abstractmethod
    def identifier(self) -> I:
        """
        Returns the unique identifier of the entity.

        Returns:
            The unique identifier of the entity.
        """
