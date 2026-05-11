import pytest
from pydantic import BaseModel
from sqlalchemy.orm import Mapped, mapped_column

from hexacore.repository.sqlalchemy.model_orm import ModelORM
from hexacore.repository.sqlalchemy.with_id import SQLAlchemyWithID


class FakeModel(BaseModel):
    name: str
    age: int


class FakeModelORM(ModelORM[FakeModel]):
    """Concrete ORM mapping used purely for unit testing.

    SQLAlchemy declarative classes are valid plain Python objects when
    instantiated outside a session; we exploit that to avoid touching a
    real database.
    """

    __tablename__ = "fake_model"

    name: Mapped[str] = mapped_column()
    age: Mapped[int] = mapped_column()

    @staticmethod
    def from_model(model: FakeModel, session) -> "FakeModelORM":
        return FakeModelORM(name=model.name, age=model.age)

    def to_model(self) -> FakeModel:
        return FakeModel(name=self.name, age=self.age)


@pytest.fixture
def model() -> FakeModel:
    return FakeModel(name="alice", age=30)


@pytest.fixture
def model_orm(model: FakeModel) -> FakeModelORM:
    return FakeModelORM(id=7, name=model.name, age=model.age)


class TestInit:
    def test_stores_model_orm_and_model(
        self, model_orm: FakeModelORM, model: FakeModel
    ) -> None:
        with_id = SQLAlchemyWithID[FakeModel](model_orm)

        assert with_id.model_orm is model_orm
        assert with_id.get_model() == model


class TestGetId:
    def test_returns_orm_id(self, model_orm: FakeModelORM, model: FakeModel) -> None:
        with_id = SQLAlchemyWithID[FakeModel](model_orm)

        assert with_id.get_id() == 7

    def test_reflects_id_changes_on_orm(
        self, model_orm: FakeModelORM, model: FakeModel
    ) -> None:
        with_id = SQLAlchemyWithID[FakeModel](model_orm)

        model_orm.id = 99

        assert with_id.get_id() == 99

    def test_returns_none_when_orm_has_no_id(self, model: FakeModel) -> None:
        # Simulates an un-flushed ORM instance whose primary key is unset.
        orm = FakeModelORM(name=model.name, age=model.age)
        with_id = SQLAlchemyWithID[FakeModel](orm)

        assert with_id.get_id() is None


class TestGetModel:
    def test_returns_stored_model(
        self,
        model_orm: FakeModelORM,
        model: FakeModel,
    ) -> None:
        with_id = SQLAlchemyWithID[FakeModel](model_orm)

        assert with_id.get_model() == model
