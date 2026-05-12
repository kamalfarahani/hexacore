import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from hexacore.repository.exceptions import NotFoundError, PromiseNotReadyError
from hexacore.repository.sqlalchemy.db_promise import SQLAlchemyDBPromise
from hexacore.repository.sqlalchemy.repository import SQLAlchemyRepository
from hexacore.repository.sqlalchemy.with_id import SQLAlchemyWithID
from tests.fakes import FakeModel, FakeModelORM


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    FakeModelORM.metadata.create_all(engine)
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def repository(session: Session) -> SQLAlchemyRepository[FakeModel]:
    return SQLAlchemyRepository[FakeModel](session, FakeModelORM)


@pytest.fixture
def model() -> FakeModel:
    return FakeModel(name="alice", age=30)


def _persist(session: Session, model: FakeModel) -> int:
    orm = FakeModelORM.from_model(model, session)
    session.add(orm)
    session.flush()
    assert orm.id is not None
    return orm.id


class TestInit:
    def test_stores_session_and_orm_class(
        self, session: Session, repository: SQLAlchemyRepository[FakeModel]
    ) -> None:
        assert repository._session is session
        assert repository._ModelORMClass is FakeModelORM


class TestAdd:
    def test_returns_promise_wrapping_with_id(
        self,
        repository: SQLAlchemyRepository[FakeModel],
        model: FakeModel,
    ) -> None:
        promise = repository.add(model)

        assert isinstance(promise, SQLAlchemyDBPromise)
        assert isinstance(promise.with_id, SQLAlchemyWithID)

    def test_promise_value_matches_added_model(
        self,
        repository: SQLAlchemyRepository[FakeModel],
        model: FakeModel,
    ) -> None:
        promise = repository.add(model)

        result = promise.value

        assert result.is_success()
        assert result.value == model

    def test_promise_not_ready_before_flush(
        self,
        repository: SQLAlchemyRepository[FakeModel],
        model: FakeModel,
    ) -> None:
        promise = repository.add(model)

        # The session has not been flushed, so the autoincrement ID is unset.
        assert promise.ready is False

    def test_promise_becomes_ready_after_flush(
        self,
        session: Session,
        repository: SQLAlchemyRepository[FakeModel],
        model: FakeModel,
    ) -> None:
        promise = repository.add(model)

        session.flush()

        assert promise.ready is True
        result = promise.result
        assert result.is_success()
        assert result.value.get_id() is not None

    def test_persists_orm_in_session(
        self,
        session: Session,
        repository: SQLAlchemyRepository[FakeModel],
        model: FakeModel,
    ) -> None:
        repository.add(model)
        session.flush()

        persisted = session.query(FakeModelORM).all()

        assert len(persisted) == 1
        assert persisted[0].name == model.name
        assert persisted[0].age == model.age


class TestGet:
    def test_returns_promise_with_model_when_id_exists(
        self,
        session: Session,
        repository: SQLAlchemyRepository[FakeModel],
        model: FakeModel,
    ) -> None:
        id_ = _persist(session, model)

        promise = repository.get(id_)

        assert promise.ready is True
        result = promise.value
        assert result.is_success()
        assert result.value == model

    def test_returns_none_wrapped_promise_when_id_missing(
        self,
        repository: SQLAlchemyRepository[FakeModel],
    ) -> None:
        promise = repository.get(404)

        assert promise.with_id is None
        assert promise.ready is False
        result = promise.value
        assert result.is_failure()
        assert isinstance(result.error, NotFoundError)

    def test_result_failure_when_missing(
        self,
        repository: SQLAlchemyRepository[FakeModel],
    ) -> None:
        promise = repository.get(404)

        result = promise.result
        assert result.is_failure()
        assert isinstance(result.error, PromiseNotReadyError)


class TestUpdate:
    def test_updates_existing_record(
        self,
        session: Session,
        repository: SQLAlchemyRepository[FakeModel],
        model: FakeModel,
    ) -> None:
        id_ = _persist(session, model)
        updated = FakeModel(name="bob", age=42)

        promise = repository.update(updated, id_)
        session.flush()

        assert promise.ready is True
        assert promise.value.is_success()
        assert promise.value.value == updated

        reloaded = session.get(FakeModelORM, id_)
        assert reloaded is not None
        assert reloaded.name == "bob"
        assert reloaded.age == 42

    def test_preserves_id_on_update(
        self,
        session: Session,
        repository: SQLAlchemyRepository[FakeModel],
        model: FakeModel,
    ) -> None:
        id_ = _persist(session, model)
        updated = FakeModel(name="bob", age=42)

        promise = repository.update(updated, id_)
        session.flush()

        assert promise.result.is_success()
        assert promise.result.value.get_id() == id_

    def test_returns_empty_promise_when_id_missing(
        self,
        repository: SQLAlchemyRepository[FakeModel],
        model: FakeModel,
    ) -> None:
        promise = repository.update(model, 404)

        assert promise.with_id is None
        assert promise.value.is_failure()
        assert isinstance(promise.value.error, NotFoundError)

    def test_does_not_create_new_record_when_id_missing(
        self,
        session: Session,
        repository: SQLAlchemyRepository[FakeModel],
        model: FakeModel,
    ) -> None:
        repository.update(model, 404)
        session.flush()

        assert session.query(FakeModelORM).count() == 0


class TestDelete:
    def test_deletes_existing_record(
        self,
        session: Session,
        repository: SQLAlchemyRepository[FakeModel],
        model: FakeModel,
    ) -> None:
        id_ = _persist(session, model)

        promise = repository.delete(id_)
        session.flush()

        assert promise.ready is True
        assert promise.value.is_success()
        assert promise.value.value == model
        assert session.get(FakeModelORM, id_) is None

    def test_returns_empty_promise_when_id_missing(
        self,
        repository: SQLAlchemyRepository[FakeModel],
    ) -> None:
        promise = repository.delete(404)

        assert promise.with_id is None
        assert promise.value.is_failure()
        assert isinstance(promise.value.error, NotFoundError)

    def test_does_not_affect_other_records_when_id_missing(
        self,
        session: Session,
        repository: SQLAlchemyRepository[FakeModel],
        model: FakeModel,
    ) -> None:
        id_ = _persist(session, model)

        repository.delete(404)
        session.flush()

        assert session.get(FakeModelORM, id_) is not None
