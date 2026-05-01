import json
from typing import Generator

from pika import BlockingConnection
from pika.adapters.blocking_connection import BlockingChannel
from pika.connection import Parameters

from .base_broker_connection import BaseBrokerConnection

type MaybeRabbitMQConnectionPair = tuple[BlockingConnection, BlockingChannel] | None


class RabbitMQConnection(BaseBrokerConnection):
    """
    This class is a wrapper around the RabbitMQ connection and channel.
    It provides a simple interface for declaring queues and exchanges,
    and for binding queues to exchanges.
    """

    _parameters: Parameters
    _connection_pair: MaybeRabbitMQConnectionPair

    def __init__(self, parameters: Parameters) -> None:
        """
        Initialize the RabbitMQ connection.

        Args:
            parameters (Parameters): The connection parameters for the RabbitMQ server.
        """
        self._parameters = parameters
        self._connection_pair = None

    def _get_channel(self) -> BlockingChannel:
        """
        Get the channel from the connection pair.

        Returns:
            BlockingChannel: The channel from the connection pair.

        Raises:
            RuntimeError: If the connection is not open.
        """
        if self._connection_pair is None:
            raise RuntimeError("Connection is not open. Call open() first.")
        _, channel = self._connection_pair
        return channel

    def open(self) -> None:
        """
        Open the connection.

        Side Effects:
            Opens the connection and channel.

        Raises:
            RuntimeError: If the connection is already open.
        """
        if self._connection_pair is not None:
            raise RuntimeError("Connection is already open. Call close() first.")
        connection = BlockingConnection(self._parameters)
        channel = connection.channel()
        self._connection_pair = (connection, channel)

    def close(self) -> None:
        """
        Close the connection.

        Side Effects:
            Closes the connection and channel.
        """
        match self._connection_pair:
            case (connection, channel):
                channel.close()
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
            queue_name (str): The name of the queue to create.
            durable (bool): Whether the queue should survive broker restarts.

        Side Effects:
            Declares the queue on the RabbitMQ server.

        Raises:
            RuntimeError: If the connection is not open.
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
            exchange_name (str): The name of the exchange to create.
            exchange_type (str): The type of exchange (direct, fanout, topic, headers).
            durable (bool): Whether the exchange should survive broker restarts.

        Side Effects:
            Declares the exchange on the RabbitMQ server.

        Raises:
            RuntimeError: If the connection is not open.
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
            queue_name (str): The name of the queue to bind.
            exchange_name (str): The name of the exchange to bind to.
            routing_key (str): The routing key for the binding.
                Pass "" explicitly for fanout exchanges
                where routing keys are ignored.

        Side Effects:
            Binds the queue to the exchange on the RabbitMQ server.

        Raises:
            RuntimeError: If the connection is not open.
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
            exchange_name (str): The name of the exchange to publish to.
            routing_key (str): The routing key for the message.
            data (dict): The data to publish.

        Side Effects:
            Publishes the data to the specified queue.

        Raises:
            RuntimeError: If the connection is not open.
        """
        self._get_channel().basic_publish(
            exchange=exchange_name,
            routing_key=routing_key,
            body=json.dumps(data),
        )

    def consume(
        self,
        queue_name: str,
    ) -> Generator[dict, None, None]:
        """
        Consume messages from a queue.

        Args:
            queue_name (str): The name of the queue to consume from.

        Yields:
            dict: The consumed message containing method_frame, header_frame, and body.

        Raises:
            RuntimeError: If the connection is not open.
        """
        channel = self._get_channel()
        try:
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
        finally:
            channel.cancel()
