from abc import ABC
from types import TracebackType
from typing import Self

from .base_relation_command import BaseRelationCommand


class BaseRelation(ABC):
    """Base class for relations between entities."""

    _commands: list[BaseRelationCommand]

    def __init__(self) -> None:
        """Initialize the relation with an empty command list."""
        self._commands = []

    def add_command(self, cmd: BaseRelationCommand) -> None:
        """Append a command to the relation.

        Args:
            cmd: Command to append.
        """
        self._commands.append(cmd)

    @property
    def commands(self) -> list[BaseRelationCommand]:
        """The mutable command list, in insertion order."""
        return self._commands

    def __enter__(self) -> Self:
        """Reset the command list and enter the relation context.

        Returns:
            This relation with a new, empty command list.
        """
        self._commands = []
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit the context without modifying commands or suppressing exceptions.

        Args:
            exc_type: Type of the exception raised in the context, or None if
                no exception occurred.
            exc_val: Exception instance, or None if no exception occurred.
            exc_tb: Exception traceback, or None if no exception occurred.
        """
