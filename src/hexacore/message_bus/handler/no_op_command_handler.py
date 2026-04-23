import logging

from hexacore.command import BaseCommand
from hexacore.event import BaseEvent

from .base_command_handler import (
    BaseCommandHandler,
)

logger = logging.getLogger(__name__)


class NoOpCommandHandler(BaseCommandHandler):
    """
    A command handler that performs no operation.
    This can be used as a default handler for commands that do not have a specific handler registered.
    """

    def handle(self, command: BaseCommand) -> tuple[None, list[BaseEvent]]:
        """
        Handle a command that has no operation.

        Args:
            command: The command to handle.

        Returns:
            A tuple containing the result of the command handling and a list of events.
        """
        logger.warning("No operation for command: %s", command)
        return None, []
