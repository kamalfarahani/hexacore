"""Build mutations representing changes to one-to-one relations."""

from katharos.types import ImmutableList

from hexacore.entity import Entity

from ..base_relation import BaseRelation
from ..base_relation_mutation import BaseRelationMutation
from .mutations import (
    CreateMutation,
    UnlinkMutation,
    UpdateLeftMutation,
    UpdateRightMutation,
)


class OneToOne[L_ID, R_ID, L: Entity, R: Entity](BaseRelation):
    """Represent a one-to-one relation between a left and a right entity."""

    CreateMutation = CreateMutation
    UnlinkMutation = UnlinkMutation
    UpdateLeftMutation = UpdateLeftMutation
    UpdateRightMutation = UpdateRightMutation

    def supported_mutations(self) -> ImmutableList[type[BaseRelationMutation]]:
        """Return the mutation classes supported by this relation.

        Returns:
            The create, left-update, right-update, and unlink mutation classes.
        """
        return ImmutableList[type[BaseRelationMutation]](
            [CreateMutation, UpdateLeftMutation, UpdateRightMutation, UnlinkMutation]
        )

    @staticmethod
    def create_mutation(left_id: L_ID, right_id: R_ID) -> CreateMutation:
        """Build a mutation that links the specified entities.

        Args:
            left_id: Identifier of the left entity to link.
            right_id: Identifier of the right entity to link.

        Returns:
            The mutation describing the new link.
        """
        return CreateMutation[L_ID, R_ID](
            left_id=left_id,
            right_id=right_id,
        )

    @staticmethod
    def update_left_mutation(right_id: R_ID, left: L) -> UpdateLeftMutation:
        """Build a mutation that changes the left entity in the relation.

        Args:
            right_id: Identifier of the right entity used to locate the left entity.
            left: Entity supplied for the left-side update.

        Returns:
            The mutation describing the left-side update.
        """
        return UpdateLeftMutation[R_ID, L](
            right_id=right_id,
            left=left,
        )

    @staticmethod
    def update_right_mutation(left_id: L_ID, right: R) -> UpdateRightMutation[L_ID, R]:
        """Build a mutation that changes the right entity in the relation.

        Args:
            left_id: Identifier of the left entity used to locate the right entity.
            right: Entity supplied for the right-side update.

        Returns:
            The mutation describing the right-side update.
        """
        return UpdateRightMutation[L_ID, R](
            left_id=left_id,
            right=right,
        )

    @staticmethod
    def unlink_mutation(left_id: L_ID, right_id: R_ID) -> UnlinkMutation[L_ID, R_ID]:
        """Build a mutation that removes the link between the specified entities.

        Args:
            left_id: Identifier of the left entity to unlink.
            right_id: Identifier of the right entity to unlink.

        Returns:
            The mutation describing the link removal.
        """
        return UnlinkMutation[L_ID, R_ID](
            left_id=left_id,
            right_id=right_id,
        )
