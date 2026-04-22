from typing import Generator

from pika.connection import Parameters

from hexacore.utils.rabbitmq import RabbitMQConnection

from .base_event_listener import BaseEventListener
from .exceptions import FailedToListenError


class RabbitMQEventListener(BaseEventListener):
    """
    A RabbitMQ event listener that consumes messages from a queue.

    Important: You should use this class with a context manager.
    Example:
       >>> with RabbitMQEventListener(parameters) as listener:
       ...     for message in listener.listen(queue_name):
       ...         process_message(message)
    """

    def __init__(
        self,
        parameters: Parameters,
        durable: bool = True,
    ) -> None:
        """
        Initialize the RabbitMQ event listener.

        Args:
            parameters: The connection parameters for the RabbitMQ server.
            durable: Whether the queue should be durable.
        """
        self.parameters = parameters
        self.durable = durable
        self.connection: RabbitMQConnection = RabbitMQConnection(parameters)

    def listen(
        self,
        queue_name: str,
    ) -> Generator[dict, None, None]:
        """
        Listen to a queue and yield messages.

        Args:
            queue_name: The name of the queue to listen to.

        Yields:
            A generator of messages containing method_frame, header_frame, and body.

        Raises:
            FailedToListenError: If the connection is not open or consuming fails.
        """
        if self.connection.connection_pair is None:
            raise FailedToListenError("Connection is not open.")

        _, channel = self.connection.connection_pair

        try:
            for method_frame, header_frame, body in channel.consume(
                queue_name,
                auto_ack=True,
            ):
                yield {
                    "method_frame": method_frame,
                    "header_frame": header_frame,
                    "body": body,
                }
        except Exception as e:
            raise FailedToListenError(f"Failed to consume from queue: {e}") from e
        finally:
            self.close()

    def open(self) -> None:
        """Open the connection and channel."""
        self.connection.open()

    def close(self) -> None:
        """Close the connection and channel."""
        self.connection.close()
