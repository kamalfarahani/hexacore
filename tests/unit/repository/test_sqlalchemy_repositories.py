from dataclasses import dataclass
from unittest.mock import patch

import pytest
from katharos.types import Lazy
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from hexacore.entity import Entity
from hexacore.relation import BaseRelationMutation, ManyToMany, OneToMany, OneToOne
from hexacore.relation.many_to_many import mutations as many_to_many
from hexacore.relation.one_to_many import mutations as one_to_many
from hexacore.relation.one_to_one import mutations as one_to_one
from hexacore.repository import (
    BaseDBCommand,
    BaseEntityRepository,
    BaseRelationRepository,
    SQLAlchemyEntityRepository,
    SQLAlchemyRelationRepository,
)
from hexacore.repository.exceptions import (
    UnsupportedCommandError,
    UnsupportedMutationError,
)


class Base(DeclarativeBase):
    pass


class UserRow(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]


class LinkRow(Base):
    __tablename__ = "links"

    left_id: Mapped[int] = mapped_column(primary_key=True)
    right_id: Mapped[int] = mapped_column(primary_key=True)


@dataclass
class User(Entity[int]):
    id: int
    name: str

    @property
    def identifier(self) -> int:
        return self.id


@dataclass
class AddUser(BaseDBCommand[User]):
    name: str

    @property
    def return_type(self) -> type[User]:
        return User


@dataclass
class GetUser(BaseDBCommand[User | None]):
    id: int

    @property
    def return_type(self) -> type[User | None]:
        return User | None


@dataclass
class RenameUser(BaseDBCommand[None]):
    id: int
    name: str

    @property
    def return_type(self) -> type[None]:
        return type(None)


@dataclass
class DeleteUser(BaseDBCommand[None]):
    id: int

    @property
    def return_type(self) -> type[None]:
        return type(None)


class Users(SQLAlchemyEntityRepository[User]):
    @property
    def command_handlers(self):
        return {
            AddUser: self.add,
            GetUser: self.get,
            RenameUser: self.rename,
            DeleteUser: self.delete,
        }

    def add(self, command: AddUser) -> Lazy[User]:
        row = UserRow(name=command.name)
        self.session.add(row)
        return Lazy(lambda: User(row.id, row.name))

    def get(self, command: GetUser) -> Lazy[User | None]:
        row = self.session.get(UserRow, command.id)
        return Lazy(lambda: None if row is None else User(row.id, row.name))

    def rename(self, command: RenameUser) -> Lazy[None]:
        row = self.session.get(UserRow, command.id)
        if row is None:
            raise LookupError(command.id)
        row.name = command.name
        return Lazy.pure(None)

    def delete(self, command: DeleteUser) -> Lazy[None]:
        row = self.session.get(UserRow, command.id)
        if row is None:
            raise LookupError(command.id)
        self.session.delete(row)
        return Lazy.pure(None)


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    try:
        with Session(engine) as session:
            yield session
    finally:
        engine.dispose()


def test_entity_crud_and_lazy_generated_identifier(session):
    repository = Users(session)
    assert isinstance(repository, BaseEntityRepository)
    assert repository.session is session

    with (
        patch.object(session, "flush", wraps=session.flush) as flush,
        patch.object(session, "commit", wraps=session.commit) as commit,
        patch.object(session, "rollback", wraps=session.rollback) as rollback,
        patch.object(session, "close", wraps=session.close) as close,
    ):
        result = repository.execute(AddUser("Alice"))
        assert result.is_success()
        row = next(iter(session.new))
        assert row.name == "Alice"
        assert row.id is None
        for operation in (flush, commit, rollback, close):
            operation.assert_not_called()

    session.flush()
    user = result.value.resolve()
    assert user == User(row.id, "Alice")
    assert user.id is not None
    assert result.value.resolve() is user
    assert repository.execute(GetUser(user.id)).value.resolve() == user
    assert repository.execute(GetUser(404)).value.resolve() is None

    repository.execute(RenameUser(user.id, "Bob"))
    session.flush()
    assert repository.execute(GetUser(user.id)).value.resolve().name == "Bob"
    repository.execute(DeleteUser(user.id))
    session.flush()
    assert repository.execute(GetUser(user.id)).value.resolve() is None


def test_entity_changes_can_be_rolled_back_by_caller(session):
    repository = Users(session)
    repository.execute(AddUser("Alice"))
    session.flush()
    session.rollback()
    assert session.scalars(select(UserRow)).all() == []


def test_entity_dispatch_requires_exact_type(session):
    class SpecialAdd(AddUser):
        pass

    repository = Users(session)
    assert repository.supported_commands == [AddUser, GetUser, RenameUser, DeleteUser]
    repository.supported_commands.clear()
    assert repository.is_command_supported(AddUser("Alice"))
    command = SpecialAdd("Alice")
    assert not repository.is_command_supported(command)
    result = repository.execute(command)
    assert result.is_failure()
    assert isinstance(result.error, UnsupportedCommandError)
    assert not session.new


def test_entity_subclass_can_override_handler(session):
    class UppercaseUsers(Users):
        def add(self, command: AddUser) -> Lazy[User]:
            return super().add(AddUser(command.name.upper()))

    result = UppercaseUsers(session).execute(AddUser("Alice"))
    session.flush()
    assert result.value.resolve().name == "ALICE"


def test_entity_handler_exceptions_propagate_immediately(session):
    with pytest.raises(LookupError):
        Users(session).execute(RenameUser(404, "Bob"))


def test_conversion_runs_only_on_resolution_and_caches_failure(session):
    conversions = []

    class BrokenUsers(Users):
        def add(self, command: AddUser) -> Lazy[User]:
            super().add(command)

            def convert():
                conversions.append(command)
                raise ValueError("conversion failed")

            return Lazy(convert)

    result = BrokenUsers(session).execute(AddUser("Alice"))
    assert result.is_success()
    assert len(session.new) == 1
    assert conversions == []
    for _ in range(2):
        with pytest.raises(ValueError, match="conversion failed"):
            result.value.resolve()
    assert len(conversions) == 1


@pytest.fixture(
    params=[
        (OneToOne, one_to_one),
        (OneToMany, one_to_many),
        (ManyToMany, many_to_many),
    ]
)
def relation_case(request):
    relation_type, mutations = request.param
    return relation_type[int, int, User, User](), mutations


def make_links(session, mutations):
    class Links(SQLAlchemyRelationRepository):
        @property
        def mutation_handlers(self):
            return {
                mutations.Create: self.create,
                mutations.UpdateLeft: self.update_left,
                mutations.UpdateRight: self.update_right,
                mutations.Unlink: self.unlink,
            }

        def create(self, mutation):
            self.session.add(
                LinkRow(left_id=mutation.left_id, right_id=mutation.right_id)
            )

        def update_left(self, mutation):
            self.session.get(UserRow, mutation.left.identifier).name = mutation.left.name

        def update_right(self, mutation):
            self.session.get(UserRow, mutation.right.identifier).name = mutation.right.name

        def unlink(self, mutation):
            self.session.execute(
                delete(LinkRow).where(
                    LinkRow.left_id == mutation.left_id,
                    LinkRow.right_id == mutation.right_id,
                )
            )

    return Links(session)


def test_relation_handlers_apply_all_mutations_in_order(session, relation_case):
    relation, mutations = relation_case
    repository = make_links(session, mutations)
    assert isinstance(repository, BaseRelationRepository)
    assert repository.session is session
    session.add_all([UserRow(id=1, name="Left"), UserRow(id=2, name="Right")])
    session.commit()

    relation.create(1, 2)
    relation.update_left(2, User(1, "Updated left"))
    relation.update_right(1, User(2, "Updated right"))
    relation.unlink(1, 2)
    pending = list(relation.mutations)
    result = repository.execute_mutations(relation)
    assert result.is_success()
    assert result.value is None
    session.flush()
    assert session.scalars(select(LinkRow)).all() == []
    assert session.get(UserRow, 1).name == "Updated left"
    assert session.get(UserRow, 2).name == "Updated right"
    assert relation.mutations == pending
    session.rollback()
    assert session.get(UserRow, 1).name == "Left"
    assert session.get(UserRow, 2).name == "Right"


def test_relation_prevalidates_entire_batch(session, relation_case):
    class Unknown(BaseRelationMutation):
        pass

    relation, mutations = relation_case
    relation.create(1, 2)
    relation.add_mutation(Unknown())
    pending = list(relation.mutations)
    result = make_links(session, mutations).execute_mutations(relation)
    assert result.is_failure()
    assert isinstance(result.error, UnsupportedMutationError)
    assert "Unknown" in str(result.error)
    assert not session.new
    assert relation.mutations == pending


def test_relation_preserves_empty_batch_and_session_ownership(session, relation_case):
    relation, mutations = relation_case
    repository = make_links(session, mutations)
    result = repository.execute_mutations(relation)
    assert result.is_success()
    assert result.value is None
    relation.create(1, 2)
    with (
        patch.object(session, "flush") as flush,
        patch.object(session, "commit") as commit,
        patch.object(session, "rollback") as rollback,
        patch.object(session, "close") as close,
    ):
        result = repository.execute_mutations(relation)
        assert result.is_success()
        assert result.value is None
        for operation in (flush, commit, rollback, close):
            operation.assert_not_called()
    assert len(session.new) == 1
    assert len(relation.mutations) == 1


def test_relation_stops_on_failure_and_leaves_rollback_to_caller(session, relation_case):
    relation, mutations = relation_case
    relation.create(1, 2)
    relation.update_left(2, User(404, "Missing"))
    relation.create(3, 4)
    pending = list(relation.mutations)
    with pytest.raises(AttributeError):
        make_links(session, mutations).execute_mutations(relation)
    assert len(session.scalars(select(LinkRow)).all()) == 1
    assert relation.mutations == pending
    session.rollback()
    assert session.scalars(select(LinkRow)).all() == []


def test_relation_uses_most_specific_handler_and_snapshots_batch(session, relation_case):
    relation, mutations = relation_case
    calls = []
    relation.create(1, 2)
    concrete_type = type(relation.mutations[0])

    class Links(SQLAlchemyRelationRepository):
        @property
        def mutation_handlers(self):
            return {
                BaseRelationMutation: lambda mutation: calls.append("base"),
                mutations.Create: lambda mutation: calls.append("generic"),
                concrete_type: self.create,
            }

        def create(self, mutation):
            calls.append("concrete")
            relation.create(3, 4)

    result = Links(session).execute_mutations(relation)
    assert result.is_success()
    assert result.value is None
    assert calls == ["concrete"]
    assert len(relation.mutations) == 2


def test_repositories_require_handler_mappings(session):
    with pytest.raises(TypeError, match="command_handlers"):
        SQLAlchemyEntityRepository(session)
    with pytest.raises(TypeError, match="mutation_handlers"):
        SQLAlchemyRelationRepository(session)


def test_public_exports():
    from hexacore.repository.sqlalchemy import (
        SQLAlchemyEntityRepository as EntityRepository,
        SQLAlchemyRelationRepository as RelationRepository,
    )

    assert EntityRepository is SQLAlchemyEntityRepository
    assert RelationRepository is SQLAlchemyRelationRepository
