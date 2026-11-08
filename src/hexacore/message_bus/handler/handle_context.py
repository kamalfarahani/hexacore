"""Handle context and unit-of-work factory protocol."""

from dataclasses import dataclass
from typing import Protocol

from hexacore.broker import EventPublisher
from hexacore.repository import BaseRepository
from hexacore.unit_of_work import BaseUnitOfWork


class BaseUnitOfWorkFactory(Protocol):
    """Protocol for factories that create ``BaseUnitOfWork`` instances."""

    def __call__[R: BaseRepository](self, RepoType: type[R]) -> BaseUnitOfWork[R]:
        """Create a unit of work for the given repository type.

        Args:
            RepoType: Repository class the unit of work will manage.

        Returns:
            A unit of work whose repository is an instance of ``RepoType``.
        """
        raise NotImplementedError()


@dataclass
class HandleContext:
    """Shared context passed to every command and event handler.

    Attributes:
        unit_of_work_factory: Factory used to create a unit of work scoped
            to a particular model type.
        event_publisher: Publisher used to dispatch integration events to
            the message broker.
    """

    unit_of_work_factory: BaseUnitOfWorkFactory
    event_publisher: EventPublisher
