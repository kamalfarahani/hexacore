"""Handle context and unit-of-work factory protocol."""

from dataclasses import dataclass
from typing import Protocol

from pydantic import BaseModel

from hexacore.broker import EventPublisher
from hexacore.unit_of_work import BaseUnitOfWork


class BaseUnitOfWorkFactory(Protocol):
    """Protocol for factories that create ``BaseUnitOfWork`` instances."""

    def __call__[M: BaseModel](self, ModelType: type[M]) -> BaseUnitOfWork[M]:
        """
        Create a new unit of work for the given model type.

        Args:
            ModelType: The Pydantic model type the unit of work will manage.

        Returns:
            A ``BaseUnitOfWork`` instance scoped to ``ModelType``.
        """
        ...


@dataclass
class HandleContext:
    """
    Shared context passed to every command and event handler.

    Attributes:
        unit_of_work_factory: Factory used to create a ``BaseUnitOfWork``
            instance scoped to a particular model type.
        event_publisher: Publisher used to dispatch integration events to
            the message broker.
    """

    unit_of_work_factory: BaseUnitOfWorkFactory
    event_publisher: EventPublisher
