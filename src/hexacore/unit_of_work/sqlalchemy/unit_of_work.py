from abc import abstractmethod
from collections.abc import Callable

from sqlalchemy.orm import Session

from hexacore.repository.sqlalchemy import (
    SQLAlchemyEntityRepository,
    SQLAlchemyRelationRepository,
)

from ..base_unit_of_work import BaseUnitOfWork

type SessionFactory = Callable[[], Session]


class SQLAlchemyUnitOfWork[
    R: (SQLAlchemyEntityRepository | SQLAlchemyRelationRepository)
](BaseUnitOfWork[R]):
    """Manage SQLAlchemy transactions and resources for a repository.

    Subclasses implement ``repository`` using the shared session and cache it
    in ``_repository``. The session is created on first access; ``start()``
    initializes the repository and releases resources if initialization fails.

    Context exit calls ``done()`` to roll back pending changes, close the
    session, and clear cached resources. Call ``commit()`` explicitly to persist
    changes. The unit of work can be reused after cleanup.
    """

    def __init__(
        self,
        session_factory: SessionFactory,
    ):
        """Configure the session factory for this unit of work.

        Args:
            session_factory: Factory that creates a session for this unit of work.
        """
        self._session_factory = session_factory
        self._session: Session | None = None
        self._repository: R | None = None

    @property
    @abstractmethod
    def repository(self) -> R:
        """The repository managed by this unit of work."""
        raise NotImplementedError()

    @property
    def session(self) -> Session:
        """The session owned by this unit of work, created on first access."""
        if self._session is None:
            self._session = self._session_factory()

        return self._session

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
