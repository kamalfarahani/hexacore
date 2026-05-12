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
        model_orm: ModelORM[M],
    ) -> None:
        """
        Initialize the SQLAlchemy WithID wrapper.

        Args:
            model_orm (ModelORM[M]): The ORM model instance.
            model (M): The domain model instance.
        """
        self.model_orm = model_orm

    def get_id(self) -> int | None:
        """
        Get the ID of the model.

        Returns:
            int | None: The ID of the model or None if not set.
        """
        return self.model_orm.id

    def get_model(self) -> M:
        """
        Get the domain model associated with this ID.

        Returns:
            M: The domain model associated with this ID.
        """
        return self.model_orm.to_model()
