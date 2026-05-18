from typing import Generator

from pydantic import BaseModel
from sqlalchemy.orm import Mapped, Session, mapped_column

from hexacore.broker.connection.base import BaseBrokerConnection
from hexacore.repository.sqlalchemy.model_orm import ModelORM
from hexacore.repository.sqlalchemy.with_id import SQLAlchemyWithID


class FakeModel(BaseModel):
    name: str
    age: int


class FakeWithID(SQLAlchemyWithID[FakeModel]):
    """A fake SQLAlchemyWithID that does not require a real ORM model.

    It bypasses the parent ``__init__`` so tests don't need a SQLAlchemy
    session or declarative-mapped instance.
    """

    def __init__(self, *, id: int | None, model: FakeModel) -> None:
        self._id = id
        self._model = model

    def get_id(self) -> int:
        # The base interface promises ``int``; tests that need to simulate an
        # un-persisted entity use ``id=None`` and assert via the promise's
        # ``ready`` / ``result`` properties without calling get_id directly.
        return self._id  # type: ignore[return-value]

    def get_model(self) -> FakeModel:
        return self._model


class FakeModelORM(ModelORM[FakeModel]):
    """Concrete ORM mapping backed by a real in-memory SQLite database.

    Using a real (but in-memory) database is preferable to mocking the
    SQLAlchemy ``Session``: the tests exercise the actual ``add`` / ``get``
    / ``merge`` / ``delete`` behavior the repository depends on.
    """

    __tablename__ = "fake_model"

    name: Mapped[str] = mapped_column()
    age: Mapped[int] = mapped_column()

    @staticmethod
    def from_model(model: FakeModel, session: Session, **kwargs) -> "FakeModelORM":
        return FakeModelORM(name=model.name, age=model.age)

    def to_model(self, session: Session, **kwargs) -> FakeModel:
        return FakeModel(name=self.name, age=self.age)


class FakeBrokerConnection(BaseBrokerConnection):
    """An in-memory fake implementation of BaseBrokerConnection.

    It is configurable per-test by populating ``queues`` (mapping a queue
    name to an iterable of messages to yield) and ``consume_errors``
    (mapping a queue name to an exception to raise on consume).

    ``publish`` is also recorded into ``published`` and may be configured to
    raise via ``publish_errors`` keyed by ``(exchange_name, routing_key)``.
    """

    def __init__(self) -> None:
        self.queues: dict[str, list[dict]] = {}
        self.consume_errors: dict[str, Exception] = {}
        self.publish_errors: dict[tuple[str, str], Exception] = {}
        self.published: list[tuple[str, str, dict]] = []
        self.open_calls = 0
        self.close_calls = 0
        self.enter_calls = 0
        self.exit_calls = 0
        self.last_exit_info: tuple | None = None
        self.consumed_queues: list[str] = []
        self.is_open = False

    def open(self) -> None:
        self.open_calls += 1
        self.is_open = True

    def close(self) -> None:
        self.close_calls += 1
        self.is_open = False

    def create_queue(self, queue_name: str, durable: bool = True) -> None:
        self.queues.setdefault(queue_name, [])

    def create_exchange(
        self,
        exchange_name: str,
        exchange_type: str = "direct",
        durable: bool = True,
    ) -> None:
        return None

    def bind_queue(self, queue_name: str, exchange_name: str, routing_key: str) -> None:
        return None

    def publish(self, exchange_name: str, routing_key: str, data: dict) -> None:
        error = self.publish_errors.get((exchange_name, routing_key))
        if error is not None:
            raise error
        self.published.append((exchange_name, routing_key, data))

    def consume(self, queue_name: str) -> Generator[dict, None, None]:
        self.consumed_queues.append(queue_name)
        if queue_name in self.consume_errors:
            raise self.consume_errors[queue_name]
        for message in self.queues.get(queue_name, []):
            yield message

    def __enter__(self) -> "FakeBrokerConnection":
        self.enter_calls += 1
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.exit_calls += 1
        self.last_exit_info = (exc_type, exc_val, exc_tb)
        self.close()
