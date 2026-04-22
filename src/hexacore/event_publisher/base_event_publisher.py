from abc import ABC, abstractmethod
from typing import Self


class BaseEventPublisher(ABC):
    """
    Base event publisher.

    This class is an abstract for context manager that handles publishing events.
    """

    @abstractmethod
    def publish(
        self,
        queue_name: str,
        event: dict,
    ) -> None:
        """
        Publish an event.

        Args:
            queue_name (str): The name of the queue to publish to.
            event (dict): The event to publish.
        """
        raise NotImplementedError()

    @abstractmethod
    def open(self) -> None:
        """
        Open the connection.
        """
        raise NotImplementedError()

    @abstractmethod
    def close(self) -> None:
        """
        Close the connection.
        """
        raise NotImplementedError()

    def __enter__(self) -> Self:
        """
        Open the connection.

        Returns:
            Self: The event publisher instance.
        """
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Close the connection.

        Args:
            exc_type: The exception type.
            exc_val: The exception value.
            exc_tb: The exception traceback.
        """
        self.close()
