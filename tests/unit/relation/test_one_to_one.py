from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from hexacore.relation.one_to_one import OneToOne
from hexacore.relation.one_to_one.mutations import (
    Create,
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
        relation.update_left(right.identifier, left),
        relation.update_right(left.identifier, right),
        relation.unlink(left.identifier, right.identifier),
    ]

    assert results == [None] * 4
    mutations = relation.mutations
    assert len(mutations) == 4
    for mutation, expected_class in zip(
        mutations,
        [Create, UpdateLeft, UpdateRight, Unlink],
        strict=True,
    ):
        assert isinstance(mutation, expected_class)

    assert mutations[0].model_dump() == {
        "left_id": left.identifier,
        "right_id": right.identifier,
    }
    assert isinstance(mutations[1], UpdateLeft)
    assert mutations[1].right_id == right.identifier
    assert mutations[1].left is left

    assert isinstance(mutations[2], UpdateRight)
    assert mutations[2].left_id == left.identifier
    assert mutations[2].right is right

    assert mutations[3].model_dump() == {
        "left_id": left.identifier,
        "right_id": right.identifier,
    }


def test_context_resets_mutations_and_retains_new_mutations() -> None:
    relation = OneToOne[int, UUID, LeftEntity, RightEntity]()
    relation.create(7, uuid4())
    previous_mutations = relation.mutations

    with relation as entered:
        assert entered is relation
        assert relation.mutations == []
        assert relation.mutations is not previous_mutations
        relation.unlink(7, uuid4())

    assert len(previous_mutations) == 1
    assert len(relation.mutations) == 1
    assert isinstance(relation.mutations[0], Unlink)


def test_context_preserves_mutations_when_exception_propagates() -> None:
    relation = OneToOne[int, UUID, LeftEntity, RightEntity]()

    with pytest.raises(RuntimeError, match="operation failed"), relation:
        relation.unlink(7, uuid4())
        raise RuntimeError("operation failed")

    assert len(relation.mutations) == 1
    assert isinstance(relation.mutations[0], Unlink)


def test_entity_mutations_accept_matching_entities() -> None:
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


def test_entity_mutations_reject_non_entities() -> None:
    with pytest.raises(ValidationError):
        UpdateLeft(right_id=uuid4(), left=object())  # type: ignore

    with pytest.raises(ValidationError):
        UpdateRight(left_id=7, right=object())  # type: ignore
