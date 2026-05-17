"""Core message bus implementation."""

from katharos.types import ImmutableList
from toolz import concat

from hexacore.command import BaseCommand
from hexacore.event import BaseEvent

from .handler import HandleContext
from .registry import CommandRegistry, EventRegistry


class BaseMessageBus:
    """
    Base message bus implementation.
    """

    _handle_context: HandleContext
    _command_registry: CommandRegistry
    _event_registry: EventRegistry

    def __init__(
        self,
        handle_context: HandleContext,
        command_registry: CommandRegistry,
        event_registry: EventRegistry,
    ) -> None:
        """
        Initialize the message bus.

        Args:
            handle_context: The context for handling commands and events.
            command_registry: The registry for command handlers.
            event_registry: The registry for event handlers.
        """
        self._handle_context = handle_context
        self._command_registry = command_registry
        self._event_registry = event_registry

    def handle(self, message: BaseCommand | BaseEvent) -> None:
        """
        Handle a message

        Args:
            message: The message to handle.
        """
        messages = [message]
        while messages:
            message = messages.pop(0)
            match message:
                case BaseCommand():
                    messages.extend(self.handle_command(message))
                case BaseEvent():
                    messages.extend(self.handle_event(message))

    def handle_command(self, command: BaseCommand) -> ImmutableList[BaseEvent]:
        """
        Handle a command

        Args:
            command: The command to handle.

        Returns:
            The events resulting from the command handling.
        """
        handler = self._command_registry[type(command)]
        return handler.handle(command)

    def handle_event(self, event: BaseEvent) -> ImmutableList[BaseEvent]:
        """
        Handle an event

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
