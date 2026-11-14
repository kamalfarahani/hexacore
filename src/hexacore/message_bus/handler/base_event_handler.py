"""Abstract base class for event handlers."""

from abc import ABC, abstractmethod

from hexacore.event import BaseEvent

from .base_handle_result import BaseHandleResult


class BaseEventHandler[Event: BaseEvent, R: BaseHandleResult](ABC):
    """React to domain events and return application-defined results.

    Subclasses implement ``handle``; calling an instance delegates to it.
    Results expose any further domain events through their ``events`` property
    and may carry additional application-specific information.
    """

    @abstractmethod
    def handle(self, event: Event) -> R:
        """Process an event and return its result, including any further events.

        Args:
            event: The event to handle.

        Returns:
            The processing result exposing any further domain events.
        """
        raise NotImplementedError()

    def __call__(self, event: Event) -> R:
        """Make the handler callable, delegating to ``handle``.

        Args:
            event: The event to handle.

        Returns:
            The result returned by ``handle``, passed through unchanged.
        """
        return self.handle(event)
