import logging

from .connection import BaseBrokerConnection
from .connection.exceptions import PublishError

logger = logging.getLogger(__name__)


class EventPublisher[C: BaseBrokerConnection]:
    """
    A generic event publisher that sends messages to a broker exchange.

    This class provides a high-level interface for publishing events to a message broker.
    It wraps a broker connection and provides context manager support for proper resource management.

    Type Parameters:
        C: The type of broker connection, must be a subclass of BaseBrokerConnection.

    Example:
        with EventPublisher(connection) as publisher:
            publisher.publish("my_exchange", "routing.key", {"message": "hello"})
    """

    def __init__(self, connection: C) -> None:
        """
        Initialize the event publisher.

        Args:
            connection (C): The broker connection to use for publishing events.
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
            exchange_name (str): The name of the exchange to publish to.
            routing_key (str): The routing key for the message.
            data (dict): The data to publish.
        """
        try:
            self._connection.publish(exchange_name, routing_key, data)
        except PublishError as e:
            logger.error(f"Error publishing to exchange {exchange_name}: {e}")

    def __enter__(self) -> "EventPublisher[C]":
        """
        Open the connection for the event publisher.

        Returns:
            EventPublisher[C]: The event publisher instance with an open connection.
        """
        self._connection.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Close the connection for the event publisher.

        Args:
            exc_type: The type of exception raised (if any).
            exc_val: The value of the exception raised (if any).
            exc_tb: The traceback of the exception raised (if any).
        """
        self._connection.__exit__(exc_type, exc_val, exc_tb)
