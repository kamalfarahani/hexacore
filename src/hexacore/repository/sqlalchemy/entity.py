"""Execute entity commands through subclass-provided SQLAlchemy handlers."""

from abc import abstractmethod
from collections.abc import Callable, Mapping
from typing import Any, cast

from katharos.types import Result
from sqlalchemy.orm import Session

from hexacore.repository.base import BaseDBCommand, BaseEntityRepository
from hexacore.repository.exceptions import UnsupportedCommandError


class SQLAlchemyEntityRepository(BaseEntityRepository):
    """Dispatch entity commands using a caller-owned SQLAlchemy session.

    Subclasses map command classes to bound methods. Each handler accepts
    its command, performs database work immediately, and returns the command's
    declared output. Commands may declare lazy outputs when conversion must
    wait for a caller-controlled flush, such as for database-generated IDs.
    The caller controls flushing and transactions.
    """

    def __init__(self, session: Session) -> None:
        """Initialize the repository.

        Args:
            session: Session used by handlers and managed by the caller.
        """
        self._session = session

    @property
    def session(self) -> Session:
        """The caller-owned session available to command handlers."""
        return self._session

    @property
    @abstractmethod
    def command_handlers(
        self,
    ) -> Mapping[type[BaseDBCommand[Any]], Callable[..., Any]]:
        """Command classes mapped to bound handlers returning declared outputs.

        Each handler accepts one instance of its registered command class
        and returns a value matching that command's result annotation.
        """
        ...

    @property
    def supported_commands(self) -> list[type[BaseDBCommand]]:
        """The exact command classes registered by this repository."""
        return list(self.command_handlers)

    def execute[O](
        self, command: BaseDBCommand[O]
    ) -> Result[UnsupportedCommandError, O]:
        """Invoke a registered handler immediately and return its output.

        Args:
            command: Command whose exact class selects the handler.

        Returns:
            Success containing the handler's output, or failure containing
            an unsupported-command error. Handler exceptions propagate;
            lazy conversion exceptions surface when a lazy output is resolved.
        """
        handler = self.command_handlers.get(type(command))
        if handler is None:
            return Result.Failure(
                UnsupportedCommandError(
                    f"Unsupported command type: {type(command).__qualname__}"
                )
            )
        return Result.Success(cast(O, handler(command)))
