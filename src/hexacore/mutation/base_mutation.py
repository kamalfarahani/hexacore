from abc import ABC, abstractmethod


class BaseMutation[T](ABC):
    """Base class for mutations."""

    @property
    @abstractmethod
    def value(self) -> T:
        """The original value before mutation."""

    @property
    @abstractmethod
    def mutated(self) -> T:
        """The value after mutation."""
