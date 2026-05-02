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
            repository (SQLAlchemyRepository[M]): The repository.
            session_factory (SessionFactory): The session factory.
        """
        self._session = None
        self._session_factory = session_factory
        self._repo_factory = repo_factory

    @property
    def session(self) -> Session:
        """
        Get the database session.

        Returns:
            Session: The database session.
        """
        if self._session is None:
            self._session = self._session_factory()

        return self._session

    @property
    def repository(self) -> SQLAlchemyRepository[M]:
        """
        Get the repository.

        Returns:
            SQLAlchemyRepository[M]: The repository.
        """
        return self._repo_factory(self.session)

    def start(self) -> None:
        """
        Make the unit of work ready for use.
        Initializes the database session.

        Side effects:
            - Initializes the database session.
        """
        self._session = self._session_factory()

    def done(self) -> None:
        """
        Finish the unit of work and release any resources.
        Rolls back any uncommitted transactions and closes the database session.

        Side effects:
            - Rolls back any uncommitted transactions.
            - Closes the database session.
        """
        self.rollback()
        if self._session is not None:
            self._session.close()

    def commit(self) -> None:
        """
        Commit the transaction.

        Side effects:
            - Commits the transaction.
        """
        if self._session is not None:
            self._session.commit()

    def rollback(self) -> None:
        """
        Rollback the transaction.

        Side effects:
            - Rolls back the transaction.
        """
        if self._session is not None:
            self._session.rollback()
