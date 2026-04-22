from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class ModelORM[M](DeclarativeBase):
    """
    Base class for SQLAlchemy ORM entities.
    """

    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    def __init__(self, model: M) -> None:
        """
        Initialize the ORM model from a domain model.

        Args:
            model (M): The domain model.
        """
        self.model = model

    @staticmethod
    def from_model(
        model: M,
        session: Session,
    ) -> "ModelORM[M]":
        """
        Create an ORM model from a domain model.

        Args:
            model (M): The domain model.
            session (Session): The SQLAlchemy session.

        Returns:
            ModelORM[M]: The ORM model.
        """
        raise NotImplementedError()

    @staticmethod
    def to_model(model_orm: "ModelORM[M]") -> M:
        """
        Convert an ORM model to a domain model.

        Args:
            model_orm (ModelORM[M]): The ORM model.

        Returns:
            M: The domain model.
        """
        raise NotImplementedError()
