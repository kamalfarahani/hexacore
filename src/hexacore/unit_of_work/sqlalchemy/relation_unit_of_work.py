"""Manage relation repository transactions and SQLAlchemy session resources."""

from collections.abc import Callable

from sqlalchemy.orm import Session

from hexacore.repository.sqlalchemy import SQLAlchemyRelationRepository

from .unit_of_work import SessionFactory, SQLAlchemyUnitOfWork

type RepositoryFactory[R: SQLAlchemyRelationRepository] = Callable[[Session], R]


class SQLAlchemyRelationUnitOfWork[R: SQLAlchemyRelationRepository](
    SQLAlchemyUnitOfWork[R]
):
    """Manage a relation repository and its session within a unit of work."""

    def __init__(
        self,
        session_factory: SessionFactory,
        repository_factory: RepositoryFactory[R],
    ) -> None:
        """Configure factories for resources owned by this unit of work.

        Args:
            session_factory: Factory that creates a session for this unit of work.
            repository_factory: Factory that creates a repository using the session.
        """
        super().__init__(session_factory)
        self._repository_factory = repository_factory

    @property
    def repository(self) -> R:
        """The repository using this unit of work's session, created on first access."""
        if self._repository is None:
            self._repository = self._repository_factory(self.session)

        return self._repository
