"""SQLAlchemy unit-of-work implementation."""

from collections.abc import Callable

from pydantic import BaseModel
from sqlalchemy.orm import Session

from hexacore.repository import SQLAlchemyRepository

from .base_unit_of_work import BaseUnitOfWork

type SessionFactory = Callable[[], Session]
type RepoFactory[M: BaseModel] = Callable[[Session], SQLAlchemyRepository[M]]


class SQLAlchemyUnitOfWork[M: BaseModel](BaseUnitOfWork[M]):
    """
    SQLAlchemy unit of work implementation.
    """

    _session: Session | None
    _session_factory: SessionFactory
    _repo_factory: RepoFactory[M]

    def __init__(
        self,
        session_factory: SessionFactory,
        repo_factory: RepoFactory[M],
    ) -> None:
        """
        Initialize the unit of work.

        Args:
            session_factory: A callable that creates a new SQLAlchemy ``Session``.
            repo_factory: A callable that creates a ``SQLAlchemyRepository``
                from an existing session.
        """
        self._session = None
        self._session_factory = session_factory
        self._repo_factory = repo_factory

    @property
    def session(self) -> Session:
        """
        Get the database session.

        Returns:
            The current database session.
        """
        if self._session is None:
            self._session = self._session_factory()

        return self._session

    @property
    def repository(self) -> SQLAlchemyRepository[M]:
        """
        Get the repository.

        Returns:
            A repository bound to the current session.
        """
        return self._repo_factory(self.session)

    def start(self) -> None:
        """
        Prepare the unit of work for use by initializing the database session.
        """
        self._session = self._session_factory()

    def done(self) -> None:
        """
        Finish the unit of work, rolling back uncommitted changes and closing
        the session.
        """
        self.rollback()
        if self._session is not None:
            self._session.close()

    def commit(self) -> None:
        """
        Flush all pending changes and commit the current transaction.
        """
        if self._session is not None:
            self._session.commit()

    def rollback(self) -> None:
        """
        Discard all pending changes by rolling back the current transaction.
        """
        if self._session is not None:
            self._session.rollback()
