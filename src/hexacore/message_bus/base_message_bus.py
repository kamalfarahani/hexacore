from abc import ABC
from typing import Any

from toolz import concat

from hexacore.command import BaseCommand
from hexacore.event import BaseEvent

from .handler import (
    CommandResult,
    HandleContext,
)
from .registry import CommandRegistry, EventRegistry


class BaseMessageBus(ABC):
    """
    Abstract base class for a message bus that handles commands and events.
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
            handle_context (HandleContext): The context for handling commands and events
            command_registry (CommandRegistry): The registry for command handlers
            event_registry (EventRegistry): The registry for event handlers
        """
        self._handle_context = handle_context
        self._command_registry = command_registry
        self._event_registry = event_registry

    def handle(self, message: BaseCommand | BaseEvent) -> list[Any]:
        """
        Handle a message

        Args:
            message (BaseCommand | BaseEvent): The message to handle

        Returns:
            list[Any]: The results of the message handling
        """
        messages = [message]
        results = []
        while messages:
            message = messages.pop(0)
            match message:
                case BaseCommand():
                    result, events = self.handle_command(message)
                    messages.extend(events)
                    results.append(result)
                case BaseEvent():
                    messages.extend(self.handle_event(message))

        return results

    def handle_command(self, command: BaseCommand) -> CommandResult:
        """
        Handle a command

        Args:
            command (BaseCommand): The command to handle

        Returns:
            CommandResult: The result of the command handling
        """
        handler = self._command_registry[type(command)]
        return handler(command)

    def handle_event(self, event: BaseEvent) -> list[BaseEvent]:
        """
        Handle an event

        Args:
            event (BaseEvent): The event to handle

        Returns:
            list[BaseEvent]: The events resulting from the event handling
        """
        handlers = self._event_registry[type(event)]
        return list(
            concat(
                [
                    handler(
                        event,
                    )
                    for handler in handlers
                ]
            )
        )
