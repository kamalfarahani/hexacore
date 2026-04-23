from collections.abc import Callable
from types import TracebackType

from pydantic import BaseModel
from sqlalchemy.orm import Session

from hexacore.repository import SqlAlchemyRepository

from .base_unit_of_work import BaseUnitOfWork

type SessionFactory = Callable[[], Session]
type RepoFactory[M: BaseModel] = Callable[[Session], SqlAlchemyRepository[M]]


class SQLAlchemyUnitOfWork[M: BaseModel](BaseUnitOfWork[M]):
    """
    SQLAlchemy unit of work implementation.
    """

    _session: Session | None
    _repo_factory: RepoFactory[M]

    def __init__(
        self,
        session_factory: SessionFactory,
        repo_factory: RepoFactory[M],
    ) -> None:
        """
        Initialize the unit of work.

        Args:
            repository (SqlAlchemyRepository[M]): The repository.
            session_factory (SessionFactory): The session factory.
        """
        self._session_factory = session_factory
        self._repo_factory = repo_factory
        self._session: Session | None = None

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
    def repository(self) -> SqlAlchemyRepository[M]:
        """
        Get the repository.

        Returns:
            SqlAlchemyRepository[M]: The repository.
        """
        return self._repo_factory(self.session)

    def __enter__(self) -> "SQLAlchemyUnitOfWork":
        """
        Enter the unit of work context manager.

        Returns:
            SQLAlchemyUnitOfWork: The unit of work context manager.
        """
        self._session: Session = self._session_factory()

        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """
        Exit the unit of work context manager.
        If we don’t commit, or if we exit the context manager by raising an error,
        we do a rollback. (The rollback has no effect if `commit()` has been called.)

        Args:
            exc_type (type[BaseException] | None): The exception type.
            exc_val (BaseException | None): The exception value.
            exc_tb (TracebackType | None): The exception traceback.
        """
        self.rollback()
        if self._session is not None:
            self._session.close()

    def commit(self) -> None:
        """
        Commit the transaction.
        """
        if self._session is not None:
            self._session.commit()

    def rollback(self) -> None:
        """
        Rollback the transaction.
        """
        if self._session is not None:
            self._session.rollback()
