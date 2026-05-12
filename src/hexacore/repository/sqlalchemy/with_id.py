"""SQLAlchemy implementation of the WithID interface."""

from pydantic import BaseModel

from hexacore.repository.base import WithID

from .model_orm import ModelORM


class SQLAlchemyWithID[M: BaseModel](WithID[M]):
    """
    SQLAlchemy implementation of the WithID interface.

    This class wraps a SQLAlchemy ORM model and provides access to its ID
    and associated domain model.
    """

    def __init__(
        self,
        model: M,
        model_orm: ModelORM[M],
    ) -> None:
        """
        Initialize the SQLAlchemy WithID wrapper.

        Args:
            model: The domain model instance.
            model_orm: The ORM model instance.
        """
        self.model = model
        self.model_orm = model_orm

    def get_id(self) -> int | None:
        """
        Get the ID of the model.

        Returns:
            The database ID, or ``None`` if not yet assigned.
        """
        return self.model_orm.id

    def get_model(self) -> M:
        """
        Get the domain model associated with this ID.

        Returns:
            The domain model associated with this ID.
        """
        return self.model
