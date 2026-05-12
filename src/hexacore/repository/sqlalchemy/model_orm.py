"""SQLAlchemy ORM base entity class."""

from abc import abstractmethod

from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class ModelORM[M: BaseModel](DeclarativeBase):
    """
    Base class for SQLAlchemy ORM entities.
    """

    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    @staticmethod
    def from_model(
        model: M,
        session: Session,
    ) -> "ModelORM[M]":
        """
        Create an ORM model from a domain model.

        Args:
            model: The domain model.
            session: The SQLAlchemy session.

        Returns:
            The ORM entity created from the domain model.
        """
        raise NotImplementedError()

    @abstractmethod
    def to_model(self) -> M:
        """
        Convert an ORM model to a domain model.

        Returns:
            The domain model corresponding to this ORM entity.
        """
        raise NotImplementedError()
