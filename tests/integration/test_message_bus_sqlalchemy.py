"""Integration tests for ``BaseMessageBus`` wired to real collaborators.

The bus is driven through real ``CommandRegistry`` / ``EventRegistry``, real
``SQLAlchemyUnitOfWork`` over an in-memory SQLite engine, and a real
``EventPublisher`` over an in-memory ``FakeBrokerConnection``. The only
"fake" is the broker connection itself — every other collaborator is the
production implementation.
"""

import pytest
from katharos.ds import ImmutableList
from pydantic import BaseModel
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

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
from tests.fakes import FakeBrokerConnection, FakeModel, FakeModelORM

EXCHANGE = "test.exchange"
ROUTING_KEY = "alice.created"


# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------


class CreateAlice(BaseCommand):
    name: str
    age: int


class AliceCreated(BaseEvent):
    name: str
    age: int


class Notified(BaseEvent):
    name: str


# ---------------------------------------------------------------------------
# Handlers (real implementations using the real UoW + publisher)
# ---------------------------------------------------------------------------


class CreateAliceHandler(BaseCommandHandler[CreateAlice]):
    def handle(self, command: CreateAlice) -> ImmutableList[BaseEvent]:
        with self.handle_context.unit_of_work_factory(FakeModel) as uow:
            uow.repository.add(FakeModel(name=command.name, age=command.age))
            uow.commit()
        return ImmutableList([AliceCreated(name=command.name, age=command.age)])


class PublishAliceCreatedHandler(BaseEventHandler[AliceCreated]):
    def handle(self, event: AliceCreated) -> ImmutableList[BaseEvent]:
        self.handle_context.event_publisher.publish(
            EXCHANGE,
            ROUTING_KEY,
            {"name": event.name, "age": event.age},
        )
        return ImmutableList([])


class FollowUpHandler(BaseEventHandler[AliceCreated]):
    def handle(self, event: AliceCreated) -> ImmutableList[BaseEvent]:
        return ImmutableList([Notified(name=event.name)])


class RecordingNotifiedHandler(BaseEventHandler[Notified]):
    def __init__(self, handle_context: HandleContext) -> None:
        super().__init__(handle_context)
        self.received: list[Notified] = []

    def handle(self, event: Notified) -> ImmutableList[BaseEvent]:
        self.received.append(event)
        return ImmutableList([])


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
def broker_connection() -> FakeBrokerConnection:
    return FakeBrokerConnection()


@pytest.fixture
def handle_context(
    engine: Engine, broker_connection: FakeBrokerConnection
) -> HandleContext:
    def session_factory() -> Session:
        return Session(engine)

    def repo_factory(session: Session) -> SQLAlchemyRepository[FakeModel]:
        return SQLAlchemyRepository[FakeModel](session, FakeModelORM)

    def uow_factory(ModelType: type[BaseModel]) -> SQLAlchemyUnitOfWork:
        # In a richer system the factory would pick the right ORM/repo per
        # model type; here we only deal with FakeModel.
        assert ModelType is FakeModel
        return SQLAlchemyUnitOfWork[FakeModel](session_factory, repo_factory)

    return HandleContext(
        unit_of_work_factory=uow_factory,
        event_publisher=EventPublisher(broker_connection),
    )


@pytest.fixture
def notified_handler(handle_context: HandleContext) -> RecordingNotifiedHandler:
    return RecordingNotifiedHandler(handle_context)


@pytest.fixture
def bus(
    handle_context: HandleContext,
    notified_handler: RecordingNotifiedHandler,
) -> BaseMessageBus:
    command_registry = CommandRegistry(lambda: NoOpCommandHandler(handle_context))
    command_registry[CreateAlice] = CreateAliceHandler(handle_context)

    event_registry = EventRegistry(list)
    event_registry[AliceCreated] = [
        PublishAliceCreatedHandler(handle_context),
        FollowUpHandler(handle_context),
    ]
    event_registry[Notified] = [notified_handler]

    return BaseMessageBus(handle_context, command_registry, event_registry)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCommandPersistence:
    def test_command_persists_to_database(
        self, bus: BaseMessageBus, engine: Engine
    ) -> None:
        bus.handle(CreateAlice(name="alice", age=30))

        with Session(engine) as verifier:
            rows = verifier.query(FakeModelORM).all()
            assert len(rows) == 1
            assert rows[0].name == "alice"
            assert rows[0].age == 30

    def test_two_commands_persist_independently(
        self, bus: BaseMessageBus, engine: Engine
    ) -> None:
        bus.handle(CreateAlice(name="alice", age=30))
        bus.handle(CreateAlice(name="bob", age=42))

        with Session(engine) as verifier:
            names = sorted(r.name for r in verifier.query(FakeModelORM).all())
            assert names == ["alice", "bob"]


class TestEventCascade:
    def test_event_cascade_publishes_to_broker(
        self,
        bus: BaseMessageBus,
        broker_connection: FakeBrokerConnection,
    ) -> None:
        bus.handle(CreateAlice(name="alice", age=30))

        assert broker_connection.published == [
            (EXCHANGE, ROUTING_KEY, {"name": "alice", "age": 30})
        ]

    def test_full_cascade_reaches_followup_handler(
        self,
        bus: BaseMessageBus,
        notified_handler: RecordingNotifiedHandler,
    ) -> None:
        bus.handle(CreateAlice(name="alice", age=30))

        assert [e.name for e in notified_handler.received] == ["alice"]


class TestUnknownCommand:
    def test_unknown_command_does_not_persist_or_publish(
        self,
        bus: BaseMessageBus,
        engine: Engine,
        broker_connection: FakeBrokerConnection,
        notified_handler: RecordingNotifiedHandler,
    ) -> None:
        class UnregisteredCommand(BaseCommand):
            pass

        bus.handle(UnregisteredCommand())

        with Session(engine) as verifier:
            assert verifier.query(FakeModelORM).count() == 0
        assert broker_connection.published == []
        assert notified_handler.received == []
