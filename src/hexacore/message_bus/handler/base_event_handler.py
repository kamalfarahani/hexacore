"""Abstract base class for event handlers."""

from abc import ABC, abstractmethod

from katharos.types import ImmutableList

from hexacore.event import BaseEvent


class BaseEventHandler[Event: BaseEvent](ABC):
    """React to domain events and optionally produce further events.

    Subclasses implement ``handle``; calling an instance delegates to it.
    """

    @abstractmethod
    def handle(
        self,
        event: Event,
    ) -> ImmutableList[BaseEvent]:
        """Handle an event and return any generated events.

        Args:
            event: The event to handle.

        Returns:
            The domain events produced by handling the event, collected immutably.
        """
        raise NotImplementedError()

    def __call__(
        self,
        event: Event,
    ) -> ImmutableList[BaseEvent]:
        """Call the handler to process an event.

        Args:
            event: The event to handle.

        Returns:
            The domain events produced by handling the event, collected immutably.
        """
        return self.handle(event)
