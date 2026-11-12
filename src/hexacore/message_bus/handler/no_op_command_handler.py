"""No-op command handler for unregistered command types."""

import logging

from katharos.types import ImmutableList

from hexacore.command import BaseCommand
from hexacore.event import BaseEvent

from .base_command_handler import (
    BaseCommandHandler,
)

logger = logging.getLogger(__name__)


class NoOpCommandHandler(BaseCommandHandler[BaseCommand]):
    """Provide a fallback that logs unhandled commands without producing events."""

    def handle(self, command: BaseCommand) -> ImmutableList[BaseEvent]:
        """Log a warning containing the command and return no events.

        Args:
            command: The command to handle.

        Returns:
            An empty immutable collection of domain events.
        """
        logger.warning("No operation for command: %s", command)
        return ImmutableList([])
