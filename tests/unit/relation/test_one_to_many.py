from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from hexacore.relation.one_to_many import OneToMany
from hexacore.relation.one_to_many.mutations import (
    Create,
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
        relation.update_left(first_right.identifier, left),
        relation.update_right(left.identifier, second_right),
        relation.unlink(left.identifier, first_right.identifier),
    ]

    assert results == [None] * 5
    mutations = relation.mutations
    assert len(mutations) == 5
    for mutation, expected_class in zip(
        mutations,
        [
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
        "left_id": left.identifier,
        "right_id": first_right.identifier,
    }

    assert mutations[1].model_dump() == {
        "left_id": left.identifier,
        "right_id": second_right.identifier,
    }

    assert isinstance(mutations[2], UpdateLeft)
    assert mutations[2].right_id == first_right.identifier
    assert mutations[2].left is left

    assert isinstance(mutations[3], UpdateRight)
    assert mutations[3].left_id == left.identifier
    assert mutations[3].right is second_right

    assert mutations[4].model_dump() == {
        "left_id": left.identifier,
        "right_id": first_right.identifier,
    }


def test_context_resets_mutations_and_retains_new_mutations() -> None:
    relation = OneToMany[int, UUID, LeftEntity, RightEntity]()
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
    relation = OneToMany[int, UUID, LeftEntity, RightEntity]()

    with pytest.raises(RuntimeError, match="operation failed"), relation:
        relation.unlink(7, uuid4())
        raise RuntimeError("operation failed")

    assert len(relation.mutations) == 1
    assert isinstance(relation.mutations[0], Unlink)


def test_entity_mutations_reject_non_entities() -> None:
    with pytest.raises(ValidationError):
        UpdateLeft(right_id=uuid4(), left=object())  # type: ignore

    with pytest.raises(ValidationError):
        UpdateRight(left_id=7, right=object())  # type: ignore
