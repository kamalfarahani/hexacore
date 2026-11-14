"""No-op command handler for unregistered command types."""

import logging

from katharos.types import ImmutableList

from hexacore.command import BaseCommand
from hexacore.event import BaseEvent

from .base_command_handler import (
    BaseCommandHandler,
)
from .base_handle_result import BaseHandleResult

logger = logging.getLogger(__name__)


class NoOpHandleResult(BaseHandleResult):
    """Represent command processing that produces no domain events."""

    @property
    def events(self) -> ImmutableList[BaseEvent]:
        """An empty immutable collection of domain events."""
        return ImmutableList([])


class NoOpCommandHandler(BaseCommandHandler[BaseCommand, NoOpHandleResult]):
    """Provide a fallback that logs unhandled commands without producing events."""

    def handle(self, command: BaseCommand) -> NoOpHandleResult:
        """Log a warning containing the command and return an empty result.

        Args:
            command: The command to handle.

        Returns:
            A result whose ``events`` property contains no domain events.
        """
        logger.warning("No operation for command: %s", command)
        return NoOpHandleResult()
