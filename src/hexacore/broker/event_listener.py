"""Event listener for consuming messages from a broker queue."""

import logging
from typing import Generator

from .connection import BaseBrokerConnection
from .connection.exceptions import ConsumeError

logger = logging.getLogger(__name__)


class EventListener[C: BaseBrokerConnection]:
    """
    Consumes messages from a broker queue.

    Wraps a broker connection and provides context manager support for
    proper resource management.  Generic over ``C``, a
    ``BaseBrokerConnection`` subtype.

    Example:
        >>> with EventListener(connection) as listener:
        ...     for message in listener.listen("my_queue"):
        ...         process_message(message)
    """

    def __init__(self, connection: C) -> None:
        """
        Initialize the active event listener.

        Args:
            connection: The broker connection to use for listening to events.
        """
        self._connection = connection

    def listen(self, queue_name: str) -> Generator[dict, None, None]:
        """
        Listen for messages from a queue.

        Args:
            queue_name: The name of the queue to listen to.

        Yields:
            Each consumed message as a dict.
        """
        try:
            yield from self._connection.consume(queue_name)
        except ConsumeError as e:
            logger.error(f"Error listening to queue {queue_name}: {e}")

    def __enter__(self) -> "EventListener[C]":
        """
        Open the connection for the event listener.

        Returns:
            This event listener instance with an open connection.
        """
        self._connection.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Close the connection for the event listener.

        Args:
            exc_type: The exception type, or ``None``.
            exc_val: The exception instance, or ``None``.
            exc_tb: The traceback, or ``None``.
        """
        self._connection.__exit__(exc_type, exc_val, exc_tb)
