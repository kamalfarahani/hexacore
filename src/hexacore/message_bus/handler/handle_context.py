from dataclasses import dataclass
from typing import Protocol

from pydantic import BaseModel

from hexacore.event_publisher import BaseEventPublisher
from hexacore.unit_of_work import BaseUnitOfWork


class BaseUnitOfWorkFactory(Protocol):
    """
    Base unit of work factory protocol.
    """

    def __call__[M: BaseModel](self, ModelType: type[M]) -> BaseUnitOfWork[M]:
        """
        Create a new unit of work.

        Args:
            ModelType (type[M]): The model type.

        Returns:
            BaseUnitOfWork[M]: The unit of work.
        """
        ...


@dataclass
class HandleContext:
    """
    Context for handling commands and events.
    """

    unit_of_work_factory: BaseUnitOfWorkFactory
    event_publisher: BaseEventPublisher
