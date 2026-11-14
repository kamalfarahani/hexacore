"""Abstract base repository interface."""

from abc import ABC, abstractmethod

from katharos.types import Result

from hexacore.repository.exceptions import UnsupportedCommandError

from .db_command import BaseDBCommand


class BaseEntityRepository(ABC):
    """Execute typed database commands returning their declared outputs."""

    @property
    @abstractmethod
    def supported_commands(self) -> list[type[BaseDBCommand]]:
        """The command types supported by this repository."""

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
    ) -> Result[UnsupportedCommandError, O]:
        """Execute a database command.

        Args:
            command: Typed command to execute.

        Returns:
            Success containing the command's output, or failure containing an
            unsupported-command error.
        """
        raise NotImplementedError()
