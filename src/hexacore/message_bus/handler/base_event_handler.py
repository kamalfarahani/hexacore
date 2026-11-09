"""Abstract base class for event handlers."""

from abc import ABC, abstractmethod

from katharos.types import ImmutableList

from hexacore.event import BaseEvent


class BaseEventHandler[Event: BaseEvent, Context](ABC):
    """Abstract base class for event handlers in the message bus.

    Subclasses must implement the ``handle`` method to process a specific
    event type and return any resulting domain events.

    The application defines and supplies the context; the handler stores the
    same instance without copying it or managing its lifecycle. Subclasses
    that need no dependencies can use ``None`` as their context.

    Attributes:
        handle_context: The context object providing shared resources and
            services available during event handling.
    """

    def __init__(self, handle_context: Context) -> None:
        """Initialize the event handler with a handle context.

        Args:
            handle_context: Application-defined dependencies used by the handler.
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
