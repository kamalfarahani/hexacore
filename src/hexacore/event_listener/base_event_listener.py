from abc import ABC, abstractmethod
from typing import Generator, Self


class BaseEventListener(ABC):
    """
    Base class for event listeners.

    This class is an abstract for context manager that handles listening for events.
    """

    @abstractmethod
    def listen(self, queue_name: str) -> Generator[dict, None, None]:
        """
        Listen to a queue and yield messages.

        Args:
            queue_name (str): The name of the queue to listen to.

        Yields:
            Generator[dict, None, None]: A generator of messages.
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
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
