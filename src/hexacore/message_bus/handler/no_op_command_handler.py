"""No-op command handler for unregistered command types."""

import logging

from katharos.types import ImmutableList

from hexacore.command import BaseCommand
from hexacore.event import BaseEvent

from .base_command_handler import (
    BaseCommandHandler,
)

logger = logging.getLogger(__name__)


class NoOpCommandHandler(BaseCommandHandler[BaseCommand, None]):
    """Fallback handler that logs a warning and produces no events.

    Requires no dependencies and sets its context to ``None``. Registries can
    use this class directly as their default handler factory.
    """

    def __init__(self) -> None:
        """Initialize the fallback handler without application dependencies."""
        super().__init__(None)

    def handle(self, command: BaseCommand) -> ImmutableList[BaseEvent]:
        """Log a warning containing the command and return no events.

        Args:
            command: The command to handle.

        Returns:
            An empty immutable collection of domain events.
        """
        logger.warning("No operation for command: %s", command)
        return ImmutableList([])
