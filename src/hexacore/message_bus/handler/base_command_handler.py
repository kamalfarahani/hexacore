from abc import ABC, abstractmethod
from typing import Any

from hexacore.command import BaseCommand
from hexacore.event import BaseEvent

from .handle_context import HandleContext

type CommandResult = tuple[Any, list[BaseEvent]]


class BaseCommandHandler[Command: BaseCommand](ABC):
    """
    Abstract base class for command handlers in the message bus.
    """

    def __init__(self, handle_context: HandleContext):
        """
        Initialize the command handler with a handle context.

        Args:
            handle_context: The handle context to use for handling commands.
        """
        self.handle_context = handle_context

    @abstractmethod
    def handle(self, command: Command) -> CommandResult:
        """
        Handle a command and return the result.

        Args:
            command: The command to handle.

        Returns:
            The result of the command handling.
        """
        raise NotImplementedError()

    def __call__(self, command: Command) -> CommandResult:
        """
        Call the handler to process a command.

        Args:
            command: The command to handle.

        Returns:
            The result of the command handling.
        """
        return self.handle(command)
