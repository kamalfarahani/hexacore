from abc import ABC, abstractmethod


class BaseDBCommand[O](ABC):
    """Abstract base class for database commands."""

    @property
    @abstractmethod
    def return_type(self) -> type[O]:
        """The type of the command result."""
        ...
