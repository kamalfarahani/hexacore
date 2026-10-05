from hexacore.entity import Entity

from ..base_relation import BaseRelation
from .mutations import Create, Unlink, UpdateLeft, UpdateRight


class OneToMany[L_ID, R_ID, L: Entity, R: Entity](BaseRelation):
    """Represents a one-to-many relation between a left entity and multiple right entities."""

    @staticmethod
    def create_mutation(left_id: L_ID, right_id: R_ID) -> Create:
        """Build a mutation that links one right entity to a left entity.

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
        """Build a mutation that changes one right entity in the relation.

        Args:
            left_id: Identifier of the left entity associated with the right entity.
            right: Entity supplied for the update, with its identifier selecting
                the right entity within the relation.

        Returns:
            The mutation describing the right-side update.
        """
        return UpdateRight[L_ID, R](
            left_id=left_id,
            right=right,
        )

    @staticmethod
    def unlink_mutation(left_id: L_ID, right_id: R_ID) -> Unlink[L_ID, R_ID]:
        """Build a mutation that removes one link between the specified entities.

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
