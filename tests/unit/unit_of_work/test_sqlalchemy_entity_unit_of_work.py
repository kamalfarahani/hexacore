from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from hexacore.repository.sqlalchemy import SQLAlchemyEntityRepository
from hexacore.unit_of_work.sqlalchemy.entity_unit_of_work import (
    SQLAlchemyEntityUnitOfWork,
)


class Base(DeclarativeBase):
    pass


class ItemRow(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]


class ItemRepository(SQLAlchemyEntityRepository):
    @property
    def command_handlers(self):
        return {}


@pytest.mark.parametrize("action", ["commit", "rollback", "exit"])
def test_transaction_persistence(action):
    engine = create_engine("sqlite:///:memory:")
    try:
        Base.metadata.create_all(engine)
        with Session(engine) as session:
            session.add(ItemRow(name="existing"))
            session.commit()

        uow = SQLAlchemyEntityUnitOfWork(lambda: Session(engine), ItemRepository)
        with uow as active:
            assert active is uow
            assert uow.repository.session is uow.session
            uow.repository.session.add(ItemRow(name="new"))
            if action == "commit":
                uow.commit()
            else:
                # Send the INSERT so rollback must undo actual database work.
                uow.session.flush()
                if action == "rollback":
                    uow.rollback()
                    assert uow.session.scalars(
                        select(ItemRow.name).order_by(ItemRow.id)
                    ).all() == ["existing"]

        with Session(engine) as session:
            names = session.scalars(select(ItemRow.name).order_by(ItemRow.id)).all()
        assert names == (["existing", "new"] if action == "commit" else ["existing"])
    finally:
        engine.dispose()


def test_body_exception_propagates_and_releases_session():
    session = Mock(spec=Session)
    uow = SQLAlchemyEntityUnitOfWork(lambda: session, Mock())
    error = ValueError("body failed")

    with pytest.raises(ValueError) as caught:
        with uow:
            raise error

    assert caught.value is error
    session.rollback.assert_called_once_with()
    session.close.assert_called_once_with()
    session.commit.assert_not_called()


def test_construction_and_inactive_transaction_methods_do_not_create_resources():
    session_factory = Mock()
    repository_factory = Mock()
    uow = SQLAlchemyEntityUnitOfWork(session_factory, repository_factory)

    session_factory.assert_not_called()
    repository_factory.assert_not_called()
    uow.commit()
    uow.rollback()
    uow.done()
    session_factory.assert_not_called()
    repository_factory.assert_not_called()


def test_failed_session_initialization_allows_retry():
    session = Mock(spec=Session)
    error = RuntimeError("session creation failed")
    session_factory = Mock(side_effect=[error, session])
    repository = Mock(spec=SQLAlchemyEntityRepository)
    repository_factory = Mock(return_value=repository)
    uow = SQLAlchemyEntityUnitOfWork(session_factory, repository_factory)

    with pytest.raises(RuntimeError) as caught:
        with uow:
            pytest.fail("Context body must not run")

    assert caught.value is error
    repository_factory.assert_not_called()
    with uow:
        assert uow.session is session
        assert uow.repository is repository

    assert session_factory.call_count == 2
    repository_factory.assert_called_once_with(session)
    session.rollback.assert_called_once_with()
    session.close.assert_called_once_with()


@pytest.mark.parametrize("access", ["session", "repository"])
def test_start_reuses_resources_created_before_context_entry(access):
    session = Mock(spec=Session)
    repository = Mock(spec=SQLAlchemyEntityRepository)
    session_factory = Mock(return_value=session)
    repository_factory = Mock(return_value=repository)
    uow = SQLAlchemyEntityUnitOfWork(session_factory, repository_factory)

    getattr(uow, access)
    with uow:
        uow.start()
        assert uow.session is session
        assert uow.repository is repository

    session_factory.assert_called_once_with()
    repository_factory.assert_called_once_with(session)
    session.rollback.assert_called_once_with()
    session.close.assert_called_once_with()


def test_failed_repository_initialization_releases_session_and_allows_retry():
    first, second = Mock(spec=Session), Mock(spec=Session)
    repository = Mock(spec=SQLAlchemyEntityRepository)
    session_factory = Mock(side_effect=[first, second])
    repository_factory = Mock(side_effect=[ValueError("factory failed"), repository])
    uow = SQLAlchemyEntityUnitOfWork(session_factory, repository_factory)

    with pytest.raises(ValueError, match="factory failed"):
        with uow:
            pytest.fail("Context body must not run")

    first.rollback.assert_called_once_with()
    first.close.assert_called_once_with()
    with uow:
        assert uow.session is second
        assert uow.repository is repository


@pytest.mark.parametrize("failing_method", ["rollback", "close"])
def test_cleanup_failure_still_closes_and_clears_resources(failing_method):
    first, second = Mock(spec=Session), Mock(spec=Session)
    getattr(first, failing_method).side_effect = RuntimeError("cleanup failed")
    repositories = [Mock(spec=SQLAlchemyEntityRepository) for _ in range(2)]
    uow = SQLAlchemyEntityUnitOfWork(
        Mock(side_effect=[first, second]), Mock(side_effect=repositories)
    )

    with pytest.raises(RuntimeError, match="cleanup failed"):
        with uow:
            pass

    first.close.assert_called_once_with()
    with uow:
        assert uow.session is second
        assert uow.repository is repositories[1]


def test_done_is_idempotent_and_next_context_uses_fresh_resources():
    sessions = [Mock(spec=Session) for _ in range(2)]
    repositories = [Mock(spec=SQLAlchemyEntityRepository) for _ in range(2)]
    uow = SQLAlchemyEntityUnitOfWork(
        Mock(side_effect=sessions), Mock(side_effect=repositories)
    )

    for session, repository in zip(sessions, repositories):
        with uow:
            assert uow.session is session
            assert uow.repository is repository
        uow.done()
        session.rollback.assert_called_once_with()
        session.close.assert_called_once_with()
