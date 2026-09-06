from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from hexacore.relation.many_to_many import ManyToMany
from hexacore.relation.many_to_many.commands import (
    Create,
    GetLefts,
    GetRights,
    Unlink,
    UpdateLeft,
    UpdateRight,
)

from ._entities import LeftEntity, RightEntity


def test_collects_operations_for_multiple_entities_on_both_sides() -> None:
    relation = ManyToMany[int, UUID, LeftEntity, RightEntity]()
    first_left = LeftEntity(7)
    second_left = LeftEntity(8)
    first_right = RightEntity(uuid4())
    second_right = RightEntity(uuid4())

    results = [
        relation.create(first_left.identifier, first_right.identifier),
        relation.create(second_left.identifier, first_right.identifier),
        relation.create(first_left.identifier, second_right.identifier),
        relation.get_lefts(first_right.identifier),
        relation.get_rights(first_left.identifier),
        relation.update_left(first_right.identifier, second_left),
        relation.update_right(first_left.identifier, second_right),
        relation.unlink(second_left.identifier, first_right.identifier),
    ]

    assert results == [None] * 8
    commands = relation.commands
    assert len(commands) == 8
    for command, expected_class in zip(
        commands,
        [
            Create,
            Create,
            Create,
            GetLefts,
            GetRights,
            UpdateLeft,
            UpdateRight,
            Unlink,
        ],
        strict=True,
    ):
        assert isinstance(command, expected_class)

    assert commands[0].model_dump() == {
        "left_id": first_left.identifier,
        "right_id": first_right.identifier,
    }
    assert commands[1].model_dump() == {
        "left_id": second_left.identifier,
        "right_id": first_right.identifier,
    }
    assert commands[2].model_dump() == {
        "left_id": first_left.identifier,
        "right_id": second_right.identifier,
    }
    assert commands[3].model_dump() == {"right_id": first_right.identifier}
    assert commands[4].model_dump() == {"left_id": first_left.identifier}

    assert isinstance(commands[5], UpdateLeft)
    assert commands[5].right_id == first_right.identifier
    assert commands[5].left is second_left

    assert isinstance(commands[6], UpdateRight)
    assert commands[6].left_id == first_left.identifier
    assert commands[6].right is second_right

    assert commands[7].model_dump() == {
        "left_id": second_left.identifier,
        "right_id": first_right.identifier,
    }


def test_context_resets_commands_and_retains_new_commands() -> None:
    relation = ManyToMany[int, UUID, LeftEntity, RightEntity]()
    relation.create(7, uuid4())
    previous_commands = relation.commands

    with relation as entered:
        assert entered is relation
        assert relation.commands == []
        assert relation.commands is not previous_commands
        relation.get_lefts(uuid4())

    assert len(previous_commands) == 1
    assert len(relation.commands) == 1
    assert isinstance(relation.commands[0], GetLefts)


def test_context_preserves_commands_when_exception_propagates() -> None:
    relation = ManyToMany[int, UUID, LeftEntity, RightEntity]()

    with pytest.raises(RuntimeError, match="operation failed"), relation:
        relation.get_rights(7)
        raise RuntimeError("operation failed")

    assert len(relation.commands) == 1
    assert isinstance(relation.commands[0], GetRights)


def test_specialized_commands_validate_identifier_direction() -> None:
    right_id = uuid4()

    assert GetLefts[UUID](right_id=right_id).right_id == right_id
    assert GetRights[int](left_id=7).left_id == 7

    with pytest.raises(ValidationError):
        GetLefts[UUID](right_id=7)  # type: ignore

    with pytest.raises(ValidationError):
        GetRights[int](left_id=right_id)  # type: ignore


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
