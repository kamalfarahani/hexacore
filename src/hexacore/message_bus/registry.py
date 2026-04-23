from collections import defaultdict
from collections.abc import Callable

from hexacore.command import BaseCommand
from hexacore.event import BaseEvent
from hexacore.message_bus.handler import (
    BaseCommandHandler,
    BaseEventHandler,
)


class CommandRegistry:
    """
    A registry for command handlers.
    """

    def __init__(
        self,
        default_handler_factory: Callable[[], BaseCommandHandler],
    ) -> None:
        """
        Initializes the command registry with an empty defaultdict.

        Args:
            default_handler_factory (Callable[[], BaseCommandHandler]): A factory function that returns a default command handler when a command type is accessed that does not have an associated handler in the registry.
        """
        self._registry = defaultdict(default_handler_factory)

    def __getitem__(self, key: type[BaseCommand]) -> BaseCommandHandler:
        """
        Retrieves the command handler associated with the given command type.

        Args:
            key (type[BaseCommand]): The command type for which to retrieve the handler.

        Returns:
            BaseCommandHandler: The command handler associated with the command type.
        """
        return self._registry[key]

    def __setitem__(
        self,
        key: type[BaseCommand],
        value: BaseCommandHandler,
    ):
        """
        Associates a command handler with a specific command type in the registry.

        Args:
            key (type[BaseCommand]): The command type to associate with the handler.
            value (BaseCommandHandler): The command handler to associate with the command type.
        """
        self._registry[key] = value


class EventRegistry:
    """
    A registry for event handlers.
    """

    def __init__(
        self,
        default_handler_factory: Callable[[], list[BaseEventHandler]],
    ) -> None:
        """
        Initializes the event registry with an empty defaultdict.

        Args:
            default_handler_factory (Callable[[], list[BaseEventHandler]]):
                A factory function that returns a default list of event handlers when an event type is accessed that does not have associated handlers in the registry.
        """
        self._registry = defaultdict(default_handler_factory)

    def __getitem__(self, key: type[BaseEvent]) -> list[BaseEventHandler]:
        """
        Retrieves the list of event handlers associated with the given event type.

        Args:
            key (type[BaseEvent]): The event type for which to retrieve handlers.

        Returns:
            list[BaseEventHandler]: A list of event handlers associated with the event type.
        """
        return self._registry[key]

    def __setitem__(
        self,
        key: type[BaseEvent],
        value: list[BaseEventHandler],
    ) -> None:
        """
        Associates a list of event handlers with a specific event type in the registry.

        Args:
            key (type[BaseEvent]): The event type to associate with the handlers.
            value (list[BaseEventHandler]): A list of event handlers to associate with the event type.
        """
        self._registry[key] = value
