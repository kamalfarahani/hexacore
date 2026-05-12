from collections.abc import Iterator

import pytest
from pika import ConnectionParameters

from hexacore.broker.connection.rabbitmq import RabbitMQConnection


@pytest.fixture
def connection(
    connection_parameters: ConnectionParameters,
) -> Iterator[RabbitMQConnection]:
    """Yield an opened RabbitMQConnection and close it on teardown."""
    conn = RabbitMQConnection(connection_parameters)
    conn.open()
    try:
        yield conn
    finally:
        conn.close()


@pytest.fixture
def closed_connection(
    connection_parameters: ConnectionParameters,
) -> RabbitMQConnection:
    """Return a RabbitMQConnection that has not been opened."""
    return RabbitMQConnection(connection_parameters)
