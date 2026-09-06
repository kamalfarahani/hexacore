from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from hexacore.relation.one_to_many import OneToMany
from hexacore.relation.one_to_many.commands import (
    Create,
    GetLeft,
    GetRights,
    Unlink,
    UpdateLeft,
    UpdateRight,
)

from ._entities import LeftEntity, RightEntity


def test_collects_operations_for_multiple_right_entities() -> None:
    relation = OneToMany[int, UUID, LeftEntity, RightEntity]()
    left = LeftEntity(7)
    first_right = RightEntity(uuid4())
    second_right = RightEntity(uuid4())

    results = [
        relation.create(left.identifier, first_right.identifier),
        relation.create(left.identifier, second_right.identifier),
        relation.get_left(second_right.identifier),
        relation.get_rights(left.identifier),
        relation.update_left(first_right.identifier, left),
        relation.update_right(left.identifier, second_right),
        relation.unlink(left.identifier, first_right.identifier),
    ]

    assert results == [None] * 7
    commands = relation.commands
    assert len(commands) == 7
    for command, expected_class in zip(
        commands,
        [
            Create,
            Create,
            GetLeft,
            GetRights,
            UpdateLeft,
            UpdateRight,
            Unlink,
        ],
        strict=True,
    ):
        assert isinstance(command, expected_class)

    assert commands[0].model_dump() == {
        "left_id": left.identifier,
        "right_id": first_right.identifier,
    }

    assert commands[1].model_dump() == {
        "left_id": left.identifier,
        "right_id": second_right.identifier,
    }

    assert commands[2].model_dump() == {"right_id": second_right.identifier}
    assert commands[3].model_dump() == {"left_id": left.identifier}

    assert isinstance(commands[4], UpdateLeft)
    assert commands[4].right_id == first_right.identifier
    assert commands[4].left is left

    assert isinstance(commands[5], UpdateRight)
    assert commands[5].left_id == left.identifier
    assert commands[5].right is second_right

    assert commands[6].model_dump() == {
        "left_id": left.identifier,
        "right_id": first_right.identifier,
    }


def test_context_resets_commands_and_retains_new_commands() -> None:
    relation = OneToMany[int, UUID, LeftEntity, RightEntity]()
    relation.create(7, uuid4())
    previous_commands = relation.commands

    with relation as entered:
        assert entered is relation
        assert relation.commands == []
        assert relation.commands is not previous_commands
        relation.get_rights(7)

    assert len(previous_commands) == 1
    assert len(relation.commands) == 1
    assert isinstance(relation.commands[0], GetRights)


def test_context_preserves_commands_when_exception_propagates() -> None:
    relation = OneToMany[int, UUID, LeftEntity, RightEntity]()

    with pytest.raises(RuntimeError, match="operation failed"), relation:
        relation.get_rights(7)
        raise RuntimeError("operation failed")

    assert len(relation.commands) == 1
    assert isinstance(relation.commands[0], GetRights)


def test_specialized_commands_validate_identifier_direction() -> None:
    right_id = uuid4()

    assert GetLeft[UUID](right_id=right_id).right_id == right_id
    assert GetRights[int](left_id=7).left_id == 7

    with pytest.raises(ValidationError):
        GetLeft[UUID](right_id=7)  # type: ignore

    with pytest.raises(ValidationError):
        GetRights[int](left_id=right_id)  # type: ignore


def test_entity_commands_reject_non_entities() -> None:
    with pytest.raises(ValidationError):
        UpdateLeft(right_id=uuid4(), left=object())  # type: ignore

    with pytest.raises(ValidationError):
        UpdateRight(left_id=7, right=object())  # type: ignore
