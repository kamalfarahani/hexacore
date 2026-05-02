import logging
from typing import Generator

from .connection import BaseBrokerConnection
from .connection.exceptions import ConsumeError

logger = logging.getLogger(__name__)


class EventListener[C: BaseBrokerConnection]:
    """
    A generic event listener that consumes messages from a broker queue.

    This class provides a high-level interface for listening to events from a message broker.
    It wraps a broker connection and provides context manager support for proper resource management.

    Type Parameters:
        C: The type of broker connection, must be a subclass of BaseBrokerConnection.

    Example:
        with EventListener(connection) as listener:
            for message in listener.listen("my_queue"):
                process_message(message)
    """

    def __init__(self, connection: C) -> None:
        """
        Initialize the active event listener.

        Args:
            connection (C): The broker connection to use for listening to events.
        """
        self._connection = connection

    def listen(self, queue_name: str) -> Generator[dict, None, None]:
        """
        Listen for messages from a queue.

        Args:
            queue_name (str): The name of the queue to listen to.

        Yields:
            dict: The consumed message from the queue.
        """
        try:
            yield from self._connection.consume(queue_name)
        except ConsumeError as e:
            logger.error(f"Error listening to queue {queue_name}: {e}")

    def __enter__(self) -> "EventListener[C]":
        """
        Open the connection for the event listener.

        Returns:
            EventListener[C]: The event listener instance with an open connection.
        """
        self._connection.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Close the connection for the event listener.

        Args:
            exc_type: The type of exception raised (if any).
            exc_val: The value of the exception raised (if any).
            exc_tb: The traceback of the exception raised (if any).
        """
        self._connection.__exit__(exc_type, exc_val, exc_tb)
