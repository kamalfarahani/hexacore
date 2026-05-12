"""End-to-end test for ``BaseMessageBus``.

Drives the bus from a real RabbitMQ queue through ``EventListener`` and
verifies that the full pipeline persists data to a real (in-memory) SQLite
database and publishes downstream events back through the broker.

Requires Docker/Podman so that the ``rabbitmq_container`` session fixture
(promoted to ``tests/conftest.py``) can start a real RabbitMQ instance.
"""

import json
import time

import pytest
from katharos.ds import ImmutableList
from pika import ConnectionParameters
from pydantic import BaseModel
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from hexacore.broker.connection.rabbitmq import RabbitMQConnection
from hexacore.broker.event_listener import EventListener
from hexacore.broker.event_publisher import EventPublisher
from hexacore.command import BaseCommand
from hexacore.event import BaseEvent
from hexacore.message_bus.base_message_bus import BaseMessageBus
from hexacore.message_bus.handler import (
    BaseCommandHandler,
    BaseEventHandler,
    HandleContext,
    NoOpCommandHandler,
)
from hexacore.message_bus.registry import CommandRegistry, EventRegistry
from hexacore.repository.sqlalchemy.repository import SQLAlchemyRepository
from hexacore.unit_of_work.sqlalchemy_unit_of_work import SQLAlchemyUnitOfWork
from tests.fakes import FakeModel, FakeModelORM


# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------


class CreateAlice(BaseCommand):
    name: str
    age: int


class AliceCreated(BaseEvent):
    name: str
    age: int


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


class CreateAliceHandler(BaseCommandHandler[CreateAlice]):
    def handle(self, command: CreateAlice) -> ImmutableList[BaseEvent]:
        with self.handle_context.unit_of_work_factory(FakeModel) as uow:
            uow.repository.add(FakeModel(name=command.name, age=command.age))
            uow.commit()
        return ImmutableList(
            [AliceCreated(name=command.name, age=command.age)]
        )


class PublishAliceCreatedHandler(BaseEventHandler[AliceCreated]):
    def __init__(self, handle_context: HandleContext, exchange: str, routing_key: str):
        super().__init__(handle_context)
        self._exchange = exchange
        self._routing_key = routing_key

    def handle(self, event: AliceCreated) -> ImmutableList[BaseEvent]:
        self.handle_context.event_publisher.publish(
            self._exchange,
            self._routing_key,
            {"name": event.name, "age": event.age},
        )
        return ImmutableList([])


# ---------------------------------------------------------------------------
# Topology helpers
# ---------------------------------------------------------------------------


def _setup_topology(
    setup_conn: RabbitMQConnection, unique_name: str
) -> tuple[str, str, str, str, str, str]:
    """Declare input/output exchanges + queues and return their names."""
    in_exchange = f"{unique_name}-in-x"
    in_queue = f"{unique_name}-in-q"
    in_rk = "create_alice"
    out_exchange = f"{unique_name}-out-x"
    out_queue = f"{unique_name}-out-q"
    out_rk = "alice_created"

    setup_conn.create_exchange(in_exchange, "direct", durable=False)
    setup_conn.create_queue(in_queue, durable=False)
    setup_conn.bind_queue(in_queue, in_exchange, in_rk)

    setup_conn.create_exchange(out_exchange, "direct", durable=False)
    setup_conn.create_queue(out_queue, durable=False)
    setup_conn.bind_queue(out_queue, out_exchange, out_rk)

    return in_queue, in_exchange, in_rk, out_queue, out_exchange, out_rk


def _cleanup(conn: RabbitMQConnection, *, queues: list[str], exchanges: list[str]) -> None:
    for q in queues:
        try:
            conn._get_channel().queue_delete(queue=q)
        except Exception:
            pass
    for x in exchanges:
        try:
            conn._get_channel().exchange_delete(exchange=x)
        except Exception:
            pass


def _drain_queue(conn: RabbitMQConnection, queue: str, expected: int) -> list[dict]:
    """Pull ``expected`` messages from ``queue`` using basic_get."""
    received: list[dict] = []
    deadline = time.monotonic() + 5.0
    while len(received) < expected and time.monotonic() < deadline:
        method, _header, body = conn._get_channel().basic_get(
            queue=queue, auto_ack=True
        )
        if method is None:
            time.sleep(0.05)
            continue
        received.append(json.loads(body))
    return received


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def engine():
    engine = create_engine("sqlite:///:memory:")
    FakeModelORM.metadata.create_all(engine)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def setup_conn(connection_parameters: ConnectionParameters):
    conn = RabbitMQConnection(connection_parameters)
    conn.open()
    try:
        yield conn
    finally:
        conn.close()


def _build_bus(
    engine: Engine,
    publisher_connection: RabbitMQConnection,
    out_exchange: str,
    out_rk: str,
) -> BaseMessageBus:
    def session_factory() -> Session:
        return Session(engine)

    def repo_factory(session: Session) -> SQLAlchemyRepository[FakeModel]:
        return SQLAlchemyRepository[FakeModel](session, FakeModelORM)

    def uow_factory(ModelType: type[BaseModel]) -> SQLAlchemyUnitOfWork:
        assert ModelType is FakeModel
        return SQLAlchemyUnitOfWork[FakeModel](session_factory, repo_factory)

    handle_context = HandleContext(
        unit_of_work_factory=uow_factory,
        event_publisher=EventPublisher(publisher_connection),
    )

    command_registry = CommandRegistry(lambda: NoOpCommandHandler(handle_context))
    command_registry[CreateAlice] = CreateAliceHandler(handle_context)

    event_registry = EventRegistry(list)
    event_registry[AliceCreated] = [
        PublishAliceCreatedHandler(handle_context, out_exchange, out_rk),
    ]

    return BaseMessageBus(handle_context, command_registry, event_registry)


def _run_pipeline(
    listener_connection: RabbitMQConnection,
    bus: BaseMessageBus,
    in_queue: str,
    expected: int,
) -> None:
    """Consume ``expected`` messages and drive each through ``bus.handle``."""
    listener = EventListener(listener_connection)
    consumed = 0
    for message in listener.listen(in_queue):
        payload = json.loads(message["body"])
        bus.handle(CreateAlice(**payload))
        consumed += 1
        if consumed >= expected:
            break


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestEndToEnd:
    def test_external_message_drives_full_pipeline(
        self,
        engine: Engine,
        setup_conn: RabbitMQConnection,
        connection_parameters: ConnectionParameters,
        unique_name: str,
    ) -> None:
        in_queue, in_exchange, in_rk, out_queue, out_exchange, out_rk = _setup_topology(
            setup_conn, unique_name
        )

        listener_conn = RabbitMQConnection(connection_parameters)
        publisher_conn = RabbitMQConnection(connection_parameters)
        listener_conn.open()
        publisher_conn.open()

        try:
            # Pre-publish one input message via the setup connection.
            setup_conn.publish(in_exchange, in_rk, {"name": "alice", "age": 30})

            bus = _build_bus(engine, publisher_conn, out_exchange, out_rk)
            _run_pipeline(listener_conn, bus, in_queue, expected=1)

            # DB persistence
            with Session(engine) as verifier:
                rows = verifier.query(FakeModelORM).all()
                assert len(rows) == 1
                assert rows[0].name == "alice"
                assert rows[0].age == 30

            # Outgoing broker message
            received = _drain_queue(setup_conn, out_queue, expected=1)
            assert received == [{"name": "alice", "age": 30}]
        finally:
            listener_conn.close()
            publisher_conn.close()
            _cleanup(
                setup_conn,
                queues=[in_queue, out_queue],
                exchanges=[in_exchange, out_exchange],
            )

    def test_pipeline_isolated_per_message(
        self,
        engine: Engine,
        setup_conn: RabbitMQConnection,
        connection_parameters: ConnectionParameters,
        unique_name: str,
    ) -> None:
        in_queue, in_exchange, in_rk, out_queue, out_exchange, out_rk = _setup_topology(
            setup_conn, unique_name
        )

        listener_conn = RabbitMQConnection(connection_parameters)
        publisher_conn = RabbitMQConnection(connection_parameters)
        listener_conn.open()
        publisher_conn.open()

        try:
            setup_conn.publish(in_exchange, in_rk, {"name": "alice", "age": 30})
            setup_conn.publish(in_exchange, in_rk, {"name": "bob", "age": 42})

            bus = _build_bus(engine, publisher_conn, out_exchange, out_rk)
            _run_pipeline(listener_conn, bus, in_queue, expected=2)

            with Session(engine) as verifier:
                names = sorted(r.name for r in verifier.query(FakeModelORM).all())
                assert names == ["alice", "bob"]

            received = _drain_queue(setup_conn, out_queue, expected=2)
            assert received == [
                {"name": "alice", "age": 30},
                {"name": "bob", "age": 42},
            ]
        finally:
            listener_conn.close()
            publisher_conn.close()
            _cleanup(
                setup_conn,
                queues=[in_queue, out_queue],
                exchanges=[in_exchange, out_exchange],
            )
