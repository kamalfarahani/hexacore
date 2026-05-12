import pytest
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from hexacore.repository.sqlalchemy.repository import SQLAlchemyRepository
from hexacore.unit_of_work.sqlalchemy_unit_of_work import SQLAlchemyUnitOfWork

from .fakes import FakeModel, FakeModelORM


class CountingSessionFactory:
    """Real session factory that records how many sessions it produced.

    Backed by an in-memory SQLite engine so the produced sessions behave
    exactly like sessions used in production. We keep references to every
    session created so tests can assert on their state (closed, etc.).
    """

    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self.calls = 0
        self.created: list[Session] = []

    def __call__(self) -> Session:
        self.calls += 1
        session = Session(self._engine)
        self.created.append(session)
        return session


class CountingRepoFactory:
    """Real repo factory that records the sessions it received."""

    def __init__(self) -> None:
        self.calls = 0
        self.received_sessions: list[Session] = []

    def __call__(self, session: Session) -> SQLAlchemyRepository[FakeModel]:
        self.calls += 1
        self.received_sessions.append(session)
        return SQLAlchemyRepository[FakeModel](session, FakeModelORM)


@pytest.fixture
def engine():
    engine = create_engine("sqlite:///:memory:")
    FakeModelORM.metadata.create_all(engine)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def session_factory(engine: Engine) -> CountingSessionFactory:
    return CountingSessionFactory(engine)


@pytest.fixture
def repo_factory() -> CountingRepoFactory:
    return CountingRepoFactory()


@pytest.fixture
def uow(
    session_factory: CountingSessionFactory,
    repo_factory: CountingRepoFactory,
) -> SQLAlchemyUnitOfWork[FakeModel]:
    return SQLAlchemyUnitOfWork[FakeModel](session_factory, repo_factory)


class TestInit:
    def test_session_starts_as_none(self, uow: SQLAlchemyUnitOfWork[FakeModel]) -> None:
        assert uow._session is None

    def test_does_not_call_factories(
        self,
        uow: SQLAlchemyUnitOfWork[FakeModel],
        session_factory: CountingSessionFactory,
        repo_factory: CountingRepoFactory,
    ) -> None:
        assert session_factory.calls == 0
        assert repo_factory.calls == 0


class TestSessionProperty:
    def test_creates_session_on_first_access(
        self,
        uow: SQLAlchemyUnitOfWork[FakeModel],
        session_factory: CountingSessionFactory,
    ) -> None:
        session = uow.session

        assert session is session_factory.created[0]
        assert session_factory.calls == 1

    def test_caches_session_across_accesses(
        self,
        uow: SQLAlchemyUnitOfWork[FakeModel],
        session_factory: CountingSessionFactory,
    ) -> None:
        first = uow.session
        second = uow.session

        assert first is second
        assert session_factory.calls == 1


class TestRepositoryProperty:
    def test_creates_repository_using_session(
        self,
        uow: SQLAlchemyUnitOfWork[FakeModel],
        session_factory: CountingSessionFactory,
        repo_factory: CountingRepoFactory,
    ) -> None:
        repository = uow.repository

        assert isinstance(repository, SQLAlchemyRepository)
        assert repo_factory.calls == 1
        assert repo_factory.received_sessions[0] is uow.session

    def test_uses_existing_session_for_repository(
        self,
        uow: SQLAlchemyUnitOfWork[FakeModel],
        session_factory: CountingSessionFactory,
        repo_factory: CountingRepoFactory,
    ) -> None:
        # Force session creation first.
        session = uow.session
        uow.repository

        assert session_factory.calls == 1
        assert repo_factory.received_sessions[0] is session

    def test_each_access_invokes_repo_factory(
        self,
        uow: SQLAlchemyUnitOfWork[FakeModel],
        repo_factory: CountingRepoFactory,
    ) -> None:
        uow.repository
        uow.repository

        assert repo_factory.calls == 2


class TestStart:
    def test_initializes_session(
        self,
        uow: SQLAlchemyUnitOfWork[FakeModel],
        session_factory: CountingSessionFactory,
    ) -> None:
        uow.start()

        assert uow._session is session_factory.created[0]
        assert session_factory.calls == 1

    def test_replaces_previously_created_session(
        self,
        uow: SQLAlchemyUnitOfWork[FakeModel],
        session_factory: CountingSessionFactory,
    ) -> None:
        first = uow.session

        uow.start()

        assert session_factory.calls == 2
        assert uow._session is session_factory.created[1]
        assert uow._session is not first


class TestDone:
    def test_closes_session_when_present(
        self,
        uow: SQLAlchemyUnitOfWork[FakeModel],
    ) -> None:
        session = uow.session

        uow.done()

        # SQLAlchemy exposes whether a session is bound/active via ``is_active``
        # on the underlying transaction; closed sessions have no transaction.
        assert session.in_transaction() is False

    def test_safe_when_no_session(self, uow: SQLAlchemyUnitOfWork[FakeModel]) -> None:
        # Should not raise and should not create a session.
        uow.done()

        assert uow._session is None

    def test_rolls_back_uncommitted_changes(
        self,
        uow: SQLAlchemyUnitOfWork[FakeModel],
        engine: Engine,
    ) -> None:
        uow.start()
        uow.repository.add(FakeModel(name="alice", age=30))
        uow.session.flush()

        uow.done()

        with Session(engine) as verifier:
            assert verifier.query(FakeModelORM).count() == 0


class TestCommit:
    def test_persists_changes_across_sessions(
        self,
        uow: SQLAlchemyUnitOfWork[FakeModel],
        engine: Engine,
    ) -> None:
        uow.start()
        uow.repository.add(FakeModel(name="alice", age=30))

        uow.commit()

        with Session(engine) as verifier:
            rows = verifier.query(FakeModelORM).all()
            assert len(rows) == 1
            assert rows[0].name == "alice"
            assert rows[0].age == 30

    def test_safe_when_no_session(self, uow: SQLAlchemyUnitOfWork[FakeModel]) -> None:
        # Should be a no-op rather than raising.
        uow.commit()

        assert uow._session is None


class TestRollback:
    def test_discards_pending_changes(
        self,
        uow: SQLAlchemyUnitOfWork[FakeModel],
        engine: Engine,
    ) -> None:
        uow.start()
        uow.repository.add(FakeModel(name="alice", age=30))
        uow.session.flush()

        uow.rollback()
        uow.commit()

        with Session(engine) as verifier:
            assert verifier.query(FakeModelORM).count() == 0

    def test_safe_when_no_session(self, uow: SQLAlchemyUnitOfWork[FakeModel]) -> None:
        uow.rollback()

        assert uow._session is None


class TestContextManager:
    def test_enter_starts_unit_of_work(
        self,
        uow: SQLAlchemyUnitOfWork[FakeModel],
        session_factory: CountingSessionFactory,
    ) -> None:
        with uow as ctx:
            assert ctx is uow
            assert session_factory.calls == 1
            assert uow._session is session_factory.created[0]

    def test_exit_calls_done_and_closes_session(
        self,
        uow: SQLAlchemyUnitOfWork[FakeModel],
    ) -> None:
        with uow:
            session = uow.session

        assert session.in_transaction() is False

    def test_exit_rolls_back_on_exception(
        self,
        uow: SQLAlchemyUnitOfWork[FakeModel],
        engine: Engine,
    ) -> None:
        with pytest.raises(RuntimeError):
            with uow:
                uow.repository.add(FakeModel(name="alice", age=30))
                uow.session.flush()
                raise RuntimeError("boom")

        with Session(engine) as verifier:
            assert verifier.query(FakeModelORM).count() == 0

    def test_exit_does_not_auto_commit(
        self,
        uow: SQLAlchemyUnitOfWork[FakeModel],
        engine: Engine,
    ) -> None:
        with uow:
            uow.repository.add(FakeModel(name="alice", age=30))

        with Session(engine) as verifier:
            assert verifier.query(FakeModelORM).count() == 0
