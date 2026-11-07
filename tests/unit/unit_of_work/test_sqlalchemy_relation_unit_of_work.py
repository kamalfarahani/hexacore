from unittest.mock import Mock

import pytest
from sqlalchemy import Column, Integer, MetaData, Table, create_engine, select
from sqlalchemy.orm import Session

from hexacore.relation import BaseRelationMutation
from hexacore.repository.sqlalchemy import SQLAlchemyRelationRepository
from hexacore.unit_of_work.sqlalchemy import SQLAlchemyRelationUnitOfWork


metadata = MetaData()
links = Table(
    "links",
    metadata,
    Column("left_id", Integer, primary_key=True),
    Column("right_id", Integer, primary_key=True),
)


class AddLink(BaseRelationMutation):
    left_id: int
    right_id: int


class LinkRepository(SQLAlchemyRelationRepository):
    @property
    def mutation_handlers(self):
        return {AddLink: self.add_link}

    def add_link(self, mutation: AddLink) -> None:
        self.session.execute(
            links.insert().values(
                left_id=mutation.left_id, right_id=mutation.right_id,
            )
        )


@pytest.mark.parametrize("action", ["commit", "rollback", "exit", "error"])
def test_relation_mutation_transaction_persistence(action):
    engine = create_engine("sqlite:///:memory:")
    try:
        metadata.create_all(engine)
        with engine.begin() as connection:
            connection.execute(links.insert().values(left_id=1, right_id=2))
        uow = SQLAlchemyRelationUnitOfWork(lambda: Session(engine), LinkRepository)
        error = ValueError("body failed")

        def execute_mutation():
            with uow as active:
                assert active is uow
                assert uow.repository.session is uow.session
                uow.repository.execute_mutations([AddLink(left_id=3, right_id=4)])
                assert uow.session.execute(
                    select(links).order_by(links.c.left_id)
                ).all() == [(1, 2), (3, 4)]
                if action == "error":
                    raise error
                if action == "commit":
                    uow.commit()
                elif action == "rollback":
                    uow.rollback()
                    assert uow.session.execute(select(links)).all() == [(1, 2)]

        if action == "error":
            with pytest.raises(ValueError) as caught:
                execute_mutation()
            assert caught.value is error
        else:
            execute_mutation()

        with Session(engine) as session:
            rows = session.execute(select(links).order_by(links.c.left_id)).all()
        assert rows == ([(1, 2), (3, 4)] if action == "commit" else [(1, 2)])
    finally:
        engine.dispose()


def test_resources_are_lazy_and_repository_is_cached():
    session = Mock(spec=Session)
    repository = LinkRepository(session)
    session_factory = Mock(return_value=session)
    repository_factory = Mock(return_value=repository)
    uow = SQLAlchemyRelationUnitOfWork(session_factory, repository_factory)

    uow.commit()
    uow.rollback()
    uow.done()
    session_factory.assert_not_called()
    repository_factory.assert_not_called()
    assert uow.session is session
    repository_factory.assert_not_called()
    assert uow.repository is repository
    with uow:
        uow.start()
        assert uow.repository is repository
    session_factory.assert_called_once_with()
    repository_factory.assert_called_once_with(session)
    session.rollback.assert_called_once_with()
    session.close.assert_called_once_with()


@pytest.mark.parametrize("failing_factory", ["session", "repository"])
def test_initialization_failure_releases_resources_and_allows_retry(failing_factory):
    first, second = Mock(spec=Session), Mock(spec=Session)
    error = RuntimeError("factory failed")
    repository = LinkRepository(second)
    session_factory = Mock(
        side_effect=[error, second]
        if failing_factory == "session" else [first, second]
    )
    repository_factory = Mock(
        side_effect=[error, repository]
        if failing_factory == "repository" else [repository]
    )
    uow = SQLAlchemyRelationUnitOfWork(session_factory, repository_factory)

    with pytest.raises(RuntimeError) as caught:
        with uow:
            pytest.fail("Context body must not run")
    assert caught.value is error
    if failing_factory == "session":
        repository_factory.assert_not_called()
    else:
        first.rollback.assert_called_once_with()
        first.close.assert_called_once_with()
    with uow:
        assert uow.repository is repository
        assert uow.session is second
    second.rollback.assert_called_once_with()
    second.close.assert_called_once_with()


@pytest.mark.parametrize("failure", [None, "rollback", "close"])
def test_cleanup_clears_resources_and_allows_reuse(failure):
    first, second = Mock(spec=Session), Mock(spec=Session)
    repositories = [LinkRepository(first), LinkRepository(second)]
    uow = SQLAlchemyRelationUnitOfWork(
        Mock(side_effect=[first, second]), Mock(side_effect=repositories)
    )
    uow.start()
    if failure is None:
        uow.done()
    else:
        error = RuntimeError("cleanup failed")
        getattr(first, failure).side_effect = error
        with pytest.raises(RuntimeError) as caught:
            uow.done()
        assert caught.value is error
    uow.done()
    first.rollback.assert_called_once_with()
    first.close.assert_called_once_with()

    with uow:
        assert uow.session is second
        assert uow.repository is repositories[1]
    second.rollback.assert_called_once_with()
    second.close.assert_called_once_with()
