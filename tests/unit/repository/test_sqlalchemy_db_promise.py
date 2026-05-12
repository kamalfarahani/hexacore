import pytest

from hexacore.repository.exceptions import NotFoundError, PromiseNotReadyError
from hexacore.repository.sqlalchemy.db_promise import SQLAlchemyDBPromise
from tests.fakes import FakeModel, FakeWithID


@pytest.fixture
def model() -> FakeModel:
    return FakeModel(name="alice", age=30)


@pytest.fixture
def persisted_with_id(model: FakeModel) -> FakeWithID:
    return FakeWithID(id=42, model=model)


@pytest.fixture
def unpersisted_with_id(model: FakeModel) -> FakeWithID:
    return FakeWithID(id=None, model=model)


class TestValue:
    def test_returns_success_with_model_when_with_id_is_set(
        self, persisted_with_id: FakeWithID, model: FakeModel
    ) -> None:
        promise = SQLAlchemyDBPromise[FakeModel](persisted_with_id)

        result = promise.value

        assert result.is_success()
        assert result.value is model

    def test_returns_success_when_unpersisted_but_with_id_present(
        self, unpersisted_with_id: FakeWithID, model: FakeModel
    ) -> None:
        # value cares about presence of with_id, not whether it has an id.
        promise = SQLAlchemyDBPromise[FakeModel](unpersisted_with_id)

        result = promise.value

        assert result.is_success()
        assert result.value is model

    def test_returns_failure_with_not_found_when_with_id_is_none(self) -> None:
        promise = SQLAlchemyDBPromise[FakeModel](None)

        result = promise.value

        assert result.is_failure()
        assert isinstance(result.error, NotFoundError)


class TestResult:
    def test_returns_success_with_with_id_when_ready(
        self, persisted_with_id: FakeWithID
    ) -> None:
        promise = SQLAlchemyDBPromise[FakeModel](persisted_with_id)

        result = promise.result

        assert result.is_success()
        assert result.value is persisted_with_id

    def test_returns_failure_when_with_id_is_none(self) -> None:
        promise = SQLAlchemyDBPromise[FakeModel](None)

        result = promise.result

        assert result.is_failure()
        assert isinstance(result.error, NotFoundError)

    def test_returns_failure_when_with_id_has_no_id(
        self, unpersisted_with_id: FakeWithID
    ) -> None:
        promise = SQLAlchemyDBPromise[FakeModel](unpersisted_with_id)

        result = promise.result

        assert result.is_failure()
        assert isinstance(result.error, PromiseNotReadyError)


class TestInit:
    def test_stores_with_id(self, persisted_with_id: FakeWithID) -> None:
        promise = SQLAlchemyDBPromise[FakeModel](persisted_with_id)
        assert promise.with_id is persisted_with_id

    def test_accepts_none(self) -> None:
        promise = SQLAlchemyDBPromise[FakeModel](None)
        assert promise.with_id is None
