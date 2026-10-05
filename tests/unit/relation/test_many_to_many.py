from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from hexacore.relation.many_to_many import ManyToMany
from hexacore.relation.many_to_many.mutations import (
    CreateMutation,
    UnlinkMutation,
    UpdateLeftMutation,
    UpdateRightMutation,
)

from ._entities import LeftEntity, RightEntity


def test_supported_mutations_lists_all_mutation_classes() -> None:
    relation = ManyToMany[int, UUID, LeftEntity, RightEntity]()

    assert list(relation.supported_mutations()) == [
        CreateMutation,
        UpdateLeftMutation,
        UpdateRightMutation,
        UnlinkMutation,
    ]


def test_create_mutation_builds_create_mutation() -> None:
    left = LeftEntity(7)
    right = RightEntity(uuid4())

    mutation = ManyToMany[int, UUID, LeftEntity, RightEntity].create_mutation(
        left.identifier, right.identifier
    )

    assert isinstance(mutation, CreateMutation)
    assert mutation.model_dump() == {
        "left_id": left.identifier,
        "right_id": right.identifier,
    }


def test_update_left_mutation_builds_update_left_mutation() -> None:
    left = LeftEntity(7)
    right = RightEntity(uuid4())

    mutation = ManyToMany[int, UUID, LeftEntity, RightEntity].update_left_mutation(
        right.identifier, left
    )

    assert isinstance(mutation, UpdateLeftMutation)
    assert mutation.right_id == right.identifier
    assert mutation.left is left


def test_update_right_mutation_builds_update_right_mutation() -> None:
    left = LeftEntity(7)
    right = RightEntity(uuid4())

    mutation = ManyToMany[int, UUID, LeftEntity, RightEntity].update_right_mutation(
        left.identifier, right
    )

    assert isinstance(mutation, UpdateRightMutation)
    assert mutation.left_id == left.identifier
    assert mutation.right is right


def test_unlink_mutation_builds_unlink_mutation() -> None:
    left = LeftEntity(7)
    right = RightEntity(uuid4())

    mutation = ManyToMany[int, UUID, LeftEntity, RightEntity].unlink_mutation(
        left.identifier, right.identifier
    )

    assert isinstance(mutation, UnlinkMutation)
    assert mutation.model_dump() == {
        "left_id": left.identifier,
        "right_id": right.identifier,
    }


def test_relation_does_not_track_mutations() -> None:
    relation = ManyToMany[int, UUID, LeftEntity, RightEntity]()

    ManyToMany[int, UUID, LeftEntity, RightEntity].create_mutation(7, uuid4())

    assert not hasattr(relation, "mutations")


def test_entity_mutations_accept_matching_entities() -> None:
    left = LeftEntity(7)
    right = RightEntity(uuid4())

    update_left = UpdateLeftMutation[UUID, LeftEntity](
        right_id=right.identifier,
        left=left,
    )
    update_right = UpdateRightMutation[int, RightEntity](
        left_id=left.identifier,
        right=right,
    )

    assert update_left.left is left
    assert update_right.right is right


def test_entity_mutations_reject_non_entities() -> None:
    with pytest.raises(ValidationError):
        UpdateLeftMutation(right_id=uuid4(), left=object())  # type: ignore

    with pytest.raises(ValidationError):
        UpdateRightMutation(left_id=7, right=object())  # type: ignore
