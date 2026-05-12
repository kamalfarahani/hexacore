"""RabbitMQ broker connection implementation."""

import json
from typing import Generator

from pika import BlockingConnection
from pika.adapters.blocking_connection import BlockingChannel
from pika.connection import Parameters

from .base import BaseBrokerConnection
from .exceptions import ConsumeError, OpenError, PublishError

type MaybeRabbitMQConnectionPair = tuple[BlockingConnection, BlockingChannel] | None


class RabbitMQConnection(BaseBrokerConnection):
    """
    RabbitMQ connection manager for message broker operations.

    Provides a high-level interface for managing RabbitMQ connections,
    including queue and exchange management, message publishing, and
    consumption.  Internally maintains a pika ``BlockingConnection`` /
    ``BlockingChannel`` pair.

    Example:
        >>> from pika import ConnectionParameters
        >>> conn = RabbitMQConnection(ConnectionParameters('localhost'))
        >>> with conn:
        ...     conn.create_queue('my_queue')
        ...     conn.publish('my_exchange', 'my_routing_key', {'key': 'value'})
    """

    _parameters: Parameters
    _connection_pair: MaybeRabbitMQConnectionPair

    def __init__(self, parameters: Parameters) -> None:
        """
        Initialize the RabbitMQ connection.

        Args:
            parameters: The pika connection parameters for the RabbitMQ server.
        """
        self._parameters = parameters
        self._connection_pair = None

    def _get_channel(self) -> BlockingChannel:
        """
        Get the channel from the connection pair.

        Returns:
            The active pika channel.

        Raises:
            OpenError: If the connection is not open.
        """
        if self._connection_pair is None:
            raise OpenError("Connection is not open. Call open() first.")
        _, channel = self._connection_pair
        return channel

    def open(self) -> None:
        """
        Open the connection.

        Note:
            Opens the underlying pika ``BlockingConnection`` and channel.

        Raises:
            OpenError: If the connection is already open.
        """
        if self._connection_pair is not None:
            raise OpenError("Connection is already open. Call close() first.")
        connection = BlockingConnection(self._parameters)
        channel = connection.channel()
        self._connection_pair = (connection, channel)

    def close(self) -> None:
        """
        Close the connection.

        Note:
            Closes the channel and underlying connection if they are open.
        """
        match self._connection_pair:
            case (connection, channel):
                if channel.is_open:
                    channel.close()
                if connection.is_open:
                    connection.close()
                self._connection_pair = None
            case _:
                pass

    def create_queue(
        self,
        queue_name: str,
        durable: bool = True,
    ) -> None:
        """
        Declare a queue on the RabbitMQ server.

        Args:
            queue_name: The name of the queue to declare.
            durable: Whether the queue should survive broker restarts.

        Raises:
            OpenError: If the connection is not open.
        """
        self._get_channel().queue_declare(
            queue=queue_name,
            durable=durable,
        )

    def create_exchange(
        self,
        exchange_name: str,
        exchange_type: str = "direct",
        durable: bool = True,
    ) -> None:
        """
        Declare an exchange on the RabbitMQ server.

        Args:
            exchange_name: The name of the exchange to declare.
            exchange_type: The exchange type (``direct``, ``fanout``, ``topic``,
                or ``headers``).
            durable: Whether the exchange should survive broker restarts.

        Raises:
            OpenError: If the connection is not open.
        """
        self._get_channel().exchange_declare(
            exchange=exchange_name,
            exchange_type=exchange_type,
            durable=durable,
        )

    def bind_queue(
        self,
        queue_name: str,
        exchange_name: str,
        routing_key: str,
    ) -> None:
        """
        Bind a queue to an exchange with a routing key.

        Args:
            queue_name: The name of the queue to bind.
            exchange_name: The name of the exchange to bind to.
            routing_key: The routing key for the binding.  Pass ``""``
                explicitly for fanout exchanges where routing keys are ignored.

        Raises:
            OpenError: If the connection is not open.
        """
        self._get_channel().queue_bind(
            queue=queue_name,
            exchange=exchange_name,
            routing_key=routing_key,
        )

    def publish(
        self,
        exchange_name: str,
        routing_key: str,
        data: dict,
    ) -> None:
        """
        Publish data to an exchange.

        Args:
            exchange_name: The name of the exchange to publish to.
            routing_key: The routing key for the message.
            data: The data to publish as a JSON-serialisable dict.

        Raises:
            PublishError: If publishing fails.
        """
        try:
            self._get_channel().basic_publish(
                exchange=exchange_name,
                routing_key=routing_key,
                body=json.dumps(data),
            )
        except Exception as e:
            raise PublishError(
                f"Failed to publish to exchange '{exchange_name}' with routing key '{routing_key}': {e}"
            ) from e

    def consume(
        self,
        queue_name: str,
    ) -> Generator[dict, None, None]:
        """
        Consume messages from a queue.

        Args:
            queue_name: The name of the queue to consume from.

        Yields:
            Each consumed message as a dict with ``method_frame``,
            ``header_frame``, and ``body`` keys.

        Raises:
            ConsumeError: If there is an error consuming from the queue.
        """
        channel = None
        try:
            channel = self._get_channel()
            for method_frame, header_frame, body in channel.consume(
                queue=queue_name,
                auto_ack=True,
            ):
                if method_frame is None:
                    break
                yield {
                    "method_frame": method_frame,
                    "header_frame": header_frame,
                    "body": body,
                }
        except Exception as e:
            raise ConsumeError(
                f"Failed to consume from queue '{queue_name}': {e}"
            ) from e
        finally:
            if channel is not None and channel.is_open:
                try:
                    channel.cancel()
                except Exception:
                    pass
