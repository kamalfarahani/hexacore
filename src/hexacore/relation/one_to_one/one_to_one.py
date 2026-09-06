"""Collect mutations representing changes to one-to-one relations."""

from hexacore.entity import Entity

from ..base_relation import BaseRelation
from .mutations import (
    Create,
    Unlink,
    UpdateLeft,
    UpdateRight,
)


class OneToOne[L_ID, R_ID, L: Entity, R: Entity](BaseRelation):
    """Collect changes to a one-to-one relation between two entities.

    Methods record mutations for later processing. They do not apply the
    represented changes.
    """

    def create(self, left_id: L_ID, right_id: R_ID) -> None:
        """Record a mutation that links the specified entities.

        Args:
            left_id: Identifier of the left entity to link.
            right_id: Identifier of the right entity to link.
        """
        self.add_mutation(
            Create[L_ID, R_ID](
                left_id=left_id,
                right_id=right_id,
            )
        )

    def update_left(self, right_id: R_ID, left: L) -> None:
        """Record a mutation that changes the left entity in the relation.

        Args:
            right_id: Identifier of the right entity used to locate the left entity.
            left: Entity supplied for the left-side update.
        """
        self.add_mutation(
            UpdateLeft[R_ID, L](
                right_id=right_id,
                left=left,
            )
        )

    def update_right(self, left_id: L_ID, right: R) -> None:
        """Record a mutation that changes the right entity in the relation.

        Args:
            left_id: Identifier of the left entity used to locate the right entity.
            right: Entity supplied for the right-side update.
        """
        self.add_mutation(
            UpdateRight[L_ID, R](
                left_id=left_id,
                right=right,
            )
        )

    def unlink(self, left_id: L_ID, right_id: R_ID) -> None:
        """Record a mutation that removes the link between the specified entities.

        Args:
            left_id: Identifier of the left entity to unlink.
            right_id: Identifier of the right entity to unlink.
        """
        self.add_mutation(
            Unlink[L_ID, R_ID](
                left_id=left_id,
                right_id=right_id,
            )
        )
