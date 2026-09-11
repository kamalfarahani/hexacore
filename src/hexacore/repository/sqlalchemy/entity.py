"""Execute entity commands through subclass-provided SQLAlchemy handlers."""

from abc import abstractmethod
from collections.abc import Callable, Mapping
from typing import Any, cast

from katharos.types import Lazy, Result
from sqlalchemy.orm import Session

from hexacore.entity import Entity
from hexacore.repository.base import BaseDBCommand, BaseEntityRepository
from hexacore.repository.exceptions import UnsupportedCommandError


class SQLAlchemyEntityRepository[E: Entity](BaseEntityRepository):
    """Dispatch entity commands using a caller-owned SQLAlchemy session.

    Subclasses map command classes to bound methods. Each handler accepts
    its command, performs database work immediately, and returns a ``Lazy``
    producing the command's declared result. The caller controls flushing
    and transactions, and must flush before resolving database-generated IDs.
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
    ) -> Mapping[type[BaseDBCommand[Any]], Callable[..., Lazy[Any]]]:
        """Command classes mapped to bound handlers returning lazy results.

        Each handler accepts one instance of its registered command class
        and returns a lazy value matching that command's result annotation.
        """
        ...

    @property
    def supported_commands(self) -> list[type[BaseDBCommand]]:
        """The exact command classes registered by this repository."""
        return list(self.command_handlers)

    def execute[O](
        self, command: BaseDBCommand[O]
    ) -> Result[UnsupportedCommandError, Lazy[O]]:
        """Invoke a registered handler immediately and return its lazy result.

        Args:
            command: Command whose exact class selects the handler.

        Returns:
            Success containing the handler's lazy result, or failure containing
            an unsupported-command error. Handler exceptions propagate;
            conversion exceptions surface when the lazy result is resolved.
        """
        handler = self.command_handlers.get(type(command))
        if handler is None:
            return Result.Failure(
                UnsupportedCommandError(
                    f"Unsupported command type: {type(command).__qualname__}"
                )
            )
        return Result.Success(cast(Lazy[O], handler(command)))
