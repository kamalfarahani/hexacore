"""Event publisher for sending messages to a broker exchange."""

import logging

from .connection import BaseBrokerConnection
from .connection.exceptions import PublishError

logger = logging.getLogger(__name__)


class EventPublisher[C: BaseBrokerConnection]:
    """
    Publishes events to a broker exchange.

    Wraps a broker connection and provides context manager support for
    proper resource management.  Generic over ``C``, a
    ``BaseBrokerConnection`` subtype.

    Example:
        >>> with EventPublisher(connection) as publisher:
        ...     publisher.publish("my_exchange", "routing.key", {"message": "hello"})
    """

    def __init__(self, connection: C) -> None:
        """
        Initialize the event publisher.

        Args:
            connection: The broker connection to use for publishing events.
        """
        self._connection = connection

    def publish(
        self,
        exchange_name: str,
        routing_key: str,
        data: dict,
    ) -> None:
        """
        Publish a message to an exchange.

        Args:
            exchange_name: The name of the exchange to publish to.
            routing_key: The routing key for the message.
            data: The data to publish as a JSON-serialisable dict.
        """
        try:
            self._connection.publish(exchange_name, routing_key, data)
        except PublishError as e:
            logger.error(f"Error publishing to exchange {exchange_name}: {e}")

    def __enter__(self) -> "EventPublisher[C]":
        """
        Open the connection for the event publisher.

        Returns:
            This event publisher instance with an open connection.
        """
        self._connection.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Close the connection for the event publisher.

        Args:
            exc_type: The exception type, or ``None``.
            exc_val: The exception instance, or ``None``.
            exc_tb: The traceback, or ``None``.
        """
        self._connection.__exit__(exc_type, exc_val, exc_tb)
