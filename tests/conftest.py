import uuid
from collections.abc import Iterator

import pytest
from pika import ConnectionParameters, PlainCredentials
from testcontainers.rabbitmq import RabbitMqContainer


@pytest.fixture(scope="session")
def rabbitmq_container() -> Iterator[RabbitMqContainer]:
    """Start a RabbitMQ container for the whole test session."""
    with RabbitMqContainer("rabbitmq:3.13-management") as container:
        yield container


@pytest.fixture(scope="session")
def connection_parameters(
    rabbitmq_container: RabbitMqContainer,
) -> ConnectionParameters:
    """Build pika ConnectionParameters pointing at the running container."""
    host = rabbitmq_container.get_container_host_ip()
    port = int(rabbitmq_container.get_exposed_port(5672))
    return ConnectionParameters(
        host=host,
        port=port,
        credentials=PlainCredentials("guest", "guest"),
        heartbeat=30,
        blocked_connection_timeout=10,
    )


@pytest.fixture
def unique_name() -> str:
    """Return a unique short identifier for queues/exchanges."""
    return f"test-{uuid.uuid4().hex[:12]}"
