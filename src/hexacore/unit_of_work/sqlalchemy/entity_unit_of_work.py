"""Manage entity repository transactions and SQLAlchemy session resources."""

from collections.abc import Callable

from sqlalchemy.orm import Session

from hexacore.repository.sqlalchemy import SQLAlchemyEntityRepository

from ..base_unit_of_work import BaseUnitOfWork

type RepositoryFactory[R: SQLAlchemyEntityRepository] = Callable[[Session], R]
type SessionFactory = Callable[[], Session]


class SQLAlchemyEntityUnitOfWork[R: SQLAlchemyEntityRepository](BaseUnitOfWork):
    """Manage an entity repository and its session within a unit of work.

    Create resources lazily on property access or initialize them with
    ``start()``. Context entry calls ``start()``; context exit calls ``done()``
    to roll back pending changes and close the session. Call ``commit()``
    explicitly to persist changes before exit.
    """

    def __init__(
        self,
        session_factory: SessionFactory,
        repository_factory: RepositoryFactory[R],
    ):
        """Configure factories for resources owned by this unit of work.

        Args:
            session_factory: Factory that creates a session for this unit of work.
            repository_factory: Factory that creates a repository using the session.
        """
        self._session_factory = session_factory
        self._repository_factory = repository_factory
        self._session: Session | None = None
        self._repository: R | None = None

    @property
    def session(self) -> Session:
        """The session owned by this unit of work, created on first access."""
        if self._session is None:
            self._session = self._session_factory()

        return self._session

    @property
    def repository(self) -> R:
        """The repository using this unit of work's session, created on first access."""
        if self._repository is None:
            self._repository = self._repository_factory(self.session)

        return self._repository

    def start(self) -> None:
        """Initialize the repository, reusing any existing session.

        Release resources if repository initialization fails.
        """
        try:
            _ = self.repository
        except BaseException:
            self.done()
            raise

    def done(self) -> None:
        """Roll back and close the session, then clear cached resources.

        Attempt to close the session even if rollback fails, and clear cached
        resources even if cleanup raises. Later access creates fresh resources.
        Do nothing if no session exists.
        """
        try:
            try:
                self.rollback()
            finally:
                if self._session is not None:
                    self._session.close()
        finally:
            self._session = None
            self._repository = None

    def commit(self) -> None:
        """Flush pending changes and commit the current session's transaction.

        Do nothing if no session exists.
        """
        if self._session is not None:
            self._session.commit()

    def rollback(self) -> None:
        """Discard pending changes in the current session's transaction.

        Do nothing if no session exists.
        """
        if self._session is not None:
            self._session.rollback()
