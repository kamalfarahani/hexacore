"""SQLAlchemy repository implementation."""

from pydantic import BaseModel
from sqlalchemy.orm import Session

from hexacore.repository.base import BaseRepository

from .db_promise import SQLAlchemyDBPromise
from .model_orm import ModelORM
from .with_id import SQLAlchemyWithID


class SQLAlchemyRepository[M: BaseModel](BaseRepository[M]):
    """SQLAlchemy-backed repository implementation."""

    _session: Session
    _ModelORMClass: type[ModelORM[M]]

    def __init__(
        self,
        session: Session,
        ModelORMClass: type[ModelORM[M]],
    ) -> None:
        """
        Initialize the repository.

        Args:
            session: The SQLAlchemy session to use for database operations.
            ModelORMClass: The ORM class that maps the domain model to the database.
        """
        self._session = session
        self._ModelORMClass = ModelORMClass

    def add(self, model: M) -> SQLAlchemyDBPromise[M]:
        """
        Add a model to the repository.

        Args:
            model: The model to add.

        Returns:
            A promise that will be fulfilled when the model is persisted to the database.
        """
        model_orm = self._ModelORMClass.from_model(
            model,
            self._session,
        )
        self._session.add(model_orm)

        return SQLAlchemyDBPromise(SQLAlchemyWithID(model_orm))

    def get(self, id: int) -> SQLAlchemyDBPromise[M]:
        """
        Get a model by its ID.

        Args:
            id: The ID of the model to retrieve.

        Returns:
            A promise that will be fulfilled when the model is retrieved from the database.
        """
        model_orm = self._session.get(
            self._ModelORMClass,
            id,
        )

        if model_orm is not None:
            return SQLAlchemyDBPromise(SQLAlchemyWithID(model_orm))
        else:
            return SQLAlchemyDBPromise(None)

    def update(self, model: M, id: int) -> SQLAlchemyDBPromise[M]:
        """
        Update a model in the repository.

        Args:
            model: The updated model data.
            id: The ID of the model to update.

        Returns:
            A promise that will be fulfilled when the model is updated in the database.
        """
        model_orm = self._session.get(
            self._ModelORMClass,
            id,
        )

        if model_orm is not None:
            updated_model_orm = self._ModelORMClass.from_model(
                model,
                self._session,
            )
            updated_model_orm.id = id
            self._session.merge(updated_model_orm)
            return SQLAlchemyDBPromise(SQLAlchemyWithID(updated_model_orm))
        else:
            return SQLAlchemyDBPromise(None)

    def delete(self, id: int) -> SQLAlchemyDBPromise[M]:
        """
        Delete a model from the repository.

        Args:
            id: The ID of the model to delete.

        Returns:
            A promise that will be fulfilled when the model is deleted from the database.
        """
        model_orm = self._session.get(
            self._ModelORMClass,
            id,
        )

        if model_orm is not None:
            self._session.delete(model_orm)
            return SQLAlchemyDBPromise(SQLAlchemyWithID(model_orm))
        else:
            return SQLAlchemyDBPromise(None)
