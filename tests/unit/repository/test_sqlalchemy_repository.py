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
        assert promise.result.is_failure()
        assert isinstance(promise.result.error, PromiseNotReadyError)

    def test_promise_becomes_ready_after_flush(
        self,
        session: Session,
        repository: SQLAlchemyRepository[FakeModel],
        model: FakeModel,
    ) -> None:
        promise = repository.add(model)

        session.flush()

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

        assert promise.result.is_success()
        result = promise.value
        assert result.is_success()
        assert result.value == model

    def test_returns_none_wrapped_promise_when_id_missing(
        self,
        repository: SQLAlchemyRepository[FakeModel],
    ) -> None:
        promise = repository.get(404)

        assert promise.with_id is None
        assert promise.result.is_failure()
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
        assert isinstance(result.error, NotFoundError)


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

        assert promise.result.is_success()
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

        assert promise.result.is_success()
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


class TestGetErrorHandling:
    def test_returns_promise_with_error_when_to_model_raises(
        self,
        session: Session,
        repository: SQLAlchemyRepository[FakeModel],
        model: FakeModel,
    ) -> None:
        """Test that get handles exceptions from to_model() gracefully."""
        id_ = _persist(session, model)

        # Create an ORM that will raise an exception when to_model is called
        class BrokenModelORM(FakeModelORM):
            def to_model(self) -> FakeModel:
                raise ValueError("Database corruption")

        # Replace the repository's ORM class with the broken one
        broken_repository = SQLAlchemyRepository[FakeModel](session, BrokenModelORM)

        promise = broken_repository.get(id_)

        assert promise.with_id is None
        assert promise.result.is_failure()
        result = promise.value
        assert result.is_failure()
        assert isinstance(result.error, ValueError)
        assert str(result.error) == "Database corruption"

    def test_result_failure_when_to_model_raises(
        self,
        session: Session,
        repository: SQLAlchemyRepository[FakeModel],
        model: FakeModel,
    ) -> None:
        """Test that result property also reflects the error from to_model()."""
        id_ = _persist(session, model)

        class BrokenModelORM(FakeModelORM):
            def to_model(self) -> FakeModel:
                raise RuntimeError("Unexpected error")

        broken_repository = SQLAlchemyRepository[FakeModel](session, BrokenModelORM)
        promise = broken_repository.get(id_)

        result = promise.result
        assert result.is_failure()
        assert isinstance(result.error, RuntimeError)


class TestDeleteErrorHandling:
    def test_returns_promise_with_error_when_to_model_raises(
        self,
        session: Session,
        repository: SQLAlchemyRepository[FakeModel],
        model: FakeModel,
    ) -> None:
        """Test that delete handles exceptions from to_model() gracefully."""
        id_ = _persist(session, model)

        class BrokenModelORM(FakeModelORM):
            def to_model(self) -> FakeModel:
                raise ValueError("Cannot deserialize model")

        broken_repository = SQLAlchemyRepository[FakeModel](session, BrokenModelORM)
        promise = broken_repository.delete(id_)

        assert promise.with_id is None
        assert promise.result.is_failure()
        result = promise.value
        assert result.is_failure()
        assert isinstance(result.error, ValueError)
        assert str(result.error) == "Cannot deserialize model"

    def test_does_not_delete_when_to_model_raises(
        self,
        session: Session,
        repository: SQLAlchemyRepository[FakeModel],
        model: FakeModel,
    ) -> None:
        """Test that record is not deleted when to_model() raises an exception."""
        id_ = _persist(session, model)

        class BrokenModelORM(FakeModelORM):
            def to_model(self) -> FakeModel:
                raise ValueError("Cannot deserialize")

        broken_repository = SQLAlchemyRepository[FakeModel](session, BrokenModelORM)
        broken_repository.delete(id_)
        session.flush()

        # The record should still exist in the database
        assert session.get(FakeModelORM, id_) is not None


class TestMultipleRecords:
    def test_adds_multiple_records(
        self,
        session: Session,
        repository: SQLAlchemyRepository[FakeModel],
    ) -> None:
        """Test that multiple add operations work correctly."""
        model1 = FakeModel(name="alice", age=30)
        model2 = FakeModel(name="bob", age=25)

        promise1 = repository.add(model1)
        promise2 = repository.add(model2)
        session.flush()

        assert promise1.result.is_success()
        assert promise2.result.is_success()
        id1 = promise1.result.value.get_id()
        id2 = promise2.result.value.get_id()

        assert id1 != id2

        records = session.query(FakeModelORM).all()
        assert len(records) == 2

    def test_gets_different_records(
        self,
        session: Session,
        repository: SQLAlchemyRepository[FakeModel],
    ) -> None:
        """Test that get returns correct records for different IDs."""
        model1 = FakeModel(name="alice", age=30)
        model2 = FakeModel(name="bob", age=25)

        id1 = _persist(session, model1)
        id2 = _persist(session, model2)

        promise1 = repository.get(id1)
        promise2 = repository.get(id2)

        assert promise1.value.value == model1
        assert promise2.value.value == model2

    def test_updates_correct_record(
        self,
        session: Session,
        repository: SQLAlchemyRepository[FakeModel],
    ) -> None:
        """Test that update only affects the specified record."""
        model1 = FakeModel(name="alice", age=30)
        model2 = FakeModel(name="bob", age=25)

        id1 = _persist(session, model1)
        id2 = _persist(session, model2)

        updated = FakeModel(name="alice_updated", age=31)
        repository.update(updated, id1)
        session.flush()

        # Check first record was updated
        reloaded1 = session.get(FakeModelORM, id1)
        assert reloaded1 is not None
        assert reloaded1.name == "alice_updated"
        assert reloaded1.age == 31

        # Check second record was not affected
        reloaded2 = session.get(FakeModelORM, id2)
        assert reloaded2 is not None
        assert reloaded2.name == "bob"
        assert reloaded2.age == 25

    def test_deletes_correct_record(
        self,
        session: Session,
        repository: SQLAlchemyRepository[FakeModel],
    ) -> None:
        """Test that delete only removes the specified record."""
        model1 = FakeModel(name="alice", age=30)
        model2 = FakeModel(name="bob", age=25)

        id1 = _persist(session, model1)
        id2 = _persist(session, model2)

        repository.delete(id1)
        session.flush()

        assert session.get(FakeModelORM, id1) is None
        assert session.get(FakeModelORM, id2) is not None

    def test_sequence_of_operations(
        self,
        session: Session,
        repository: SQLAlchemyRepository[FakeModel],
    ) -> None:
        """Test a realistic sequence of CRUD operations."""
        # Add
        model = FakeModel(name="charlie", age=35)
        add_promise = repository.add(model)
        session.flush()
        id_result = add_promise.result
        assert id_result.is_success()
        id_ = id_result.value.get_id()
        assert id_ is not None

        # Get
        get_promise = repository.get(id_)
        assert get_promise.value.value == model

        # Update
        updated = FakeModel(name="charlie_updated", age=36)
        update_promise = repository.update(updated, id_)
        session.flush()
        assert update_promise.value.value == updated

        # Verify update
        get_promise2 = repository.get(id_)
        assert get_promise2.value.value.name == "charlie_updated"

        # Delete
        delete_promise = repository.delete(id_)
        session.flush()
        assert delete_promise.value.value == updated

        # Verify deletion
        get_promise3 = repository.get(id_)
        assert get_promise3.with_id is None
