"""Abstract base class for event handlers."""

from abc import ABC, abstractmethod

from katharos.types import ImmutableList

from hexacore.event import BaseEvent

from .handle_context import HandleContext


class BaseEventHandler[Event: BaseEvent](ABC):
    """Abstract base class for event handlers in the message bus.

    Subclasses must implement the ``handle`` method to process a specific
    event type and return any resulting domain events.

    Attributes:
        handle_context: The context object providing shared resources and
            services available during event handling.
    """

    def __init__(self, handle_context: HandleContext) -> None:
        """Initialize the event handler with a handle context.

        Args:
            handle_context: The handle context to use for handling events.
        """
        self.handle_context = handle_context

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
