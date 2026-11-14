"""Abstract base class for command handlers."""

from abc import ABC, abstractmethod

from hexacore.command import BaseCommand

from .base_handle_result import BaseHandleResult


class BaseCommandHandler[Command: BaseCommand, R: BaseHandleResult](ABC):
    """Process commands and return application-defined results.

    Subclasses implement ``handle``; calling an instance delegates to it.
    Results expose produced domain events through their ``events`` property
    and may carry additional application-specific information.
    """

    @abstractmethod
    def handle(self, command: Command) -> R:
        """Process a command and return its result, including produced events.

        Args:
            command: The command instance to handle.

        Returns:
            The processing result exposing the produced domain events.
        """
        raise NotImplementedError()

    def __call__(self, command: Command) -> R:
        """Make the handler callable, delegating to ``handle``.

        Args:
            command: The command instance to handle.

        Returns:
            The result returned by ``handle``, passed through unchanged.
        """
        return self.handle(command)
