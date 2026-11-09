"""Abstract base class for command handlers."""

from abc import ABC, abstractmethod

from katharos.types import ImmutableList

from hexacore.command import BaseCommand
from hexacore.event import BaseEvent


class BaseCommandHandler[Command: BaseCommand](ABC):
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
