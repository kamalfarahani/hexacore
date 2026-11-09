"""Abstract base class for command handlers."""

from abc import ABC, abstractmethod

from katharos.types import ImmutableList

from hexacore.command import BaseCommand
from hexacore.event import BaseEvent


class BaseCommandHandler[Command: BaseCommand, Context](ABC):
    """Abstract base class for command handlers in the message bus.

    Subclasses must implement the ``handle`` method to process a specific
    command type and return the resulting domain events.

    The application defines and supplies the context; the handler stores the
    same instance without copying it or managing its lifecycle. Subclasses
    that need no dependencies can use ``None`` as their context.

    Attributes:
        handle_context: The context object providing shared resources and
            services available during command handling.
    """

    def __init__(self, handle_context: Context) -> None:
        """Initialize the command handler with a handle context.

        Args:
            handle_context: Application-defined dependencies used by the handler.
        """
        self.handle_context = handle_context

    @abstractmethod
    def handle(self, command: Command) -> ImmutableList[BaseEvent]:
        """Handle the given command and return the resulting domain events.

        Args:
            command: The command instance to handle.

        Returns:
            The domain events produced by handling the command, collected immutably.
        """
        raise NotImplementedError()

    def __call__(self, command: Command) -> ImmutableList[BaseEvent]:
        """Make the handler callable, delegating to ``handle``.

        Args:
            command: The command instance to handle.

        Returns:
            The domain events produced by handling the command, collected immutably.
        """
        return self.handle(command)
