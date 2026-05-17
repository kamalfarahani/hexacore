"""Abstract base class for command handlers."""

from abc import ABC, abstractmethod

from katharos.types import ImmutableList

from hexacore.command import BaseCommand
from hexacore.event import BaseEvent

from .handle_context import HandleContext


class BaseCommandHandler[Command: BaseCommand](ABC):
    """
    Abstract base class for command handlers in the message bus.

    Subclasses must implement the ``handle`` method to process a specific
    command type and return the resulting domain events.  Generic over
    ``Command``, a ``BaseCommand`` subtype representing the command this
    handler processes.

    Attributes:
        handle_context: The context object providing shared resources and
            services available during command handling.
    """

    def __init__(self, handle_context: HandleContext) -> None:
        """
        Initialize the command handler with a handle context.

        Args:
            handle_context: The context object providing shared resources and
                services available during command handling.
        """
        self.handle_context = handle_context

    @abstractmethod
    def handle(self, command: Command) -> ImmutableList[BaseEvent]:
        """
        Handle the given command and return the resulting domain events.

        Args:
            command: The command instance to handle.

        Returns:
            An immutable list of domain events produced by handling the command.
        """
        raise NotImplementedError()

    def __call__(self, command: Command) -> ImmutableList[BaseEvent]:
        """
        Make the handler callable, delegating to ``handle``.

        Args:
            command: The command instance to handle.

        Returns:
            An immutable list of domain events produced by handling the command.
        """
        return self.handle(command)
