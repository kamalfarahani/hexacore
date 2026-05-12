"""Abstract broker connection interface."""

from abc import ABC, abstractmethod
from typing import Generator, Self


class BaseBrokerConnection(ABC):
    """
    Base class for broker connections.

    This class is an abstract context manager that handles broker connections.
    """

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

    @abstractmethod
    def create_queue(
        self,
        queue_name: str,
        durable: bool = True,
    ) -> None:
        """
        Declare a queue on the broker.

        Args:
            queue_name: The name of the queue to declare.
            durable: Whether the queue should survive broker restarts.
        """
        raise NotImplementedError()

    @abstractmethod
    def create_exchange(
        self,
        exchange_name: str,
        exchange_type: str = "direct",
        durable: bool = True,
    ) -> None:
        """
        Declare an exchange on the broker.

        Args:
            exchange_name: The name of the exchange to declare.
            exchange_type: The exchange type (``direct``, ``fanout``, ``topic``,
                or ``headers``).
            durable: Whether the exchange should survive broker restarts.
        """
        raise NotImplementedError()

    @abstractmethod
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
            routing_key: The routing key for the binding.
        """
        raise NotImplementedError()

    @abstractmethod
    def publish(
        self,
        exchange_name: str,
        routing_key: str,
        data: dict,
    ) -> None:
        """
        Publish data to an exchange with a routing key.

        Args:
            exchange_name: The name of the exchange to publish to.
            routing_key: The routing key for the message.
            data: The data to publish as a JSON-serialisable dict.
        """
        raise NotImplementedError()

    @abstractmethod
    def consume(
        self,
        queue_name: str,
    ) -> Generator[dict, None, None]:
        """
        Consume messages from a queue.

        Args:
            queue_name: The name of the queue to consume from.

        Yields:
            Each consumed message as a dict.
        """
        raise NotImplementedError()

    def __enter__(self) -> Self:
        """
        Open the connection.

        Returns:
            This broker connection instance.
        """
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Close the connection.

        Args:
            exc_type: The exception type, or ``None``.
            exc_val: The exception instance, or ``None``.
            exc_tb: The traceback, or ``None``.
        """
        self.close()
