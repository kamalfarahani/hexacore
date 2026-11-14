"""Shared result contract for command and event processing."""

from abc import ABC, abstractmethod

from katharos.types import ImmutableList

from hexacore.event import BaseEvent


class BaseHandleResult(ABC):
    """Expose domain events produced by processing a message.

    Subclasses provide ``events`` and may include additional application-specific
    information about the outcome. Results with no produced events expose an
    empty collection.
    """

    @property
    @abstractmethod
    def events(self) -> ImmutableList[BaseEvent]:
        """The produced domain events in order, collected immutably."""
