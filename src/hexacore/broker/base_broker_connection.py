from abc import ABC, abstractmethod
from typing import Self


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
            queue_name (str): The name of the queue to create.
            durable (bool): Whether the queue should survive broker restarts.
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
            exchange_name (str): The name of the exchange to create.
            exchange_type (str): The type of exchange (direct, fanout, topic, headers).
            durable (bool): Whether the exchange should survive broker restarts.
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
            queue_name (str): The name of the queue to bind.
            exchange_name (str): The name of the exchange to bind to.
            routing_key (str): The routing key for the binding.
        """
        raise NotImplementedError()

    def __enter__(self) -> Self:
        """
        Open the connection.

        Returns:
            Self: The broker connection instance.
        """
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Close the connection.

        Args:
            exc_type: The exception type.
            exc_val: The exception value.
            exc_tb: The exception traceback.
        """
        self.close()
