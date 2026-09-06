from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from hexacore.relation.one_to_one import OneToOne
from hexacore.relation.one_to_one.commands import (
    Create,
    GetLeft,
    GetRight,
    Unlink,
    UpdateLeft,
    UpdateRight,
)

from ._entities import LeftEntity, RightEntity


def test_collects_one_to_one_operations_in_order() -> None:
    relation = OneToOne[int, UUID, LeftEntity, RightEntity]()
    left = LeftEntity(7)
    right = RightEntity(uuid4())

    results = [
        relation.create(left.identifier, right.identifier),
        relation.get_left(right.identifier),
        relation.get_right(left.identifier),
        relation.update_left(right.identifier, left),
        relation.update_right(left.identifier, right),
        relation.unlink(left.identifier, right.identifier),
    ]

    assert results == [None] * 6
    commands = relation.commands
    assert len(commands) == 6
    for command, expected_class in zip(
        commands,
        [Create, GetLeft, GetRight, UpdateLeft, UpdateRight, Unlink],
        strict=True,
    ):
        assert isinstance(command, expected_class)

    assert commands[0].model_dump() == {
        "left_id": left.identifier,
        "right_id": right.identifier,
    }
    assert commands[1].model_dump() == {"right_id": right.identifier}
    assert commands[2].model_dump() == {"left_id": left.identifier}

    assert isinstance(commands[3], UpdateLeft)
    assert commands[3].right_id == right.identifier
    assert commands[3].left is left

    assert isinstance(commands[4], UpdateRight)
    assert commands[4].left_id == left.identifier
    assert commands[4].right is right

    assert commands[5].model_dump() == {
        "left_id": left.identifier,
        "right_id": right.identifier,
    }


def test_context_resets_commands_and_retains_new_commands() -> None:
    relation = OneToOne[int, UUID, LeftEntity, RightEntity]()
    relation.create(7, uuid4())
    previous_commands = relation.commands

    with relation as entered:
        assert entered is relation
        assert relation.commands == []
        assert relation.commands is not previous_commands
        relation.get_right(7)

    assert len(previous_commands) == 1
    assert len(relation.commands) == 1
    assert isinstance(relation.commands[0], GetRight)


def test_context_preserves_commands_when_exception_propagates() -> None:
    relation = OneToOne[int, UUID, LeftEntity, RightEntity]()

    with pytest.raises(RuntimeError, match="operation failed"), relation:
        relation.get_right(7)
        raise RuntimeError("operation failed")

    assert len(relation.commands) == 1
    assert isinstance(relation.commands[0], GetRight)


def test_specialized_commands_validate_identifier_direction() -> None:
    right_id = uuid4()

    assert GetLeft[UUID](right_id=right_id).right_id == right_id
    assert GetRight[int](left_id=7).left_id == 7

    with pytest.raises(ValidationError):
        GetLeft[UUID](right_id=7)  # type: ignore

    with pytest.raises(ValidationError):
        GetRight[int](left_id=right_id)  # type: ignore


def test_entity_commands_accept_matching_entities() -> None:
    left = LeftEntity(7)
    right = RightEntity(uuid4())

    update_left = UpdateLeft[UUID, LeftEntity](
        right_id=right.identifier,
        left=left,
    )
    update_right = UpdateRight[int, RightEntity](
        left_id=left.identifier,
        right=right,
    )

    assert update_left.left is left
    assert update_right.right is right


def test_entity_commands_reject_non_entities() -> None:
    with pytest.raises(ValidationError):
        UpdateLeft(right_id=uuid4(), left=object())  # type: ignore

    with pytest.raises(ValidationError):
        UpdateRight(left_id=7, right=object())  # type: ignore
