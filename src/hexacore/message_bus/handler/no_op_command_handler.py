"""No-op command handler for unregistered command types."""

import logging

from katharos.ds import ImmutableList

from hexacore.command import BaseCommand
from hexacore.event import BaseEvent

from .base_command_handler import (
    BaseCommandHandler,
)

logger = logging.getLogger(__name__)


class NoOpCommandHandler(BaseCommandHandler):
    """Command handler that performs no operation, used as a default fallback."""

    def handle(self, command: BaseCommand) -> ImmutableList[BaseEvent]:
        """
        Handle a command that has no operation.

        Args:
            command: The command to handle.

        Returns:
            An empty immutable list
        """
        logger.warning("No operation for command: %s", command)
        return ImmutableList([])
