"""Abstract base repository interface."""

from abc import ABC, abstractmethod

from katharos.types import Lazy, Result

from hexacore.repository.exceptions import UnsupportedCommandError

from .db_command import BaseDBCommand


class BaseRepository(ABC):
    """Execute typed database commands returning promises."""

    @property
    @abstractmethod
    def supported_commands(self) -> list[type[BaseDBCommand]]:
        """Return the list of supported command types."""

    def is_command_supported(self, command: BaseDBCommand) -> bool:
        """Check if a command is supported by the repository.

        Args:
            command: Command to check.

        Returns:
            True if the command is supported, False otherwise.
        """
        return type(command) in self.supported_commands

    @abstractmethod
    def execute[O](
        self,
        command: BaseDBCommand[O],
    ) -> Result[UnsupportedCommandError, Lazy[O]]:
        """Execute a database command.

        Args:
            command: Typed command to execute.

        Returns:
            Result containing the command result wrapped in a Lazy.
        """
        raise NotImplementedError()
