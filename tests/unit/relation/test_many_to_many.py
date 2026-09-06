from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from hexacore.relation.many_to_many import ManyToMany
from hexacore.relation.many_to_many.mutations import (
    Create,
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
        relation.update_left(first_right.identifier, second_left),
        relation.update_right(first_left.identifier, second_right),
        relation.unlink(second_left.identifier, first_right.identifier),
    ]

    assert results == [None] * 6
    mutations = relation.mutations
    assert len(mutations) == 6
    for mutation, expected_class in zip(
        mutations,
        [
            Create,
            Create,
            Create,
            UpdateLeft,
            UpdateRight,
            Unlink,
        ],
        strict=True,
    ):
        assert isinstance(mutation, expected_class)

    assert mutations[0].model_dump() == {
        "left_id": first_left.identifier,
        "right_id": first_right.identifier,
    }
    assert mutations[1].model_dump() == {
        "left_id": second_left.identifier,
        "right_id": first_right.identifier,
    }
    assert mutations[2].model_dump() == {
        "left_id": first_left.identifier,
        "right_id": second_right.identifier,
    }
    assert isinstance(mutations[3], UpdateLeft)
    assert mutations[3].right_id == first_right.identifier
    assert mutations[3].left is second_left

    assert isinstance(mutations[4], UpdateRight)
    assert mutations[4].left_id == first_left.identifier
    assert mutations[4].right is second_right

    assert mutations[5].model_dump() == {
        "left_id": second_left.identifier,
        "right_id": first_right.identifier,
    }


def test_context_resets_mutations_and_retains_new_mutations() -> None:
    relation = ManyToMany[int, UUID, LeftEntity, RightEntity]()
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
    relation = ManyToMany[int, UUID, LeftEntity, RightEntity]()

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
