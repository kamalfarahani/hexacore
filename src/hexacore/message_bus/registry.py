"""Handler registries for commands and events."""

from collections import defaultdict
from collections.abc import Callable

from katharos.types import ImmutableList

from hexacore.command import BaseCommand
from hexacore.event import BaseEvent
from hexacore.message_bus.handler import (
    BaseCommandHandler,
    BaseEventHandler,
    BaseHandleResult,
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

    def __getitem__[C: BaseCommand](
        self,
        key: type[C],
    ) -> BaseCommandHandler[C, BaseHandleResult]:
        """Retrieve the command handler associated with the given command type.

        Args:
            key: The command type for which to retrieve the handler.

        Returns:
            The registered handler, creating and storing a default handler if
            the command type is missing.
        """
        return self._registry[key]

    def __setitem__[C: BaseCommand](
        self,
        key: type[C],
        value: BaseCommandHandler[C, BaseHandleResult],
    ):
        """Associate a command handler with a specific command type in the registry.

        Args:
            key: The command type to associate with the handler.
            value: The command handler to associate with the command type.
        """
        self._registry[key] = value


class EventRegistry:
    """Map exact event types to immutable handler lists, creating defaults on lookup."""

    def __init__(
        self,
        default_handler_factory: Callable[[], ImmutableList[BaseEventHandler]],
    ) -> None:
        """Initialize the event registry with a default handler factory.

        Args:
            default_handler_factory: A factory that returns an immutable list of
                event handlers when an event type has no registered handlers.
        """
        self._registry = defaultdict(default_handler_factory)

    def __getitem__[E: BaseEvent](
        self,
        key: type[E],
    ) -> ImmutableList[BaseEventHandler[E, BaseHandleResult]]:
        """Retrieve the list of event handlers associated with the given event type.

        Args:
            key: The event type for which to retrieve handlers.

        Returns:
            The stored immutable handler list, creating and storing a default
            immutable list if the event type is missing.
        """
        return self._registry[key]

    def __setitem__[E: BaseEvent](
        self,
        key: type[E],
        value: ImmutableList[BaseEventHandler[E, BaseHandleResult]],
    ) -> None:
        """Associate an immutable handler list with a specific event type.

        Args:
            key: The event type to associate with the handlers.
            value: The event handlers to associate with the event type.
        """
        self._registry[key] = value
