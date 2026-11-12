"""Handler registries for commands and events."""

from collections import defaultdict
from collections.abc import Callable

from hexacore.command import BaseCommand
from hexacore.event import BaseEvent
from hexacore.message_bus.handler import (
    BaseCommandHandler,
    BaseEventHandler,
)


class CommandRegistry:
    """Map exact command types to handlers, creating defaults on first lookup."""

    def __init__(
        self,
        default_handler_factory: Callable[[], BaseCommandHandler],
    ) -> None:
        """Initialize the command registry with a default handler factory.

        Args:
            default_handler_factory: A factory that returns a default command handler
                when a command type has no registered handler.
        """
        self._registry = defaultdict(default_handler_factory)

    def __getitem__(self, key: type[BaseCommand]) -> BaseCommandHandler:
        """Retrieve the command handler associated with the given command type.

        Args:
            key: The command type for which to retrieve the handler.

        Returns:
            The registered handler, creating and storing a default handler if
            the command type is missing.
        """
        return self._registry[key]

    def __setitem__(
        self,
        key: type[BaseCommand],
        value: BaseCommandHandler,
    ):
        """Associate a command handler with a specific command type in the registry.

        Args:
            key: The command type to associate with the handler.
            value: The command handler to associate with the command type.
        """
        self._registry[key] = value


class EventRegistry:
    """Map exact event types to ordered handler lists, creating defaults on lookup."""

    def __init__(
        self,
        default_handler_factory: Callable[[], list[BaseEventHandler]],
    ) -> None:
        """Initialize the event registry with a default handler factory.

        Args:
            default_handler_factory: A factory that returns a default list of event
                handlers when an event type has no registered handlers.
        """
        self._registry = defaultdict(default_handler_factory)

    def __getitem__(self, key: type[BaseEvent]) -> list[BaseEventHandler]:
        """Retrieve the list of event handlers associated with the given event type.

        Args:
            key: The event type for which to retrieve handlers.

        Returns:
            The stored handler list, creating and storing a default list if the
            event type is missing. Changes to the returned list affect the registry.
        """
        return self._registry[key]

    def __setitem__(
        self,
        key: type[BaseEvent],
        value: list[BaseEventHandler],
    ) -> None:
        """Associate a list of event handlers with a specific event type in the registry.

        Args:
            key: The event type to associate with the handlers.
            value: The event handlers to associate with the event type.
        """
        self._registry[key] = value
