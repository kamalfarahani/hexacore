import json

from pika.connection import Parameters

from hexacore.utils.rabbitmq import RabbitMQConnection

from .base_event_publisher import BaseEventPublisher
from .exceptions import FailedToPublishEventError


class RabbitMQEventPublisher(BaseEventPublisher):
    """
    A RabbitMQ event publisher that sends messages to a queue.

    Important: You should use this class with a context manager.
    Example:
        with RabbitMQEventPublisher(parameters, exchange_name) as publisher:
            publisher.publish(queue_name, event)
    """

    def __init__(
        self,
        parameters: Parameters,
        exchange_name: str,
        durable: bool = True,
    ) -> None:
        """
        Initialize the RabbitMQ event publisher.

        Args:
            parameters (Parameters): The connection parameters for the RabbitMQ server.
            exchange_name (str): The name of the exchange to publish to.
            durable (bool): Whether the queue should be durable.
        """
        self.parameters = parameters
        self.exchange_name = exchange_name
        self.durable = durable
        self.connection: RabbitMQConnection = RabbitMQConnection(parameters)

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

        Side Effects:
            Publishes the event to the specified queue.

        Raises:
            FailedToPublishEventError: If the event fails to publish.
        """
        if self.connection.connection_pair is None:
            raise FailedToPublishEventError("Connection or channel is not open")

        _, channel = self.connection.connection_pair

        try:
            channel.basic_publish(
                exchange=self.exchange_name,
                routing_key=queue_name,
                body=json.dumps(event),
            )
        except Exception as e:
            raise FailedToPublishEventError(
                f"Failed to publish event to queue {queue_name}: {str(e)}"
            ) from e

    def open(self) -> None:
        """
        Open the connection.

        Side Effects:
            Opens the connection and channel.
        """
        self.connection.open()

    def close(self) -> None:
        """
        Close the connection.

        Side Effects:
            Closes the connection and channel.
        """
        self.connection.close()
