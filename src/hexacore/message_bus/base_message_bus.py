"""Core message bus implementation."""

from katharos.types import ImmutableList
from toolz import concat

from hexacore.command import BaseCommand
from hexacore.event import BaseEvent

from .registry import CommandRegistry, EventRegistry


class BaseMessageBus:
    """Base message bus implementation."""

    _command_registry: CommandRegistry
    _event_registry: EventRegistry

    def __init__(
        self,
        command_registry: CommandRegistry,
        event_registry: EventRegistry,
    ) -> None:
        """Initialize the message bus.

        Args:
            command_registry: The registry for command handlers.
            event_registry: The registry for event handlers.
        """
        self._command_registry = command_registry
        self._event_registry = event_registry

    def handle(self, message: BaseCommand | BaseEvent) -> ImmutableList[BaseEvent]:
        """Handle a message and all events produced by its handlers.

        Args:
            message: The message to handle.

        Returns:
            The events already dispatched in FIFO processing order, including
            the original message if it is an event. If a handler raises, the
            exception propagates without returning a partial result.
        """
        messages = [message]
        events = []
        while messages:
            message = messages.pop(0)
            if isinstance(message, BaseEvent):
                events.append(message)
            match message:
                case BaseCommand():
                    messages.extend(self.handle_command(message))
                case BaseEvent():
                    messages.extend(self.handle_event(message))

        return ImmutableList(events)

    def handle_command(self, command: BaseCommand) -> ImmutableList[BaseEvent]:
        """Handle a command.

        Args:
            command: The command to handle.

        Returns:
            The events resulting from the command handling.
        """
        handler = self._command_registry[type(command)]
        return handler.handle(command)

    def handle_event(self, event: BaseEvent) -> ImmutableList[BaseEvent]:
        """Handle an event.

        Args:
            event: The event to handle.

        Returns:
            The events resulting from the event handling.
        """
        handlers = self._event_registry[type(event)]
        return ImmutableList(
            concat(
                [
                    handler(
                        event,
                    )
                    for handler in handlers
                ]
            )
        )
