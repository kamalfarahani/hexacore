from pika import BlockingConnection
from pika.adapters.blocking_connection import BlockingChannel
from pika.connection import Parameters

type MaybeRabbitMQConnectionPair = tuple[BlockingConnection, BlockingChannel] | None


class RabbitMQConnection:
    """
    This class is a wrapper around the RabbitMQ connection and channel.
    It provides a simple interface for declaring queues and exchanges,
    and for binding queues to exchanges.
    """

    def __init__(self, parameters: Parameters) -> None:
        """
        Initialize the RabbitMQ connection.

        Args:
            parameters (Parameters): The connection parameters for the RabbitMQ server.
        """
        self.parameters = parameters
        self.connection_pair: MaybeRabbitMQConnectionPair = None

    def open(self) -> None:
        """
        Open the connection.

        Side Effects:
            Opens the connection and channel.
        """
        connection = BlockingConnection(self.parameters)
        channel = connection.channel()
        self.connection_pair = (connection, channel)

    def close(self) -> None:
        """
        Close the connection.

        Side Effects:
            Closes the connection and channel.
        """
        match self.connection_pair:
            case (connection, channel):
                channel.close()
                connection.close()
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
        """
        if self.connection_pair is None:
            raise RuntimeError("Connection is not open. Call open() first.")

        _, channel = self.connection_pair
        channel.queue_declare(queue=queue_name, durable=durable)

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
        """
        if self.connection_pair is None:
            raise RuntimeError("Connection is not open. Call open() first.")

        _, channel = self.connection_pair
        channel.exchange_declare(
            exchange=exchange_name, exchange_type=exchange_type, durable=durable
        )

    def bind_queue(
        self,
        queue_name: str,
        exchange_name: str,
        routing_key: str = "",
    ) -> None:
        """
        Bind a queue to an exchange with a routing key.

        Args:
            queue_name (str): The name of the queue to bind.
            exchange_name (str): The name of the exchange to bind to.
            routing_key (str): The routing key for the binding.

        Side Effects:
            Binds the queue to the exchange on the RabbitMQ server.
        """
        if self.connection_pair is None:
            raise RuntimeError("Connection is not open. Call open() first.")

        _, channel = self.connection_pair
        channel.queue_bind(
            queue=queue_name,
            exchange=exchange_name,
            routing_key=routing_key,
        )
