"""Reusable collections of command handler registrations."""

from dataclasses import dataclass

from katharos.types import ImmutableList

from hexacore.command import BaseCommand
from hexacore.message_bus.handler import BaseCommandHandler


@dataclass(frozen=True)
class HandlerPair[C: BaseCommand]:
    """Bind an exact command type to the handler used to process it."""

    command: type[C]
    handler: BaseCommandHandler[C]


class Extension:
    """Group command handler registrations for installation on message buses.

    Registrations retain their supplied order. When installed, later entries
    for the same command type replace earlier entries.
    """

    def __init__(self, handlers: ImmutableList[HandlerPair]):
        """Initialize the extension with its command handler registrations.

        Args:
            handlers: Ordered registrations to install on a message bus.
        """
        self._handlers = handlers

    @property
    def handlers(self) -> ImmutableList[HandlerPair]:
        """Return the command handler registrations in installation order."""
        return self._handlers
