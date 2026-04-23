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
    Abstract base class for message bus implementations following the Command-Query Separation pattern.

    The message bus serves as a central dispatcher for commands and events, routing them to their
    registered handlers. It processes messages in a queue-based manner to handle cascading events
    that may be generated during message processing.

    Architecture:
        - **Commands**: Represent intent to change system state. Each command type has exactly one
          handler that executes the command and returns a result. Commands may generate events as
          side effects.
        - **Events**: Represent facts about state changes that have occurred. Each event type can
          have multiple handlers (observers). Events do not return results to the caller.
        - **Message Queue**: All messages (commands and events) are processed sequentially through
          a queue, ensuring that cascading events generated during processing are handled in order.

    Processing Flow:
        1. A command or event is submitted to the message bus
        2. The message is added to an internal queue
        3. Messages are processed one at a time:
           - Commands: Handler executes, returns result, and may emit events
           - Events: All registered handlers execute and may emit additional events
        4. Any generated events are added to the queue and processed in turn
        5. Results from commands are collected and returned to the caller

    Note:
        This implementation follows the architecture described in "Architecture Patterns with Python"
        (Cosmic Python). For detailed information, see:
        https://www.cosmicpython.com/book/chapter_10_commands.html

    Attributes:
        command_handlers: Mapping of command types to their single handler function
        event_handlers: Mapping of event types to their list of handler functions
        handle_context: Context for handling commands and events
    """

    def __init__(
        self,
        handle_context: HandleContext,
        command_registry: CommandRegistry,
        event_registry: EventRegistry,
    ):
        """
        Initialize the message bus.

        Args:
            handle_context (HandleContext): The context for handling commands and events
        """
        self.handle_context = handle_context
        self.command_registry = command_registry
        self.event_registry = event_registry

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
        handler = self.command_registry[type(command)]
        return handler(command)

    def handle_event(self, event: BaseEvent) -> list[BaseEvent]:
        """
        Handle an event

        Args:
            event (BaseEvent): The event to handle

        Returns:
            list[BaseEvent]: The events resulting from the event handling
        """
        handlers = self.event_registry[type(event)]
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
