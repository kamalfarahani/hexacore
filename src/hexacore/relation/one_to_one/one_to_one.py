"""Build mutations representing changes to one-to-one relations."""

from hexacore.entity import Entity

from ..base_relation import BaseRelation
from .mutations import (
    Create,
    Unlink,
    UpdateLeft,
    UpdateRight,
)


class OneToOne[L_ID, R_ID, L: Entity, R: Entity](BaseRelation):
    """Represent a one-to-one relation between a left and a right entity."""

    @staticmethod
    def create_mutation(left_id: L_ID, right_id: R_ID) -> Create:
        """Build a mutation that links the specified entities.

        Args:
            left_id: Identifier of the left entity to link.
            right_id: Identifier of the right entity to link.

        Returns:
            The mutation describing the new link.
        """
        return Create[L_ID, R_ID](
            left_id=left_id,
            right_id=right_id,
        )

    @staticmethod
    def update_left_mutation(right_id: R_ID, left: L) -> UpdateLeft:
        """Build a mutation that changes the left entity in the relation.

        Args:
            right_id: Identifier of the right entity used to locate the left entity.
            left: Entity supplied for the left-side update.

        Returns:
            The mutation describing the left-side update.
        """
        return UpdateLeft[R_ID, L](
            right_id=right_id,
            left=left,
        )

    @staticmethod
    def update_right_mutation(left_id: L_ID, right: R) -> UpdateRight[L_ID, R]:
        """Build a mutation that changes the right entity in the relation.

        Args:
            left_id: Identifier of the left entity used to locate the right entity.
            right: Entity supplied for the right-side update.

        Returns:
            The mutation describing the right-side update.
        """
        return UpdateRight[L_ID, R](
            left_id=left_id,
            right=right,
        )

    @staticmethod
    def unlink_mutation(left_id: L_ID, right_id: R_ID) -> Unlink[L_ID, R_ID]:
        """Build a mutation that removes the link between the specified entities.

        Args:
            left_id: Identifier of the left entity to unlink.
            right_id: Identifier of the right entity to unlink.

        Returns:
            The mutation describing the link removal.
        """
        return Unlink[L_ID, R_ID](
            left_id=left_id,
            right_id=right_id,
        )
